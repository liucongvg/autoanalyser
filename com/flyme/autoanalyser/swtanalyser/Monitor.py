from com.flyme.autoanalyser.swtanalyser.BaseChecker import BaseChecker


class Monitor(BaseChecker):
    def __init__(self, swt_time_struct, pid, class_name, checker_name,
                 thread_name, event_log,
                 whole_previous_trace_content, whole_later_trace_content):
        BaseChecker.__init__(self, swt_time_struct, pid, checker_name,
                             thread_name, event_log,
                             whole_previous_trace_content,
                             whole_later_trace_content)
        self.class_name = class_name
