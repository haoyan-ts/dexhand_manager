import json
import math
import socket
import time
from piper_sdk import *
import asyncio
import websockets

class TestData:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return TestData(**data)

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=10.0)
            except asyncio.TimeoutError:
                print(f"Connection timeout from {addr}")
                break

            if not data:
                break

            raw_json = data.decode(encoding="utf-8")
            print(f"Received: {raw_json}")
            
            test_data = TestData.from_json(raw_json)

            response = "{response: true}"
            # convert str to bytes
            
            writer.write(response.encode())
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


class DexHandManager:
    tcp_server: socket.socket
    # ws: websockets.Server
    piper: C_PiperInterface

    def __init__(self, host="0.0.0.0", port=8765):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (host, port)
        self.server.bind(self.server_address)

        # self.piper = C_PiperInterface()
        # self.piper.ConnectPort()
        # asyncio.run(start_tcp_server())
        start_tcp_server()
        # start_tcp_server_sync()


    def arm_enable(self):
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

            piper.EnableArm(7)
            piper.GripperCtrl(0, 1000, 0x00, 0)
            
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

    def arm_disable(self):
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
    
    def arm_joint_ctrl(self, joints, speed_ratio=30):
        piper = self.piper

        factor = 1000 * 180 / math.PI
        position = joints

        joint_0 = round(position[0]*factor)
        joint_1 = round(position[1]*factor)
        joint_2 = round(position[2]*factor)
        joint_3 = round(position[3]*factor)
        joint_4 = round(position[4]*factor)
        joint_5 = round(position[5]*factor)

        joint_6 = round(position[6] * 1000 * 1000)

        piper.MotionCtrl_2(0x01, 0x01, speed_ratio, 0x00)
        piper.JointCtrl(joint_0, joint_1, joint_2, joint_3, joint_4, joint_5)
        piper.GripperCtrl(abs(joint_6), 1000, 0x01, 0)
        piper.MotionCtrl_2(0x01, 0x01, speed_ratio, 0x00)

    def arm_status(self):
        return self.piper.GetArmStatus()


if __name__ == "__main__":
    dexhand_manager = DexHandManager()
