import json
import math
import socket
import time
import pydantic
from piper_sdk import *
import asyncio
from typing import Literal, Optional, Union

from arm_control import BaseArm, PiperArm, PiperArmStatus, PiperJointStatus
# from pydantic.dataclasses import dataclass
from pydantic import BaseModel

from inspire_hand import InspireHand


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



class DexHandManager:
    arm_left: Union[PiperArm, None]
    arm_right: Union[PiperArm, None]

    hand_left: Union[InspireHand, None]
    hand_right: Union[InspireHand, None]

    test_mode: bool = False

    def __init__(self, arm_type="piper", hand_type="inspire", test_mode=False):
        self.test_mode = test_mode

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




MANAGER = DexHandManager(test_mode=True)

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
    else:
        response = BoolResponse(command=cmd, response=False)

    print(f"Response: {response}")

    return response


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=100.0)
            except asyncio.TimeoutError:
                print(f"Connection timeout from {addr}")
                break

            if not data:
                break

            raw_json = data.decode(encoding="utf-8")
            print(f"Received: {raw_json}")
            
            # test_data = TestData.from_json(raw_json)
            response = handle_message(raw_json)

            writer.write(response.model_dump_json().encode(encoding="utf-8"))
            await writer.drain()
    except asyncio.CancelledError:
        pass
    finally:
        print(f"Disconnected by {addr}")
        writer.close()
        await writer.wait_closed()


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
