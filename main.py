import matplotlib.pyplot as plt
import matplotlib
from matplotlib.animation import FuncAnimation
import json
import math
import queue
import socket
import time
import numpy as np
import pydantic
from piper_sdk import *
import asyncio
from typing import Literal, Optional, Union

from arm_control import BaseArm, PiperArm, PiperArmStatus, PiperJointStatus
# from pydantic.dataclasses import dataclass
from pydantic import BaseModel

from inspire_hand import InspireHand
from kalman import KalmanFilter

from logging import getLogger

logger = getLogger(__name__)

class BaseRequest(BaseModel):
    pass

class TestData(BaseModel):
    x: int
    y: int
    z: int

class ArmEnableRequest(BaseModel):
    command: str = "arm_enable"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]

class ArmDisableRequest(BaseModel):
    command: str = "arm_disable"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]

class ArmGetArmStatusRequest(BaseModel):
    command: str = "arm_get_arm_status"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]

class ArmGetJointStatusRequest(BaseModel):
    command: str = "arm_get_joint_status"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]

class ArmSetJointAnglesRequest(BaseModel):
    command: str = "arm_set_joint_angles"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]
    joint_angles: list

class ArmSetEndEffectorPoseRequest(BaseModel):
    command: str = "arm_set_end_effector_pose"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]
    pose: list

class BoolResponse(BaseModel):
    command: str
    response: bool

class ArmGetArmStatusResponse(BaseModel):
    command: str = "arm_get_arm_status"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]
    response: bool
    arm_status: Optional[PiperArmStatus]

class ArmGetJointStatusResponse(BaseModel):
    command: str = "arm_get_joint_status"
    arm_side: Literal["left", "right"]
    arm_type: Literal["piper", "nova"]
    response: bool
    joint_status: Optional[PiperJointStatus]

class WrappedPose:
    timestamp: float
    pose: list

    def __init__(self, timestamp, pose):
        self.timestamp = timestamp
        self.pose = pose

def plot_data_queue():
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))
    x_data, y_data, z_data = [], [], []
    rx_data, ry_data, rz_data = [], [], []

    def update(frame):
        if not MANAGER.data_queue.empty():
            wrapped_pose = MANAGER.data_queue.get()
            pose = wrapped_pose.pose
            x_data.append(pose[0])
            y_data.append(pose[1])
            z_data.append(pose[2])
            rx_data.append(pose[3])
            ry_data.append(pose[4])
            rz_data.append(pose[5])

            ax[0].clear()
            ax[0].plot(x_data, label='X')
            ax[0].plot(y_data, label='Y')
            ax[0].plot(z_data, label='Z')
            ax[0].legend()
            ax[0].set_title('Position')

            ax[1].clear()
            ax[1].plot(rx_data, label='Rx')
            ax[1].plot(ry_data, label='Ry')
            ax[1].plot(rz_data, label='Rz')
            ax[1].legend()
            ax[1].set_title('Orientation')

    ani = FuncAnimation(fig, update, interval=100)
    plt.show()

class DexHandManager:
    arm_left: Union[PiperArm, None]
    arm_right: Union[PiperArm, None]

    hand_left: Union[InspireHand, None]
    hand_right: Union[InspireHand, None]

    test_mode: bool = False

    data_queue: queue.Queue

    def __init__(self, arm_type="piper", hand_type="inspire", test_mode=False):
        self.test_mode = test_mode
        self.data_queue = queue.Queue(100)

        # plot_data_queue()

        if not self.test_mode:
            if arm_type == "piper":
                self.arm_left = PiperArm()
                self.arm_right = PiperArm()
            else:
                print(f"Unsupported arm type: {arm_type}")

            try:
                self.arm_left.connect()
                self.arm_right.connect()
            except Exception as e:
                print(f"Failed to connect to arm: {e}")
        else:
            if arm_type == "piper":
                self.arm_right = PiperArm()
            else:
                print(f"Unsupported arm type: {arm_type}")

            try:
                self.arm_right.connect()
            except Exception as e:
                print(f"Failed to connect to arm: {e}")

    def arm_enable(self, request: ArmEnableRequest):
        if self.test_mode:
            self.arm_right.enable()

            return BoolResponse(command=request.command, response=True)
        else:
            self.arm_left.enable()
            self.arm_right.enable()

            return BoolResponse(command=request.command, response=True)
    
    def arm_disable(self, request: ArmDisableRequest):
        if self.test_mode:
            self.arm_right.disable()

            return BoolResponse(command=request.command, response=True)
        else:
            self.arm_left.disable()
            self.arm_right.disable()

            return BoolResponse(command=request.command, response=True)
    
    def arm_get_joint_status(self, request: ArmGetJointStatusRequest):
        if self.test_mode:
            if (request.arm_type == "piper"):
                # assert the arm is a PiperArm
                assert isinstance(self.arm_right, PiperArm)
                joint_status = self.arm_right.get_joint_status()
                data = {
                    "command": request.command,
                    "arm_side": request.arm_side,
                    "arm_type": request.arm_type,
                    "response": True,
                    "joint_status": joint_status

                }
                return ArmGetJointStatusResponse(**data)

        # if (request.arm_side == "left"):
        #     if (request.arm_type == "piper"):
        #         # assert the arm is a PiperArm
        #         assert isinstance(self.arm_left, PiperArm)
        #         joint_status = self.arm_left.get_joint_status()
        # elif (request.arm_side == "right"):
        #     if (request.arm_type == "piper"):
        #         # assert the arm is a PiperArm
        #         assert isinstance(self.arm_right, PiperArm)
        #         joint_status = self.arm_right.get_joint_status()
        # if (request.arm_type == "piper"):
        #     # assert the arm is a PiperArm
        #     assert isinstance(self.arm, PiperArm)
        #     joint_status = self.arm.get_joint_status()



    def arm_get_arm_status(self, request: ArmGetArmStatusRequest):
        if self.test_mode:
            if (request.arm_type == "piper"):
                # assert the arm is a PiperArm
                assert isinstance(self.arm_right, PiperArm)
                arm_status = self.arm_right.get_arm_status()
                data = {
                    "command": request.command,
                    "arm_side": request.arm_side,
                    "arm_type": request.arm_type,
                    "response": True,
                    "arm_status": arm_status

                }
                return ArmGetArmStatusResponse(**data)
    
    def arm_set_joint_angles(self, request: ArmSetJointAnglesRequest):
        if self.test_mode:
            if (request.arm_type == "piper"):
                # assert the arm is a PiperArm
                assert isinstance(self.arm_right, PiperArm)
                assert len(request.joint_angles) == 6
                self.arm_right.joint_ctrl(request.joint_angles)
                return BoolResponse(command=request.command, response=True)
    
    def arm_set_end_effector_pose(self, request: ArmSetEndEffectorPoseRequest):
        if self.test_mode:
            if (request.arm_type == "piper"):
                # assert the arm is a PiperArm
                assert isinstance(self.arm_right, PiperArm)
                assert len(request.pose) == 7

                self.data_queue.put(WrappedPose(timestamp=time.time(), pose=request.pose))

                print(f"Pose: {request.pose}, timestamp: {time.time()}")

                # self.arm_right.pose_ctrl(request.pose)
                return BoolResponse(command=request.command, response=True)




