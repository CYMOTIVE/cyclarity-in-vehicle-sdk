#!/bin/bash        
set -e

export PYPI_TOKEN

poetry install
poetry build
poetry config pypi-token.pypi $PYPI_TOKEN
new_version=$(poetry version --short)

echo "uploading $new_version"

poetry publish

echo "Upload finished, stopping script." 
exit 0             
