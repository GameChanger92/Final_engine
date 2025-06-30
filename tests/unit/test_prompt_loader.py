"""
Tests for prompt_loader.py module
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.prompt_loader import load_style, get_available_platforms


class TestLoadStyle:
    """Test cases for load_style function."""
    
    def test_load_style_munpia_platform(self):
        """Test loading munpia platform style configuration."""
        style = load_style("munpia")
        
        assert isinstance(style, dict)
        assert style["platform"] == "munpia"
        assert style["tone"] == "대사 중심 경쾌"
        assert style["voice_main"] == "3인칭 관찰자"
        assert style["voice_side"] == "감정 몰입형"
        assert style["enter_rule"] == "액션마다 줄바꿈"
        assert "prompt_suffix" in style
    
    def test_load_style_kakao_platform(self):
        """Test loading kakao platform style configuration."""
        style = load_style("kakao")
        
        assert isinstance(style, dict)
        assert style["platform"] == "kakao"
        assert style["tone"] == "정서적 깊이감"
        assert style["voice_main"] == "1인칭 내레이터"
        assert style["voice_side"] == "심리 묘사형"
        assert style["enter_rule"] == "장면전환시 줄바꿈"
        assert "prompt_suffix" in style
    
    def test_load_style_default_from_env(self, monkeypatch):
        """Test loading style using PLATFORM environment variable."""
        monkeypatch.setenv("PLATFORM", "munpia")
        
        style = load_style()  # No platform parameter
        
        assert style["platform"] == "munpia"
        assert style["tone"] == "대사 중심 경쾌"
    
    def test_load_style_nonexistent_platform_returns_default(self):
        """Test that requesting non-existent platform returns munpia default."""
        style = load_style("nonexistent_platform")
        
        # Should fall back to munpia
        assert isinstance(style, dict)
        assert style["platform"] == "munpia"
        assert style["tone"] == "대사 중심 경쾌"
    
    def test_load_style_with_corrupted_json_file(self, monkeypatch):
        """Test behavior when JSON file is corrupted."""
        # Create a temporary corrupted JSON file
        with tempfile.TemporaryDirectory() as temp_dir:
            style_configs_dir = Path(temp_dir) / "templates" / "style_configs"
            style_configs_dir.mkdir(parents=True)
            
            corrupted_file = style_configs_dir / "corrupted.json"
            with open(corrupted_file, "w") as f:
                f.write("{ invalid json content")
            
            # Mock the style configs directory path
            def mock_path():
                return Path(temp_dir) / "templates" / "style_configs"
            
            with patch("src.prompt_loader.Path") as mock_path_class:
                mock_path_class.return_value.parent.parent = Path(temp_dir)
                
                style = load_style("corrupted")
                
                # Should fall back to munpia or hardcoded default
                assert isinstance(style, dict)
                assert "platform" in style
                assert "tone" in style
    
    def test_load_style_hardcoded_fallback(self):
        """Test that hardcoded fallback is used when all files fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the style configs directory to point to empty temp directory
            with patch("src.prompt_loader.Path") as mock_path_class:
                mock_path_class.return_value.parent.parent = Path(temp_dir)
                
                style = load_style("any_platform")
                
                # Should use hardcoded fallback
                assert style["platform"] == "default"
                assert style["tone"] == "균형 잡힌"
                assert style["voice_main"] == "3인칭 관찰자"
                assert style["voice_side"] == "표준형"
                assert style["enter_rule"] == "문단별 줄바꿈"
                assert style["prompt_suffix"] == "일반적인 소설 형식으로 작성해주세요."
    
    def test_load_style_env_fallback_to_munpia(self, monkeypatch):
        """Test that missing PLATFORM env var defaults to munpia."""
        monkeypatch.delenv("PLATFORM", raising=False)
        
        style = load_style()
        
        # Should default to munpia
        assert style["platform"] == "munpia"
        assert style["tone"] == "대사 중심 경쾌"


class TestGetAvailablePlatforms:
    """Test cases for get_available_platforms function."""
    
    def test_get_available_platforms_returns_list(self):
        """Test that function returns a list of available platforms."""
        platforms = get_available_platforms()
        
        assert isinstance(platforms, list)
        assert "munpia" in platforms
        assert "kakao" in platforms
        assert len(platforms) >= 2
    
    def test_get_available_platforms_sorted(self):
        """Test that platforms are returned in sorted order."""
        platforms = get_available_platforms()
        
        assert platforms == sorted(platforms)
    
    def test_get_available_platforms_empty_directory(self):
        """Test behavior when style_configs directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.prompt_loader.Path") as mock_path_class:
                mock_path_class.return_value.parent.parent = Path(temp_dir)
                
                platforms = get_available_platforms()
                
                assert platforms == []


class TestIntegration:
    """Integration tests for prompt_loader functionality."""
    
    def test_style_switching_via_environment(self, monkeypatch):
        """Test that changing PLATFORM env var switches styles correctly."""
        # Test munpia
        monkeypatch.setenv("PLATFORM", "munpia")
        munpia_style = load_style()
        assert munpia_style["platform"] == "munpia"
        assert munpia_style["tone"] == "대사 중심 경쾌"
        
        # Test kakao
        monkeypatch.setenv("PLATFORM", "kakao")
        kakao_style = load_style()
        assert kakao_style["platform"] == "kakao"
        assert kakao_style["tone"] == "정서적 깊이감"
        
        # Verify they are different
        assert munpia_style["tone"] != kakao_style["tone"]
        assert munpia_style["voice_main"] != kakao_style["voice_main"]
    
    def test_all_required_fields_present(self):
        """Test that all required style fields are present in configurations."""
        required_fields = ["platform", "tone", "voice_main", "voice_side", "enter_rule", "prompt_suffix"]
        
        for platform in ["munpia", "kakao"]:
            style = load_style(platform)
            for field in required_fields:
                assert field in style, f"Missing field '{field}' in {platform} style"
                assert style[field] is not None, f"Field '{field}' is None in {platform} style"
                assert isinstance(style[field], str), f"Field '{field}' is not string in {platform} style"