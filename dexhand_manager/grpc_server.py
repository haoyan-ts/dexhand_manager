import sys
from typing import Iterable, Literal, Union
import uuid
import grpc
from concurrent import futures
from arm_control import PiperArm
from inspire_hand import InspireHand

import ts.dexhand.v1.services_pb2 as dexhand_pb2
import ts.dexhand.v1.services_pb2_grpc as dexhand_pb2_grpc
import ts.dexhand.v1.dexhand_service_pb2 as dexhand_srv_pb2
import ts.dexhand.v1.dexhand_service_pb2_grpc as dexhand_srv_pb2_grpc
import ts.dexhand.v1.piper_pb2 as piper_pb2

from ts.dexhand.v1.dexhand_service_pb2 import *
from ts.dexhand.v1.services_pb2 import Side, ArmType, HandType

from google.protobuf.empty_pb2 import Empty

import time
import logging
from logging import getLogger, config
import json


with open("./dexhand_manager/log_config.json", "r") as f:
    config.dictConfig(json.load(f))

LOG = getLogger(__name__)

class DexHandEntity():
    id = ""
    name = ""
    side = Side.SIDE_UNSPECIFIED
    arm_type = ArmType.ARM_TYPE_UNSPECIFIED
    hand_type = HandType.HAND_TYPE_UNSPECIFIED

    arm = None
    hand = None

    def __init__(self):
        self.id = str(uuid.uuid4())
   
    def create(self, config: DexHandConfig):
        kwargs = {
            "side": config.side,
            "arm_type": config.arm_type,
            "hand_type": config.hand_type
        }
        self._update_from_dict(**kwargs)

        self._create_arm()
        self._create_hand()

    def update(self, dex_hand: DexHand):
        kwargs = {
            "side": dex_hand.side,
            "arm_type": dex_hand.arm_type,
            "hand_type": dex_hand.hand_type
        }

        self._update_from_dict(**kwargs)

    def _update_from_dict(self, **kwargs):
        for key, item in kwargs.items():
            if key == "side":
                self._update_side(item)
            elif key == "arm_type":
                self._update_arm_type(item)
            elif key == "hand_type":
                self._update_hand_type(item)

        self.name = ArmType.Name(self.arm_type) + "_" + HandType.Name(self.hand_type) + "_" + Side.Name(self.side)

    def _update_side(self, side: Side):
        if side == Side.SIDE_UNSPECIFIED:
            raise ValueError("Side cannot be unspecified.")
        else:
            self.side = side

    def _update_arm_type(self, arm_type: ArmType):
        if arm_type == ArmType.ARM_TYPE_UNSPECIFIED:
            raise ValueError("Arm type cannot be unspecified.")
        else:
            self.arm_type = arm_type

    def _update_hand_type(self, hand_type: HandType):
        if hand_type == HandType.HAND_TYPE_UNSPECIFIED:
            raise ValueError("Hand type cannot be unspecified.")
        else:
            self.hand_type = hand_type

    def _create_arm(self):
        if self.arm_type == dexhand_pb2.ArmType.ARM_TYPE_PIPER:
            self.arm = PiperArm()
            # self.arm.connect()
        else:
            raise ValueError(f"Invalid arm type: {self.arm_type}")
    
    def _create_hand(self):
        if self.hand_type == dexhand_pb2.HandType.HAND_TYPE_INSPIRE:
            self.hand = InspireHand()
        else:
            raise ValueError(f"Invalid hand type: {self.hand_type}")

    def __str__(self):
        return f"id: {self.id}, side: {self.side}, arm_type: {self.arm_type}, hand_type: {self.hand_type}"

    def __repr__(self):
        return self.__str__()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "side": self.side,
            "arm_type": self.arm_type,
            "hand_type": self.hand_type
        }
    

