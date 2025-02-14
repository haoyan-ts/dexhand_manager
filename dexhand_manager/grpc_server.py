import sys
from typing import Iterable, Literal, Union
import uuid
import grpc
from concurrent import futures
from arm_control import PiperArm
from inspire_hand import InspireHand

import ts.dexhand.v1.services_pb2 as dexhand_pb2
import ts.dexhand.v1.services_pb2_grpc as dexhand_pb2_grpc
import ts.dexhand.v1.piper_pb2 as piper_pb2

import time
import logging
from logging import getLogger, config
import json


with open("./dexhand_manager/log_config.json", "r") as f:
    config.dictConfig(json.load(f))

LOG = getLogger(__name__)


class DexHand():
    uuid: str
    side: Literal["left", "right"] = "left"
    arm: Union[PiperArm, None] = None
    hand: Union[InspireHand, None] = None

    world_coordinates: dict[str, dict[str, float]] = {}

    def __init__(self, side: Literal["left", "right"]):
        self.side = side
        self.uuid = str(uuid.uuid4())

    def create_arm(self, type: dexhand_pb2.ArmType):
        if type == dexhand_pb2.ArmType.ARM_TYPE_PIPER:
            self.arm = PiperArm()
            self.arm.connect()
        else:
            raise ValueError(f"Invalid arm type: {type}")
        
    def create_hand(self, type: dexhand_pb2.HandType):
        if type == dexhand_pb2.HandType.HAND_TYPE_INSPIRE:
            self.hand = InspireHand()
        else:
            raise ValueError(f"Invalid hand type: {type}")
        
    def set_arm_pose(self, pose):
        if self.arm is None:
            raise ValueError("Arm not initialized.")
        # self.arm.set_pose(pose)

    def get_arm_status(self):
        if self.arm is None:
            raise ValueError("Arm not initialized.")
        
        raw_status = self.arm.get_arm_status()

        arm_status = piper_pb2.PiperArmStatus()

        # Set the raw status to the arm status
        arm_status.ctrl_mode = piper_pb2.CtrlMode(raw_status.ctrl_mode)
        arm_status.arm_status = piper_pb2.ArmStatus(raw_status.arm_status + 1)
        arm_status.mode_feed = piper_pb2.ModeFeed(raw_status.mode_feed + 1)
        arm_status.teach_status = piper_pb2.TeachStatus(raw_status.teach_status + 1)
        arm_status.motion_status = piper_pb2.MotionStatus(raw_status.motion_status + 1)
        arm_status.trajectory_num = raw_status.trajectory_num
        arm_status.error_code = raw_status.err_code

        return arm_status
    
    def get_arm_joint_status(self):
        if self.arm is None:
            raise ValueError("Arm not initialized.")
        return self.arm.get_joint_status()
    
    def enable(self):
        if self.arm is None or self.hand is None:
            raise ValueError("Arm not initialized.")
        
        self.arm.enable()
        # self.hand.enable()

    def disable(self):
        if self.arm is None or self.hand is None:
            raise ValueError("Arm not initialized.")
        
        self.arm.disable()
        # self.hand.disable()
    
    def enable_arm(self):
        if self.arm is None:
            raise ValueError("Arm not initialized.")
        self.arm.enable()

    def disable_arm(self):
        if self.arm is None:
            raise ValueError("Arm not initialized.")
        self.arm.disable()

    def enable_hand(self):
        if self.hand is None:
            raise ValueError("Hand not initialized.")
        # self.hand.enable()

    def disable_hand(self):
        if self.hand is None:
            raise ValueError("Hand not initialized.")
        # self.hand.disable()
    

