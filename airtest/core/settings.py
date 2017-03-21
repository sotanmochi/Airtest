# -*- coding: utf-8 -*-
from .utils.decouple import config, undefined


class SConfig(object):
    """SimpleConfig Class"""
    def __init__(self, default=undefined, cast=undefined):
        self.default = default
        self.cast = cast


class MetaSettings(type):
    def __new__(meta, name, bases, class_dict):
        for k, v in class_dict.items():
            if isinstance(v, SConfig):
                class_dict[k] = config(k, default=v.default, cast=v.cast)
        cls = type.__new__(meta, name, bases, class_dict)
        return cls


class Settings(object):

    __metaclass__ = MetaSettings

    DEBUG = SConfig(False, bool)
    ADDRESS = SConfig(('127.0.0.1', 5037))
    BASE_DIR = SConfig(None)
    LOG_DIR = SConfig(None)
    LOG_FILE = SConfig("log.txt")
    SCREEN_DIR = SConfig("img_record")
    SAVE_SCREEN = SConfig(None)
    RESIZE_METHOD = SConfig(None)
    SCRIPTHOME = SConfig(None)
    SRC_RESOLUTION = SConfig([])  # to be move to DEVICE
    CVSTRATEGY = SConfig(None)
    CVSTRATEGY_ANDROID = SConfig(["tpl", "siftpre", "siftnopre"])
    CVSTRATEGY_WINDOWS = SConfig(["tpl", "siftnopre"])
    FIND_INSIDE = SConfig(None)
    FIND_OUTSIDE = SConfig(None)
    WHOLE_SCREEN = SConfig(False)  # 指定WHOLE_SCREEN时，就默认截取全屏(而非hwnd窗口截图)
    CHECK_COLOR = SConfig(False)  # 针对灰化按钮的情形，如果遇到彩色按钮-灰化按钮识别问题，打开即可
    THRESHOLD = SConfig(0.6, float)
    THRESHOLD_STRICT = SConfig(0.7, float)
    STRICT_RET = SConfig(False, float)
    OPDELAY = SConfig(0.1, float)
    WINDOW_TITLE = SConfig(None)
    FIND_TIMEOUT = SConfig(20, float)
    FIND_TIMEOUT_TMP = SConfig(3, float)
    DESIGN_RESOLUTION = SConfig([960, 640])
    RADIUS_X = SConfig(250)
    RADIUS_Y = SConfig(250)

    @classmethod
    def set_basedir(cls, filepath):
        cls.BASE_DIR = filepath

    @classmethod
    def set_logdir(cls, dirpath=None):
        if dirpath is not None:
            cls.LOG_DIR = dirpath
        elif cls.BASE_DIR is not None:
            cls.LOG_DIR = cls.BASE_DIR
        else:
            cls.LOG_DIR = "."

    @classmethod
    def set_threshold(cls, value):
        if value > 1 or value < 0:
            raise ValueError("invalid threshold: %s" % value)
        cls.THRESHOLD = value

    @classmethod
    def set_find_outside(cls, find_outside):
        """设置FIND_OUTSIDE, IDE中调用遮挡脚本编辑区."""
        str_rect = find_outside.split('-')
        find_outside = []
        for i in str_rect:
            find_outside.append(max(int(i), 0))  # 如果有负数，就用0 代替
        cls.FIND_OUTSIDE = find_outside
