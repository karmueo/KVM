# @File     : WenZiShiBie.py
# @Author   : 沈昌力
# @Date     :2018/11/20
# @Desc     :
import pytesseract
import os
import configparser
import win32gui, win32ui, win32con, win32api
from PIL import Image
from pykeyboard import PyKeyboard
import time
import logging
from logging.config import fileConfig
import threading
import UdpInterface

fileConfig('Config/logging.conf')
logger = logging.getLogger('warninglogger')
logger.warning('warning')



class kvm_event():
    def __init__(self, wnd_class, wnd_name, server_ip, server_port):
        self.handle = handle = win32gui.FindWindow(wnd_class, wnd_name)
        assert self.handle is not 0, "无法获取KVM的窗口句柄"
        self.udp = UdpInterface.UdpClient(server_ip, int(server_port))
        # self.udp.send(b'-1')

    def parse_cfg(self, cfgfile):
        fp = open(cfgfile, 'r')
        blocks = []
        block = None
        line = fp.readline()
        while line != "":
            line = line.rstrip()
            if line == '' or line[0] == '#':
                line = fp.readline()
                continue
            elif line[0] == '[':
                if block:
                    blocks.append(block)
                block = dict()
                block['type'] = line.lstrip('[').rstrip(']')
            else:
                key, value = line.split('=')
                key = key.strip()
                value = value.strip()
                block[key] = value
            line = fp.readline()

        if block:
            blocks.append(block)
        fp.close()
        return blocks

    def keydown_test(self):
        win32gui.SetForegroundWindow(self.handle)
        win32gui.SetWindowPos(self.handle, win32con.HWND_TOPMOST)
        # win32gui.SetForegroundWindow(self.handle)
        k = PyKeyboard()
        k.tap_key('7')
        # k.tap_key(k.backspace_key)
        print('7')

    def kvm_key_down(self, key):
        k = PyKeyboard()
        win32gui.SetForegroundWindow(self.handle)
        if key == '7':
            print("send keydown '7'")
            k.tap_key('7')
            win32gui.PostMessage(self.handle, win32con.WM_KEYDOWN, 55, 0)
        elif key == '2':
            print("send keydown '2'")
            k.tap_key('2')
            win32gui.PostMessage(self.handle, win32con.WM_KEYDOWN, 50, 0)
        elif key == '3':
            print("send keydown '3'")
            k.tap_key('3')
        elif key == 'esc':
            print("send keydown 'esc'")
            k.tap_key(k.escape_key)
            win32gui.PostMessage(self.handle, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
        elif key == 'f1':
            print("send keydown 'f1'")
            k.tap_key(k.function_keys[1])
            win32gui.PostMessage(self.handle, win32con.WM_KEYDOWN, win32con.VK_F1, 0)
        elif key == 'enter':
            print("send keydown 'enter'")
            k.tap_key(k.enter_key)
        else:
            return

    def window_capture(self, filename):
        """
        截图
        :param filename:
        :return:
        """
        # hwnd = 0 # 窗口的编号，0号表示当前活跃窗口
        # 根据窗口句柄获取窗口的设备上下文DC（Divice Context）
        hwndDC = win32gui.GetWindowDC(self.handle)
        # 根据窗口的DC获取mfcDC
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        # mfcDC创建可兼容的DC
        saveDC = mfcDC.CreateCompatibleDC()
        # 创建bigmap准备保存图片
        saveBitMap = win32ui.CreateBitmap()
        # 获取监控器信息
        MoniterDev = win32api.EnumDisplayMonitors(None, None)
        w = MoniterDev[0][2][2]
        h = MoniterDev[0][2][3]
        # print w,h　　　#图片大小
        # 为bitmap开辟空间
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        # 高度saveDC，将截图保存到saveBitmap中
        saveDC.SelectObject(saveBitMap)
        # 截取从左上角（0，0）长宽为（w，h）的图片
        saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
        saveBitMap.SaveBitmapFile(saveDC, filename)

    def process_first(self, block):
        for i in range(int(block['key_tap_times'])):
            self.kvm_key_down(block['key_down'])
        # 等1秒
        time.sleep(1)
        # 截图
        img_path = block['capture_save_path']
        self.window_capture(img_path)

    def process_block(self, block):
        # 文字识别框
        box = (int(block['box_tl_x']),
               int(block['box_tl_y']),
               int(block['box_br_x']),
               int(block['box_br_y']))

        if 'time_out' in block.keys():
            # 如果设置了time_out，则循环检测该block
            is_timeout = False
            time_out = int(block['time_out'])
            def timer_fun():
                # 定时器到了，就结束循环
                nonlocal is_timeout
                is_timeout = True

            timer = threading.Timer(time_out, timer_fun)
            timer.start()
            while not is_timeout:
                time.sleep(2)
                # 截图
                img_path = block['capture_save_path']
                self.window_capture(img_path)
                sb_str = wzsb(block['capture_save_path'], box)
                print(sb_str)
                if block['key_text'] in sb_str:
                    # 如果检测到指定的文字了，则说明执行成功，退出
                    timer.cancel()
                    print('done')
                    return 0
                else:
                    # 如果没有检测到指定的文字，进入下一次循环
                    continue
            # 如果time_out后依然没有识别，则说明出现问题
            logger.warning('time_out.')
            print('time_out.')
            return -1
        else:
            # 如果没有设置time_out，则正常识别文字，发送按键指令
            sb_str = wzsb(block['last_image_path'], box)
            print(sb_str)
            if block['key_text'] in sb_str:
                # 执行
                for i in range(int(block['key_tap_times'])):
                    self.kvm_key_down(block['key_down'])
                # 等1秒
                time.sleep(1)
                # 截图
                img_path = block['capture_save_path']
                self.window_capture(img_path)

                return 0
            else:
                if 'error_box_tl_x' in block.keys():
                    error_box = (int(block['error_box_tl_x']),
                                 int(block['error_box_tl_y']),
                                 int(block['error_box_br_x']),
                                 int(block['error_box_br_y']))
                    error_sb_str = wzsb(block['last_image_path'], error_box)
                    print(error_sb_str)
                    if block['error_key_text'] in error_sb_str:
                        # 执行
                        for i in range(int(block['key_tap_times'])):
                            self.kvm_key_down(block['error_key_down'])
                            # 等1秒
                            time.sleep(1)
                        logger.warning(block['error_log_text'])
                        return -1
                    else:
                        print("识别{} 和 {} 失败。".format(block['key_text'], block['error_key_text']))
                        return -1

    def process(self, blocks):
        for block in blocks:
            # if not block['key_tap_times'].isdigit():
            #     logger.warning('配置文件格式错误.')
            #     return
            if 'box_tl_x' in block.keys() and 'box_tl_y' in block.keys() and 'box_br_x' in block.keys()  \
                and 'box_br_y' in block.keys() and 'error_times' in block.keys():
                if not block['box_tl_x'].isdigit() \
                        or not block['box_tl_y'].isdigit() \
                        or not block['box_br_x'].isdigit() \
                        or not block['box_br_y'].isdigit() \
                        or not block['error_times'].isdigit():
                    logger.warning('配置文件格式错误.')
                    return

                failure_count = 0
                while failure_count < int(block['error_times']):
                    res1 = self.process_block(block)
                    if res1 != 0:
                        failure_count = failure_count + 1
                        time.sleep(1)
                    else:
                        failure_count = 0
                        break
                if failure_count > 0:
                    logger.warning('步骤：{} 失败！'.format(block['type']))
                    # 失败发送-1
                    self.udp.send(b'-1')
                    return
            else:
                self.process_first(block)
            # 成功发送0
            self.udp.send(b'0')

def wzsb(imgPath, box):
    """
    图片文字识别
    :param imgPath:
    :param box:
    :return:
    """
    pathsp = os.path.splitext(imgPath)
    img = Image.open(imgPath)
    imgry = img.convert('L')
    # 保存灰度图像
    gray_img_path = pathsp[0] + '_gray' + pathsp[1]
    imgry.save(gray_img_path)

    # 二值化，采用阈值分割法，threshold为分割点
    threshold = 100
    table = []
    for j in range(256):
        if j < threshold:
            table.append(0)
        else:
            table.append(1)
    out = imgry.point(table, '1')
    b_img_path = pathsp[0] + '_b' + pathsp[1]
    out.save(b_img_path)

    if (box[0] < box[2]) and (box[1] < box[3]):
        img_box = img.crop(box)
        box_img_path = pathsp[0] + '_box' + pathsp[1]
        img_box.save(box_img_path)
        res = pytesseract.image_to_string(img_box).replace(' ', '')
        return res
    else:
        return -1

def process1(cf, ke):
    """
    第一步，按8下esc
    :return:
    """
    print("process1")
    # 按8下esc
    for i in range(8):
        ke.kvm_key_down('esc')
    # 截图1
    img_path = cf.get('Img1', 'path')
    ke.window_capture(img_path)

    # 文字识别
    box = (cf.getint('Img1', 'box_tl_x'),
           cf.getint('Img1', 'box_tl_y'),
           cf.getint('Img1', 'box_br_x'),
           cf.getint('Img1', 'box_br_y'))

    sb_str = wzsb(img_path, box)
    print(sb_str)
    if "Main" in sb_str or "menu" in sb_str:
        # 执行7
        ke.kvm_key_down('7')
        # 等1秒
        time.sleep(1)
        # 截图
        ke.window_capture(cf.get('Img2', 'path'))
        return 0
    else:
        print("识别Main menu失败。")
        return -1

def process2(cf, ke):
    print("process2")
    # 截图2
    # 文字识别
    img_path = cf.get('Img2', 'path')
    box = (cf.getint('Img2', 'box_tl_x'),
           cf.getint('Img2', 'box_tl_y'),
           cf.getint('Img2', 'box_br_x'),
           cf.getint('Img2', 'box_br_y'))

    sb_str = wzsb(img_path, box)
    if "Utilities" in sb_str:
        # 执行2
        ke.kvm_key_down('2')
        # 等1秒
        time.sleep(1)
        # 截图
        ke.window_capture(cf.get('Img3', 'path'))
        return 0
    else:
        print("识别Utilities失败。")
        return -1

def process3(cf, ke):
    print("process3")
    # 截图3
    # 文字识别
    img_path = cf.get('Img3', 'path')
    box = (cf.getint('Img3', 'box_tl_x'),
           cf.getint('Img3', 'box_tl_y'),
           cf.getint('Img3', 'box_br_x'),
           cf.getint('Img3', 'box_br_y'))

    sb_str = wzsb(img_path, box)
    print(sb_str)
    if "Caution" in sb_str:
        # 执行f1
        ke.kvm_key_down('f1')
        # 等1秒
        time.sleep(1)
        # 截图
        ke.window_capture(cf.get('Img4', 'path'))
        return 0
    else:
        print("Caution Error。")
        return -1

def chuliliucheng():
    """
    主进入口
    :return:
    """
    config_path = 'Config/window.cfg'
    cf = configparser.ConfigParser()

    if not cf.read(config_path, encoding='utf-8-sig'):
        msg = "配置文件不存在！"
        win32api.MessageBox(win32con.NULL, msg)
        msg = "clear"
        os._exit(-1)

    # 这里需要知道kvm的calssname或者窗口标题名
    # ke = kvm_event(None, "Remote View:[01] HPOTT6")
    ke = kvm_event(None, "test.txt - 记事本")

    failure_count1 = 0

    while failure_count1 <=3:
        res1 = process1(cf, ke)
        if res1 != 0:
            failure_count1 = failure_count1 + 1
            time.sleep(1)
        else:
            failure_count1 = 0
            break
    if failure_count1 > 0:
        logger.warning('第一步超过三次失败.')
        return

    failure_count2 = 0
    while failure_count2 <= 3:
        res2 = process2(cf, ke)
        if res2 != 0:
            failure_count2 = failure_count2 + 1
            time.sleep(1)
        else:
            failure_count2 = 0
            break

    if failure_count2 > 0:
        logger.warning('第二步超过三次失败.')
        return

    failure_count3 = 0
    while failure_count3 <= 3:
        res3 = process3(cf, ke)
        if res3 != 0:
            failure_count3 = failure_count3 + 1
            time.sleep(1)
        else:
            failure_count3 = 0
            break

    if failure_count3 > 0:
        logger.warning('第三步超过三次失败.')
        return

def kvm_process():
    config_path = 'Config/window.cfg'
    cf = configparser.ConfigParser()
    if not cf.read(config_path, encoding='utf-8-sig'):
        msg = "配置文件不存在！"
        win32api.MessageBox(win32con.NULL, msg)
        os._exit(-1)
    server_ip = cf.get('server', 'ip')
    server_port = cf.get('server', 'port')
    wnd_class = cf.get('window', 'wnd_class')
    if wnd_class == 'None':
        wnd_class = None
    wnd_name = cf.get('window', 'wnd_name')
    if wnd_name == 'None':
        wnd_name = None
    ke = kvm_event(wnd_class, wnd_name, server_ip, server_port)
    blocks = ke.parse_cfg("Config/wzsb_restore.cfg")
    ke.process(blocks)

if __name__ == '__main__':
    kvm_process()
