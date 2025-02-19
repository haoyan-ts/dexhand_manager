import logging
import threading
import uuid
from typing import Iterable, Iterator, Union

from google.protobuf.empty_pb2 import Empty
from grpc import ServicerContext, StatusCode
from injector import Injector, inject
from models.arm_control import PiperArm
from models.inspire_hand import InspireHand
from repositories.repository import LocalRepository
from ts.dexhand.v1.common_pb2 import ArmType, HandType, Side
from ts.dexhand.v1.dexhand_control_service_pb2 import (
    ConnectDexHandRequest,
    DisableDexHandRequest,
    EnableDexHandRequest,
    SendPoseRequest,
)
from ts.dexhand.v1.dexhand_control_service_pb2_grpc import DexHandControlServiceServicer
from ts.dexhand.v1.dexhand_service_pb2 import CreateDexHandRequest, DeleteDexHandRequest
from ts.dexhand.v1.dexhand_service_pb2 import DexHand as DexHandProto
from ts.dexhand.v1.dexhand_service_pb2 import (
    GetDexHandRequest,
    ListDexHandsRequest,
    ListDexHandsResponse,
    UpdateDexHandRequest,
)
from ts.dexhand.v1.dexhand_service_pb2_grpc import DexHandServiceServicer

# Import DexHandController from the new location
from models.dexhand_controller import DexHandController

LOG = logging.getLogger(__name__)


class DexHandService(DexHandServiceServicer):
    dex_hands: dict[str, DexHandController]

    def __init__(self, dex_hands: dict[str, DexHandController]):
        self.dex_hands = dex_hands

    def ListDexHands(self, request: ListDexHandsRequest, context: ServicerContext):
        LOG.info("ListDexHands request received.")

        return ListDexHandsResponse(
            dex_hands=[dex_hand.to_proto() for dex_hand in self.dex_hands.values()]
        )

    def CreateDexHand(self, request: CreateDexHandRequest, context: ServicerContext):
        LOG.info("CreateDexHand request received.")

        dex_hand = DexHandController(
            arm_type=request.config.arm_type,
            hand_type=request.config.hand_type,
            side=request.config.side,
        )

        self.dex_hands[dex_hand.id] = dex_hand
        return dex_hand.to_proto()

    def GetDexHand(self, request: GetDexHandRequest, context: ServicerContext):
        LOG.info("GetDexHand request received.")

        # Validate if DexHand exists
        if request.id not in self.dex_hands:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            return self.dex_hands[request.id].to_proto()

    def DeleteDexHand(self, request: DeleteDexHandRequest, context: ServicerContext):
        LOG.info("DeleteDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dex_hand.id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dex_hand.id}")
        else:
            del self.dex_hands[dex_hand.id]
            return Empty()


class DexHandControlService(DexHandControlServiceServicer):
    dex_hands: dict[str, DexHandController]

    def __init__(self, dex_hands: dict[str, DexHandController]):
        self.dex_hands = dex_hands

    def ConnectDexHand(self, request: ConnectDexHandRequest, context: ServicerContext):
        LOG.info("ConnectDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # connect dex_hand
            dex_hand.connect()
            return Empty()

    def DisconnectDexHand(self, request, context: ServicerContext):
        LOG.info("DisconnectDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # disconnect dex_hand
            dex_hand.disconnect()
            return Empty()

    def EnableDexHand(self, request: EnableDexHandRequest, context: ServicerContext):
        LOG.info("EnableDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # enable dex_hand
            dex_hand.enable()
            return Empty()

    def DisableDexHand(self, request: DisableDexHandRequest, context: ServicerContext):
        LOG.info("DisableDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # disable dex_hand
            dex_hand.disable()
            return Empty()

    def SendJoint(
        self, request_iterator: Iterable[SendPoseRequest], context: ServicerContext
    ):
        LOG.info("SendJoint request received.")

        dex_hand = None

        for request in request_iterator:
            request_name = request.WhichOneof("request")
            LOG.info(f"Request oneof: {request_name}")

            if request_name == "setup_request":
                if request.setup_request.dexhand_id not in self.dex_hands:
                    context.set_code(StatusCode.NOT_FOUND)
                    context.set_details(
                        f"Invalid DexHand ID: {request.setup_request.dexhand_id}"
                    )
                else:
                    dex_hand = self.dex_hands.get(
                        request.setup_request.dexhand_id, None
                    )
                    yield Empty()
            elif request_name == "packet_request":
                if dex_hand is not None:
                    # send joint
                    LOG.info(f"Sending joint: {request.packet_request}")
                    dex_hand.move_j(list(request.packet_request.poses))
                    yield Empty()
            elif request_name == "cancel_request":
                LOG.info("Exiting...")
                break

        return Empty()