class DexHandService(dexhand_pb2_grpc.DexHandControlServiceServicer):
    arms: dict[str, DexHand] = {}
    left: Union[DexHand, None] = None
    right: Union[DexHand, None] = None

    def Create(self, request: dexhand_pb2.CreateRequest, context):
        if self.left is None and request.side == dexhand_pb2.Side.SIDE_LEFT:
            self.left = DexHand("left")
            self.left.create_arm(request.arm)
            self.left.create_hand(request.hand)

            return dexhand_pb2.CreateResponse(success=True, message=self.left.uuid)
        
        if self.right is None and request.side == dexhand_pb2.Side.SIDE_RIGHT:
            self.right = DexHand("right")
            self.right.create_arm(request.arm)
            self.right.create_hand(request.hand)

            return dexhand_pb2.CreateResponse(success=True, message=self.right.uuid)

        LOG.warning("Hand already created.")
        return dexhand_pb2.CreateResponse(success=False, message="Hand already created.")


    def Enable(self, request: dexhand_pb2.EnableRequest, context):
        LOG.info("Enable request received.")

        if self.left != None and request.uuid == self.left.uuid:
            self.left.enable()
            return dexhand_pb2.EnableResponse(success=True, message="Left hand enabled.")
        
        if self.right != None and request.uuid == self.right.uuid:
            self.right.enable()
            return dexhand_pb2.EnableResponse(success=True, message="Right hand enabled.")
    
        return dexhand_pb2.EnableResponse(success=False, message="Invalid UUID.")
    
    def Disable(self, request: dexhand_pb2.DisableRequest, context):
        LOG.info("Disable request received.")

        if self.left != None and request.uuid == self.left.uuid:
            self.left.disable()
            return dexhand_pb2.DisableResponse(success=True)
        
        if self.right != None and request.uuid == self.right.uuid:
            self.right.disable()
            return dexhand_pb2.DisableResponse(success=True)
        
        return dexhand_pb2.DisableResponse(success=False, message="Invalid UUID.")
    
    def CalibrateWorldCoordinates(self, request: dexhand_pb2.CalibrateWorldCoordinatesRequest, context):
        LOG.info("CalibrateWorldCoordinates request received.")

        if self.left != None and request.uuid == self.left.uuid:
            idx = request.idx

        return super().CalibrateWorldCoornates(request, context)

    def CalibrateComplex(self, request: dexhand_pb2.CalibrateComplexRequest, context):
        return super().CalibrateComplex(request, context)
    
    def GetArmStatus(self, request: dexhand_pb2.GetArmStatusRequest, context):
        LOG.info("GetArmStatus request received.")

        if self.left != None and request.uuid == self.left.uuid:
            piper_status = self.left.get_arm_status()

            return dexhand_pb2.GetArmStatusResponse(success=True, details=piper_status)

        return dexhand_pb2.GetArmStatusResponse(success=False, details=None)
    
    def GetArmJointStatus(self, request, context):
        return super().GetArmJointStatus(request, context)
    
    def SetArmPoseStream(self, request_iterator: Iterable[dexhand_pb2.SetArmPoseRequest], context):
        LOG.info(f"SetPoseStream request received. Starting to stream...")
        last_time = time.time()

        try:
            for request in request_iterator:
                # print delta time
                
                LOG.info(f"Received request. {time.time() - last_time}s since last request.")
                last_time = time.time()
                # yield
        except Exception as e:
            LOG.error(f"Error while streaming: {e}")
            raise
        finally:
            LOG.info("Stream ended.")
            return dexhand_pb2.SetArmPoseResponse(success=True)
        
    def SetArmJointStream(self, request_iterator: Iterable[dexhand_pb2.SetArmJointStreamRequest], context):
        LOG.info(f"SetJointStream request received. Starting to stream...")
        last_time = time.time()

        try:
            for request in request_iterator:
                # print delta time
                
                LOG.info(f"Received request. {time.time() - last_time}s since last request.")
                LOG.info(f"[{request.seq_num}] Joint angles: {request.angles}")
                last_time = time.time()
                # yield
        except Exception as e:
            LOG.error(f"Error while streaming: {e}")
            raise
        finally:
            LOG.info("Stream ended.")
            return dexhand_pb2.SetArmPoseResponse(success=True)

    
    def SetArmPose(self, request, context):
        return super().SetArmPose(request, context)
    
    def SetArmJoint(self, request, context):
        return super().SetArmJoint(request, context)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dexhand_pb2_grpc.add_DexHandControlServiceServicer_to_server(DexHandService(), server)
    server.add_insecure_port('[::]:50051')  # Use [::] for IPv6 and IPv4
    server.start()
    logging.info("Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()