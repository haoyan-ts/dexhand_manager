import logging
from typing import Optional

import grpc
from repositories.error import (
    RepositoryAlreadyExistsError,
    RepositoryError,
)
from entities.base_entities import Session, World
from google.longrunning import operations_pb2
from google.protobuf import any_pb2
from google.protobuf.empty_pb2 import Empty
from injector import inject
from repositories.repository import LocalRepository
from ts.dexhand.v1.session_service_pb2 import (
    Session as SessionProto,
    ListSessionsRequest,
    ListSessionsResponse,
    CreateSessionRequest,
    GetSessionRequest,
    UpdateSessionRequest,
    DeleteSessionRequest,
    CalibrateWorldRequest,
)
from ts.dexhand.v1.session_service_pb2_grpc import SessionServiceServicer

LOG = logging.getLogger(__name__)


class SessionService(SessionServiceServicer):
    @inject
    def __init__(self, repository: LocalRepository) -> None:
        self._repository = repository
        super().__init__()

    def ListSessions(self, request: ListSessionsRequest, context: grpc.ServicerContext):
        LOG.info("ListSessions request received.")

        try:
            _session = self._repository.get_session()
            return ListSessionsResponse([SessionProto(**_session.to_dict())])
        except RepositoryError as e:
            if e is RepositoryError:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No session exists.")

    def CreateSession(
        self, request: CreateSessionRequest, context: grpc.ServicerContext
    ):
        LOG.info("CreateSession request received.")

        try:
            _session = self._repository.create_session()
            return SessionProto(**_session.to_dict())
        except RepositoryError as e:
            if e is RepositoryAlreadyExistsError:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("Session already exists.")

    def GetSession(self, request: GetSessionRequest, context: grpc.ServicerContext):
        LOG.info("GetSession request received.")

        try:
            _session = self._repository.get_session()
            return SessionProto(**_session.to_dict())
        except RepositoryError as e:
            if e is RepositoryError:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No session exists.")

    def UpdateSession(
        self, request: UpdateSessionRequest, context: grpc.ServicerContext
    ):
        LOG.info("UpdateSession request received.")

        try:
            _session = self._repository.update_session()
            return SessionProto(**_session.to_dict())
        except RepositoryError as e:
            if e is RepositoryError:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No session exists.")

    def DeleteSession(
        self, request: DeleteSessionRequest, context: grpc.ServicerContext
    ):
        LOG.info("DeleteSession request received.")

        try:
            self._repository.delete_session()
            return Empty()
        except RepositoryError as e:
            if e is RepositoryError:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No session exists.")
