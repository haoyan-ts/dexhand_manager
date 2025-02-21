# DexHand Manager

## Overview
DexHand Manager is a Python project that implements gRPC services to control DexHand robots.  
It handles external gRPC service calls, executes corresponding processes, and enables web access via Envoy acting as a reverse proxy to connect gRPC-web and the original gRPC.

## Features
- Implements gRPC services in Python to manage DexHand robots.
- Handles external service calls and triggers robot control processes.
- Uses Envoy for reverse proxy, supporting gRPC-web to gRPC communication.
- Provides load balancing and real-time monitoring via the Envoy admin interface.

## Prerequisites
- Python 3.x installed.
- Required Python packages in requirements.txt installed.
- Envoy proxy installed (https://www.envoyproxy.io/).
- A running instance of the DexHand gRPC service (modifiable in envoy.yaml).

## Configuration
Review and adjust the Envoy configuration in:
`./dexhand_manager/envoy.yaml`

## Using Envoy
1. Ensure Envoy is installed.
2. Verify or modify the config at `./dexhand_manager/envoy.yaml`.
3. Start Envoy:
   ```bash
   envoy -c /home/dobot/li/repositories/dexhand_manager/envoy.yaml
   ```
4. Check the admin interface on port 9901 for logs and status.

## Running DexHand Manager
1. Set up the Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the gRPC services:
   ```bash
   python dexhand_manager/main.py
   ```
3. Ensure the service endpoints and processes are reachable as per the configured settings.

## Additional Information
For further details, check the project documentation or contact the development team.
