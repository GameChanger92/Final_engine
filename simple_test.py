#!/usr/bin/env python3
"""
간단한 임베딩 테스트 스크립트
"""

import sys
from unittest.mock import MagicMock, patch

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, "/workspaces/Final_engine")

try:
    from src.embedding.embedder import embed_scene

    print("✅ embedder 모듈 import 성공")
except ImportError as e:
    print(f"❌ embedder 모듈 import 실패: {e}")
    sys.exit(1)


def test_priority():
    """UNIT_TEST_MODE가 FAST_MODE보다 우선되는지 테스트"""
    print("\n테스트: UNIT_TEST_MODE 우선순위")

    # Mock OpenAI 응답
    with patch("openai.OpenAI") as mock_openai:
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # UNIT_TEST_MODE=1, FAST_MODE=1로 설정 (UNIT_TEST_MODE가 우선해야 함)
        with patch.dict(
            "os.environ", {"OPENAI_API_KEY": "test-key", "UNIT_TEST_MODE": "1", "FAST_MODE": "1"}
        ):
            result = embed_scene("test text")

            if result == [0.1, 0.2, 0.3]:
                print("✅ PASS: UNIT_TEST_MODE가 FAST_MODE보다 우선됨")
                return True
            else:
                print(f"❌ FAIL: 예상 [0.1, 0.2, 0.3], 실제 {result}")
                return False


def test_fast_mode():
    """FAST_MODE에서 더미 벡터 반환 테스트"""
    print("\n테스트: FAST_MODE 더미 벡터")

    with patch.dict(
        "os.environ", {"OPENAI_API_KEY": "test-key", "UNIT_TEST_MODE": "0", "FAST_MODE": "1"}
    ):
        result = embed_scene("test text")

        if len(result) == 1536 and result[0] == 0.1:
            print("✅ PASS: FAST_MODE에서 더미 벡터 반환")
            return True
        else:
            print(
                f"❌ FAIL: 예상 길이 1536, 첫 값 0.1, 실제 길이 {len(result)}, 첫 값 {result[0] if result else 'None'}"
            )
            return False


def test_no_api_key():
    """API 키 없을 때 더미 벡터 반환 테스트"""
    print("\n테스트: API 키 없음")

    with patch.dict("os.environ", {"UNIT_TEST_MODE": "0", "FAST_MODE": "0"}, clear=True):
        result = embed_scene("test text")

        if len(result) == 1536 and result[0] == 0.1:
            print("✅ PASS: API 키 없을 때 더미 벡터 반환")
            return True
        else:
            print(
                f"❌ FAIL: 예상 길이 1536, 첫 값 0.1, 실제 길이 {len(result)}, 첫 값 {result[0] if result else 'None'}"
            )
            return False


if __name__ == "__main__":
    print("임베딩 수정 사항 테스트 시작")

    results = [test_priority(), test_fast_mode(), test_no_api_key()]

    passed = sum(results)
    total = len(results)

    print("\n=== 테스트 결과 ===")
    print(f"통과: {passed}/{total}")

    if passed == total:
        print("🎉 모든 테스트 통과! 수정이 성공적으로 완료되었습니다.")
    else:
        print("⚠️ 일부 테스트 실패. 추가 수정이 필요합니다.")
