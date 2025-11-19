"""
Unit tests for AI Schedule Service.

This module contains tests for the AIScheduleService class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.services.ai_schedule_service import AIScheduleService


class TestAIScheduleServiceInitialization:
    """Tests for AIScheduleService initialization."""
    
    def test_initialization_without_api_key(self):
        """Test service initializes correctly without API key."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": None,
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            service = AIScheduleService()
            
            assert service.api_key is None
            assert service.model == "gpt-4o-mini"
            assert not service.is_available()
    
    def test_initialization_with_api_key(self):
        """Test service initializes correctly with API key."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                service = AIScheduleService()
                
                assert service.api_key == "sk-test-key"
                assert service.model == "gpt-4o-mini"
                assert service.max_tokens == 2000
                assert service.temperature == 0.1
    
    def test_get_model_info(self):
        """Test getting model information."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test-key",
                "model": "gpt-4o",
                "max_tokens": 3000,
                "temperature": 0.2
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                service = AIScheduleService()
                info = service.get_model_info()
                
                assert info["model"] == "gpt-4o"
                assert info["max_tokens"] == 3000
                assert info["temperature"] == 0.2


class TestInputValidation:
    """Tests for input validation."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                service = AIScheduleService()
                service.client = MagicMock()
                return service
    
    def test_description_too_short(self, service):
        """Test rejection of too-short descriptions."""
        result = service.parse_schedule_description(
            description="Too short",
            existing_period_labels=["Off-Peak", "Peak"],
            num_periods=2
        )
        
        assert not result["success"]
        assert "too short" in result["error"].lower()
    
    def test_description_too_long(self, service):
        """Test rejection of too-long descriptions."""
        long_description = "x" * 2001
        result = service.parse_schedule_description(
            description=long_description,
            existing_period_labels=["Off-Peak", "Peak"],
            num_periods=2
        )
        
        assert not result["success"]
        assert "too long" in result["error"].lower()
    
    def test_invalid_num_periods(self, service):
        """Test rejection of invalid number of periods."""
        result = service.parse_schedule_description(
            description="This is a valid length description about rate schedules.",
            existing_period_labels=["Off-Peak"],
            num_periods=0
        )
        
        assert not result["success"]
        assert "invalid" in result["error"].lower()
    
    def test_mismatched_labels_and_periods(self, service):
        """Test rejection when labels don't match period count."""
        result = service.parse_schedule_description(
            description="This is a valid length description about rate schedules.",
            existing_period_labels=["Off-Peak", "Peak"],
            num_periods=3
        )
        
        assert not result["success"]
        assert "doesn't match" in result["error"].lower()


class TestResponseValidation:
    """Tests for AI response validation."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                return AIScheduleService()
    
    def test_valid_response(self, service):
        """Test validation of a valid response."""
        response = {
            "weekday_schedule": [0] * 24,
            "weekend_schedule": [0] * 24,
            "period_mapping": {"peak": "On-Peak"},
            "confidence": 0.9,
            "explanation": "Test explanation"
        }
        
        error = service._validate_response(response, num_periods=2)
        assert error is None
    
    def test_missing_required_field(self, service):
        """Test rejection of response missing required fields."""
        response = {
            "weekday_schedule": [0] * 24,
            # Missing weekend_schedule
            "period_mapping": {},
            "confidence": 0.9,
            "explanation": "Test"
        }
        
        error = service._validate_response(response, num_periods=2)
        assert error is not None
        assert "missing" in error.lower()
    
    def test_invalid_schedule_length(self, service):
        """Test rejection of schedule with wrong length."""
        response = {
            "weekday_schedule": [0] * 20,  # Should be 24
            "weekend_schedule": [0] * 24,
            "period_mapping": {},
            "confidence": 0.9,
            "explanation": "Test"
        }
        
        error = service._validate_response(response, num_periods=2)
        assert error is not None
        assert "24 hours" in error
    
    def test_invalid_period_index(self, service):
        """Test rejection of invalid period indices."""
        response = {
            "weekday_schedule": [0, 1, 2, 3] + [0] * 20,  # Index 3 invalid for 2 periods
            "weekend_schedule": [0] * 24,
            "period_mapping": {},
            "confidence": 0.9,
            "explanation": "Test"
        }
        
        error = service._validate_response(response, num_periods=2)
        assert error is not None
        assert "Invalid period" in error
    
    def test_invalid_confidence(self, service):
        """Test rejection of invalid confidence values."""
        response = {
            "weekday_schedule": [0] * 24,
            "weekend_schedule": [0] * 24,
            "period_mapping": {},
            "confidence": 1.5,  # Invalid: > 1.0
            "explanation": "Test"
        }
        
        error = service._validate_response(response, num_periods=2)
        assert error is not None
        assert "confidence" in error.lower()


class TestCostEstimation:
    """Tests for cost estimation."""
    
    def test_estimate_cost_gpt4o_mini(self):
        """Test cost estimation for gpt-4o-mini."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test",
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                service = AIScheduleService()
                
                description = "Peak rates 4 PM to 9 PM" * 10  # ~250 chars
                cost = service.estimate_cost(description)
                
                assert cost > 0
                assert cost < 0.01  # Should be very cheap
    
    def test_estimate_cost_gpt4o(self):
        """Test cost estimation for gpt-4o."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test",
                "model": "gpt-4o",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                service = AIScheduleService()
                
                description = "Peak rates 4 PM to 9 PM" * 10
                cost = service.estimate_cost(description)
                
                assert cost > 0
                # GPT-4o should be more expensive than mini
                # (though we can't directly compare without both instances)


class TestPromptBuilding:
    """Tests for prompt building."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with patch('src.services.ai_schedule_service.openai'):
                return AIScheduleService()
    
    def test_system_prompt_contains_key_instructions(self, service):
        """Test system prompt contains essential instructions."""
        prompt = service._build_system_prompt()
        
        assert "TOU" in prompt or "Time-of-Use" in prompt
        assert "24" in prompt  # Hours
        assert "JSON" in prompt
        assert "weekday_schedule" in prompt
        assert "weekend_schedule" in prompt
    
    def test_user_prompt_includes_context(self, service):
        """Test user prompt includes all necessary context."""
        description = "Peak rates from 4 PM to 9 PM"
        labels = ["Off-Peak", "On-Peak"]
        num_periods = 2
        
        prompt = service._build_user_prompt(description, labels, num_periods)
        
        assert description in prompt
        assert "Off-Peak" in prompt
        assert "On-Peak" in prompt
        assert "2" in prompt


