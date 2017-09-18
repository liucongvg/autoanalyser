from com.flyme.autoanalyser.exceptionanalyser.BException import BException
from com.flyme.autoanalyser.utils import flymeparser


class NE(BException):
    def __init__(self, whole_trace, file_name):
        BException.__init__(self, whole_trace, file_name)
        self.exception_type = 'NE'
        self.reason = 'NE cause system_server crash'

    def get_brief_trace(self):
        return flymeparser.get_brief_ne_trace(self.whole_trace)
