from com.flyme.autoanalyser.swtanalyser.LaterChecker import LaterChecker
from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.swtanalyser.PrevChecker import PrevChecker
from com.flyme.autoanalyser.utils import flymeprint, flymeparser


class BaseSwtEntry:
    def __init__(self, swt_time_struct, pid, checker_name, thread_name,
                 event_log,
                 whole_previous_trace_content,
                 whole_later_trace_content):
        self.prev = PrevChecker(swt_time_struct, pid,
                                thread_name,
                                whole_previous_trace_content, self.is_monitor)
        self.later = LaterChecker(swt_time_struct, pid,
                                  thread_name,
                                  whole_later_trace_content,
                                  self.is_monitor)
        self.checker_name = checker_name
        self.event_log = event_log
        self.is_dead_lock = False
        self.is_binder_full = False
        self.is_hang = False
        self.is_unknown = False
        self.error_message = None
        self.error_trace = None
        self.brief_trace = None

    def generate_report(self, fd):
        fd.write(self.event_log + '\n')
        # fd.write('previous ---> time: ' + self.previous_trace['time'] + '\n')
        fd.write('previous trace:\n')
        fd.write(self.prev.whole_trace['head'] + '\n')
        fd.write(self.prev.whole_trace['file_name'] + '\n')
        if self.prev.whole_trace['is_valid']:
            self.prev.generate_report(fd, self.prev.whole_trace['content'],
                                      self.prev.thread_name)
        else:
            self.prev.trace_valid = False
            fd.write(self.prev.whole_trace['i_r'] + '\n')
        # fd.write('later ---> time: ' + self.later_trace['time'] + '\n')
        fd.write('later trace:\n')
        fd.write(self.later.whole_trace['head'] + '\n')
        fd.write(self.later.whole_trace['file_name'] + '\n')
        if self.later.whole_trace['is_valid']:
            self.later.generate_report(fd, self.later.whole_trace['content'],
                                       self.later.thread_name)
        else:
            self.later.trace_valid = False
            fd.write(self.later.whole_trace['i_r'] + '\n')
            # if self.pre_trace_valid and self.later_trace_valid:
            #    if self.is_dead_lock:
            #        self.exception_reason = 'dead lock, ' \
            #                                '' + self.dead_lock_message
            #    elif self.is_binder_full:
            #        self.exception_reason = 'binder full, random binder
            # thread ' \
            #                                'final trace is:\n' +
            # self.last_trace
            #    elif self.is_binder_blocked:
            #        self.exception_reason = 'blocked in binder transaction:'
            # + \
            #                                self.blocked_message + '\n' + \
            #                                self.last_trace
            #    elif self.is_thread_not_scheduled:
            #        self.exception_reason = 'thread not scheduled by
            # kernel\n' + \
            #                                self.last_trace
            #    elif self.is_unkown:
            #        self.exception_reason = 'unknown reason, need to analyse
            #  ' \
            #                                'manually'
            #    else:
            #        self.exception_reason = 'bug detected, contact ' \
            #                                'liucong@meizu.com'
            #    self.brief_trace = flymeparser.get_brief_trace(self.last_trace,
            #                                                   False)
            # else:
            #    self.is_not_judgeable = True
            #    self.exception_reason = 'trace is incomplete, not enough to
            # know ' \
            #                            'the real reason, please reproduce
            # this ' \
            #                            'case'
            #    self.brief_trace = 'incomplete trace'
        pre_brief_trace = flymeparser.get_brief_trace(self.prev.last_trace,
                                                      False)
        if not pre_brief_trace:
            pre_brief_trace = flymeparser.get_brief_ne_trace(
                self.prev.last_trace)
        later_brief_trace = flymeparser.get_brief_trace(self.later.last_trace,
                                                        False)
        if not later_brief_trace:
            later_brief_trace = flymeparser.get_brief_ne_trace(
                self.later.last_trace)
        if self.prev.is_dead_lock or self.later.is_dead_lock:
            self.is_dead_lock = True
            temp_obj = self.prev if self.prev.is_dead_lock else self.later
            trace = temp_obj.last_process_trace if \
                temp_obj.last_process_trace else temp_obj.last_trace
            self.brief_trace = flymeparser.get_brief_trace(trace, False)
            self.error_message = temp_obj.dead_lock_message
            self.error_trace = temp_obj.blocked_circle_trace
            return
        elif self.prev.is_binder_full or self.later.is_binder_full:
            self.is_binder_full = True
            temp_obj = self.prev if self.prev.is_binder_full else self.later
            trace = temp_obj.last_process_trace if \
                temp_obj.last_process_trace else temp_obj.last_trace
            self.brief_trace = flymeparser.get_brief_trace(trace, False)
            self.error_message = temp_obj.binder_full_message
            self.error_trace = temp_obj.last_trace
            return
        elif pre_brief_trace and later_brief_trace and pre_brief_trace == \
                later_brief_trace:
            self.is_hang = True
            self.brief_trace = pre_brief_trace
            self.error_message = 'hang in ' + self.prev.last_process + ':' + \
                                 self.prev.last_thread_name
            self.error_trace = self.prev.last_trace
        else:
            self.is_unknown = True
            self.brief_trace = pre_brief_trace
            self.error_message = 'unknown reason, trace missed probably'
            self.error_trace = 'refers to details'
