"""
SDC Output Validator

Validator for SDC workload summary measurements against the SDC output schema.
Includes business logic checks beyond basic JSON schema validation.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import jsonschema
    from jsonschema import ValidationError
except ImportError:
    raise ImportError(
        "jsonschema library is required. Install with: pip install jsonschema"
    )


class SDCValidationError(Exception):
    """Custom exception for SDC validation errors."""
    pass


class SDCOutputValidator:
    """Validator for SDC workload summary output."""
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize validator with SDC output schema.
        
        Args:
            schema_path: Path to sdc_output_schema.json file.
                        Defaults to schema in same package.
        """
        if schema_path is None:
            # Default to schema in the same package
            current_dir = Path(__file__).parent.parent
            schema_path = current_dir / "schema" / "sdc_output_schema.json"
        
        self.schema_path = Path(schema_path)
        self._load_schema()
    
    def _load_schema(self):
        """Load and parse the SDC output schema."""
        try:
            with open(self.schema_path, 'r') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            raise SDCValidationError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise SDCValidationError(f"Invalid JSON in schema file: {e}")
    
    def validate_measurement(self, measurement: Dict[str, Any]) -> None:
        """
        Validate a single SDC measurement artifact.
        
        Args:
            measurement: Dictionary containing measurement data
            
        Raises:
            SDCValidationError: If validation fails
        """
        if not isinstance(measurement, dict):
            raise SDCValidationError("Measurement must be a dictionary")
        
        name = measurement.get("name")
        value = measurement.get("value")
        unit = measurement.get("unit")
        
        # Validate required fields
        if name is None:
            raise SDCValidationError("Measurement must have 'name' field")
        if "value" not in measurement:
            raise SDCValidationError("Measurement must have 'value' field")
        if unit is None:
            raise SDCValidationError("Measurement must have 'unit' field")
        
        # Validate specific SDC measurement types
        if name == "ttf_seconds":
            self._validate_ttf_seconds(value, unit)
        elif name == "repeatability_rate":
            self._validate_repeatability_rate(value, unit)
        elif name == "footprint_tax_percent":
            self._validate_footprint_tax_percent(value, unit)
        else:
            # Allow other measurement types (standard OCP measurements)
            pass
    
    def _validate_ttf_seconds(self, value: Any, unit: str) -> None:
        """Validate TTF (Time to Failure) measurement."""
        if unit != "s":
            raise SDCValidationError("ttf_seconds must have unit 's'")
        
        if value is not None:
            if not isinstance(value, (int, float)):
                raise SDCValidationError("ttf_seconds value must be a number or null")
            if value < 0:
                raise SDCValidationError("ttf_seconds value must be non-negative")
    
    def _validate_repeatability_rate(self, value: Any, unit: str) -> None:
        """Validate repeatability rate measurement."""
        if unit != "ratio":
            raise SDCValidationError("repeatability_rate must have unit 'ratio'")
        
        if value is not None:
            if not isinstance(value, (int, float)):
                raise SDCValidationError("repeatability_rate value must be a number or null")
            if not (0.0 <= value <= 1.0):
                raise SDCValidationError("repeatability_rate value must be between 0.0 and 1.0")
    
    def _validate_footprint_tax_percent(self, value: Any, unit: str) -> None:
        """Validate footprint tax measurement."""
        if unit != "%":
            raise SDCValidationError("footprint_tax_percent must have unit '%'")
        
        if value is not None:
            if not isinstance(value, (int, float)):
                raise SDCValidationError("footprint_tax_percent value must be a number or null")
            if value < 0.0:
                raise SDCValidationError("footprint_tax_percent value must be non-negative")
    
    def validate_workload_summary_step(self, test_step_start: Dict[str, Any]) -> None:
        """
        Validate a workload summary step metadata.
        
        Args:
            test_step_start: testStepStart artifact content
            
        Raises:
            SDCValidationError: If validation fails
        """
        if not isinstance(test_step_start, dict):
            raise SDCValidationError("testStepStart must be a dictionary")
        
        name = test_step_start.get("name")
        metadata = test_step_start.get("metadata", {})
        
        if not name:
            raise SDCValidationError("testStepStart must have 'name' field")
        
        # Check for SDC workload summary step type
        step_type = metadata.get("stepType")
        if step_type == "sdc-workload-summary":
            # Validate naming convention
            if not name.endswith("-summary"):
                raise SDCValidationError(
                    f"SDC workload summary step name must end with '-summary', got: {name}"
                )
            
            # Extract workload name and validate it
            workload_name = name.replace("-summary", "")
            if not workload_name:
                raise SDCValidationError("Workload name cannot be empty")
            
            # Basic workload name validation (alphanumeric, underscore, hyphen)
            if not all(c.isalnum() or c in "_-" for c in workload_name):
                raise SDCValidationError(
                    f"Workload name must contain only alphanumeric characters, underscores, and hyphens: {workload_name}"
                )
    
    def validate_workload_summary(self, content: Dict[str, Any]) -> None:
        """
        Validate complete workload summary content including business logic.
        
        Args:
            content: Full JSONL artifact content to validate
            
        Raises:
            SDCValidationError: If validation fails
        """
        if not isinstance(content, dict):
            raise SDCValidationError("Content must be a dictionary")
        
        # Check if this is a test step artifact
        test_step_artifact = content.get("testStepArtifact")
        if not test_step_artifact:
            return  # Not a test step artifact, skip validation
        
        # Validate testStepStart if present
        test_step_start = test_step_artifact.get("testStepStart")
        if test_step_start:
            self.validate_workload_summary_step(test_step_start)
        
        # Validate measurement if present
        measurement = test_step_artifact.get("measurement")
        if measurement:
            self.validate_measurement(measurement)
        
        # Validate common artifact fields
        self._validate_common_fields(content)
    
    def _validate_common_fields(self, content: Dict[str, Any]) -> None:
        """Validate common OCP artifact fields."""
        # Sequence number validation
        seq_num = content.get("sequenceNumber")
        if seq_num is not None:
            if not isinstance(seq_num, int) or seq_num < 0:
                raise SDCValidationError("sequenceNumber must be a non-negative integer")
        
        # Timestamp validation (basic format check)
        timestamp = content.get("timestamp")
        if timestamp is not None:
            if not isinstance(timestamp, str):
                raise SDCValidationError("timestamp must be a string")
            # Basic ISO format check
            if not timestamp.endswith("Z") and "T" not in timestamp:
                raise SDCValidationError("timestamp should be in ISO format")


def validate_workload_summary(content: Dict[str, Any], schema_path: Optional[str] = None) -> None:
    """
    Convenience function to validate workload summary content.
    
    Args:
        content: JSONL artifact content to validate
        schema_path: Optional path to schema file
        
    Raises:
        SDCValidationError: If validation fails
    """
    validator = SDCOutputValidator(schema_path)
    validator.validate_workload_summary(content)