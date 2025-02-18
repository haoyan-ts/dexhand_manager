import logging
from typing import Optional

import grpc
from google.longrunning import operations_pb2
from google.protobuf import any_pb2
from google.protobuf.empty_pb2 import Empty

from entities.base_entities import SessionEntity, WorldEntity
from ts.dexhand.v1.session_service_pb2 import *
from ts.dexhand.v1.session_service_pb2_grpc import SessionServiceServicer


from injector import inject
from repositories.repository import LocalRepository

LOG = logging.getLogger(__name__)


class SessionService(SessionServiceServicer):
    session: Optional[SessionEntity] = None

    @inject
    def __init__(self, repository: LocalRepository) -> None:
        self._repository = repository
        super().__init__()

    def ListSessions(self, request: ListSessionsRequest, context: grpc.ServicerContext):
        LOG.info("ListSessions request received.")

        if self.session is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No session exists.")
            return Empty()
        else:
            session_proto = Session(
                id=self.session.id,
                name=self.session.name,
            )

            return ListSessionsResponse(sessions=[session_proto])

    def CreateSession(
        self, request: CreateSessionRequest, context: grpc.ServicerContext
    ):
        LOG.info("CreateSession request received.")

        if self.session is not None:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("Session already exists.")
            return Empty()
        else:
            self.session = SessionEntity()
            return Session(id=self.session.id, name=self.session.name)

    def GetSession(self, request: GetSessionRequest, context: grpc.ServicerContext):
        LOG.info("GetSession request received.")

        if self.session is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No session exists.")
            return Empty()
        else:
            return Session(id=self.session.id, name=self.session.name)

    def UpdateSession(
        self, request: UpdateSessionRequest, context: grpc.ServicerContext
    ):
        LOG.info("UpdateSession request received.")

        if self.session is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No session exists.")
            return Empty()
        else:
            LOG.debug("Update a session.")

            return Session(
                id=self.session.id,
                name=self.session.name,
            )

    def DeleteSession(
        self, request: DeleteSessionRequest, context: grpc.ServicerContext
    ):
        LOG.info("DeleteSession request received.")

        if self.session is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No session exists.")
            return Empty()
        else:
            self.session = None
            return Empty()

    def CalibrateWorld(
        self, request: CalibrateWorldRequest, context: grpc.ServicerContext
    ):
        LOG.info("CalibrateWorld request received.")

        if self.session is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No session exists.")
            return Empty()
        else:
            world = WorldEntity()
            world.set_coordinates(dict(request.data))
            self.session.world = world

            return operations_pb2.Operation(
                name="CalibrateWorld", done=True, response=any_pb2.Any(value=None)
            )
