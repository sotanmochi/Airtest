# -*- coding: utf-8 -*-
import re
from airtest.core.android.yosemite import Yosemite
from airtest.core.android.constant import YOSEMITE_PACKAGE
from airtest.core.error import AirtestError
from airtest.utils.logger import get_logger
from airtest.utils.nbsp import NonBlockingStreamReader
from airtest.utils.snippet import on_method_ready
LOGGING = get_logger('recorder')


class Recorder(Yosemite):
    """Screen recorder."""

    def __init__(self, adb):
        super(Recorder, self).__init__(adb)
        self.recording_proc = None
        self.recording_file = None

    @on_method_ready('install_or_upgrade')
    def start_recording(self, max_time=1800, bit_rate=None, vertical=None):
        if getattr(self, "recording_proc", None):
            raise AirtestError("recording_proc has already started")
        pkg_path = self.adb.path_app(YOSEMITE_PACKAGE)
        max_time_param = "-Dduration=%d" % max_time if max_time else ""
        bit_rate_param = "-Dbitrate=%d" % bit_rate if bit_rate else ""
        if vertical is None:
            vertical_param = ""
        else:
            vertical_param = "-Dvertical=true" if vertical else "-Dvertical=false"
        p = self.adb.start_shell('CLASSPATH=%s exec app_process %s %s %s /system/bin %s.Recorder --start-record' %
                                 (pkg_path, max_time_param, bit_rate_param, vertical_param, YOSEMITE_PACKAGE))
        nbsp = NonBlockingStreamReader(p.stdout)
        while True:
            line = nbsp.readline(timeout=5)
            if line is None:
                raise RuntimeError("recording setup error")
            m = re.match("start result: Record start success! File path:(.*\.mp4)", line.strip())
            if m:
                output = m.group(1)
                self.recording_proc = p
                self.recording_file = output
                return True

    @on_method_ready('install_or_upgrade')
    def stop_recording(self, output="screen.mp4", is_interrupted=False):
        pkg_path = self.adb.path_app(YOSEMITE_PACKAGE)
        p = self.adb.start_shell('CLASSPATH=%s exec app_process /system/bin %s.Recorder --stop-record' % (pkg_path, YOSEMITE_PACKAGE))
        p.wait()
        self.recording_proc = None
        if is_interrupted:
            return
        for line in p.stdout.readlines():
            m = re.match("stop result: Stop ok! File path:(.*\.mp4)", line.strip())
            if m:
                self.recording_file = m.group(1)
                self.adb.pull(self.recording_file, output)
                self.adb.shell("rm %s" % self.recording_file)
                return
        raise AirtestError("start_recording first")
