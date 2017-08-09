import os

from com.flyme.autoanalyser.utils import flymeparser


class SwtObj:
    def __init__(self, pid, time, event_log, handler_list, monitor_list):
        self.pid = pid
        self.time = time
        self.event_log = event_log
        self.handler_list = handler_list
        self.monitor_list = monitor_list

    def generate_report(self, dir):
        file = os.path.join(dir, self.time.replace(':', '_') + '_swt.txt')
        flymeparser.clean_files(file)
        fd = open(file, 'a', encoding='utf-8')
        fd.write(self.event_log + '\n\n')
        for handler in self.handler_list:
            handler.generate_report(fd)
            fd.write('\n')
        for monitor in self.monitor_list:
            monitor.generate_report(fd)
            fd.write('\n')
        fd.close()
