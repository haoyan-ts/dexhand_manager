from collections import deque
from enum import IntEnum
import logging.handlers
from piper_sdk import *
import time
import math

from scipy.spatial.transform import Rotation as R
import pydantic
from pydantic import BaseModel, ConfigDict, TypeAdapter

from mapping import Complex
from logging import getLogger

LOG = getLogger(__name__)


class BaseArm:
    def connect(self):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def joint_ctrl(self, joints):
        pass

    def get_latest_status(self):
        pass


class MotionCtrl2CtrlMode(IntEnum):
    IDLE = 0x00
    CAN = 0x01
    TEACHING = 0x02
    ETHERNET = 0x03
    WIFI = 0x04
    REMOTE = 0x05
    TEACHING_LINKAGE = 0x06
    OFFLINE_TRAJECTORY = 0x07

class PiperJointStatus(BaseModel):
    joint_1: int
    joint_2: int
    joint_3: int
    joint_4: int
    joint_5: int
    joint_6: int

    def __str__(self):
        return f"joint_1: {self.joint_1}, joint_2: {self.joint_2}, joint_3: {self.joint_3}, " \
               f"joint_4: {self.joint_4}, joint_5: {self.joint_5}, joint_6: {self.joint_6}"

    @staticmethod
    def validate_from_raw(raw_data: C_PiperInterface.ArmJoint):
        data = {
            "timestamp": raw_data.time_stamp,
            "joint_1": raw_data.joint_state.joint_1,
            "joint_2": raw_data.joint_state.joint_2,
            "joint_3": raw_data.joint_state.joint_3,
            "joint_4": raw_data.joint_state.joint_4,
            "joint_5": raw_data.joint_state.joint_5,
            "joint_6": raw_data.joint_state.joint_6
        }

        return PiperJointStatus(**data)

class PiperArmStatus(BaseModel):
    ctrl_mode: int
    arm_status: int
    mode_feed: int
    teach_status: int
    motion_status: int
    trajectory_num: int
    err_code: int

    def __str__(self):
        return f"ctrl_mode: {self.ctrl_mode}, arm_status: {self.arm_status}, mode_feed: {self.mode_feed}, " \
               f"teach_status: {self.teach_status}, motion_status: {self.motion_status}, " \
               f"trajectory_num: {self.trajectory_num}, err_code: {self.err_code}"

    @staticmethod
    def validate_from_raw(raw_data: C_PiperInterface.ArmStatus):
        data = {
            "timestamp": raw_data.time_stamp,
            "ctrl_mode": raw_data.arm_status.ctrl_mode,
            "arm_status": raw_data.arm_status.arm_status,
            "mode_feed": raw_data.arm_status.mode_feed,
            "teach_status": raw_data.arm_status.teach_status,
            "motion_status": raw_data.arm_status.motion_status,
            "trajectory_num": raw_data.arm_status.trajectory_num,
            "err_code": raw_data.arm_status.err_code,
            "err_status": raw_data.arm_status.err_status
        }

        return PiperArmStatus(**data)

