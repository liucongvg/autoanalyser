import os

from com.flyme.autoanalyser.utils import flymeparser


class BException:
    def __init__(self, whole_trace, file_name):
        self.whole_trace = whole_trace
        self.file_name = file_name
        pass

    def get_brief_trace(self):
        pass

    def generate_report(self, report_dir, file_name):
        whole_file_name = os.path.join(report_dir, file_name)
        fd = open(whole_file_name, mode='w', encoding='utf-8')
        flymeparser.write_exception_head(fd, self.exception_type, self.reason,
                                         self.whole_trace)
        fd.close()
