import asyncio
import logging
import threading
import uuid
from typing import AsyncIterator, Iterable, Iterator, Union

from google.protobuf.empty_pb2 import Empty
from grpc import ServicerContext, StatusCode
from models.arm_control import PiperArm

# Import DexHandController from the new location
from models.dexhand_controller import DexHandController
from models.inspire_hand import InspireHand
from repositories.repository import LocalRepository
from ts.dexhand.v1.common_pb2 import ArmType, HandType, Side
from ts.dexhand.v1.dexhand_control_service_pb2 import (
    ChangeControlModeRequest,
    ConnectDexHandRequest,
    DisableDexHandRequest,
    EnableDexHandRequest,
    GetJointStateRequest,
    GetStatusRequest,
    JointState,
    ModelType,
    ReceiveStatusRequest,
    ReceiveStatusResponse,
    SendPoseRequest,
    SetJointRequest,
    SetPoseRequest,
    SetupInterpolantRequest,
    SetupModelRequest,
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

    def ChangeControlMode(
        self, request: ChangeControlModeRequest, context: ServicerContext
    ):
        LOG.info("ChangeControlMode request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dexhand_id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dexhand_id}")
        else:
            # change control mode
            dex_hand.change_ctrl_mode(request.control_mode)
            return Empty()

    def SetupModel(self, request: SetupModelRequest, context: ServicerContext):
        LOG.info("SetupModel request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dexhand_id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dexhand_id}")
        else:
            # setup model
            if request.model_type == ModelType.MODEL_TYPE_IK:
                raise NotImplementedError("IK model is not implemented yet.")
            elif request.model_type == ModelType.MODEL_TYPE_LERP:
                dex_hand.setup_model(
                    request.model_type,
                    [list(data.angles) for data in request.lerp_model.data],
                )
                return Empty()
            else:
                raise ValueError(f"Invalid model type: {request.model_type}")

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

    def SetupInterpolant(
        self, request: SetupInterpolantRequest, context: ServicerContext
    ):
        LOG.info("SetupInterpolant request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            # setup interpolant
            dex_hand.setup_interpolant(
                request.target.index, list(request.target.angles)
            )
            return Empty()

    def SetPose(self, request: SetPoseRequest, context: ServicerContext):
        LOG.info("SetPose request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dexhand_id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dexhand_id}")
        else:
            # set pose
            dex_hand.move_p(list(request.poses))
            return Empty()

    def SetJoint(self, request: SetJointRequest, context: ServicerContext):
        LOG.info("SetJoint request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dexhand_id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dexhand_id}")
        else:
            # set joint
            dex_hand.move_j(list(request.angles))
            return Empty()

    def GetJointState(self, request: GetJointStateRequest, context: ServicerContext):
        LOG.info("GetJointState request received.")

        # Validate if DexHand exists
        dex_hand = self.dex_hands.get(request.dexhand_id, None)

        if dex_hand is None:
            context.set_code(StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dexhand_id}")
            return None
        else:
            # get status
            status = dex_hand.get_status()
            LOG.info(f"Status: {status}")
            response = JointState()
            response.id = dex_hand.id
            response.name = dex_hand.name
            response.angles.extend(status["joint_states"])
            # Assuming 'status' dictionary contains 'arm_status' and 'joint_states'
            # and that 'arm_status' is a protobuf message that needs to be packed.
            LOG.info(f"Response: {response}")
            return response

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

    def SendPose(
        self, request_iterator: Iterable[SendPoseRequest], context: ServicerContext
    ):
        LOG.info("SendPose request received.")

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
                    # send pose
                    LOG.info(f"Sending pose: {request.packet_request}")
                    dex_hand.move_p(list(request.packet_request.poses))
                    yield Empty()
            elif request_name == "cancel_request":
                LOG.info("Exiting...")
                break

        return Empty()

    async def ReceiveStatus(
        self,
        request_iterator: AsyncIterator[ReceiveStatusRequest],
        context: ServicerContext,
    ):
        # Wait for initial setup request to determine which dex_hand to use.
        dex_hand = None
        async for request in request_iterator:
            if request.WhichOneof("request") == "setup_request":
                if request.setup_request.dexhand_id not in self.dex_hands:
                    context.set_code(StatusCode.NOT_FOUND)
                    context.set_details(
                        f"Invalid DexHand ID: {request.setup_request.dexhand_id}"
                    )
                    return
                dex_hand = self.dex_hands[request.setup_request.dexhand_id]
                break
        if dex_hand is None:
            context.set_code(StatusCode.INVALID_ARGUMENT)
            context.set_details("Setup request missing")
            return

        # Start a background task to catch cancel_request.
        async def check_cancel():
            async for req in request_iterator:
                if req.WhichOneof("request") == "cancel_request":
                    return

        cancel_task = asyncio.create_task(check_cancel())
        try:
            while not cancel_task.done():
                # Get and yield status every second.
                raw_status = dex_hand.get_status()  # assumes async get_status()
                response = ReceiveStatusResponse()
                response.status.id = dex_hand.id
                response.status.name = dex_hand.name
                response.status.data.Pack(raw_status["arm_status"])
                response.status.angles.extend(raw_status["joint_states"])

                yield response
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            cancel_task.cancel()
