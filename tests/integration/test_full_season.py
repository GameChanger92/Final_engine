"""
test_full_season.py

Integration tests for the Full Season Runner.
Tests end-to-end functionality of episode batch processing and KPI reporting.
"""

import pytest
import time
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import modules we need to test
from scripts.run_full_season import (
    KPITracker, 
    run_episodes, 
    parse_episode_range, 
    check_single_episode_guards
)
from src.utils.report_writer import generate_season_report, validate_kpi_data


class TestFullSeasonRunner:
    """Integration test class for Full Season Runner."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.test_project = "test_full_season"
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up any test report files
        test_report = self.reports_dir / "season_KPI.html"
        if test_report.exists():
            test_report.unlink()
    
    def test_1_to_3_episodes_execution_and_html_generation(self):
        """Test 1: 1-3 episode execution → .html file generation confirmation."""
        # Run episodes 1-3
        kpi_tracker = run_episodes(1, 3, self.test_project)
        
        # Verify we got results
        summary = kpi_tracker.get_summary()
        assert summary['total_episodes'] == 3
        
        # Generate HTML report
        report_path = self.reports_dir / "season_KPI.html"
        generate_season_report(summary, report_path)
        
        # Verify HTML file was created
        assert report_path.exists(), "HTML report file should be created"
        
        # Verify file contains content
        content = report_path.read_text(encoding='utf-8')
        assert len(content) > 0, "HTML report should not be empty"
        assert "Final Engine" in content, "HTML should contain project title"
    
    def test_kpi_dict_keys_existence(self):
        """Test 2: KPI dict keys existence (avg_fun, avg_logic, guard_pass_rate, avg_chars)."""
        kpi_tracker = KPITracker()
        
        # Add some test data
        kpi_tracker.add_episode(1, 8.5, 8.2, True, 1500)
        kpi_tracker.add_episode(2, 7.8, 8.0, False, 1400)
        
        summary = kpi_tracker.get_summary()
        
        # Verify all required KPI keys exist
        required_keys = ['avg_fun', 'avg_logic', 'guard_pass_rate', 'avg_chars']
        for key in required_keys:
            assert key in summary, f"KPI summary should contain '{key}' key"
        
        # Verify values are reasonable
        assert 0 <= summary['avg_fun'] <= 10, "avg_fun should be between 0-10"
        assert 0 <= summary['avg_logic'] <= 10, "avg_logic should be between 0-10"
        assert 0 <= summary['guard_pass_rate'] <= 100, "guard_pass_rate should be between 0-100"
        assert summary['avg_chars'] >= 0, "avg_chars should be non-negative"
    
    def test_guard_pass_90_percent_no_errors(self):
        """Test 3: Guard PASS ≥ 90% when executed without errors."""
        kpi_tracker = KPITracker()
        
        # Simulate 10 episodes with 9 passing (90% pass rate)
        for i in range(1, 10):
            kpi_tracker.add_episode(i, 8.0, 8.0, True, 1500)
        kpi_tracker.add_episode(10, 6.0, 6.0, False, 1500)  # One failure
        
        summary = kpi_tracker.get_summary()
        
        # Verify high pass rate doesn't cause errors
        assert summary['guard_pass_rate'] == 90.0, "Should have exactly 90% pass rate"
        assert summary['total_episodes'] == 10, "Should process all episodes"
        assert summary['passed_episodes'] == 9, "Should have 9 passed episodes"
        assert summary['failed_episodes'] == 1, "Should have 1 failed episode"
    
    @patch('scripts.run_full_season.run_pipeline')
    @patch('scripts.run_full_season.check_single_episode_guards')
    def test_execution_time_under_30_seconds(self, mock_guards, mock_pipeline):
        """Test 4: Execution time < 30s (monkeypatch for LLM stub)."""
        # Mock pipeline to return quickly
        mock_pipeline.return_value = "Test episode content for performance testing"
        mock_guards.return_value = (True, 8.0, 8.0)  # All guards pass
        
        start_time = time.time()
        
        # Run 5 episodes (should be fast with mocked LLM)
        kpi_tracker = run_episodes(1, 5, self.test_project)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify execution time is reasonable
        assert execution_time < 30.0, f"Execution took {execution_time:.1f}s, should be < 30s"
        
        # Verify we processed all episodes
        summary = kpi_tracker.get_summary()
        assert summary['total_episodes'] == 5, "Should process all 5 episodes"
    
    def test_cli_argument_parsing(self):
        """Test 5: CLI argument parsing test."""
        # Test episode range parsing
        assert parse_episode_range("1-10") == (1, 10)
        assert parse_episode_range("5") == (5, 5)
        assert parse_episode_range("1,5,7") == (1, 7)  # Should take min-max
        
        # Test edge cases
        assert parse_episode_range("100-240") == (100, 240)
        assert parse_episode_range("42") == (42, 42)
        
        # Test invalid ranges (should raise errors)
        with pytest.raises(ValueError):
            parse_episode_range("invalid")
        
        with pytest.raises(ValueError):
            parse_episode_range("10-5")  # Invalid order should raise error
    
    def test_report_file_contains_table_tags(self):
        """Test 6: Report file content contains <table> tags."""
        # Create sample KPI data
        kpi_data = {
            'avg_fun': 8.2,
            'avg_logic': 8.1,
            'guard_pass_rate': 85.0,
            'avg_chars': 1500,
            'total_episodes': 20,
            'passed_episodes': 17,
            'failed_episodes': 3,
            'episode_details': [
                {'episode': 1, 'fun_score': 8.0, 'logic_score': 8.2, 'guard_passed': True, 'char_count': 1500},
                {'episode': 2, 'fun_score': 8.4, 'logic_score': 8.0, 'guard_passed': True, 'char_count': 1600},
            ]
        }
        
        # Generate HTML report
        report_path = self.reports_dir / "season_KPI.html"
        generate_season_report(kpi_data, report_path)
        
        # Read the report content
        content = report_path.read_text(encoding='utf-8')
        
        # Verify it contains <table> tags
        assert '<table' in content, "Report should contain <table> tags"
        assert '</table>' in content, "Report should contain closing </table> tags"
        assert 'summary-table' in content, "Report should contain table CSS class"
        
        # Verify it contains expected data
        assert '8.2' in content, "Report should contain fun score"
        assert '8.1' in content, "Report should contain logic score"
        assert '85' in content, "Report should contain pass rate"
    
    def test_kpi_tracker_functionality(self):
        """Additional test for KPI tracker edge cases."""
        tracker = KPITracker()
        
        # Test empty tracker
        summary = tracker.get_summary()
        assert summary['total_episodes'] == 0
        assert summary['avg_fun'] == 0.0
        assert summary['avg_logic'] == 0.0
        
        # Test single episode
        tracker.add_episode(1, 9.5, 8.8, True, 2000)
        summary = tracker.get_summary()
        assert summary['total_episodes'] == 1
        assert summary['avg_fun'] == 9.5
        assert summary['avg_logic'] == 8.8
        assert summary['guard_pass_rate'] == 100.0
        assert summary['avg_chars'] == 2000
    
    def test_validate_kpi_data_function(self):
        """Test the KPI data validation utility."""
        # Valid data
        valid_data = {
            'avg_fun': 8.0,
            'avg_logic': 8.0,
            'guard_pass_rate': 90.0,
            'avg_chars': 1500,
            'total_episodes': 10,
            'passed_episodes': 9,
            'failed_episodes': 1
        }
        assert validate_kpi_data(valid_data) == True
        
        # Invalid data (missing field)
        invalid_data = {
            'avg_fun': 8.0,
            'avg_logic': 8.0,
            # Missing other required fields
        }
        assert validate_kpi_data(invalid_data) == False
    
    def test_single_episode_guard_testing(self):
        """Test the single episode guard testing functionality."""
        # This should work even without API keys (uses fallback)
        all_passed, fun_score, logic_score = check_single_episode_guards(1, self.test_project)
        
        # Verify we get reasonable values
        assert isinstance(all_passed, bool)
        assert 1.0 <= fun_score <= 10.0, f"Fun score {fun_score} should be between 1-10"
        assert 1.0 <= logic_score <= 10.0, f"Logic score {logic_score} should be between 1-10"


if __name__ == "__main__":
    pytest.main([__file__])