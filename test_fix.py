#!/usr/bin/env python3
"""
임베딩 수정 사항을 테스트하기 위한 간단한 스크립트
"""

import os
import sys
from unittest.mock import MagicMock, patch

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, '/workspaces/Final_engine')

from src.embedding.embedder import embed_scene

def test_unit_test_mode_priority():
    """UNIT_TEST_MODE가 FAST_MODE보다 우선되는지 테스트"""
    print("테스트 1: UNIT_TEST_MODE가 FAST_MODE보다 우선되는지 확인")
    
    # Mock OpenAI 응답
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3]
    
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.dict("os.environ", {
            "OPENAI_API_KEY": "test-key",
            "UNIT_TEST_MODE": "1", 
            "FAST_MODE": "1"  # FAST_MODE도 켜져 있지만 UNIT_TEST_MODE가 우선해야 함
        }):
            result = embed_scene("test text")
            print(f"결과: {result}")
            
            if result == [0.1, 0.2, 0.3]:
                print("✅ 성공: UNIT_TEST_MODE가 FAST_MODE보다 우선됨")
                return True
            else:
                print(f"❌ 실패: 예상 [0.1, 0.2, 0.3], 실제 {result}")
                return False

def test_fast_mode_only():
    """FAST_MODE만 켜져 있을 때 더미 벡터 반환 테스트"""
    print("\n테스트 2: FAST_MODE만 켜져 있을 때 더미 벡터 반환")
    
    with patch.dict("os.environ", {
        "OPENAI_API_KEY": "test-key",
        "UNIT_TEST_MODE": "0", 
        "FAST_MODE": "1"
    }):
        result = embed_scene("test text")
        print(f"결과 길이: {len(result)}")
        print(f"첫 번째 값: {result[0] if result else 'None'}")
        
        if len(result) == 1536 and result[0] == 0.1:
            print("✅ 성공: FAST_MODE에서 더미 벡터 반환")
            return True
        else:
            print(f"❌ 실패: 예상 길이 1536, 첫 값 0.1, 실제 길이 {len(result)}, 첫 값 {result[0] if result else 'None'}")
            return False

if __name__ == "__main__":
    print("임베딩 수정 사항 테스트 시작\n")
    
    test1_result = test_unit_test_mode_priority()
    test2_result = test_fast_mode_only()
    
    print(f"\n테스트 결과:")
    print(f"테스트 1 (UNIT_TEST_MODE 우선순위): {'✅ 통과' if test1_result else '❌ 실패'}")
    print(f"테스트 2 (FAST_MODE 더미 반환): {'✅ 통과' if test2_result else '❌ 실패'}")
    
    if test1_result and test2_result:
        print("\n🎉 모든 테스트 통과! 수정이 성공적으로 완료되었습니다.")
    else:
        print("\n⚠️ 일부 테스트 실패. 추가 수정이 필요합니다.")
