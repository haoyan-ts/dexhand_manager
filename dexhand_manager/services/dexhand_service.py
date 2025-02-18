import logging

import grpc
from google.protobuf.empty_pb2 import Empty

from repositories.repository import LocalRepository
from ts.dexhand.v1.dexhand_service_pb2 import *
from ts.dexhand.v1.dexhand_service_pb2_grpc import DexHandServiceServicer
from ts.dexhand.v1.common_pb2 import Side
from injector import Injector, inject
from grpc import ServicerContext

LOG = logging.getLogger(__name__)


class DexHandService(DexHandServiceServicer):
    repository: LocalRepository = LocalRepository()

    @inject
    def __init__(self, repository: LocalRepository):
        self.repository = repository

    def ListDexHands(self, request: ListDexHandsRequest, context: ServicerContext):
        LOG.info("ListDexHands request received.")

        dex_hands = [
            DexHand(**dex_hand.to_dict())
            for dex_hand in self.repository.dex_hands.values()
        ]

        return ListDexHandsResponse(dex_hands=dex_hands)

    def CreateDexHand(
        self, request: CreateDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("CreateDexHand request received.")

        if not self.repository.validate_create_dex_hand_request():
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(
                f"DexHand already exists on the side: {Side.Name(request.config.side)}"
            )
            return Empty()
        else:
            dex_hand = self.repository.create_dex_hand_from_config(request.config)

            return DexHand(**dex_hand.to_dict())

    def GetDexHand(self, request: GetDexHandRequest, context: grpc.ServicerContext):
        LOG.info("GetDexHand request received.")

        dex_hand = self.repository.get_dex_hand_by_id(request.id)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            return DexHand(**dex_hand.to_dict())

    def UpdateDexHand(
        self, request: UpdateDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("UpdateDexHand request received.")

        try:
            # dex_hand = self.repository.update_dex_hand(request)
            dex_hand = None
            pass
        except grpc.RpcError as e:
            LOG.error(f"Error while updating DexHand: {e}")

            context.set_code(e.args[0])
            context.set_details(e.args[1])

        return DexHand(**dex_hand.to_dict())

    def DeleteDexHand(
        self, request: DeleteDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("DeleteDexHand request received.")

        dex_hand = self.repository.get_dex_hand_by_id(request.dex_hand.id)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dex_hand.id}")
        else:
            del self.repository.dex_hands[dex_hand.side]
            return Empty()
