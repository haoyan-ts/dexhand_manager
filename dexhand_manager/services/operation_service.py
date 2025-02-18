import grpc
from google.longrunning import operations_grpc
from google.longrunning import operations_pb2
import logging

from repositories.repository import LocalRepository
from injector import inject

LOG = logging.getLogger(__name__)


class OperationService(operations_grpc.OperationsServicer):
    @inject
    def __init__(self, repository: LocalRepository) -> None:
        self._repository = repository
        super().__init__()

    def GetOperation(self, request, context):
        LOG.info("GetOperation request received.")

        return operations_pb2.Operation(name="test", done=True)
