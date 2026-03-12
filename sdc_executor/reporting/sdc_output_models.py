"""
SDC Output Models

Python dataclasses for SDC workload summary and iteration results,
extending OCP diagnostic output format with SDC-specific fields.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import statistics


@dataclass
class IterationResult:
    """Results from a single iteration of a workload."""
    
    iteration_index: int
    result: str  # "PASS", "FAIL", etc.
    ttf_seconds: Optional[float] = None  # Time to failure for this iteration
    footprint_tax_percent: Optional[float] = None  # Footprint tax for this iteration
    
    def __post_init__(self):
        """Validate the iteration result."""
        if self.iteration_index < 0:
            raise ValueError("iteration_index must be non-negative")
        
        if self.ttf_seconds is not None and self.ttf_seconds < 0:
            raise ValueError("ttf_seconds must be non-negative when not None")
            
        if self.footprint_tax_percent is not None and self.footprint_tax_percent < 0:
            raise ValueError("footprint_tax_percent must be non-negative when not None")


@dataclass
class WorkloadSummary:
    """Summary metrics for a workload after all iterations complete."""
    
    workload_name: str
    ttf_seconds: Optional[float] = None
    repeatability_rate: Optional[float] = None
    footprint_tax_percent: Optional[float] = None
    
    def __post_init__(self):
        """Validate the workload summary fields."""
        if not self.workload_name:
            raise ValueError("workload_name cannot be empty")
            
        if self.ttf_seconds is not None and self.ttf_seconds < 0:
            raise ValueError("ttf_seconds must be non-negative when not None")
            
        if self.repeatability_rate is not None:
            if not (0.0 <= self.repeatability_rate <= 1.0):
                raise ValueError("repeatability_rate must be between 0.0 and 1.0 when not None")
                
        if self.footprint_tax_percent is not None and self.footprint_tax_percent < 0:
            raise ValueError("footprint_tax_percent must be non-negative when not None")
    
    @classmethod
    def from_iteration_results(cls, workload_name: str, iter_results: List[IterationResult]) -> 'WorkloadSummary':
        """
        Compute WorkloadSummary metrics from a list of IterationResult objects.
        
        Args:
            workload_name: Name of the workload
            iter_results: List of IterationResult objects from all iterations
            
        Returns:
            WorkloadSummary with computed metrics
        """
        if not iter_results:
            return cls(workload_name=workload_name)
        
        # Compute TTF (Time to Failure) - minimum across all iterations that failed
        ttf_values = [r.ttf_seconds for r in iter_results 
                     if r.ttf_seconds is not None and r.result != "PASS"]
        ttf_seconds = min(ttf_values) if ttf_values else None
        
        # Compute repeatability rate - fraction matching iteration 0 result
        if len(iter_results) <= 1:
            repeatability_rate = None  # No loop, so no repeatability to measure
        else:
            baseline_result = iter_results[0].result
            matching_results = sum(1 for r in iter_results if r.result == baseline_result)
            repeatability_rate = matching_results / len(iter_results)
        
        # Compute footprint tax - maximum across all iterations
        footprint_values = [r.footprint_tax_percent for r in iter_results 
                           if r.footprint_tax_percent is not None]
        footprint_tax_percent = max(footprint_values) if footprint_values else None
        
        return cls(
            workload_name=workload_name,
            ttf_seconds=ttf_seconds,
            repeatability_rate=repeatability_rate,
            footprint_tax_percent=footprint_tax_percent
        )
    
    def to_jsonl_artifacts(self, start_seq: int, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Convert WorkloadSummary to OCP JSONL artifact format.
        
        Args:
            start_seq: Starting sequence number for the artifacts
            timestamp: ISO timestamp string, defaults to current time
            
        Returns:
            List of OCP artifact dictionaries ready to write to JSONL
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        step_id = f"{self.workload_name}_summary"
        step_name = f"{self.workload_name}-summary"
        
        artifacts = []
        seq = start_seq
        
        # testStepStart artifact
        artifacts.append({
            "sequenceNumber": seq,
            "timestamp": timestamp,
            "testStepArtifact": {
                "testStepId": step_id,
                "testStepStart": {
                    "name": step_name,
                    "metadata": {
                        "stepType": "sdc-workload-summary"
                    }
                }
            }
        })
        seq += 1
        
        # TTF measurement artifact
        if self.ttf_seconds is not None or True:  # Always emit, even if null
            artifacts.append({
                "sequenceNumber": seq,
                "timestamp": timestamp,
                "testStepArtifact": {
                    "testStepId": step_id,
                    "measurement": {
                        "name": "ttf_seconds",
                        "value": self.ttf_seconds,
                        "unit": "s"
                    }
                }
            })
            seq += 1
        
        # Repeatability rate measurement artifact
        if self.repeatability_rate is not None or True:  # Always emit, even if null
            artifacts.append({
                "sequenceNumber": seq,
                "timestamp": timestamp,
                "testStepArtifact": {
                    "testStepId": step_id,
                    "measurement": {
                        "name": "repeatability_rate",
                        "value": self.repeatability_rate,
                        "unit": "ratio"
                    }
                }
            })
            seq += 1
        
        # Footprint tax measurement artifact
        if self.footprint_tax_percent is not None or True:  # Always emit, even if null
            artifacts.append({
                "sequenceNumber": seq,
                "timestamp": timestamp,
                "testStepArtifact": {
                    "testStepId": step_id,
                    "measurement": {
                        "name": "footprint_tax_percent",
                        "value": self.footprint_tax_percent,
                        "unit": "%"
                    }
                }
            })
            seq += 1
        
        # testStepEnd artifact
        artifacts.append({
            "sequenceNumber": seq,
            "timestamp": timestamp,
            "testStepArtifact": {
                "testStepId": step_id,
                "testStepEnd": {
                    "status": "COMPLETE"
                }
            }
        })
        
        return artifacts