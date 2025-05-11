#!/bin/bash        
set -e

export PYPI_TOKEN
VERSION_FILE_NAME="cyclarity-in-vehicle-sdk.txt"

if [ "$BITBUCKET_BRANCH"  = "main" ]; then
    echo "The branch is main, releasing new version"
    poetry version patch
else
    echo "Releasing a prerelease version"
    base_version=$(echo $(poetry version -s) | grep -oP '^\d+\.\d+\.\d+')  
    new_version="${base_version}a$(shuf -i 10000-99999 -n 1)"
    poetry version $new_version
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
git push --follow-tags

echo "Upload finished, stopping script." 
exit 0             
