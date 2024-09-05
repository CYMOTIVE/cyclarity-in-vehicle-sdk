#!/bin/bash        
set -e

export PYPI_TOKEN

if [ "$BITBUCKET_BRANCH"  = "release" ]; then
    echo "The branch is release, releasing new version"
else
    echo "Releasing a prerelease version"
    poetry version prerelease
fi

poetry install
poetry build
poetry config pypi-token.pypi $PYPI_TOKEN
new_version=$(poetry version --short)

echo "uploading $new_version"

poetry publish

echo "Upload finished, stopping script." 
exit 0             
