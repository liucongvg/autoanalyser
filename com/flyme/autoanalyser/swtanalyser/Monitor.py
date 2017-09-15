from com.flyme.autoanalyser.swtanalyser.BaseSwtEntry import BaseSwtEntry


class Monitor(BaseSwtEntry):
    def __init__(self, swt_time_struct, pid, class_name, checker_name,
                 thread_name, event_log,
                 whole_previous_trace_content, whole_later_trace_content):
        self.is_monitor = True
        self.class_name = class_name
        BaseSwtEntry.__init__(self, swt_time_struct, pid, checker_name,
                              thread_name, event_log,
                              whole_previous_trace_content,
                              whole_later_trace_content)

        # def is_binder_full(self):
        #    if self.thread_name == 'android.fg':
        #        if self.pre_trace_dict.get('thread_state', None) == 'Native'
        # and \
        #                flymeparser.is_binder_full(
        #                    self.pre_trace_dict.get('trace', None)):
        #            return True
        #        elif self.pre_trace_dict.get('thread_state',
        #                                     None) == 'Native' and \
        #                flymeparser.is_binder_full(
        #                    self.later_trace_dict.get('trace', None)):
        #            return True
        #        else:
        #            return False
