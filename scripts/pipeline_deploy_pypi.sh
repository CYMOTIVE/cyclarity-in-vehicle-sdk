#!/bin/bash        
set -e

export PYPI_TOKEN
VERSION_FILE_NAME="cyclarity-in-vehicle-sdk.txt"

if [ "$BITBUCKET_BRANCH"  = "release" ]; then
    echo "The branch is release, releasing new version"
    poetry version patch
else
    echo "Releasing a prerelease version"
    poetry version prerelease
fi

#check lock file
if [ -e "poetry.lock" ]; then  
  # Remove the file  
  rm "poetry.lock"  
  echo "File poetry.lock has been removed."  
else  
  echo "File poetry.lock does not exist."  
fi

poetry install
poetry build
poetry config pypi-token.pypi $PYPI_TOKEN
new_version=$(poetry version --short)

if [ -f ${VERSION_FILE_NAME} ]; then    
    echo "${VERSION_FILE_NAME} exists, proceed."    
else    
    echo "${VERSION_FILE_NAME} does not exist, creating now."    
    touch ${VERSION_FILE_NAME}   
    echo "${VERSION_FILE_NAME} created."    
fi

echo "$new_version" > ${VERSION_FILE_NAME}
echo "uploading $new_version"

poetry publish

git config --local user.name ci_user
git config --local user.email bitbucket@ci

git pull
git add pyproject.toml
git add poetry.lock
git add ${VERSION_FILE_NAME}
git commit -m "[skip ci] ${new_version}"
git tag ${new_version}
git push origin ${new_version}

echo "Upload finished, stopping script." 
exit 0             
