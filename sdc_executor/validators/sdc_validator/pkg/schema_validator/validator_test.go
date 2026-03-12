package schemavalidator

import (
	"testing"

	js "github.com/santhosh-tekuri/jsonschema/v5"
	"github.com/stretchr/testify/require"
)

func TestSDCWorkloadSummaryValid(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "ttf_seconds",
				"value": 42.3,
				"unit": "s"
			}
		},
		"sequenceNumber": 11,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.NoError(t, err)
}

func TestSDCRepeatabilityRateValid(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "repeatability_rate",
				"value": 0.95,
				"unit": "ratio"
			}
		},
		"sequenceNumber": 12,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.NoError(t, err)
}

func TestSDCFootprintTaxValid(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "footprint_tax_percent",
				"value": 1.3,
				"unit": "%"
			}
		},
		"sequenceNumber": 13,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.NoError(t, err)
}

func TestSDCNullValuesValid(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "ttf_seconds",
				"value": null,
				"unit": "s"
			}
		},
		"sequenceNumber": 11,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.NoError(t, err)
}

func TestSDCRepeatabilityRateInvalidHigh(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "repeatability_rate",
				"value": 1.5,
				"unit": "ratio"
			}
		},
		"sequenceNumber": 12,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.Error(t, err)
	require.Contains(t, err.Error(), "repeatability_rate value must be between 0.0 and 1.0")
}

func TestSDCRepeatabilityRateInvalidLow(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "repeatability_rate",
				"value": -0.1,
				"unit": "ratio"
			}
		},
		"sequenceNumber": 12,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.Error(t, err)
	require.Contains(t, err.Error(), "repeatability_rate value must be between 0.0 and 1.0")
}

func TestSDCFootprintTaxInvalid(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "footprint_tax_percent",
				"value": -1.5,
				"unit": "%"
			}
		},
		"sequenceNumber": 13,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.Error(t, err)
	require.Contains(t, err.Error(), "footprint_tax_percent value must be >= 0.0")
}

func TestSDCTTFSecondsInvalid(t *testing.T) {
	json := `{
		"testStepArtifact": {
			"testStepId": "workload_a_summary",
			"measurement": {
				"name": "ttf_seconds",
				"value": -42.3,
				"unit": "s"
			}
		},
		"sequenceNumber": 11,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.Error(t, err)
	require.Contains(t, err.Error(), "ttf_seconds value must be >= 0.0")
}

func TestSchemaVersion(t *testing.T) {
	json := `{
		"schemaVersion": {
			"major": 2,
			"minor": 0
		},
		"sequenceNumber": 0,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	require.NoError(t, err)
}

func TestValidateBytesInvalid(t *testing.T) {
	json := `{
		"testRunArtifact": {
			"log": {
				"text": "log text",
				"severity": "INFO"
			}
		},
		"testStepArtifact": {
			"testStepId": "1",
			"log": {
				"text": "log text",
				"severity": "INFO"
			}
		},
		"sequenceNumber": 0,
		"timestamp": "2021-10-19T22:59:20+00:00"
	}`

	err := validateString(t, json)
	var ve *js.ValidationError
	require.ErrorAs(t, err, &ve)
}

func validateString(t *testing.T, json string) error {
	// Use the OCP root schema as the base schema for SDC validation
	// This follows the requirement to extend OCP format, not replace it
	const schema string = "../../../../json_spec/output/root.json"

	sv, err := New(schema)
	require.NoError(t, err)

	err = sv.ValidateBytes([]byte(json))
	if err != nil {
		t.Logf("error in validation: %#v", err)
	}

	return err
}