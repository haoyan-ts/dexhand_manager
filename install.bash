#!/bin/bash

cd api
rm -rf /gen
# Run buf build
buf generate

# Check if buf build was successful
if [ $? -eq 0 ]; then
    cd ..   
    # Copy gen/python/ts to workspace
    cp -r api/gen/python/ts dexhand_manager/
    cp -r api/gen/python/ts client/
    # Create __init__.py files for all subdirectories
    find dexhand_manager -type d -exec touch {}/__init__.py \;
    find client -type d -exec touch {}/__init__.py \;
    echo "buf build successful"
else
    echo "buf build failed"
    exit 1
fi