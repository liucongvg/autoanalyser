from com.flyme.autoanalyser.swtanalyser.BaseSwtEntry import BaseSwtEntry


class Handler(BaseSwtEntry):
    def __init__(self, swt_time_struct, pid, checker_name, thread_name,
                 event_log,
                 whole_previous_trace_content,
                 whole_later_trace_content):
        self.is_monitor = True
        BaseSwtEntry.__init__(self, swt_time_struct, pid, checker_name,
                              thread_name, event_log,
                              whole_previous_trace_content,
                              whole_later_trace_content)
