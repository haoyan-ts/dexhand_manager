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
else
    echo "buf build failed"
    exit 1
fi