class Repository:
    dex_hands: dict[Side, DexHandEntity] = {}

    def validate_create_dex_hand_request(self, request: dexhand_srv_pb2.CreateDexHandRequest):
        tester = self.dex_hands.get(request.config.side, None)
       
        return True if tester is None else False
        

    def create_dex_hand_from_config(self, config: DexHandConfig):
        dex_hand = DexHandEntity()
        dex_hand.create(config)

        self.dex_hands[dex_hand.side] = dex_hand

        return dex_hand
    
    def get_dex_hand_by_id(self, id: str):
        for dex_hand in self.dex_hands.values():
            if dex_hand.id == id:
                return dex_hand
        return None
    
    def get_dex_hand_by_name(self, name: str):
        for dex_hand in self.dex_hands.values():
            if dex_hand.name == name:
                return dex_hand
        return None
    
    def get_dex_hand_by_side(self, side: Side):
        return self.dex_hands.get(side, None)
    
    def update_dex_hand(self, request: dexhand_srv_pb2.UpdateDexHandRequest):
        dex_hand = self.get_dex_hand_by_id(request.dex_hand.id)
        LOG.debug(f"Received a update mask. {request.update_mask}")

        if dex_hand is None:
            raise grpc.RpcError(grpc.StatusCode.NOT_FOUND, f"Invalid DexHand ID: {request.dex_hand.id}")
        else:
            dex_hand.update(request.dex_hand)
            return dex_hand
        


class DexHandService(dexhand_srv_pb2_grpc.DexHandServiceServicer):
    repository: Repository = Repository()

    def ListDexHands(self, request: dexhand_srv_pb2.ListDexHandsRequest, context: grpc.ServicerContext):
        LOG.info("ListDexHands request received.")

        dex_hands = [dexhand_srv_pb2.DexHand(**dex_hand.to_dict()) for dex_hand in self.repository.dex_hands.values()]

        return dexhand_srv_pb2.ListDexHandsResponse(dex_hands=dex_hands)

    def CreateDexHand(self, request: dexhand_srv_pb2.CreateDexHandRequest, context: grpc.ServicerContext):
        LOG.info("CreateDexHand request received.")
        
        if not self.repository.validate_create_dex_hand_request(request):
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"DexHand already exists on the side: {Side.Name(request.config.side)}")
            return Empty()
        else:
            dex_hand = self.repository.create_dex_hand_from_config(request.config)
            
            return dexhand_srv_pb2.DexHand(**dex_hand.to_dict())
    
    def GetDexHand(self, request: dexhand_srv_pb2.GetDexHandRequest, context: grpc.ServicerContext):
        LOG.info("GetDexHand request received.")

        dex_hand = self.repository.get_dex_hand_by_id(request.id)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.id}")
        else:
            return dexhand_srv_pb2.DexHand(**dex_hand.to_dict())
        
    def UpdateDexHand(self, request: dexhand_srv_pb2.UpdateDexHandRequest, context: grpc.ServicerContext):
        LOG.info("UpdateDexHand request received.")

        try:
            dex_hand = self.repository.update_dex_hand(request)
        except grpc.RpcError as e:
            LOG.error(f"Error while updating DexHand: {e}")

            context.set_code(e.args[0])
            context.set_details(e.args[1])
        
        return dexhand_srv_pb2.DexHand(**dex_hand.to_dict())
    
    def DeleteDexHand(self, request: dexhand_srv_pb2.DeleteDexHandRequest, context: grpc.ServicerContext):
        LOG.info("DeleteDexHand request received.")

        dex_hand = self.repository.get_dex_hand_by_id(request.dex_hand.id)

        if dex_hand is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Invalid DexHand ID: {request.dex_hand.id}")
        else:
            del self.repository.dex_hands[dex_hand.side]
            return Empty()


# class DexHandService(dexhand_srv_pb2_grpc.DexHandServiceServicer):
#     id: str
#     side: dexhand_pb2.Side
#     arm: Union[PiperArm, None] = None
#     hand: Union[InspireHand, None] = None

#     world_coordinates: dict[str, dict[str, float]] = {}


#     def CreateDexHand(self, request: dexhand_srv_pb2.CreateDexHandRequest, context):
#         LOG.info("CreateDexHand request received.")

