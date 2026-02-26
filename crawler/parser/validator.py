"""Data validator for parsed results."""

from typing import Dict, Any, List, Optional, Tuple


class DataValidator:
    """
    Validates parsed data against business rules.
    
    Validations:
    - Required fields
    - Field formats (regex patterns)
    - Value ranges
    - Custom validation functions
    """

    def __init__(self):
        self.validators = {
            "required": self._validate_required,
            "pattern": self._validate_pattern,
            "min_length": self._validate_min_length,
            "max_length": self._validate_max_length,
            "min_value": self._validate_min_value,
            "max_value": self._validate_max_value,
            "enum": self._validate_enum,
            "email": self._validate_email,
            "url": self._validate_url,
            "phone": self._validate_phone,
        }

    def validate(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against rules.
        
        Args:
            data: Data to validate
            rules: Validation rules
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required fields
        required_fields = rules.get("required", [])
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"Missing required field: {field}")

        # Check field-specific rules
        field_rules = rules.get("fields", {})
        for field, field_config in field_rules.items():
            if not isinstance(field_config, dict):
                continue

            value = data.get(field)
            if value is None:
                continue  # Skip validation, required check handles this

            # Apply each validation rule
            for rule_name, rule_value in field_config.items():
                validator = self.validators.get(rule_name)
                if validator:
                    is_valid, error = validator(field, value, rule_value)
                    if not is_valid and error:
                        errors.append(error)

        is_valid = len(errors) == 0
        return is_valid, errors

    # === Validation Methods ===

    def _validate_required(
        self,
        field: str,
        value: Any,
        rule: bool,
    ) -> Tuple[bool, Optional[str]]:
        """Validate required field."""
        if rule and (value is None or value == ""):
            return False, f"Field '{field}' is required"
        return True, None

    def _validate_pattern(
        self,
        field: str,
        value: Any,
        pattern: str,
    ) -> Tuple[bool, Optional[str]]:
        """Validate field matches regex pattern."""
        import re
        if not re.match(pattern, str(value)):
            return False, f"Field '{field}' does not match pattern"
        return True, None

    def _validate_min_length(
        self,
        field: str,
        value: Any,
        min_len: int,
    ) -> Tuple[bool, Optional[str]]:
        """Validate minimum length."""
        if len(str(value)) < min_len:
            return False, f"Field '{field}' must be at least {min_len} characters"
        return True, None

    def _validate_max_length(
        self,
        field: str,
        value: Any,
        max_len: int,
    ) -> Tuple[bool, Optional[str]]:
        """Validate maximum length."""
        if len(str(value)) > max_len:
            return False, f"Field '{field}' must be at most {max_len} characters"
        return True, None

    def _validate_min_value(
        self,
        field: str,
        value: Any,
        min_val: float,
    ) -> Tuple[bool, Optional[str]]:
        """Validate minimum value."""
        try:
            if float(value) < min_val:
                return False, f"Field '{field}' must be at least {min_val}"
        except (ValueError, TypeError):
            return False, f"Field '{field}' must be a number"
        return True, None

    def _validate_max_value(
        self,
        field: str,
        value: Any,
        max_val: float,
    ) -> Tuple[bool, Optional[str]]:
        """Validate maximum value."""
        try:
            if float(value) > max_val:
                return False, f"Field '{field}' must be at most {max_val}"
        except (ValueError, TypeError):
            return False, f"Field '{field}' must be a number"
        return True, None

    def _validate_enum(
        self,
        field: str,
        value: Any,
        allowed: List[Any],
    ) -> Tuple[bool, Optional[str]]:
        """Validate value is in allowed list."""
        if value not in allowed:
            return False, f"Field '{field}' must be one of: {allowed}"
        return True, None

    def _validate_email(
        self,
        field: str,
        value: Any,
        rule: bool,
    ) -> Tuple[bool, Optional[str]]:
        """Validate email format."""
        import re
        if rule:
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(pattern, str(value)):
                return False, f"Field '{field}' must be a valid email"
        return True, None

    def _validate_url(
        self,
        field: str,
        value: Any,
        rule: bool,
    ) -> Tuple[bool, Optional[str]]:
        """Validate URL format."""
        import re
        if rule:
            pattern = r"^https?://[^\s]+$"
            if not re.match(pattern, str(value)):
                return False, f"Field '{field}' must be a valid URL"
        return True, None

    def _validate_phone(
        self,
        field: str,
        value: Any,
        rule: bool,
    ) -> Tuple[bool, Optional[str]]:
        """Validate phone number format."""
        import re
        if rule:
            # Simple phone validation - digits, spaces, dashes, parens, plus
            pattern = r"^[\d\s\-\(\)\+]+$"
            if not re.match(pattern, str(value)):
                return False, f"Field '{field}' must be a valid phone number"
        return True, None
