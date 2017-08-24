# -*- coding: utf-8 -*-
"""
    api definition
"""
import os
import time
import aircv
from airtest.core import android
from airtest.core.error import MoaError, MoaNotFoundError
from airtest.core.settings import Settings as ST
from airtest.core.cv import loop_find, device_snapshot
from airtest.core.helper import G, MoaPic, MoaText, log_in_func, logwrap, moapicwrap, \
    get_platform, platform, register_device, delay_after_operation, set_default_st
from airtest.core.device import DEV_TYPE_DICT
from urlparse import urlparse, parse_qsl
try:
    from airtest.core import win
except ImportError as e:
    win = None
try:
    from airtest.core import ios
except ImportError as e:
    ios = None


"""
Environment initialization
"""


def set_serialno(sn=None, cap_method="minicap_stream", adbhost=None):
    '''
    auto set if only one device
    support filepath match pattern, eg: c123*
    '''
    dev = android.Android(sn, cap_method=cap_method, adbhost=adbhost)
    register_device(dev)
    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_ANDROID
    return sn


def set_udid(udid):
    '''
    auto set if only one device
    support filepath match patten, eg: c123*
    '''
    dev = ios.client.IOS(udid)
    register_device(dev)
    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_ANDROID


def set_windows(handle=None, window_title=None):
    if win is None:
        raise RuntimeError("win module is not available")
    window_title = window_title or ST.WINDOW_TITLE
    dev = win.Windows()
    if handle:
        dev.set_handle(int(handle))
    elif window_title:
        devs = dev.find_window_list(window_title)
        if not devs:
            raise MoaError("no window found with title: '%s'" % window_title)
        dev.set_handle(devs[0])
    else:
        G.LOGGING.info("handle not set, use entire screen")
    if dev.handle:
        dev.set_foreground()
    register_device(dev)

    ST.CVSTRATEGY = ST.CVSTRATEGY or ST.CVSTRATEGY_WINDOWS
    # # set no resize on windows as default (会导致函数的调用报错！)
    # ST.RESIZE_METHOD = ST.RESIZE_METHOD


def init_device(uri):
    """用uri连接设备
    android://adbhost:adbport/serialno?p1=v1
    """
    d = urlparse(uri)
    platform = d.scheme
    host = d.netloc
    uuid = d.path.lstrip("/")
    params = dict(parse_qsl(d.query))

    if platform == "android":
        if host:
            params["adbhost"] = host.split(":")
        set_serialno(uuid, **params)
    elif platform == "ios":
        set_udid(uuid, **params)
    elif platform == "windows":
        set_windows(uuid, **params)
    else:
        raise RuntimeError("unknown platform %s" % platform)


def set_device(pltf, uid=None, *args, **kwargs):
    """用这个接口替代set_android/set_uuid/set_windows"""
    try:
        cls = DEV_TYPE_DICT[pltf]
    except KeyError:
        raise MoaError("platform should be in %s" % DEV_TYPE_DICT.keys())
    device = cls(uid, *args, **kwargs)
    register_device(device)
    set_default_st(pltf)


def device():
    return G.DEVICE


@platform(on=["Android", "Windows", "IOS"])
def set_current(index):
    try:
        G.DEVICE = G.DEVICE_LIST[index]
    except IndexError:
        raise IndexError("device index out of range: %s/%s" % (index, len(G.DEVICE_LIST)))
    if win and get_platform() == "Windows":
        G.DEVICE.set_foreground()


"""
Device operation
"""


@logwrap
@platform(on=["Android"])
def shell(cmd):
    return G.DEVICE.shell(cmd)


@logwrap
@platform(on=["Android", "IOS"])
def amstart(package, activity=None):
    G.DEVICE.start_app(package, activity)


@logwrap
@platform(on=["Android", "IOS"])
def amstop(package):
    G.DEVICE.stop_app(package)


@logwrap
@platform(on=["Android", "IOS"])
def amclear(package):
    G.DEVICE.clear_app(package)


@logwrap
@platform(on=["Android", "IOS"])
def install(filepath, package=None):
    return G.DEVICE.install_app(filepath, package)


@logwrap
@platform(on=["Android", "IOS"])
def uninstall(package):
    return G.DEVICE.uninstall_app(package)


@logwrap
def snapshot(filename=None, msg=""):
    """capture device screen and save it into file."""
    screen, default_filepath = device_snapshot()
    if not filename:
        filepath = default_filepath
    elif not os.path.isabs(filename):
        filepath = os.path.join(ST.LOG_DIR, ST.SCREEN_DIR, filename)
    else:
        filepath = filename
    aircv.imwrite(filepath, screen)


