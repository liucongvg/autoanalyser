import os

from com.flyme.autoanalyser.utils import flymeparser
from com.flyme.autoanalyser.utils import flymeprint
import io


class SwtObj:
    def __init__(self, pid, time, event_log, file_name, handler_list,
                 monitor_list, is_sf_hang):
        self.pid = pid
        self.time = time
        self.event_log = event_log
        self.file_name = file_name
        self.handler_list = handler_list
        self.monitor_list = monitor_list
        self.is_sf_hang = is_sf_hang
        self.ex_type = 'SWT'
        self.ex_reason = None
        self.ex_final_trace = None
        self.ex_brief_trace = None

    def generate_report(self, dir):
        file = os.path.join(dir, self.time.replace(':', '_') + '_swt.txt')
        flymeparser.clean_files(file)
        # fd = open(file, 'a', encoding='utf-8')
        si = io.StringIO()
        si.write(self.file_name + '\n')
        si.write(self.event_log + '\n\n')
        ex_reason = ''
        ex_final_trace = ''
        ex_brief_trace = ''
        if self.is_sf_hang:
            ex_brief_trace = flymeparser.get_sf_hang_brief_trace(self.event_log)
            if ex_brief_trace is None:
                ex_brief_trace = 'null'
            ex_reason = 'sf hang'
            ex_final_trace = 'refer to trace file'
        else:
            self.handler_list.extend(self.monitor_list)
            has_dead_lock = False
            dead_lock_brief_trace = None
            dead_lock_message = None
            dead_lock_error_trace = None
            has_binder_full = False
            binder_full_brief_trace = None
            binder_full_message = None
            binder_full_error_trace = None
            has_hang = False
            hang_brief_trace = list()
            hang_message = list()
            hang_error_trace = list()
            has_unknown = False
            unknown_brief_trace = list()
            unknown_message = None
            unknown_error_trace = list()
            for checker in self.handler_list:
                checker.generate_report(si)
                si.write('\n')
                if checker.is_dead_lock:
                    has_dead_lock = True
                    dead_lock_message = checker.error_message
                    dead_lock_error_trace = checker.error_trace
                    dead_lock_brief_trace = checker.brief_trace
                    break
                elif checker.is_binder_full:
                    if has_binder_full:
                        continue
                    has_binder_full = True
                    binder_full_message = checker.error_message
                    binder_full_error_trace = checker.error_trace
                    binder_full_brief_trace = checker.brief_trace
                elif checker.is_hang:
                    has_hang = True
                    if checker.brief_trace is None:
                        continue
                    if checker.brief_trace in hang_brief_trace and \
                                    checker.error_message in hang_message and \
                                    hang_brief_trace.index(
                                        checker.brief_trace) == \
                                    hang_message.index(
                                        checker.error_message):
                        flymeprint.debug('ignore duplication')
                        continue
                    hang_brief_trace.append(checker.brief_trace)
                    if checker.error_trace is None:
                        continue
                    hang_error_trace.append(checker.error_trace)
                    if checker.error_message is None:
                        continue
                    hang_message.append(checker.error_message)
                elif checker.is_unknown:
                    has_unknown = True
                    if checker.brief_trace is None:
                        unknown_message = checker.error_message
                        continue
                    if checker.brief_trace in unknown_brief_trace:
                        continue
                    unknown_brief_trace.append(checker.brief_trace)
                    unknown_error_trace.append(checker.error_trace)
                    unknown_message = checker.error_message
                else:
                    flymeprint.error(
                        'should not be in this case, check your code!!!')
            if has_dead_lock:
                ex_reason = dead_lock_message
                ex_final_trace = dead_lock_error_trace
                ex_brief_trace = dead_lock_brief_trace
            elif has_binder_full:
                ex_reason = binder_full_message
                ex_final_trace = binder_full_error_trace
                ex_brief_trace = binder_full_brief_trace
            elif has_hang:
                ex_reason = ', '.join(hang_message)
                ex_final_trace = '\n'.join(hang_error_trace)
                ex_brief_trace = '_'.join(hang_brief_trace)
            elif has_unknown:
                ex_reason = unknown_message
                ex_final_trace = '\n'.join(unknown_error_trace)
                ex_brief_trace = '_'.join(unknown_brief_trace)
            if ex_brief_trace:
                ex_brief_trace = ex_brief_trace.rstrip('_')
            else:
                ex_brief_trace = 'null'
            if ex_final_trace:
                ex_final_trace = ex_final_trace.rstrip('\n')
            else:
                ex_final_trace = 'null'
            if ex_reason:
                ex_reason = ex_reason.rstrip(',')
            else:
                ex_reason = 'null'
        self.ex_reason = ex_reason
        self.ex_brief_trace = ex_brief_trace
        self.ex_final_trace = ex_final_trace
        # for monitor in self.monitor_list:
        # monitor.generate_report(si)
        #    si.write('\n')
        flymeprint.debug('exception reason:' + self.ex_reason)
        flymeprint.debug('exception brief trace:\n' + self.ex_brief_trace)
        fd = open(file, 'a', encoding='utf-8')
        flymeparser.write_exception_head(fd, self.ex_type, self.ex_reason,
                                         self.ex_final_trace, None)
        fd.write(si.getvalue().rstrip('\n'))
        fd.close()
        si.close()
        return self.ex_brief_trace