MANAGER = DexHandManager(test_mode=True)
# declare the Kalman Filter object
KF: Union[KalmanFilter, None] = None

def initialize_kalman_filter():
    dt = 0.01  # Time step

    # Initial state (example: starting at origin, no rotation, no velocity)
    initial_state = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]  # x, y, z, vx, vy, vz, qw, qx, qy, qz, wx, wy, wz

    # Initial covariance
    initial_covariance = np.diag([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.01, 0.01, 0.01, 0.01, 0.1, 0.1, 0.1])

    # Process noise (tune these values)
    process_noise = np.diag([0.01, 0.01, 0.01, 0.1, 0.1, 0.1, 0.001, 0.001, 0.001, 0.001, 0.01, 0.01, 0.01])

    # Measurement noise (tune these values)
    measurement_noise = np.diag([0.05, 0.05, 0.05, 0.01, 0.01, 0.01, 0.01])

    KF = KalmanFilter(initial_state, initial_covariance, process_noise, measurement_noise, dt)


def start_tcp_server_sync():
    server_ip = "0.0.0.0"
    server_port = 8765
    listen_num = 5
    buffer_size = 1024

    # 1.ソケットオブジェクトの作成
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 2.作成したソケットオブジェクトにIPアドレスとポートを紐づける
    tcp_server.bind((server_ip, server_port))

    # 3.作成したオブジェクトを接続可能状態にする
    tcp_server.listen(listen_num)

    # 4.ループして接続を待ち続ける
    while True:
        # 5.クライアントと接続する
        client,address = tcp_server.accept()
        print("[*] Connected!! [ Source : {}]".format(address))

        # 6.データを受信する
        data = client.recv(buffer_size)
        print("[*] Received Data : {}".format(data))

        # 7.クライアントへデータを返す
        client.send(b"ACK!!")

        # 8.接続を終了させる
        client.close()


def handle_message(message: str) -> BoolResponse:
    json_data = json.loads(message)
    cmd = json_data["command"]
    
    if cmd == "arm_enable":
        request = ArmEnableRequest.model_validate_json(message)
        response = MANAGER.arm_enable(request)
    elif cmd == "arm_disable":
        request = ArmDisableRequest.model_validate_json(message)
        response = MANAGER.arm_disable(request)

    elif cmd == "arm_get_arm_status":
        request = ArmGetArmStatusRequest.model_validate_json(message)
        response = MANAGER.arm_get_arm_status(request)

    elif cmd == "arm_get_joint_status":
        request = ArmGetJointStatusRequest.model_validate_json(message)
        response = MANAGER.arm_get_joint_status(request)

    elif cmd == "arm_set_joint_angles":
        request = ArmSetJointAnglesRequest.model_validate_json(message)
        response = MANAGER.arm_set_joint_angles(request)
    elif cmd == "arm_set_end_effector_pose":
        request = ArmSetEndEffectorPoseRequest.model_validate_json(message)
        response = MANAGER.arm_set_end_effector_pose(request)
    else:
        response = BoolResponse(command=cmd, response=False)

    print(f"Response: {response}")

    return response


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                logger.info(f"Client {addr} disconnected (received 0 bytes).")
                break
            logger.debug(f"Received from {addr}: {data.decode()}")
            writer.write(data) #send back
            await writer.drain()
    except Exception as e:
        logger.exception(f"Error during communication: {e}")
    finally:
        logger.info(f"Closing connection to {addr}.")
        writer.close()
        await writer.wait_closed()  # Ensure closure with asyncio


def start_tcp_server(host='0.0.0.0', port=8765):
    event_loop = asyncio.get_event_loop()

    factory = asyncio.start_server(handle_client, host, port)
    server = event_loop.run_until_complete(factory)

    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        event_loop.run_until_complete(server.wait_closed())
        print('closing event loop')
        event_loop.close()





if __name__ == "__main__":
    start_tcp_server()
    # Start the TCP server in a separate thread
    # import threading
    # server_thread = threading.Thread(target=start_tcp_server)
    # server_thread.start()

    # Plot data from the queue
    # plot_data_queue()
