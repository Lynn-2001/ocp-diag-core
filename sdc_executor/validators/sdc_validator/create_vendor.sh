#!/bin/bash

# Script to create vendor directory for offline builds
# Run this script to generate the vendor directory with all Go dependencies

set -e

echo "Creating vendor directory for offline builds..."
echo "Current directory: $(pwd)"

# Ensure we're in the right directory
if [ ! -f "go.mod" ]; then
    echo "Error: go.mod not found. Make sure you're in the sdc_validator directory."
    exit 1
fi

# Download and vendor all dependencies
echo "Running: go mod vendor"
go mod vendor

# Check if vendor directory was created
if [ ! -d "vendor" ]; then
    echo "Error: vendor directory was not created."
    exit 1
fi

echo "✅ Successfully created vendor directory"
echo "📊 Vendor directory contents:"
ls -la vendor/

echo ""
echo "📁 Vendor modules:"
find vendor -name "*.go" | wc -l | xargs echo "Go files:"
du -sh vendor/ | xargs echo "Total size:"

echo ""
echo "🎯 Next steps:"
echo "1. git add vendor/"
echo "2. git commit -m 'feat: add vendor directory for offline builds'"
echo "3. git push origin $(git branch --show-current)"
echo ""
echo "✅ You can now build offline with: go build -mod=vendor -o sdc_validator"