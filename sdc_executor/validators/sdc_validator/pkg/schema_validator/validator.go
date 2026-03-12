package schemavalidator

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"io/ioutil"
	"log"
	"os"
	"path"
	"path/filepath"

	js "github.com/santhosh-tekuri/jsonschema/v5"
)

func getSchemaURL(schemaPath string) (string, error) {
	if _, err := os.Lstat(schemaPath); err != nil {
		return "", fmt.Errorf("no such folder: %s", schemaPath)
	}

	data, err := ioutil.ReadFile(schemaPath)
	if err != nil {
		return "", fmt.Errorf("failed to read the spec file: %s, %w", schemaPath, err)
	}

	var content struct {
		Url string `json:"$id"`
	}

	if err := json.Unmarshal(data, &content); err != nil {
		return "", fmt.Errorf("input schema for <%s> was invalid json or missing $id: %w", schemaPath, err)
	}

	return content.Url, nil
}

type SchemaValidator struct {
	s *js.Schema
}

// New makes a new SchemaValidator given the path to a root schema json file
func New(schemaPath string) (*SchemaValidator, error) {
	c := js.NewCompiler()

	// Load OCP standard schemas
	err := filepath.WalkDir(path.Dir(schemaPath), func(fpath string, d fs.DirEntry, err error) error {
		// SDC fix: Handle WalkDir errors and nil DirEntry to prevent panic
		if err != nil {
			return err
		}
		if d == nil {
			return nil
		}
		if !d.IsDir() && filepath.Ext(fpath) == ".json" {
			url, err := getSchemaURL(fpath)
			if err != nil {
				return fmt.Errorf("failed to get schema $id: %w", err)
			}

			f, err := os.Open(fpath)
			if err != nil {
				return fmt.Errorf("could not open extension spec: %v", err)
			}
			defer f.Close()

			if err := c.AddResource(url, f); err != nil {
				return err
			}
			log.Printf("Registered ext schema %v -> %v\n", url, fpath)
		}

		return nil
	})
	if err != nil {
		return nil, err
	}

	// Load SDC extension schemas - override OCP schemas where they exist
	// SDC extension: Load modified schemas from sdc_executor/schema/output/ to override OCP versions
	// Fixed path: should be ../../schema/output from pkg/schema_validator directory
	sdcSchemaDir := "../../schema/output"
	if _, err := os.Stat(sdcSchemaDir); err == nil {
		err := filepath.WalkDir(sdcSchemaDir, func(fpath string, d fs.DirEntry, err error) error {
			// SDC fix: Handle WalkDir errors and nil DirEntry to prevent panic
			if err != nil {
				return err
			}
			if d == nil {
				return nil
			}
			if !d.IsDir() && filepath.Ext(fpath) == ".json" {
				url, err := getSchemaURL(fpath)
				if err != nil {
					return fmt.Errorf("failed to get SDC schema $id: %w", err)
				}

				f, err := os.Open(fpath)
				if err != nil {
					return fmt.Errorf("could not open SDC extension spec: %v", err)
				}
				defer f.Close()

				if err := c.AddResource(url, f); err != nil {
					return err
				}
				log.Printf("Registered SDC extension schema %v -> %v\n", url, fpath)
			}

			return nil
		})
		if err != nil {
			return nil, fmt.Errorf("failed to load SDC extension schemas: %w", err)
		}
	}

	mainURL, err := getSchemaURL(schemaPath)
	if err != nil {
		return nil, fmt.Errorf("failed to get $id for root schema: %w", err)
	}

	s, err := c.Compile(mainURL)
	if err != nil {
		return nil, err
	}

	return &SchemaValidator{s}, nil
}

func (sv *SchemaValidator) ValidateBytes(input []byte) error {
	var obj interface{}
	if err := json.Unmarshal(input, &obj); err != nil {
		return fmt.Errorf("unable to unmarshal json: %v", err)
	}

	// First run standard schema validation
	if err := sv.s.Validate(obj); err != nil {
		return err
	}

	// Then run SDC-specific validation
	return sv.ValidateSDCMeasurement(input)
}

func (sv *SchemaValidator) ValidateFile(filename string) error {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("cannot open input file: %v", err)
	}

	return sv.ValidateBytes(data)
}

// ValidateSDCMeasurement validates SDC-specific measurement fields after base schema validation passes
func (sv *SchemaValidator) ValidateSDCMeasurement(input []byte) error {
	var obj map[string]interface{}
	if err := json.Unmarshal(input, &obj); err != nil {
		return nil // Already validated in ValidateBytes, skip if not valid JSON
	}

	// Check if this is a testStepArtifact with measurement
	if testStepArtifact, ok := obj["testStepArtifact"].(map[string]interface{}); ok {
		if measurement, ok := testStepArtifact["measurement"].(map[string]interface{}); ok {
			if name, ok := measurement["name"].(string); ok {
				// Validate SDC-specific measurement fields
				switch name {
				case "ttf_seconds":
					// ttf_seconds value must be >= 0.0 when not null
					// (JSON schema range validation is not sufficient for null-allowed float fields)
					if value, exists := measurement["value"]; exists && value != nil {
						if floatVal, ok := value.(float64); ok {
							if floatVal < 0.0 {
								return fmt.Errorf("ttf_seconds value must be >= 0.0, got %f", floatVal)
							}
						}
					}
				case "repeatability_rate":
					// repeatability_rate value must be between 0.0 and 1.0 when not null
					// (JSON schema range validation is not sufficient for null-allowed float fields)
					if value, exists := measurement["value"]; exists && value != nil {
						if floatVal, ok := value.(float64); ok {
							if floatVal < 0.0 || floatVal > 1.0 {
								return fmt.Errorf("repeatability_rate value must be between 0.0 and 1.0, got %f", floatVal)
							}
						}
					}
				case "footprint_tax_percent":
					// footprint_tax_percent value must be >= 0.0 when not null
					// (JSON schema range validation is not sufficient for null-allowed float fields)
					if value, exists := measurement["value"]; exists && value != nil {
						if floatVal, ok := value.(float64); ok {
							if floatVal < 0.0 {
								return fmt.Errorf("footprint_tax_percent value must be >= 0.0, got %f", floatVal)
							}
						}
					}
				}
			}
		}
	}

	return nil
}