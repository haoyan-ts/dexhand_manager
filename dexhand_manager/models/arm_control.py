import logging.handlers
import math
import time
from collections import deque
from enum import IntEnum
from logging import getLogger

import pydantic
import piper_sdk
from pydantic import BaseModel, ConfigDict, TypeAdapter
from scipy.spatial.transform import Rotation as R


from ts.dexhand.v1.common_pb2 import Side
from ts.dexhand.v1.piper_pb2 import (
    ArmMsgStatus as PiperArmStatusProto,
    ArmStatus,
    ControlMode,
    ErrorStatus,
    ModeFeedback,
    MotionStatus,
    TeachStatus,
)

from .mapping import LinearInterpModel

LOG = getLogger(__name__)


class PiperArm:
    _is_connected = False
    _is_enabled = False

    piper: piper_sdk.C_PiperInterface
    speed_ratio: int = 30
    command_timestamps: deque

    def __init__(self):
        self.command_timestamps = deque(maxlen=10)

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
        self.piper = piper_sdk.C_PiperInterface()
        self.piper.ConnectPort()

        self._is_connected = True

    def disconnect(self):
        del self.piper

        self._is_connected = False

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
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_4.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status
            )
            enable_flag = all(enable_list)

            LOG.debug(f"Enable flags: {enable_list}")

            piper.EnableArm(7)
            # piper.GripperCtrl(0, 1000, 0x00, 0)

            print(f"使能状态: {enable_flag}")
            print(f"--------------------")

            if enable_flag == True:
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

        self._is_enabled = True
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
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_4.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status
            )
            enable_list.append(
                piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status
            )

            enable_flag = any(enable_list)

            LOG.debug(f"Enable flags: {enable_list}")

            piper.DisableArm(7)
            piper.GripperCtrl(0, 1000, 0x02, 0)

            print(f"使能状态: {enable_flag}")
            print(f"--------------------")

            if enable_flag == False:
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

        self._is_enabled = False

        return resp

    def change_ctrl_mode(self, mode: int):
        self.piper.MotionCtrl_1(0x00, 0x00, mode)

    def move_j(self, joints: list[float]):
        if not (self._is_enabled and self._is_connected):
            raise ValueError("Arm is not enabled or connected.")

        if len(joints) != 6:
            raise ValueError("Invalid joint values.")

        self.joint_ctrl(joints)

    def joint_ctrl(self, joints):
        self.record_timestamp()
        piper = self.piper

        # degree to radian
        factor = 1000

        joint_0 = round(joints[0] * factor)
        joint_1 = round(joints[1] * factor)
        joint_2 = round(joints[2] * factor)
        joint_3 = round(joints[3] * factor)
        joint_4 = round(joints[4] * factor)
        joint_5 = round(joints[5] * factor)

        # joint_6 = round(position[6] * 1000 * 1000)

        piper.MotionCtrl_2(0x01, 0x01, self.speed_ratio, 0x00)
        piper.JointCtrl(joint_0, joint_1, joint_2, joint_3, joint_4, joint_5)
        # piper.GripperCtrl(abs(joint_6), 1000, 0x01, 0)
        piper.MotionCtrl_2(0x01, 0x01, self.speed_ratio, 0x00)

        # print(f"freq: {self.calculate_average_rate()} Hz")

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

    def get_joint_states(self):
        raw_data = self.piper.GetArmJointMsgs()

        factor = 0.001
        # Process the raw data to list(float)
        joint_status = [
            raw_data.joint_state.joint_1 * factor,
            raw_data.joint_state.joint_2 * factor,
            raw_data.joint_state.joint_3 * factor,
            raw_data.joint_state.joint_4 * factor,
            raw_data.joint_state.joint_5 * factor,
            raw_data.joint_state.joint_6 * factor,
        ]

        return joint_status

    def get_arm_status(self):
        raw_data = self.piper.GetArmStatus().arm_status

        # Process the raw data (ArmMsgStatus) to PiperArmStatusProto
        arm_status = PiperArmStatusProto(
            ctrl_mode=ControlMode.Name(raw_data.ctrl_mode + 1),
            arm_status=ArmStatus.Name(raw_data.arm_status + 1),
            mode_feed=ModeFeedback.Name(raw_data.mode_feed + 1),
            motion_status=MotionStatus.Name(raw_data.motion_status + 1),
            teach_status=TeachStatus.Name(raw_data.teach_status + 1),
            trajectory_num=raw_data.trajectory_num,
            err_code=raw_data.err_code,
            err_status=ErrorStatus(),
        )

        arm_status.err_status.communication_status_joint_1 = (
            raw_data.err_status.communication_status_joint_1
        )
        arm_status.err_status.communication_status_joint_2 = (
            raw_data.err_status.communication_status_joint_2
        )
        arm_status.err_status.communication_status_joint_3 = (
            raw_data.err_status.communication_status_joint_3
        )
        arm_status.err_status.communication_status_joint_4 = (
            raw_data.err_status.communication_status_joint_4
        )
        arm_status.err_status.communication_status_joint_5 = (
            raw_data.err_status.communication_status_joint_5
        )
        arm_status.err_status.communication_status_joint_6 = (
            raw_data.err_status.communication_status_joint_6
        )
        arm_status.err_status.joint_1_angle_limit = (
            raw_data.err_status.joint_1_angle_limit
        )
        arm_status.err_status.joint_2_angle_limit = (
            raw_data.err_status.joint_2_angle_limit
        )
        arm_status.err_status.joint_3_angle_limit = (
            raw_data.err_status.joint_3_angle_limit
        )
        arm_status.err_status.joint_4_angle_limit = (
            raw_data.err_status.joint_4_angle_limit
        )
        arm_status.err_status.joint_5_angle_limit = (
            raw_data.err_status.joint_5_angle_limit
        )
        arm_status.err_status.joint_6_angle_limit = (
            raw_data.err_status.joint_6_angle_limit
        )

        return arm_status


if __name__ == "__main__":
    arm = PiperArm()

    arm.connect()

    # status = arm.get_latest_status()
    # # print arm status
    # print(f"Arm Status: \n{status}")

    arm.enable()
    time.sleep(10)
    arm.disable()

    # average_rate = arm.calculate_average_rate()
    # print(f"Average command sending rate: {average_rate} Hz")
