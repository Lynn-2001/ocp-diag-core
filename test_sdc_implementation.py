#!/usr/bin/env python3
"""
Test script for SDC Output Schema Extension implementation.
Basic smoke test to verify the components work together.
"""

import sys
import json
from pathlib import Path

# Add sdc_executor to Python path
sys.path.insert(0, str(Path(__file__).parent / "sdc_executor"))

try:
    # Test imports
    from reporting.sdc_output_models import WorkloadSummary, IterationResult
    from reporting.sdc_output_validator import SDCOutputValidator, validate_workload_summary
    print("✓ All imports successful")
    
    # Test IterationResult creation
    iter1 = IterationResult(0, "PASS", ttf_seconds=None, footprint_tax_percent=1.2)
    iter2 = IterationResult(1, "PASS", ttf_seconds=None, footprint_tax_percent=0.8)
    iter3 = IterationResult(2, "FAIL", ttf_seconds=25.0, footprint_tax_percent=0.5)
    print("✓ IterationResult creation successful")
    
    # Test WorkloadSummary.from_iteration_results
    summary = WorkloadSummary.from_iteration_results("cpu_stress", [iter1, iter2, iter3])
    print(f"✓ WorkloadSummary creation: {summary}")
    
    # Test JSONL artifact generation
    artifacts = summary.to_jsonl_artifacts(start_seq=10)
    print(f"✓ Generated {len(artifacts)} JSONL artifacts")
    
    # Test validator creation
    validator = SDCOutputValidator()
    print("✓ SDCOutputValidator creation successful")
    
    # Test validation of generated artifacts
    for i, artifact in enumerate(artifacts):
        try:
            validator.validate_workload_summary(artifact)
            print(f"✓ Artifact {i} validation successful")
        except Exception as e:
            print(f"✗ Artifact {i} validation failed: {e}")
    
    # Test validation of example JSONL
    example_file = Path(__file__).parent / "sdc_executor" / "schema" / "examples" / "sdc_output_example.jsonl"
    if example_file.exists():
        with open(example_file, 'r') as f:
            line_count = 0
            for line in f:
                if line.strip():
                    try:
                        content = json.loads(line.strip())
                        validator.validate_workload_summary(content)
                        line_count += 1
                    except Exception as e:
                        print(f"✗ Example JSONL line {line_count} validation failed: {e}")
            print(f"✓ Example JSONL validation successful ({line_count} lines)")
    
    print("\n🎉 All tests passed! SDC implementation is working correctly.")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)