class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        with patch('src.config.settings.Settings.get_openai_config') as mock_config:
            mock_config.return_value = {
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            # Mock the openai module
            with patch('src.services.ai_schedule_service.openai') as mock_openai:
                service = AIScheduleService()
                service.openai = mock_openai
                service.client = MagicMock()
                return service
    
    def test_handles_api_error(self, service):
        """Test handling of OpenAI API errors."""
        from openai import APIError
        
        service.openai.APIError = APIError
        service.client.chat.completions.create.side_effect = APIError("API Error", response=Mock(), body={})
        
        result = service.parse_schedule_description(
            description="Valid description about peak rates from 4 PM to 9 PM on weekdays",
            existing_period_labels=["Off-Peak", "Peak"],
            num_periods=2
        )
        
        assert not result["success"]
        assert "API error" in result["error"]
    
    def test_handles_rate_limit_error(self, service):
        """Test handling of rate limit errors."""
        from openai import RateLimitError
        
        service.openai.RateLimitError = RateLimitError
        service.client.chat.completions.create.side_effect = RateLimitError("Rate limit", response=Mock(), body={})
        
        result = service.parse_schedule_description(
            description="Valid description about peak rates from 4 PM to 9 PM on weekdays",
            existing_period_labels=["Off-Peak", "Peak"],
            num_periods=2
        )
        
        assert not result["success"]
        assert "rate limit" in result["error"].lower()
    
    def test_handles_connection_error(self, service):
        """Test handling of connection errors."""
        from openai import APIConnectionError
        
        service.openai.APIConnectionError = APIConnectionError
        service.client.chat.completions.create.side_effect = APIConnectionError("Connection failed")
        
        result = service.parse_schedule_description(
            description="Valid description about peak rates from 4 PM to 9 PM on weekdays",
            existing_period_labels=["Off-Peak", "Peak"],
            num_periods=2
        )
        
        assert not result["success"]
        assert "connection" in result["error"].lower()


class TestIntegration:
    """Integration tests (require actual API key)."""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Integration tests require --run-integration flag"
    )
    def test_real_api_call(self):
        """Test with real OpenAI API (requires valid API key)."""
        # This test is skipped by default and requires:
        # 1. Valid OpenAI API key in environment
        # 2. Running with: pytest --run-integration
        
        service = AIScheduleService()
        
        if not service.is_available():
            pytest.skip("OpenAI API key not configured")
        
        result = service.parse_schedule_description(
            description="Peak rates from 4 PM to 9 PM on weekdays. Off-Peak all other times including weekends.",
            existing_period_labels=["Off-Peak", "On-Peak"],
            num_periods=2
        )
        
        assert result["success"]
        assert len(result["weekday_schedule"]) == 24
        assert len(result["weekend_schedule"]) == 24
        assert result["confidence"] > 0.5
        
        # Check that peak hours (16-20) are assigned to period 1
        for hour in range(16, 21):
            assert result["weekday_schedule"][hour] == 1
        
        # Check that weekend is all off-peak (period 0)
        assert all(p == 0 for p in result["weekend_schedule"])


def pytest_addoption(parser):
    """Add command-line option for integration tests."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require OpenAI API key"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API key)"
    )

