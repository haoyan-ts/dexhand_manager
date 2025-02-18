import json
from concurrent import futures
from logging import config, getLogger

import grpc

from repositories.repository import LocalRepository
from services.dexhand_service import DexHandService
from services.session_service import SessionService
from ts.dexhand.v1.dexhand_service_pb2 import *
from ts.dexhand.v1.dexhand_service_pb2_grpc import add_DexHandServiceServicer_to_server
from ts.dexhand.v1.session_service_pb2 import *
from ts.dexhand.v1.session_service_pb2_grpc import add_SessionServiceServicer_to_server


LOG = getLogger(__name__)


def serve():
    LOG.info("Starting DexHand Manager")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    repository = LocalRepository()

    add_DexHandServiceServicer_to_server(DexHandService(repository), server)
    add_SessionServiceServicer_to_server(SessionService(repository), server)

    server.add_insecure_port("[::]:50051")  # Use [::] for IPv6 and IPv4
    LOG.info("Server started on port 50051")
    server.start()
    server.wait_for_termination()
