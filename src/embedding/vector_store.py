"""
vector_store.py
===============

ChromaDB 래퍼 – Final Engine 전용
* 프로젝트별 벡터 DB 경로 관리
* scene 임베딩 저장 / 유사도 검색
"""

from __future__ import annotations

import gc
import json
import os
from pathlib import Path
from typing import Any, List, Tuple

import chromadb
from chromadb.config import Settings

from src.embedding.embedder import embed_scene
from src.utils.path_helper import data_path

__all__ = ["VectorStore"]


class VectorStore:
    """
    프로젝트 단위 Scene 임베딩 저장소.

    Parameters
    ----------
    project : str, optional
        프로젝트 ID (기본값 ``"default"``)
    test_mode : bool, optional
        • ``True``  → 메모리 DB(in‑memory) 사용 – 단위테스트 용도  
        • ``False`` → Persistent DB(Chroma SQLite) 사용
    """

    def __init__(self, project: str = "default", *, test_mode: bool = False) -> None:
        # -------- 기본 설정 --------
        self.project: str = project
        # 환경변수(UNIT_TEST_MODE)와 인자 두 가지를 모두 허용
        env_test = os.getenv("UNIT_TEST_MODE") == "1"
        self.test_mode: bool = test_mode or env_test

        # 임베딩/DB 경로 설정 불러오기
        self.config: dict[str, Any] = self._load_config()

        # -------- Chroma 클라이언트/컬렉션 --------
        if self.test_mode:
            # 메모리 전용 클라이언트 (파일 락 우려 無)
            self.client = chromadb.Client()
        else:
            db_path = self._get_db_path()
            self.client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(anonymized_telemetry=False),
            )

        # 컬렉션 생성 or 조회
        self.collection = self.client.get_or_create_collection(
            name=f"scenes_{self.project}",
            metadata={"hnsw:space": "cosine"},
        )

        # 내부 카운터 – test_mode일 땐 직접 관리(쿼리 속도 절약)
        self._count: int = (
            0 if self.test_mode else self.collection.count()
        )

    # --------------------------------------------------------------------- #
    # 내부 유틸
    # --------------------------------------------------------------------- #
    def _load_config(self) -> dict[str, Any]:
        """embedding_config.json 로드 (없으면 기본값 생성)."""
        cfg_path = data_path("embedding_config.json", self.project)

        default_cfg = {
            "model": "text-embedding-3-small",
            "chroma_path": f"projects/{self.project}/db",
        }

        if not cfg_path.exists():
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(default_cfg, f, indent=2)
            return default_cfg

        try:
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
            cfg.setdefault("model", default_cfg["model"])
            cfg.setdefault("chroma_path", default_cfg["chroma_path"])
            return cfg
        except (json.JSONDecodeError, OSError):
            # 손상 시 기본값으로 복구
            return default_cfg

    def _get_db_path(self) -> Path:
        """프로젝트별 ChromaDB 경로(Path 객체) 반환."""
        chroma_path = self.config["chroma_path"].replace("{id}", self.project)

        if not os.path.isabs(chroma_path):
            chroma_path = Path("projects") / self.project / "db"
        else:
            chroma_path = Path(chroma_path)

        chroma_path.mkdir(parents=True, exist_ok=True)
        return chroma_path

    # --------------------------------------------------------------------- #
    # 공용 API
    # --------------------------------------------------------------------- #
    def add(self, scene_id: str, text: str, metadata: dict | None = None) -> bool:
        """
        Scene 임베딩 추가.

        Returns
        -------
        bool
            성공 여부
        """
        if not text or not text.strip():
            return False

        try:
            # 임베딩 생성 (FAST_MODE or UNIT_TEST_MODE시 embedder가 dummy 벡터 반환)
            embedding: List[float] = embed_scene(text, self.config["model"])

            # 중복 ID 덮어쓰기 대비 → upsert 사용
            if hasattr(self.collection, "upsert"):
                self.collection.upsert(
                    embeddings=[embedding],
                    documents=[text],
                    ids=[scene_id],
                    metadatas=[metadata] if metadata else None,
                )
            else:
                # 구버전 호환
                self.collection.add(
                    embeddings=[embedding],
                    documents=[text],
                    ids=[scene_id],
                    metadatas=[metadata] if metadata else None,
                )

            # 파일 DB라면 바로 flush
            if not self.test_mode and hasattr(self.collection, "persist"):
                self.collection.persist()

            # 카운트 업데이트
            self._count = (
                self._count + 1
                if self.test_mode
                else self.collection.count()
            )
            return True

        except Exception:
            return False

    # ------------------------------------------------------------------ #
    def similar(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        코사인 유사도 기준 scene 검색.

        Notes
        -----
        * 빈 컬렉션일 경우 **빈 리스트** 반환 (예외 아님).
        """
        if not query or top_k <= 0:
            return []

        try:
            query_vec = embed_scene(query, self.config["model"])
            n_results = min(top_k, self.count())
            if n_results == 0:
                return []

            results = self.collection.query(
                query_embeddings=[query_vec],
                n_results=n_results,
            )

            ids = results.get("ids", [[]])[0]
            dists = results.get("distances", [[]])[0]
            sims = [1.0 - d for d in dists]
            return list(zip(ids, sims, strict=False))
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    def count(self) -> int:
        """저장된 scene 개수."""
        return self._count if self.test_mode else self.collection.count()

    # ------------------------------------------------------------------ #
    def clear(self) -> bool:
        """모든 임베딩 삭제."""
        try:
            self.client.delete_collection(f"scenes_{self.project}")
            self.collection = self.client.get_or_create_collection(
                name=f"scenes_{self.project}",
                metadata={"hnsw:space": "cosine"},
            )
            self._count = 0
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # Context / cleanup
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "VectorStore":  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        self.close()

    def close(self) -> None:
        """
        리소스 해제 – 윈도우 파일 락 방지.

        * 컬렉션 persist → 클라이언트 reset → 레퍼런스 제거 → GC
        """
        try:
            if self.collection is not None and hasattr(self.collection, "persist"):
                self.collection.persist()

            if isinstance(self.client, chromadb.PersistentClient):
                # 0.4.x 이상: reset() 존재 → 연결 종료 & 락 해제
                if hasattr(self.client, "reset"):
                    self.client.reset()

            # 참조 끊고 GC
            self.collection = None
            self.client = None
            gc.collect()
        except Exception:
            pass

    def __del__(self) -> None:  # noqa: D401
        self.close()
