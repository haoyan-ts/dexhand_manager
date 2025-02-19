import serial
import time
import asyncio

regdict = {
    "ID": 1000,
    "baudrate": 1001,
    "clearErr": 1004,
    "forceClb": 1009,
    "angleSet": 1486,
    "forceSet": 1498,
    "speedSet": 1522,
    "angleAct": 1546,
    "forceAct": 1582,
    "errCode": 1606,
    "statusCode": 1612,
    "temp": 1618,
    "actionSeq": 2320,
    "actionRun": 2322,
}


class InspireHand:
    ser: serial.Serial

    def __init__(self):
        pass

    def open_serial(self, port, baudrate):
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = baudrate
        ser.open()
        return ser

    def write_register(self, id, addr, num, val):
        bytes = [0xEB, 0x90]
        bytes.append(id)  # id
        bytes.append(num + 3)  # len
        bytes.append(0x12)  # cmd
        bytes.append(addr & 0xFF)
        bytes.append((addr >> 8) & 0xFF)  # add
        for i in range(num):
            bytes.append(val[i])
        checksum = 0x00
        for i in range(2, len(bytes)):
            checksum += bytes[i]
        checksum &= 0xFF
        bytes.append(checksum)
        self.ser.write(bytearray(bytes))

        time.sleep(0.01)

        self.ser.read_all()  # 把返回帧读掉，不处理

    def read_register(self, id, addr, num, verbose=False):
        bytes = [0xEB, 0x90]
        bytes.append(id)  # id
        bytes.append(0x04)  # len
        bytes.append(0x11)  # cmd
        bytes.append(addr & 0xFF)
        bytes.append((addr >> 8) & 0xFF)  # add
        bytes.append(num)
        checksum = 0x00
        for i in range(2, len(bytes)):
            checksum += bytes[i]
        checksum &= 0xFF
        bytes.append(checksum)
        self.ser.write(bytearray(bytes))

        time.sleep(0.01)

        recv = self.ser.read_all()

        if recv is None or len(recv) == 0:
            return []
        num = (recv[3] & 0xFF) - 3
        val = []
        for i in range(num):
            val.append(recv[7 + i])

        if verbose:
            print("读到的寄存器值依次为：", end="")
            for i in range(num):
                print(val[i], end=" ")
            print()

        return val

    # def write6(self, id, str, val):
    #     if str == 'angleSet' or str == 'forceSet' or str == 'speedSet':
    #         val_reg = []
    #         for i in range(6):
    #             val_reg.append(val[i] & 0xFF)
    #             val_reg.append((val[i] >> 8) & 0xFF)
    #         self.write_register(id, regdict[str], 12, val_reg)
    #     else:
    #         print('函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'，val为长度为6的list，值为0~1000，允许使用-1作为占位符')

    def read6(self, id, str):
        if str not in regdict:
            print(f"Incorrect command.")
            return
        len = 6
        # str == 'errCode' or str == 'statusCode' or str == 'temp':
        val_act = self.read_register(id, regdict[str], len, True)
        if val_act is None or len(val_act) < len:
            print("没有读到数据")
            return
        print("读到的值依次为：", end="")
        for i in range(len):
            print(val_act[i], end=" ")
        print()

    def read12(self, id, str):
        if str not in regdict:
            print(f"Incorrect command.")
            return

        len = 12
        # if str == 'angleSet' or str == 'forceSet' or str == 'speedSet' or str == 'angleAct' or str == 'forceAct':
        val = self.read_register(id, regdict[str], len, True)
        if len(val) < len:
            print("没有读到数据")
            return
        val_act = []
        for i in range(len / 2):
            val_act.append((val[2 * i] & 0xFF) + (val[1 + 2 * i] << 8))
        print("读到的值依次为：", end="")

        for i in range(len / 2):
            print(val_act[i], end=" ")
        print()

    def set_angle(self, hand_id, angles):
        val_reg = []
        for angle in angles:
            val_reg.append(angle & 0xFF)
            val_reg.append((angle >> 8) & 0xFF)

        self.write_register(hand_id, regdict["angleSet"], 12, val_reg)

    def set_pos(self, hand_id, positions):
        val_reg = []
        for pos in positions:
            val_reg.append(pos & 0xFF)
            val_reg.append((pos >> 8) & 0xFF)

        self.write_register(hand_id, regdict["angleSet"], 12, val_reg)

    def set_speed(self, hand_id, speeds):
        val_reg = []
        for speed in speeds:
            val_reg.append(speed & 0xFF)
            val_reg.append((speed >> 8) & 0xFF)

        self.write_register(hand_id, regdict["speedSet"], 12, val_reg)

    def set_force(self, hand_id, forces):
        val_reg = []
        for force in forces:
            val_reg.append(force & 0xFF)
            val_reg.append((force >> 8) & 0xFF)

        self.write_register(hand_id, regdict["forceSet"], 12, val_reg)

    # def set_wristangle(self, hand_id, yaw, pitch):
    #     val_reg = [
    #         (yaw - 2550) & 0xFF, ((yaw - 2550) >> 8) & 0xFF,
    #         (pitch - 2266) & 0xFF, ((pitch - 2266) >> 8) & 0xFF
    #     ]

    #     self.write_register(hand_id, regdict['angleSet'], 4, val_reg)

    # def getwristangleact(self, hand_id):
    # return self.read6(hand_id, 'angleAct')

    def getangleact(self, hand_id):
        return self.read12(hand_id, "angleAct")

    def getangleset(self, hand_id):
        return self.read12(hand_id, "angleSet")

    def getposact(self, hand_id):
        return self.read12(hand_id, "angleAct")

    def getposset(self, hand_id):
        return self.read12(hand_id, "angleSet")

    def getspeedset(self, hand_id):
        return self.read12(hand_id, "speedSet")

    def getforceact(self, hand_id):
        return self.read12(hand_id, "forceAct")

    def getforceset(self, hand_id):
        return self.read12(hand_id, "forceSet")

    def getcurrentact(self, hand_id):
        return self.read6(hand_id, "angleAct")

    def geterror(self, hand_id):
        return self.read6(hand_id, "errCode")

    def gettemp(self, hand_id):
        return self.read6(hand_id, "temp")

    # def getwristangleset(self, hand_id):
    #     return self.read6(hand_id, 'angleSet')

    # def getwristposact(self, hand_id):
    #     return self.read6(hand_id, 'angleAct')

    # def getwristposset(self, hand_id):
    #     return self.read6(hand_id, 'angleSet')

    # def getwristcurrentact(self, hand_id):
    #     return self.read6(hand_id, 'angleAct')

    # def getwristerror(self, hand_id):
    #     return self.read6(hand_id, 'errCode')

    # def getwristtemp(self, hand_id):
    #     return self.read6(hand_id, 'temp')


