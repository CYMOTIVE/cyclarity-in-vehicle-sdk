#!/bin/bash
set -euo pipefail
  
# Variables
VERSION_FILE_NAME="cyclarity-in-vehicle-sdk.txt"

# Detect current branch (compatible with GitHub Actions)
if [[ -n "${GITHUB_REF-}" ]]; then
    BRANCH=$(echo "${GITHUB_REF##*/}")
else
    BRANCH=$(git branch --show-current 2>/dev/null || echo "")
fi

# Version bump logic
if [[ "$BRANCH" == "main" ]]; then
    echo "The branch is main, releasing new version"
    poetry version patch
else
    echo "Releasing a prerelease version"
    base_version=$(poetry version -s | grep -oP '^\d+\.\d+\.\d+')
    new_version="${base_version}a$(shuf -i 10000-99999 -n 1)"
    poetry version $new_version
fi
# Remove poetry.lock if exists
if [ -e "poetry.lock" ]; then
    rm "poetry.lock"
    echo "File poetry.lock has been removed."
else
    echo "File poetry.lock does not exist."
fi

poetry install
poetry build
  
if [[ -z "${PYPI_TOKEN-}" ]]; then
    echo "PYPI_TOKEN environment variable is not set. Exiting."
    exit 1
fi
poetry config pypi-token.pypi "$PYPI_TOKEN"
  
new_version=$(poetry version --short)

echo "uploading $new_version"
poetry publish

echo "Upload finished, stopping script."
exit 0