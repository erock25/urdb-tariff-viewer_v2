"""
AI-powered schedule generation service using OpenAI API.

This module provides the AIScheduleService class for generating Time-of-Use (TOU)
energy schedules from natural language descriptions using OpenAI's GPT models.
"""

from typing import Dict, List, Any, Optional
import json
import time

from src.config.settings import Settings


class AIScheduleService:
    """
    Service for generating TOU schedules using AI.
    
    This service takes natural language descriptions of utility rate schedules
    and converts them into structured 24-hour schedules for weekdays and weekends.
    It uses OpenAI's API to parse and understand the schedule descriptions.
    
    Attributes:
        api_key (str): OpenAI API key
        model (str): OpenAI model to use (e.g., 'gpt-4o-mini', 'gpt-4o')
        max_tokens (int): Maximum tokens for API response
        temperature (float): Temperature for API calls (0.0-2.0)
    
    Example:
        >>> service = AIScheduleService()
        >>> if service.is_available():
        >>>     result = service.parse_schedule_description(
        >>>         "Peak rates 4PM-9PM weekdays...",
        >>>         ["Off-Peak", "Mid-Peak", "On-Peak"],
        >>>         3
        >>>     )
        >>>     if result["success"]:
        >>>         print(result["weekday_schedule"])
    """
    
    def __init__(self):
        """Initialize the AI service with configuration from Settings."""
        config = Settings.get_openai_config()
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4o-mini")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.1)
        
        # Only import and configure openai if we have an API key
        if self.api_key:
            try:
                import openai
                self.openai = openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                self.openai = None
                self.client = None
        else:
            self.openai = None
            self.client = None
    
    def is_available(self) -> bool:
        """
        Check if AI service is available.
        
        Returns:
            bool: True if OpenAI API is configured and available
        """
        return self.api_key is not None and self.client is not None
    
    def parse_schedule_description(
        self,
        description: str,
        existing_period_labels: List[str],
        num_periods: int
    ) -> Dict[str, Any]:
        """
        Parse natural language schedule description and generate schedules.
        
        This method takes a user's description of when different rate periods apply
        and generates two 24-hour schedules (weekday and weekend) with each hour
        assigned to a TOU period.
        
        Args:
            description: User's natural language description of the schedule
            existing_period_labels: List of period labels from Energy Rate Structure
            num_periods: Number of TOU periods defined
        
        Returns:
            Dict containing:
                - success (bool): Whether the generation was successful
                - weekday_schedule (List[int]): 24-hour weekday schedule (if success)
                - weekend_schedule (List[int]): 24-hour weekend schedule (if success)
                - period_mapping (Dict[str, str]): Detected to existing label mapping
                - confidence (float): Confidence score 0-1 (if success)
                - explanation (str): AI's explanation of the schedule
                - warnings (List[str]): Any warnings or assumptions made
                - error (str): Error message (if not success)
        
        Example:
            >>> result = service.parse_schedule_description(
            ...     "Peak rates 4PM-9PM weekdays, Off-Peak all other times",
            ...     ["Off-Peak", "On-Peak"],
            ...     2
            ... )
            >>> if result["success"]:
            ...     print(f"Weekday: {result['weekday_schedule']}")
            ...     print(f"Confidence: {result['confidence']:.0%}")
        """
        
        # Check if service is available
        if not self.is_available():
            return {
                "success": False,
                "error": "AI service is not available. Please configure OpenAI API key."
            }
        
        # Input validation
        if not description or len(description.strip()) < 20:
            return {
                "success": False,
                "error": "Description too short. Please provide more details (at least 20 characters)."
            }
        
        if len(description) > 2000:
            return {
                "success": False,
                "error": "Description too long. Please keep it under 2000 characters."
            }
        
        if num_periods < 1 or num_periods > 12:
            return {
                "success": False,
                "error": f"Invalid number of periods: {num_periods}. Must be between 1 and 12."
            }
        
        if len(existing_period_labels) != num_periods:
            return {
                "success": False,
                "error": f"Number of labels ({len(existing_period_labels)}) doesn't match periods ({num_periods})."
            }
        
        # Build the prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            description, existing_period_labels, num_periods
        )
        
        try:
            # Call OpenAI API with retry logic
            response = self._call_openai_with_retry(system_prompt, user_prompt)
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Validate response structure
            validation_error = self._validate_response(result, num_periods)
            if validation_error:
                return {
                    "success": False,
                    "error": f"AI response validation failed: {validation_error}"
                }
            
            return {
                "success": True,
                "weekday_schedule": result["weekday_schedule"],
                "weekend_schedule": result["weekend_schedule"],
                "period_mapping": result.get("period_mapping", {}),
                "confidence": result.get("confidence", 0.0),
                "explanation": result.get("explanation", ""),
                "warnings": result.get("warnings", [])
            }
            
        except self.openai.APIError as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}"
            }
        except self.openai.RateLimitError:
            return {
                "success": False,
                "error": "Rate limit exceeded. Please try again in a moment."
            }
        except self.openai.APIConnectionError:
            return {
                "success": False,
                "error": "Connection error. Please check your internet connection."
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse AI response. Please try again."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _call_openai_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3
    ):
        """
        Call OpenAI API with exponential backoff retry logic.
        
        Args:
            system_prompt: System prompt for the AI
            user_prompt: User prompt with the request
            max_retries: Maximum number of retry attempts
        
        Returns:
            OpenAI API response
        
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                return response
            
            except self.openai.RateLimitError:
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise
            
            except Exception:
                # For other exceptions, don't retry
                raise
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for OpenAI.
        
        Returns:
            str: System prompt defining the AI's role and output format
        """
        return """You are an expert at analyzing utility tariff rate schedules. 
Your task is to parse natural language descriptions of Time-of-Use (TOU) energy 
schedules and convert them into structured hourly schedules.

You will be given:
1. A natural language description of when different rate periods apply
2. A list of existing period labels (e.g., "Summer On-Peak", "Winter Off-Peak")
3. The number of TOU periods

Your job is to:
1. Parse the description to understand when each rate period applies
2. Match detected periods to the existing period labels (fuzzy matching is OK)
3. Generate two 24-hour schedules (one for weekday, one for weekend)
4. Each hour should be assigned a period number (0 to num_periods-1)
5. Provide a confidence score and explanation

Return your response as JSON with this EXACT structure:
{
  "weekday_schedule": [2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,0,0,0,0,0,1,1,2],
  "weekend_schedule": [2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],
  "period_mapping": {"off-peak": "Off-Peak", "mid-peak": "Mid-Peak", "peak": "Peak"},
  "confidence": 0.95,
  "explanation": "Detected 3 periods: Off-Peak (hours 0-6, 23), Mid-Peak (hours 7-15, 21-22), Peak (hours 16-20). Mid-Peak has two time windows: 7AM-4PM and 9PM-11PM. Peak is 4PM-9PM. Off-Peak is 11PM-7AM.",
  "warnings": []
}

CRITICAL: Both weekday_schedule and weekend_schedule arrays MUST have EXACTLY 24 elements (hours 0-23).

TIME CONVERSION RULES (memorize these):
- "7 AM to 4 PM" = hours [7,8,9,10,11,12,13,14,15] (9 hours)
- "4 PM to 9 PM" = hours [16,17,18,19,20] (5 hours)  
- "9 PM to 11 PM" = hours [21,22] (2 hours)
- "11 PM to 7 AM" = hours [23,0,1,2,3,4,5,6] (8 hours)
The END time is NEVER included in the range!

For the example above (EV Charging schedule):
- Position 0-6, 23 gets period 2 (Off-Peak)
- Position 7-15 gets period 1 (Mid-Peak)
- Position 16-20 gets period 0 (Peak)
- Position 21-22 gets period 1 (Mid-Peak again for split period)

SPLIT PERIODS: When a period has multiple time windows, use the SAME period number for BOTH.
Example: "Mid-Peak: 7AM-4PM and 9PM-11PM" means period 1 at BOTH positions [7-15] AND [21-22].

Important rules:
- Each hour represents 0-59 minutes of that hour (hour 16 = 4:00-4:59 PM)
- Always generate EXACTLY 24 values in each schedule array
- Use case-insensitive fuzzy matching for period names
- If weekend not mentioned, assume all off-peak
- Always return valid JSON"""

    def _build_user_prompt(
        self,
        description: str,
        existing_labels: List[str],
        num_periods: int
    ) -> str:
        """
        Build the user prompt with context.
        
        Args:
            description: User's schedule description
            existing_labels: List of existing period labels
            num_periods: Number of periods
        
        Returns:
            str: Formatted user prompt
        """
        labels_str = "\n".join([f"  Period {i}: {label}" 
                               for i, label in enumerate(existing_labels)])
        
        return f"""Please analyze this TOU schedule description and generate hourly schedules:

DESCRIPTION:
{description}

EXISTING PERIOD LABELS:
{labels_str}

NUMBER OF PERIODS: {num_periods}

Please generate the weekday and weekend schedules, matching the periods in the 
description to the existing period labels as closely as possible. Return your 
response as JSON following the specified structure."""

    def _validate_response(
        self,
        response: Dict[str, Any],
        num_periods: int
    ) -> Optional[str]:
        """
        Validate the AI response structure and values.
        
        Args:
            response: Parsed JSON response from AI
            num_periods: Expected number of periods
        
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        # Check required fields
        required_fields = [
            "weekday_schedule", "weekend_schedule", 
            "period_mapping", "confidence", "explanation"
        ]
        
        missing_fields = [f for f in required_fields if f not in response]
        if missing_fields:
            return f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate schedules
        weekday = response["weekday_schedule"]
        weekend = response["weekend_schedule"]
        
        if not isinstance(weekday, list):
            return "weekday_schedule must be a list"
        
        if len(weekday) != 24:
            return f"weekday_schedule must have 24 hours, got {len(weekday)}"
        
        if not isinstance(weekend, list):
            return "weekend_schedule must be a list"
        
        if len(weekend) != 24:
            return f"weekend_schedule must have 24 hours, got {len(weekend)}"
        
        # Check all values are valid period indices
        all_values = weekday + weekend
        for i, val in enumerate(all_values):
            if not isinstance(val, int):
                return f"Schedule value at index {i} is not an integer: {val}"
            if val < 0 or val >= num_periods:
                hour_type = "weekday" if i < 24 else "weekend"
                hour = i if i < 24 else i - 24
                return f"Invalid period {val} at {hour_type} hour {hour}. Must be 0-{num_periods-1}"
        
        # Validate confidence
        confidence = response.get("confidence", 0)
        if not isinstance(confidence, (int, float)):
            return f"Confidence must be a number, got {type(confidence)}"
        if not (0 <= confidence <= 1):
            return f"Confidence must be between 0 and 1, got {confidence}"
        
        # Validate period_mapping
        if not isinstance(response.get("period_mapping"), dict):
            return "period_mapping must be a dictionary"
        
        # Validate explanation
        if not isinstance(response.get("explanation"), str):
            return "explanation must be a string"
        
        return None  # All validations passed
    
    def estimate_cost(self, description: str) -> float:
        """
        Estimate the cost of processing a description.
        
        This provides a rough estimate based on token counts and model pricing.
        Actual costs may vary slightly.
        
        Args:
            description: The schedule description to estimate
        
        Returns:
            float: Estimated cost in USD
        """
        # Rough token estimation (1 token ≈ 4 characters)
        system_prompt_tokens = 500  # Approximate
        user_prompt_tokens = len(description) / 4 + 100
        input_tokens = system_prompt_tokens + user_prompt_tokens
        output_tokens = 500  # Max expected output
        
        # Pricing per 1K tokens (as of 2024)
        if "gpt-4o" in self.model and "mini" not in self.model:
            # GPT-4o pricing
            input_cost = input_tokens * 0.0025 / 1000
            output_cost = output_tokens * 0.01 / 1000
        elif "gpt-4o-mini" in self.model:
            # GPT-4o-mini pricing
            input_cost = input_tokens * 0.00015 / 1000
            output_cost = output_tokens * 0.0006 / 1000
        elif "gpt-4" in self.model:
            # GPT-4 pricing
            input_cost = input_tokens * 0.03 / 1000
            output_cost = output_tokens * 0.06 / 1000
        else:
            # GPT-3.5-turbo pricing (fallback)
            input_cost = input_tokens * 0.0005 / 1000
            output_cost = output_tokens * 0.0015 / 1000
        
        return input_cost + output_cost
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dict with model name, max_tokens, temperature, and availability
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "available": self.is_available()
        }