if __name__ == "__main__":
    print("打开串口！")
    hand_api = InspireHand(
        "/dev/ttyACM0", 115200
    )  # 改成自己的串口号和波特率，波特率默认115200
    print("设置灵巧手运动速度参数，-1为不设置该运动速度！")
    hand_api.set_speed(1, [100, 100, 100, 100, 100, 100])
    time.sleep(2)
    print("设置灵巧手抓握力度参数！")
    hand_api.set_force(1, [500, 500, 500, 500, 500, 500])
    time.sleep(1)
    print("设置灵巧手运动角度参数0，-1为不设置该运动角度！")
    hand_api.set_angle(1, [0, 0, 0, 0, 400, -1])
    time.sleep(3)
    hand_api.getangleact(1)
    time.sleep(1)
    print("设置灵巧手运动角度参数1000，-1为不设置该运动角度！")
    hand_api.set_angle(1, [1000, 1000, 1000, 1000, 400, -1])
    time.sleep(3)
    hand_api.getangleact(1)
    time.sleep(1)
    hand_api.geterror(1)
    time.sleep(1)
    print("设置灵巧手动作库序列：8！")
    hand_api.write_register(1, regdict["actionSeq"], 1, [8])
    time.sleep(1)
    print("运行灵巧手当前序列动作！")
    hand_api.write_register(1, regdict["actionRun"], 1, [1])
    # hand_api.write_register(1, regdict['forceClb'], 1, [1])
    # time.sleep(10) # 由于力校准时间较长，请不要漏过这个sleep并尝试重新与手通讯，可能导致插件崩溃
