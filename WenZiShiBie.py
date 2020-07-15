# @File     : WenZiShiBie.py
# @Author   : 沈昌力
# @Date     :2018/11/20
# @Desc     :
import pytesseract
import os
import configparser
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
from pykeyboard import PyKeyboard
import time
import logging
from logging.config import fileConfig
import threading
import UdpInterface
import argparse
import psutil
import win32process


def killOldProcess():
    # kill 已有的进程id
    try:
        with open('pid.txt', 'r') as f:
            old_pid = int(f.readline().rstrip('\n'))
            if old_pid:
                # 确定进程id是运行的当前程序，防止误杀
                # ps_info = os.popen("ps -ef | grep %s | awk '{print $2}'" % __file__)
                ps_info = psutil.pids()
                if old_pid in ps_info:
                    os.system('taskkill /pid %d  -t  -f' % old_pid)
    except IOError:
        pass
    # 保存当前进程id
    with open('pid.txt', 'w') as f:
        f.write('%d\n' % os.getpid())


def init_args():
    args = argparse.ArgumentParser()
    args.add_argument('-c',
                      '--config_root',
                      type=str,
                      help='config root path',
                      default='Config')
    args.add_argument('-t',
                      '--type',
                      type=str,
                      help='backup or restore',
                      default='backup')

    args.add_argument('-p',
                      '--pid',
                      type=int,
                      help='pid',
                      default=0)
    return args.parse_args()


class kvm_event():
    def __init__(self, wnd_class, wnd_name, pid, server_ip, server_port, logger):
        self.udp = UdpInterface.UdpClient(server_ip, int(server_port))
        self.get_handle(wnd_class, wnd_name, pid)
        # 开始等待
        time_index = 0
        while self.handle == 0:
            time.sleep(1)
            time_index += 1
            self.get_handle(wnd_class, wnd_name, pid)
            if time_index > 30:
                self.udp.send(b'-1')
                break
        self.logger = logger
        if self.handle == 0:
            self.logger.warning('无法获取KVM的窗口句柄')
        assert self.handle != 0, "无法获取KVM的窗口句柄"
        # self.udp.send(b'-1')

    def get_handle(self, wnd_class, wnd_name, pid):
        """
        获取handle
        :param wnd_class:
        :param wnd_name:
        :param pid:
        :return:
        """
        hd1 = win32gui.FindWindow(wnd_class, wnd_name)
        hd2_list = self.get_hwnds_for_pid(pid)
        if hd2_list.__len__() == 0:
            hd2 = 0
        else:
            hd2 = hd2_list[0]
        if hd1 == 0 and hd2 != 0:
            self.handle = hd2
        elif hd1 != 0 and hd2 == 0:
            self.handle = hd1
        elif hd1 == 0 and hd2 == 0:
            self.handle = 0
        elif hd1 == hd2:
            self.handle = hd1
        else:
            self.handle = hd2

    @staticmethod
    def get_hwnds_for_pid(pid):
        """
        通过PID获取handle
        :param pid:
        :return:
        """
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
                return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds

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
        """
        发送按键
        :param key:
        :return:
        """
        k = PyKeyboard()
        win32gui.SetForegroundWindow(self.handle)
        if key == '8':
            print("send keydown '8'")
            k.tap_key('8')
            win32gui.PostMessage(self.handle, win32con.WM_KEYDOWN, 56, 0)
        elif key == '7':
            print("send keydown '7'")
            k.tap_key('7')
        elif key == '1':
            print("send keydown '1'")
            k.tap_key('1')
        elif key == '2':
            print("send keydown '2'")
            k.tap_key('2')
            win32gui.PostMessage(self.handle, win32con.WM_KEYDOWN, 50, 0)
        elif key == '3':
            print("send keydown '3'")
            k.tap_key('3')
        elif key == '4':
            print("send keydown '4'")
            k.tap_key('4')
        elif key == '5':
            print("send keydown '5'")
            k.tap_key('5')
        elif key == '6':
            print("send keydown '6'")
            k.tap_key('6')
        elif key == '9':
            print("send keydown '9'")
            k.tap_key('9')
        elif key == '0':
            print("send keydown '0'")
            k.tap_key('0')
        elif key == 'esc':
            print("send keydown 'esc'")
            k.tap_key(k.escape_key)
            win32gui.PostMessage(
                self.handle, win32con.WM_KEYDOWN, win32con.VK_ESCAPE, 0)
        elif key == 'f1':
            print("send keydown 'f1'")
            k.tap_key(k.function_keys[1])
            win32gui.PostMessage(
                self.handle, win32con.WM_KEYDOWN, win32con.VK_F1, 0)
        elif key == 'enter':
            print("send keydown 'enter'")
            k.tap_key(k.enter_key)
        elif key == 'home':
            print("send keydown 'home'")
            k.tap_key(k.home_key)
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
            time.sleep(0.2)
        # 截图
        img_path = block['capture_save_path']
        self.window_capture(img_path)

    def process_block(self, block):
        """
        处理流程，处理每一个步骤Block
        :param block:
        :return:
        """
        self.window_capture('last_image_path')
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
            msg_str = ""
            while not is_timeout:
                time.sleep(2)
                # 截图
                img_path = block['capture_save_path']
                self.window_capture(img_path)
                sb_str = wzsb_times(label=block['key_text'],
                                    img=block['capture_save_path'],
                                    box=box)
                # sb_str = wzsb(block['capture_save_path'], box)
                # if sb_str == "":
                #     sb_str = '...'
                #     msg_str = '等待中' + sb_str
                # print(msg_str)
                self.logger.warning(msg_str)
                if block['key_text'] in sb_str:
                    # 如果检测到指定的文字了，则说明执行成功，退出
                    timer.cancel()
                    print('done')
                    self.logger.warning('done')
                    return 0
                else:
                    # 如果没有检测到指定的文字，进入下一次循环
                    sb_str = '...'
                    msg_str = '等待中' + sb_str
                    print(msg_str)
                    self.logger.warning(msg_str)
                    continue
            # 如果time_out后依然没有识别，则说明出现问题
            self.logger.warning('time_out.')
            print('time_out.')
            return -1
        else:
            # 如果没有设置time_out，则正常识别文字，发送按键指令
            # sb_str = wzsb(block['last_image_path'], box)
            sb_str = wzsb_times(label=block['key_text'],
                                img=block['last_image_path'],
                                box=box)
            msg_str = '识别结果: ' + sb_str
            print(msg_str)
            self.logger.warning(msg_str)
            if sb_str != 'error':
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
                    error_sb_str = wzsb_times(label=block['error_key_text'],
                                              img=block['last_image_path'],
                                              box=error_box)
                    # error_sb_str = wzsb(block['last_image_path'], error_box)
                    msg_str = '识别错误字符: ' + error_sb_str
                    print(msg_str)
                    self.logger.warning(msg_str)
                    if block['error_key_text'] in error_sb_str:
                        # 执行
                        for i in range(int(block['key_tap_times'])):
                            self.kvm_key_down(block['error_key_down'])
                            # 等1秒
                            time.sleep(1)
                        msg_str = '识别到错误字符：' + block['error_log_text']
                        self.logger.warning(msg_str)
                        return -1
                    else:
                        error_str = "识别{} 和 {} 失败。".format(
                            block['key_text'], block['error_key_text'])
                        print("识别{} 和 {} 失败。".format(
                            block['key_text'], block['error_key_text']))
                        self.logger.warning(error_str)
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
                    self.logger.warning('配置文件格式错误.')
                    self.udp.send(b'-1')
                    win32gui.PostMessage(self.handle, win32con.WM_CLOSE, 0, 0)
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
                    send_msg = '步骤：{} 失败！'.format(block['type'])
                    self.logger.warning(send_msg)
                    # 失败发送-1
                    self.udp.send(b'-1')
                    win32gui.PostMessage(self.handle, win32con.WM_CLOSE, 0, 0)
                    return
            else:
                self.process_first(block)
            # 成功发送0
        self.udp.send(b'0')
        win32gui.PostMessage(self.handle, win32con.WM_CLOSE, 0, 0)


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