@logwrap
@platform(on=["Android", "IOS"])
def wake():
    G.DEVICE.wake()


@logwrap
@platform(on=["Android", "IOS"])
def home():
    G.DEVICE.home()


@logwrap
@moapicwrap
@platform(on=["Android", "Windows", "IOS"])
def touch(v, timeout=0, delay=0, offset=None, if_exists=False, times=1, right_click=False, duration=0.01):
    '''
    @param if_exists: touch only if the target pic exists
    @param offset: {'x':10,'y':10,'percent':True}
    '''
    timeout = timeout or ST.FIND_TIMEOUT
    if isinstance(v, (MoaPic, MoaText)):
        try:
            pos = loop_find(v, timeout=timeout)
        except MoaNotFoundError:
            if if_exists:
                return False
            raise
    else:
        pos = v
        # 互通版需求：点击npc，传入FIND_INSIDE参数作为touch位置矫正(此时的v非img_name_str、非MoaPic、MoaText)
        if ST.FIND_INSIDE and get_platform() == "Windows" and G.DEVICE.handle:
            wnd_pos = G.DEVICE.get_wnd_pos_by_hwnd(G.DEVICE.handle)
            # 操作坐标 = 窗口坐标 + 有效画面在窗口内的偏移坐标 + 传入的有效画面中的坐标
            pos = (wnd_pos[0] + ST.FIND_INSIDE[0] + pos[0],
                   wnd_pos[1] + ST.FIND_INSIDE[1] + pos[1])

    if offset:
        if offset['percent']:
            w, h = G.DEVICE.size['width'], G.DEVICE.size['height']
            pos = (pos[0] + offset['x'] * w / 100,
                   pos[1] + offset['y'] * h / 100)
        else:
            pos = (pos[0] + offset['x'], pos[1] + offset['y'])
        G.LOGGING.debug('touchpos after offset %s', pos)
    else:
        G.LOGGING.debug('touchpos: %s', pos)

    if get_platform() == "Windows":
        G.DEVICE.touch(pos, right_click)
    else:
        G.DEVICE.touch(pos, times, duration)

    delay_after_operation(delay)


@logwrap
@moapicwrap
@platform(on=["Android", "Windows", "IOS"])
def swipe(v1, v2=None, delay=0, vector=None, target_poses=None, duration=0.5, steps=5):
    """滑动，共有3种参数方式：
       1. swipe(v1, v2) v1/v2分别是起始点和终止点，可以是(x,y)坐标或者是图片
       2. swipe(v1, vector) v1是起始点，vector是滑动向量，向量数值小于1会被当作屏幕百分比，否则是坐标
       3. swipe(v1, target_poses) v1是滑动区域，target_poses是(t1,t2)，t1是起始位置，t2是终止位置，数值为图片九宫格
    """
    if target_poses:
        v1.target_pos = target_poses[0]
        pos1 = loop_find(v1)
        v1.new_snapshot = False
        v1.target_pos = target_poses[1]
        pos2 = loop_find(v1)
    else:
        if isinstance(v1, (MoaPic, MoaText)):
            pos1 = loop_find(v1)
        else:
            pos1 = v1

        if v2:
            if isinstance(v2, (MoaPic, MoaText)):
                v2.new_snapshot = False
                pos2 = loop_find(v2)
            else:
                pos2 = v2
        elif vector:
            if vector[0] <= 1 and vector[1] <= 1:
                w, h = ST.SRC_RESOLUTION or G.DEVICE.getCurrentScreenResolution()

                # 减去windows窗口的边框
                if ST.FIND_INSIDE and get_platform() == "Windows" and G.DEVICE.handle:
                    w -= 2 * ST.FIND_INSIDE[0]
                    h -= ST.FIND_INSIDE[0] + ST.FIND_INSIDE[1]
                vector = (int(vector[0] * w), int(vector[1] * h))
            pos2 = (pos1[0] + vector[0], pos1[1] + vector[1])
        else:
            raise Exception("no enouph params for swipe")

    if ST.FIND_INSIDE and get_platform() == "Windows" and G.DEVICE.handle:
        wnd_pos = G.DEVICE.get_wnd_pos_by_hwnd(G.DEVICE.handle)
        # 操作坐标 = 窗口坐标 + 有效画面在窗口内的偏移坐标 + 传入的有效画面中的坐标
        pos1 = (wnd_pos[0] + ST.FIND_INSIDE[0] + pos1[0],
                wnd_pos[1] + ST.FIND_INSIDE[1] + pos1[1])
        pos2 = (wnd_pos[0] + ST.FIND_INSIDE[0] + pos2[0],
                wnd_pos[1] + ST.FIND_INSIDE[1] + pos2[1])
    G.DEVICE.swipe(pos1, pos2, duration=duration, steps=steps)
    delay_after_operation(delay)


