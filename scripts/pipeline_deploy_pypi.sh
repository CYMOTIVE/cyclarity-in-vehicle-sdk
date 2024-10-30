#!/bin/bash        
set -e

export PYPI_TOKEN

if [ "$BITBUCKET_BRANCH"  = "release" ]; then
    echo "The branch is release, releasing new version"
    poetry version patch
else
    echo "Releasing a prerelease version"
    poetry version prerelease
fi

poetry install
poetry build
poetry config pypi-token.pypi $PYPI_TOKEN
new_version=$(poetry version --short)

if [ -f "cyclarity-in-vehicle-sdk.txt" ]; then    
    echo "cyclarity-in-vehicle-sdk.txt exists, proceed."    
else    
    echo "cyclarity-in-vehicle-sdk.txt does not exist, creating now."    
    touch cyclarity-in-vehicle-sdk.txt   
    echo "cyclarity-in-vehicle-sdk.txt created."    
fi

echo "$new_version" > ./cyclarity-in-vehicle-sdk.txt
echo "uploading $new_version"

poetry publish

git config --local user.name ci_user
git config --local user.email bitbucket@ci

git pull
git add pyproject.toml
git add cyclairty-sdk.txt
git commit -m "[skip ci] ${new_version}"
git tag ${new_version}
git push origin ${new_version}

echo "Upload finished, stopping script." 
exit 0             