#         try:
#             self.create_from_config(request.config)
#         except Exception as e:
#             LOG.error(f"Error while creating DexHand: {e}")

#             return dexhand_srv_pb2.DexHand(**self)

#         return dexhand_srv_pb2.CreateDexHandResponse(success=True, message=self.id)
#             raise
#         self.create_from_config(request.config)

#         return super().CreateDexHand(request, context)

#     def create_arm(self, type: dexhand_pb2.ArmType):
#         if type == dexhand_pb2.ArmType.ARM_TYPE_PIPER:
#             self.arm = PiperArm()
#             self.arm.connect()
#         else:
#             raise ValueError(f"Invalid arm type: {type}")
        
#     def create_hand(self, type: dexhand_pb2.HandType):
#         if type == dexhand_pb2.HandType.HAND_TYPE_INSPIRE:
#             self.hand = InspireHand()
#         else:
#             raise ValueError(f"Invalid hand type: {type}")
        
#     def set_arm_pose(self, pose):
#         if self.arm is None:
#             raise ValueError("Arm not initialized.")
#         # self.arm.set_pose(pose)

#     def get_arm_status(self):
#         if self.arm is None:
#             raise ValueError("Arm not initialized.")
        
#         raw_status = self.arm.get_arm_status()

#         arm_status = piper_pb2.PiperArmStatus()

#         # Set the raw status to the arm status
#         arm_status.ctrl_mode = piper_pb2.CtrlMode(raw_status.ctrl_mode)
#         arm_status.arm_status = piper_pb2.ArmStatus(raw_status.arm_status + 1)
#         arm_status.mode_feed = piper_pb2.ModeFeed(raw_status.mode_feed + 1)
#         arm_status.teach_status = piper_pb2.TeachStatus(raw_status.teach_status + 1)
#         arm_status.motion_status = piper_pb2.MotionStatus(raw_status.motion_status + 1)
#         arm_status.trajectory_num = raw_status.trajectory_num
#         arm_status.error_code = raw_status.err_code

#         return arm_status
    
#     def get_arm_joint_status(self):
#         if self.arm is None:
#             raise ValueError("Arm not initialized.")
#         return self.arm.get_joint_status()
    
#     def enable(self):
#         if self.arm is None or self.hand is None:
#             raise ValueError("Arm not initialized.")
        
#         self.arm.enable()
#         # self.hand.enable()

#     def disable(self):
#         if self.arm is None or self.hand is None:
#             raise ValueError("Arm not initialized.")
        
#         self.arm.disable()
#         # self.hand.disable()
    
#     def enable_arm(self):
#         if self.arm is None:
#             raise ValueError("Arm not initialized.")
#         self.arm.enable()

#     def disable_arm(self):
#         if self.arm is None:
#             raise ValueError("Arm not initialized.")
#         self.arm.disable()

#     def enable_hand(self):
#         if self.hand is None:
#             raise ValueError("Hand not initialized.")
#         # self.hand.enable()

#     def disable_hand(self):
#         if self.hand is None:
#             raise ValueError("Hand not initialized.")
#         # self.hand.disable()
    

# # class DexHandService(dexhand_srv_pb2_grpc.DexHandServiceServicer):
#     arms: dict[str, DexHand] = {}
#     left: Union[DexHand, None] = None
#     right: Union[DexHand, None] = None


#     def Create(self, request: dexhand_pb2.CreateRequest, context):
#         if self.left is None and request.side == dexhand_pb2.Side.SIDE_LEFT:
#             self.left = DexHand("left")
#             self.left.create_arm(request.arm)
#             self.left.create_hand(request.hand)

#             return dexhand_pb2.CreateResponse(success=True, message=self.left.id)
        
#         if self.right is None and request.side == dexhand_pb2.Side.SIDE_RIGHT:
#             self.right = DexHand("right")
#             self.right.create_arm(request.arm)
#             self.right.create_hand(request.hand)

#             return dexhand_pb2.CreateResponse(success=True, message=self.right.id)

