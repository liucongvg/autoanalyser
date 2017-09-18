from com.flyme.autoanalyser.exceptionanalyser.BException import BException
from com.flyme.autoanalyser.utils import flymeparser


class JE(BException):
    def __init__(self, whole_trace, file_name):
        BException.__init__(self, whole_trace, file_name);
        self.exception_type = 'JE'
        self.reason = 'JE cause system_server crash'

    def get_brief_trace(self):
        return flymeparser.get_brief_trace(self.whole_trace, True)
