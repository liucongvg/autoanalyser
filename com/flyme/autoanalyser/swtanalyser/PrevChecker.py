from com.flyme.autoanalyser.swtanalyser.BaseChecker import BaseChecker


class PrevChecker(BaseChecker):
    def __init__(self, swt_time_struct, pid, thread_name,
                 whole_trace, is_monitor):
        BaseChecker.__init__(self, swt_time_struct, pid,
                             thread_name,
                             whole_trace, is_monitor)
