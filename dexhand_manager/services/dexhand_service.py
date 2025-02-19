import logging
import threading
import uuid
from typing import Union

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc import ServicerContext
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

LOG = logging.getLogger(__name__)


class DexHandController:
    _lock: threading.RLock = threading.RLock()
    id: str
    name: str = ""
    side: Side = Side.SIDE_UNSPECIFIED
    arm_type: ArmType = ArmType.ARM_TYPE_UNSPECIFIED
    hand_type: HandType = HandType.HAND_TYPE_UNSPECIFIED

    _arm: Union[PiperArm, None]
    _hand: Union[InspireHand, None]

    def __init__(self, side: Side, arm_type: ArmType, hand_type: HandType):
        self.side = side
        self.arm_type = arm_type
        self.hand_type = hand_type

        self.id = str(uuid.uuid4())
        self.name = (
            f"{Side.Name(side)}_{ArmType.Name(arm_type)}_{HandType.Name(hand_type)}"
        )

        self._setup_arm()
        self._setup_hand()

    def _setup_arm(self):
        if self.arm_type == ArmType.ARM_TYPE_PIPER:
            self._arm = PiperArm()
        elif self.arm_type == ArmType.ARM_TYPE_NOVA:
            raise NotImplementedError("Nova arm is not implemented yet.")
        else:
            raise ValueError(f"Invalid arm type: {self.arm_type}")

    def _setup_hand(self):
        if self.hand_type == HandType.HAND_TYPE_INSPIRE:
            self._hand = InspireHand()
        elif self.hand_type == HandType.HAND_TYPE_DH:
            raise NotImplementedError("DH hand is not implemented yet.")
        else:
            raise ValueError(f"Invalid hand type: {self.hand_type}")

    def connect(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.connect()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to connect to devices: {e}")

    def disconnect(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.disconnect()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to disconnect to devices: {e}")

    def enable(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.enable()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to enable devices: {e}")

    def disable(self):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                self._arm.disable()
                # self.hand.connect()
            except Exception as e:
                raise Exception(f"Failed to disable devices: {e}")

    def move_to_j(self, joints):
        with self._lock:
            self.__validate_instances()

            assert self._arm is not None
            assert self._hand is not None

            try:
                # move to joints
                pass
            except Exception as e:
                raise Exception(f"Failed to move to joints: {e}")

    def __validate_instances(self):
        if self._arm is None:
            raise Exception("Arm is not set.")
        if self._hand is None:
            raise Exception("Hand is not set.")

    def to_proto(self):
        with self._lock:
            return DexHandProto(
                id=self.id,
                name=self.name,
                side=self.side,
                arm_type=self.arm_type,
                hand_type=self.hand_type,
            )


class DexHandService(DexHandServiceServicer):
    dex_hands: dict[str, DexHandController]

    def __init__(self, dex_hands: dict[str, DexHandController]):
        self.dex_hands = dex_hands

    def ListDexHands(self, request: ListDexHandsRequest, context: ServicerContext):
        LOG.info("ListDexHands request received.")

        return ListDexHandsResponse(
            dex_hands=[dex_hand.to_proto() for dex_hand in self.dex_hands.values()]
        )

    def CreateDexHand(
        self, request: CreateDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("CreateDexHand request received.")

        dex_hand = DexHandController(
            arm_type=request.config.arm_type,
            hand_type=request.config.hand_type,
            side=request.config.side,
        )

        self.dex_hands[dex_hand.id] = dex_hand
        return dex_hand.to_proto()

    def GetDexHand(self, request: GetDexHandRequest, context: grpc.ServicerContext):
        LOG.info("GetDexHand request received.")

        # Validate if DexHand exists
        if request.id not in self.dex_hands:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            return self.dex_hands[request.id].to_proto()

    def DeleteDexHand(
        self, request: DeleteDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("DeleteDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dex_hand.id, None)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dex_hand.id}")
        else:
            del self.dex_hands[dex_hand.id]
            return Empty()


class DexHandControlService(DexHandControlServiceServicer):
    dex_hands: dict[str, DexHandController]

    def __init__(self, dex_hands: dict[str, DexHandController]):
        self.dex_hands = dex_hands

    def ConnectDexHand(
        self, request: ConnectDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("ConnectDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # connect dex_hand
            dex_hand.connect()
            return Empty()

    def DisconnectDexHand(self, request, context):
        LOG.info("DisconnectDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # disconnect dex_hand
            dex_hand.disconnect()
            return Empty()

    def EnableDexHand(
        self, request: EnableDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("EnableDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # enable dex_hand
            dex_hand.enable()
            return Empty()

    def DisableDexHand(
        self, request: DisableDexHandRequest, context: grpc.ServicerContext
    ):
        LOG.info("DisableDexHand request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # disable dex_hand
            dex_hand.disable()
            return Empty()
