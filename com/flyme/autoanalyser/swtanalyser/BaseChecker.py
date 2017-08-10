from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.utils import flymeparser, flymeprint


class BaseChecker:
    def __init__(self, swt_time_struct, pid, checker_name, thread_name,
                 event_log,
                 whole_previous_trace,
                 whole_later_trace):
        self.swt_time_struct = swt_time_struct
        self.pid = pid
        self.checker_name = checker_name
        self.thread_name = thread_name
        self.event_log = event_log
        self.previous_trace = whole_previous_trace
        self.later_trace = whole_later_trace

    def generate_report(self, fd):
        fd.write(self.event_log + '\n')
        fd.write('previous ---> time: ' + self.previous_trace['time'] + '\n')
        fd.write(self.previous_trace['file_name'] + '\n')
        if self.previous_trace['is_valid']:
            self.__generate_report_final(fd, self.previous_trace['content'],
                                         self.thread_name, False)
        else:
            fd.write(self.previous_trace['i_r'] + '\n')
        fd.write('later ---> time: ' + self.later_trace['time'] + '\n')
        fd.write(self.later_trace['file_name'] + '\n')
        if self.later_trace['is_valid']:
            self.__generate_report_final(fd, self.later_trace['content'],
                                         self.thread_name, True)
        else:
            fd.write(self.later_trace['i_r'] + '\n')

    def __generate_report_final(self, fd, whole_trace, thread_name, is_later):
        if not whole_trace:
            flymeprint.error('trace content empty')
            return
        thread_state = flymeparser.get_thread_state(whole_trace, thread_name)
        if not thread_state:
            flymeprint.error('error in generate_report for ' + thread_name)
            return
        last_trace_state = None
        last_thread_name = None
        last_trace = None
        if thread_state == 'Blocked':
            trace_dict = flymeparser.get_blocked_trace(whole_trace,
                                                       thread_name)
            trace = str()
            for i in trace_dict['__thread_sequece__']:
                last_thread_name = trace_dict[i]['thread_name']
                last_trace_state = trace_dict[i]['thread_state']
                last_trace = trace_dict[i]['trace']
                trace += (last_trace + '\n')
        else:
            trace_dict = flymeparser.get_trace(whole_trace, thread_name)
            last_trace_state = trace_dict['thread_state']
            last_thread_name = thread_name
            trace = last_trace = trace_dict['trace']
        fd.write(trace + '\n')
        # if not is_later:
        #    return
        if (last_trace_state != 'Native') or (
                not flymeparser.is_trace_blocked_in_binder(last_trace)):
            return
        db_pt_dict = cachemanager.get_db_pt_dict()
        for pid in db_pt_dict:
            if pid != self.pid:
                continue
            flymeprint.debug('db process and threads file:' + db_pt_dict[pid])
            pt_content = cachemanager.get_file_content(db_pt_dict[pid])
            pid_tid_dict = flymeparser.parse_db_pt_by_pid_tname(pt_content, pid,
                                                                thread_name)
            if not pid_tid_dict:
                flymeprint.warning('can not find process or thread')
                return
            from_pid = pid
            if thread_name == 'main':
                from_tid = pid
            else:
                from_tid = pid_tid_dict['pid']
            from_process = 'system_server'
            from_thread = thread_name
            file_name = cachemanager.get_db_bi_dict()[pid]
            bi_content = cachemanager.get_file_content(file_name)
            if thread_name == 'main':
                real_process_id = pid_tid_dict['pid']
                real_thread_id = pid_tid_dict['pid']
            else:
                real_process_id = pid_tid_dict['ppid']
                real_thread_id = pid_tid_dict['pid']
            pid_tid_dict = flymeparser.parse_db_bi_by_pid_tid(bi_content,
                                                              real_process_id,
                                                              real_thread_id)
            if not pid_tid_dict:
                flymeprint.warning('can not find binder entry')
                return
            to_pid = pid_tid_dict['pid']
            to_tid = pid_tid_dict['tid']
            pid_tid_dict = flymeparser.parse_db_pt_by_pid_tid(pt_content,
                                                              pid_tid_dict[
                                                                  'pid'],
                                                              pid_tid_dict[
                                                                  'tid'])
            to_process = pid_tid_dict['process_name']
            to_thread = pid_tid_dict['thread_name']
            fd.write(
                'Blocked in binder ---> from ' + from_pid + '(' +
                from_process + '):' + from_tid + '(' + from_thread + ') to '
                + to_pid + '(' + to_process + '):' + to_tid + '(' + to_thread +
                ')\n')
            file_name = cachemanager.get_db_trace_dict()[pid]
            content = cachemanager.get_file_content(file_name)
            process_name = pid_tid_dict['process_name']
            match = flymeparser.get_trace_time_pid(content, pid_tid_dict['pid'],
                                                   process_name)
            if not match:
                flymeprint.warning(
                    'no ' + process_name + ' trace found in ' + file_name)
                return
            time_str_list = list()
            for i in match:
                time_str_list.append(i[1])
            if is_later:
                target_time_str = self.later_trace['time']
            else:
                target_time_str = self.previous_trace['time']
            time_str = flymeparser.find_min_time(target_time_str, time_str_list,
                                                 is_later)
            if not time_str:
                fd.write('no matched binder trace\n')
                return
            whole_trace_str = flymeparser.get_whole_trace_str_pid_process_time(
                content, pid_tid_dict['pid'], time_str, process_name)
            fd.write('binder trace:' + time_str + ' for ' + to_process + '\n')
            if not whole_trace_str:
                fd.write(
                    'no matched binder trace found for ' + to_process + '\n')
                return
            whole_trace = flymeparser.get_trace(whole_trace_str, to_thread)
            if not whole_trace:
                fd.write(
                    'no matched binder trace found for ' + to_thread + '\n')
                return
            fd.write(whole_trace)