@logwrap
@moapicwrap
@platform(on=["Android", "Windows"])
def operate(v, route, timeout=ST.FIND_TIMEOUT, delay=0):
    if isinstance(v, (MoaPic, MoaText)):
        pos = loop_find(v, timeout=timeout)
    else:
        pos = v

    G.DEVICE.operate({"type": "down", "x": pos[0], "y": pos[1]})
    for vector in route:
        if (vector[0] <= 1 and vector[1] <= 1):
            w, h = ST.SRC_RESOLUTION or G.DEVICE.getCurrentScreenResolution()
            vector = [vector[0] * w, vector[1] * h, vector[2]]
        pos2 = (pos[0] + vector[0], pos[1] + vector[1])
        G.DEVICE.operate({"type": "move", "x": pos2[0], "y": pos2[1]})
        time.sleep(vector[2])
    G.DEVICE.operate({"type": "up"})
    delay_after_operation(delay)


@logwrap
@platform(on=["Android"])
def pinch(in_or_out='in', center=None, percent=0.5, delay=0):
    G.DEVICE.pinch(in_or_out=in_or_out, center=center, percent=percent)
    delay_after_operation(delay)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def keyevent(keyname, escape=False, combine=None, delay=0, times=1, shift=False, ctrl=False):
    """模拟设备的按键功能, times为点击次数.
        shift/ctrl/combine only works on windows
    """
    if get_platform() == "Windows":
        if not combine:
            combine = []
        if ctrl:
            combine.append("ctrl")
        if shift:
            combine.append("shift")
        G.DEVICE.keyevent(keyname, escape, combine)
    else:
        G.DEVICE.keyevent(keyname)
    delay_after_operation(delay)


@logwrap
@platform(on=["Android", "Windows", "IOS"])
def text(text, delay=0, clear=False, enter=True):
    """
        输入文字
        clear: 输入前清空输入框
        enter: 输入后执行enter操作
    """
    device_platform = get_platform()
    if clear:
        if device_platform == "Windows":
            for i in range(20):
                G.DEVICE.keyevent('backspace', escape=True)
        else:
            G.DEVICE.shell(" && ".join(["input keyevent KEYCODE_DEL"] * 30))
    G.DEVICE.text(text, enter=enter)
    delay_after_operation(delay)


@logwrap
def sleep(secs=1.0):
    time.sleep(secs)


@logwrap
@moapicwrap
def wait(v, timeout=0, interval=0.5, intervalfunc=None):
    timeout = timeout or ST.FIND_TIMEOUT
    pos = loop_find(v, timeout=timeout, interval=interval, intervalfunc=intervalfunc)
    return pos


@logwrap
@moapicwrap
def exists(v, timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        pos = loop_find(v, timeout=timeout)
        return pos
    except MoaNotFoundError:
        return False


@logwrap
@moapicwrap
def find_all(v, timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        return loop_find(v, timeout=timeout, find_all=True)
    except MoaNotFoundError:
        return []


@logwrap
@platform(on=["Android"])
def logcat(grep_str="", extra_args="", read_timeout=10):
    return G.DEVICE.logcat(grep_str, extra_args, read_timeout)


@logwrap
def add_watcher(name, func):
    G.WATCHER[name] = func


@logwrap
def remove_watcher(name):
    G.WATCHER.pop(name)


"""
Assert functions
"""


@logwrap
@moapicwrap
def assert_exists(v, msg="", timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT
    try:
        pos = loop_find(v, timeout=timeout, threshold=ST.THRESHOLD_STRICT)
        return pos
    except MoaNotFoundError:
        raise AssertionError("%s does not exist in screen" % v)


@logwrap
@moapicwrap
def assert_not_exists(v, msg="", timeout=0):
    timeout = timeout or ST.FIND_TIMEOUT_TMP
    try:
        pos = loop_find(v, timeout=timeout)
        raise AssertionError("%s exists unexpectedly at pos: %s" % (v, pos))
    except MoaNotFoundError:
        pass


@logwrap
def assert_equal(first, second, msg=""):
    if first != second:
        raise AssertionError("%s and %s are not equal" % (first, second))


@logwrap
def assert_not_equal(first, second, msg=""):
    if first == second:
        raise AssertionError("%s and %s are equal" % (first, second))


if __name__ == '__main__':
    set_windows()