#         LOG.warning("Hand already created.")
#         return dexhand_pb2.CreateResponse(success=False, message="Hand already created.")


#     def Enable(self, request: dexhand_pb2.EnableRequest, context):
#         LOG.info("Enable request received.")

#         if self.left != None and request.uuid == self.left.id:
#             self.left.enable()
#             return dexhand_pb2.EnableResponse(success=True, message="Left hand enabled.")
        
#         if self.right != None and request.uuid == self.right.id:
#             self.right.enable()
#             return dexhand_pb2.EnableResponse(success=True, message="Right hand enabled.")
    
#         return dexhand_pb2.EnableResponse(success=False, message="Invalid UUID.")
    
#     def Disable(self, request: dexhand_pb2.DisableRequest, context):
#         LOG.info("Disable request received.")

#         if self.left != None and request.uuid == self.left.id:
#             self.left.disable()
#             return dexhand_pb2.DisableResponse(success=True)
        
#         if self.right != None and request.uuid == self.right.id:
#             self.right.disable()
#             return dexhand_pb2.DisableResponse(success=True)
        
#         return dexhand_pb2.DisableResponse(success=False, message="Invalid UUID.")
    
#     def CalibrateWorldCoordinates(self, request: dexhand_pb2.CalibrateWorldCoordinatesRequest, context):
#         LOG.info("CalibrateWorldCoordinates request received.")

#         if self.left != None and request.uuid == self.left.id:
#             idx = request.idx

#         return super().CalibrateWorldCoornates(request, context)

#     def CalibrateComplex(self, request: dexhand_pb2.CalibrateComplexRequest, context):
#         return super().CalibrateComplex(request, context)
    
#     def GetArmStatus(self, request: dexhand_pb2.GetArmStatusRequest, context):
#         LOG.info("GetArmStatus request received.")

#         if self.left != None and request.uuid == self.left.id:
#             piper_status = self.left.get_arm_status()

#             return dexhand_pb2.GetArmStatusResponse(success=True, details=piper_status)

#         return dexhand_pb2.GetArmStatusResponse(success=False, details=None)
    
#     def GetArmJointStatus(self, request, context):
#         return super().GetArmJointStatus(request, context)
    
#     def SetArmPoseStream(self, request_iterator: Iterable[dexhand_pb2.SetArmPoseRequest], context):
#         LOG.info(f"SetPoseStream request received. Starting to stream...")
#         last_time = time.time()

#         try:
#             for request in request_iterator:
#                 # print delta time
                
#                 LOG.info(f"Received request. {time.time() - last_time}s since last request.")
#                 last_time = time.time()
#                 # yield
#         except Exception as e:
#             LOG.error(f"Error while streaming: {e}")
#             raise
#         finally:
#             LOG.info("Stream ended.")
#             return dexhand_pb2.SetArmPoseResponse(success=True)
        
#     def SetArmJointStream(self, request_iterator: Iterable[dexhand_pb2.SetArmJointStreamRequest], context):
#         LOG.info(f"SetJointStream request received. Starting to stream...")
#         last_time = time.time()

#         try:
#             for request in request_iterator:
#                 # print delta time
                
#                 LOG.info(f"Received request. {time.time() - last_time}s since last request.")
#                 LOG.info(f"[{request.seq_num}] Joint angles: {request.angles}")
#                 last_time = time.time()
#                 # yield
#         except Exception as e:
#             LOG.error(f"Error while streaming: {e}")
#             raise
#         finally:
#             LOG.info("Stream ended.")
#             return dexhand_pb2.SetArmPoseResponse(success=True)

    
#     def SetArmPose(self, request, context):
#         return super().SetArmPose(request, context)
    
#     def SetArmJoint(self, request, context):
#         return super().SetArmJoint(request, context)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dexhand_srv_pb2_grpc.add_DexHandServiceServicer_to_server(DexHandService(), server)
    server.add_insecure_port('[::]:50051')  # Use [::] for IPv6 and IPv4
    server.start()
    logging.info("Server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()