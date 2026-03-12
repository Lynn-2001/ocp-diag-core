# SDC Output Validator

A Go-based validator for SDC (Silent Data Corruption) custom output schema extensions on top of the OCP (Open Compute Project) diagnostic output standard.

## Prerequisites

- Go 1.16 or higher
- Clone the repository:
```bash
git clone https://github.com/Lynn-2001/ocp-diag-core.git
cd ocp-diag-core
```

## Building the SDC Validator

### Online Build (requires internet access)

```bash
cd sdc_executor/validators/sdc_validator
go mod tidy
go build -o sdc_validator
```

### Offline Build (uses vendored dependencies)

For environments behind corporate proxies that block proxy.golang.org:

```bash
cd sdc_executor/validators/sdc_validator
go build -mod=vendor -o sdc_validator
```

**Note:** The vendor directory contains all dependencies and is committed to the repository for offline builds.

## Running the SDC Validator

### Against the Example JSONL File

**Command:**
```bash
./sdc_validator -schema ../../../../json_spec/output/root.json ../../schema/examples/sdc_output_example.jsonl
```

**Expected Output (when validation passes):**
```
all ok
```

**Expected Output (when validation fails):**
```
JSONL validation failed: <detailed error message>
```

### Against Custom JSONL Files

```bash
./sdc_validator -schema ../../../../json_spec/output/root.json path/to/your/file.jsonl
```

## Running the OCP Validator

To verify that our SDC example is still OCP-compliant, run the original OCP validator:

### Build OCP Validator

```bash
cd ../../../../validators/spec_validator
go mod tidy
go build -o ocp_validator
```

### Validate SDC Example with OCP Validator

**Command:**
```bash
./ocp_validator -schema ../../json_spec/output/root.json ../../sdc_executor/schema/examples/sdc_output_example.jsonl
```

**Expected Output (when validation passes):**
```
all ok
```

## Running the Tests

### SDC Validator Tests

**Online mode:**
```bash
cd sdc_executor/validators/sdc_validator
go test ./pkg/schema_validator/
```

**Offline mode (using vendor):**
```bash
cd sdc_executor/validators/sdc_validator
go test -mod=vendor ./pkg/schema_validator/
```

**Expected Output:**
```
PASS
ok      github.com/Lynn-2001/ocp-diag-core/sdc_executor/validators/sdc_validator/pkg/schema_validator    0.XXXs
```

### OCP Validator Tests

```bash
cd validators/spec_validator
go test ./pkg/schema_validator/
```

## Troubleshooting

### Common Errors and Solutions

**1. `no such file or directory: go`**
- **Solution:** Install Go 1.16+ from https://golang.org/dl/

**2. `cannot find module`**
- **Solution:** Run `go mod tidy` in the validator directory before building
- **Alternative:** Use offline mode with `go build -mod=vendor` if behind a corporate proxy

**3. `failed to get schema $id`**
- **Solution:** Ensure all schema files have valid `$id` fields and are properly formatted JSON

**4. `no such folder: <schema-path>`**
- **Solution:** Verify the schema path exists relative to your current directory

**5. `repeatability_rate value must be between 0.0 and 1.0`**
- **Solution:** Check that repeatability_rate measurements have values in the valid range

**6. `ttf_seconds value must be >= 0.0`**
- **Solution:** Ensure ttf_seconds values are non-negative or null

**7. `footprint_tax_percent value must be >= 0.0`**
- **Solution:** Verify footprint_tax_percent values are non-negative or null

### Validation Details

The SDC validator performs two levels of validation:

1. **JSON Schema Validation:** Uses the OCP root schema with SDC extensions to validate structure and data types
2. **Business Logic Validation:** Applies SDC-specific constraints that cannot be expressed in JSON Schema:
   - `ttf_seconds`: value ≥ 0.0 or null, unit = "s"
   - `repeatability_rate`: value 0.0-1.0 or null, unit = "ratio"
   - `footprint_tax_percent`: value ≥ 0.0 or null, unit = "%"

### File Structure

```
sdc_executor/
├── validators/sdc_validator/
│   ├── README.md                    # This file
│   ├── main.go                      # CLI entry point
│   ├── go.mod                       # Go module definition
│   └── pkg/schema_validator/
│       ├── validator.go             # Core validation logic
│       └── validator_test.go        # Unit tests
├── schema/output/                   # SDC schema extensions
│   ├── measurement.json             # Extended measurement schema
│   ├── metadata.json               # Extended metadata schema
│   └── test_step_start.json        # Extended test step schema
└── schema/examples/
    └── sdc_output_example.jsonl     # Example JSONL with SDC extensions
```