class PiperArm(BaseArm):
    piper: C_PiperInterface
    speed_ratio: int = 30
    command_timestamps: deque
    mapping: Complex

    def __init__(self):
        self.command_timestamps = deque(maxlen=10)
        self.mapping = Complex.CreateDefaultComplex()

    def record_timestamp(self):
        self.command_timestamps.append(time.time())

    def calculate_average_rate(self):
        if len(self.command_timestamps) < 2:
            return 0
        stamps = list(self.command_timestamps)
        intervals = [t - s for s, t in zip(stamps, stamps[1:])]

        average_interval = sum(intervals) / len(intervals)
        
        return 1 / average_interval if average_interval > 0 else 0

    def connect(self):
        # self.record_timestamp()
        self.piper = C_PiperInterface()
        self.piper.ConnectPort()

    def enable(self):
        # self.record_timestamp()
        piper = self.piper

        enable_flag = False
        loop_flag = False
        timeout = 5
        start_time = time.time()
        elapsed_time_flag = False

        while not (loop_flag):
            elapsed_time = time.time() - start_time
            print(f"--------------------")
            
            enable_list = []
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_4.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status)
            enable_flag = all(enable_list)

            LOG.debug(f"Enable flags: {enable_list}")


            piper.EnableArm(7)
            # piper.GripperCtrl(0, 1000, 0x00, 0)
            
            print(f"使能状态: {enable_flag}")
            print(f"--------------------")
            
            if(enable_flag == True):
                loop_flag = True
                enable_flag = True
            else: 
                loop_flag = False
                enable_flag = False
            
            if elapsed_time > timeout:
                print(f"超时....")
                elapsed_time_flag = True
                enable_flag = False
                loop_flag = True
                break
            time.sleep(0.5)

        resp = enable_flag
        print(f"Returning response: {resp}")

        return resp
    
    def disable(self):
        # self.record_timestamp()
        piper = self.piper

        enable_flag = False
        loop_flag = False
        timeout = 5
        start_time = time.time()
        elapsed_time_flag = False

        while not (loop_flag):
            elapsed_time = time.time() - start_time
            print(f"--------------------")
            
            enable_list = []
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_4.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status)
            enable_list.append(piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status)

            enable_flag = any(enable_list)

            LOG.debug(f"Enable flags: {enable_list}")

            piper.DisableArm(7)
            piper.GripperCtrl(0, 1000, 0x02, 0)
            
            print(f"使能状态: {enable_flag}")
            print(f"--------------------")
            
            if(enable_flag == False):
                loop_flag = True
                enable_flag = False
            else: 
                loop_flag = False
                enable_flag = True
            
            if elapsed_time > timeout:
                print(f"超时....")
                elapsed_time_flag = True
                enable_flag = True
                loop_flag = True
                break
            time.sleep(0.5)

        resp = enable_flag
        print(f"Returning response: {resp}")

        return resp
    
    def calibrate(self, vertex_targets: list[list[float]]):
        self.mapping.set_targets(vertex_targets)
        
    
    def joint_ctrl(self, joints):
        self.record_timestamp()
        piper = self.piper

        # degree to radian
        factor = 1000

        joint_0 = round(joints[0]*factor)
        joint_1 = round(joints[1]*factor)
        joint_2 = round(joints[2]*factor)
        joint_3 = round(joints[3]*factor)
        joint_4 = round(joints[4]*factor)
        joint_5 = round(joints[5]*factor)

        # joint_6 = round(position[6] * 1000 * 1000)

        piper.MotionCtrl_2(0x01, 0x01, self.speed_ratio, 0x00)
        piper.JointCtrl(joint_0, joint_1, joint_2, joint_3, joint_4, joint_5)
        # piper.GripperCtrl(abs(joint_6), 1000, 0x01, 0)
        piper.MotionCtrl_2(0x01, 0x01, self.speed_ratio, 0x00)

        print(f"freq: {self.calculate_average_rate()} Hz")

    def pose_ctrl(self, pose):
        self.record_timestamp()
        piper = self.piper

        position = pose[:3]
        orientation = pose[3:]

        x = position[0]
        y = position[1]
        z = position[2]
        orientation = orientation

        print(f"Position: {position}")
        print(f"Orientation: {orientation}")

        # Convert Euler angles to quaternion
        # r = R.from_euler('xyz', orientation, degrees=False)
        # quaternion = r.as_quat()


    def get_joint_status(self):
        raw_data = self.piper.GetArmJointMsgs()
        joint_status = PiperJointStatus.validate_from_raw(raw_data)

        return joint_status
    
    def get_arm_status(self) -> ArmMsgStatus:
        raw_data = self.piper.GetArmStatus()

        return raw_data.arm_status

if __name__ == "__main__":
    arm = PiperArm()

    arm.connect()

    status = arm.get_latest_status()
    # print arm status
    print(f"Arm Status: \n{status}")

    arm.enable()
    time.sleep(10)
    arm.disable()

    # average_rate = arm.calculate_average_rate()
    # print(f"Average command sending rate: {average_rate} Hz")