def wzsb_times(label, img, box, move_list=[-1, 0, 1]):
    """
    多次识别，每次把识别窗口移动move_list中的值
    :param label:
    :param img:
    :param box:
    :param move_list:
    :return:
    """
    box_tl_x = box[0]
    box_tl_y = box[1]
    box_br_x = box[2]
    box_br_y = box[3]
    for i in move_list:
        for j in move_list:
            box_tl_x += i
            box_br_x += i
            box_tl_y += j
            box_br_y += j
            bbox = [box_tl_x, box_tl_y, box_br_x, box_br_y]
            sb_str = wzsb(img, bbox)
            if label in sb_str:
                return sb_str
    return 'error'


def kvm_process(cfg_root_path, type, pid):
    config_path = os.path.join(cfg_root_path, 'window.cfg')
    cf = configparser.ConfigParser()
    if not cf.read(config_path, encoding='utf-8-sig'):
        msg = "配置文件不存在！"
        win32api.MessageBox(win32con.NULL, msg)
        os._exit(-1)

    fileConfig(os.path.join(cfg_root_path, 'logging.conf'))
    logger = logging.getLogger('warninglogger')
    logger.warning('warning')

    server_ip = cf.get('server', 'ip')
    server_port = cf.get('server', 'port')
    wnd_class = cf.get('window', 'wnd_class')
    if wnd_class == 'None':
        wnd_class = None
    wnd_name = cf.get('window', 'wnd_name')
    # pid = cf.getint('window', 'pid')
    if wnd_name == 'None':
        wnd_name = None
    ke = kvm_event(wnd_class, wnd_name, pid, server_ip, server_port, logger)

    if type == 'backup':
        blocks = ke.parse_cfg(os.path.join(cfg_root_path, 'wzsb.cfg'))
    elif type == 'restore':
        blocks = ke.parse_cfg(os.path.join(cfg_root_path, 'wzsb_restore.cfg'))
    else:
        blocks = ke.parse_cfg(os.path.join(cfg_root_path, 'wzsb.cfg'))

    ke.process(blocks)


# def _MyCallback( hwnd, extra ):
#     windows = extra
#     temp=[]
#     temp.append(hex(hwnd))
#     temp.append(win32gui.GetClassName(hwnd))
#     temp.append(win32gui.GetWindowText(hwnd))
#     windows[hwnd] = temp

# def TestEnumWindows():
#     windows = {}
#     win32gui.EnumWindows(_MyCallback, windows)
#     print("Enumerated a total of  windows with %d classes" ,(len(windows)))
#     print('------------------------------')
#     #print classes
#     print('-------------------------------')
#     for item in windows :
#         print(windows[item])


if __name__ == '__main__':
    killOldProcess()
    # TestEnumWindows()
    args = init_args()
    kvm_process(args.config_root, args.type, args.pid)
