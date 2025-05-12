#!/bin/bash        
set -e

if pip show cyclarity-in-vehicle-sdk 1>/dev/null; then
    pip uninstall -y cyclarity-in-vehicle-sdk
fi