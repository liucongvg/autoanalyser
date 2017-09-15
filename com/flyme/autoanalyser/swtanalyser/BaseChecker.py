from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.utils import flymeprint, flymeparser


class BaseChecker:
    def __init__(self, swt_time_struct, pid, thread_name,
                 whole_trace, is_monitor):
        self.swt_time_struct = swt_time_struct
        self.pid = pid
        self.thread_name = thread_name
        self.whole_trace = whole_trace
        self.is_monitor = is_monitor
        self.is_dead_lock = False
        self.dead_lock_message = None
        self.is_binder_full = False
        self.binder_full_message = None
        self.last_trace = None
        self.last_thread_name = None
        self.last_process_trace = None
        self.all_pid_thread_name_dict = dict()
        self.trace_valid = True
        # self.dead_lock_thread = dict()
        self.blocked_circle_trace = None
        self.last_process = None

    def generate_report(self, fd, whole_trace, thread_name):
        if not whole_trace:
            flymeprint.error('trace content empty')
            return None
        # last_thread_state = flymeparser.get_thread_state(whole_trace,
        #                                                 thread_name)
        # if not last_thread_state:
        #    flymeprint.error('error in generate_report for ' + thread_name)
        #    return None
        last_whole_trace = whole_trace
        last_thread_name = thread_name
        trace_dict = flymeparser.get_trace(last_whole_trace, last_thread_name)
        if not trace_dict:
            flymeprint.error('trace_dict null')
            return
        # last_trace = trace_dict['trace']
        last_trace = None
        last_thread_state = trace_dict['thread_state']
        last_pid = self.pid
        last_process = 'system_server'
        should_loop = True
        # self.all_pid_thread_name_dict[last_pid] = {
        #    'thread_set': {'__thread_sequence__': list()},
        #    'process_name':
        #        'system_server',
        #    '__pid_thread_name_list__': list()}
        while should_loop:
            if last_pid not in self.all_pid_thread_name_dict:
                self.all_pid_thread_name_dict[last_pid] = dict()
                if '__pid_thread_name_list__' not in \
                        self.all_pid_thread_name_dict:
                    self.all_pid_thread_name_dict[
                        '__pid_thread_name_list__'] = list()
                self.all_pid_thread_name_dict[last_pid][
                    'thread_set'] = dict()
                self.all_pid_thread_name_dict[last_pid][
                    'process_name'] = last_process
                # self.all_pid_thread_name_dict[
                # '__pid_thread_name_list__'].append(last_pid)
            if (last_pid, last_thread_name) not in \
                    self.all_pid_thread_name_dict['__pid_thread_name_list__']:
                trace_dict = flymeparser.get_trace(last_whole_trace,
                                                   last_thread_name)
                if not trace_dict:
                    flymeprint.error('get trace error, trace dict null')
                    break
                # last_thread_name = trace_dict['thread_name']
                # last_thread_state = trace_dict['thread_state']
                last_trace = trace_dict['trace']
                self.all_pid_thread_name_dict[last_pid]['thread_set'][
                    last_thread_name] = last_trace
                self.all_pid_thread_name_dict[
                    '__pid_thread_name_list__'].append(
                    (last_pid, last_thread_name))
                self.last_trace = last_trace
                self.last_thread_name = last_thread_name
                self.last_process = last_process
                fd.write(last_trace + '\n')
                # continue
            else:
                self.is_dead_lock = True
                self.dead_lock_message = last_process + ':' + \
                                         last_thread_name + ' dead locked ' \
                                                            'with ' + \
                                         self.last_process + ':' + \
                                         self.last_thread_name
                self.generate_blocked_circle_trace(last_pid, last_thread_name)
                break
            if last_thread_state == 'Blocked':
                # trace_dict = flymeparser.get_blocked_trace(last_whole_trace,
                #
                #                                            last_thread_name)
                trace_dict = flymeparser.get_blocked_next_trace(
                    last_whole_trace, last_thread_name)
                if not trace_dict:
                    flymeprint.error('Blocked error')
                    break
                last_thread_name = trace_dict['thread_name']
                last_thread_state = trace_dict['thread_state']
                continue
                # trace = str()
                # for i in trace_dict['__thread_sequece__']:
                #    last_thread_name = trace_dict[i]['thread_name']
                #    last_thread_state = trace_dict[i]['thread_state']
                #    last_trace = trace_dict[i]['trace']
                #    self.all_pid_thread_name_dict[last_pid]['thread_set'][
                #        last_thread_name] = last_trace
                #    self.all_pid_thread_name_dict[last_pid]['thread_set'][
                #        '__thread_sequence__'].append(last_thread_name)
                #    trace += (last_trace + '\n')
                # trace = trace.rstrip('\n')
                # if trace_dict['is_dead_lock']:
                #    should_loop = False
                #    self.is_dead_lock = True
                #    self.dead_lock_message = trace_dict[
                # 'dead_lock_message']
                #    self.blocked_circle_trace = str()
                #    for i in trace_dict['dead_lock_trace']:
                #        self.blocked_circle_trace += (i + '\n')
                #    self.blocked_circle_trace = \
                #        self.blocked_circle_trace.rstrip(
                #            '\n')
            elif self.is_monitor and last_thread_name == 'android.fg' and \
                            last_thread_state == 'Native' and \
                    flymeparser.is_binder_full(
                        last_trace):
                self.is_binder_full = True
                self.binder_full_message = str()
                self.binder_full_message += 'binder full'
                random_dict = flymeparser.get_random_binder_trace(
                    last_whole_trace)
                if random_dict:
                    last_thread_name = random_dict.get('thread_name', '')
                    last_thread_state = random_dict.get('thread_state', '')
                    self.binder_full_message += ', go along with random ' \
                                                'binder ' \
                                                '' \
                                                'thread:' + last_thread_name
                else:
                    self.binder_full_message += ', no random binder trace found'
                    flymeprint.error(self.binder_full_message)
                    break
                continue
            elif (last_thread_state == 'Native') and (
                    flymeparser.is_trace_blocked_in_binder(last_trace)):
                if (
                            self.is_dead_lock or self.is_binder_full) and not \
                        self.last_process_trace:
                    self.last_process_trace = last_trace
                db_pt_dict = cachemanager.get_db_pt_dict()
                if (not db_pt_dict) or (not db_pt_dict.get(self.pid)):
                    flymeprint.warning(
                        'no process and thread file found for pid:' + self.pid)
                    break
                process_and_thread_file = db_pt_dict.get(self.pid)
                # for pid in db_pt_dict:
                # if pid != self.pid:
                #    continue
                # flymeprint.debug(
                #    'db process and threads file:' + db_pt_dict[pid])
                pt_content = cachemanager.get_file_content(
                    process_and_thread_file)
                pid_tid_dict = flymeparser.parse_db_pt_by_pid_tname(
                    pt_content,
                    last_pid,
                    last_thread_name)
                if not pid_tid_dict:
                    flymeprint.warning('can not find process or thread')
                    break
                from_pid = last_pid
                if last_thread_name == 'main':
                    from_tid = last_pid
                else:
                    from_tid = pid_tid_dict['pid']
                from_process = pid_tid_dict['process_name']
                from_thread = last_thread_name
                from_trace = last_trace
                file_name = cachemanager.get_db_bi_dict()[self.pid]
                if not file_name:
                    flymeprint.warning('can not find binder info file')
                    break
                bi_content = cachemanager.get_file_content(file_name)
                # if thread_name == 'main':
                #    real_process_id = pid_tid_dict['pid']
                #    real_thread_id = pid_tid_dict['pid']
                # else:
                #    real_process_id = pid_tid_dict['ppid']
                #    real_thread_id = pid_tid_dict['pid']
                pid_tid_dict = flymeparser.parse_db_bi_by_pid_tid(
                    bi_content,
                    from_pid,
                    from_tid)
                if not pid_tid_dict:
                    flymeprint.warning(
                        'can not find binder entry ' + from_pid + ':' +
                        from_tid)
                    break
                to_pid = pid_tid_dict['pid']
                to_tid = pid_tid_dict['tid']
                pid_tid_dict = flymeparser.parse_db_pt_by_pid_tid(pt_content,
                                                                  to_pid,
                                                                  to_tid)
                if not pid_tid_dict:
                    error_message = 'can not find process and thread entry ' \
                                    'for ' + to_pid + ':' + to_tid
                    flymeprint.warning(error_message)
                    fd.write(error_message + '\n')
                    break
                to_process = pid_tid_dict['process_name']
                to_thread = pid_tid_dict['thread_name']
                blocked_message = 'Blocked in binder ---> from ' + \
                                  from_pid + \
                                  '(' + from_process + '):' + from_tid + \
                                  '(' \
                                  + from_thread + ') to ' + to_pid + '(' \
                                  + \
                                  to_process + '):' + to_tid + '(' + \
                                  to_thread + ')\n';
                fd.write(blocked_message)
                file_name = cachemanager.get_db_trace_dict()[self.pid]
                content = cachemanager.get_file_content(file_name)
                process_name = pid_tid_dict['process_name']
                match = flymeparser.get_trace_time_pid(content,
                                                       pid_tid_dict['pid'],
                                                       process_name)
                if not match:
                    flymeprint.warning(
                        'no ' + process_name + ' trace found in ' +
                        file_name)
                    break
                time_str_list = list()
                for i in match:
                    time_str_list.append(i[2])
                target_time_str = self.whole_trace['time']
                time_str = flymeparser.find_min_time(target_time_str,
                                                     time_str_list)
                if not time_str:
                    fd.write('no matched binder trace\n')
                    break
                whole_trace_str = \
                    flymeparser.get_whole_trace_str_pid_process_time(
                        content, to_pid, time_str,
                        process_name)
                fd.write(
                    'binder trace:' + time_str + ' for ' + to_process +
                    '\n')
                if not whole_trace_str:
                    fd.write(
                        'no matched binder trace found for ' + to_process +
                        '\n')
                    break
                to_trace_dict = flymeparser.get_trace(whole_trace_str,
                                                      to_thread)
                if not to_trace_dict:
                    fd.write(
                        'no matched binder trace found for ' + to_thread
                        + '\n')
                    break
                # if to_pid not in self.all_pid_thread_name_dict:
                #    self.all_pid_thread_name_dict[to_pid] = dict()
                #    self.all_pid_thread_name_dict[
                # '__pid_thread_name_list__'] = list()
                #    self.all_pid_thread_name_dict[to_pid][
                #        'thread_set'] = dict()
                #    self.all_pid_thread_name_dict[to_pid]['thread_set'][
                #        '__thread_sequence__'] = list()
                #    self.all_pid_thread_name_dict[to_pid][
                #        'process_name'] = to_process
                #    self.all_pid_thread_name_dict[
                # '__pid_thread_name_list__'].append(
                # to_pid)
                #    self.all_pid_thread_name_dict[to_pid][
                #        'process_name'] = to_process
                # elif to_thread in \
                #        self.all_pid_thread_name_dict[to_pid]['thread_set'][
                #            '__thread_sequence__']:
                #    self.is_dead_lock = True
                #    self.dead_lock_message = from_process + ':' + from_thread \
                #                             + ' dead locked with ' + \
                #                             self.all_pid_thread_name_dict[
                #                                 to_pid][
                #                                 'process_name'] + ':' + \
                #                             to_thread
                #    self.generate_blocked_circle_trace(to_pid, to_thread)
                #    break
                last_pid = to_pid
                last_thread_name = to_thread
                last_whole_trace = whole_trace_str
                last_thread_state = flymeparser.get_thread_state(
                    last_whole_trace, last_thread_name)
                last_process = to_process
                continue
                # last_trace = to_trace_dict['trace']
                # fd.write(last_trace + '\n')
            else:
                break
                # self.last_trace = last_trace
                # self.last_thread_name = last_thread_name
                # self.last_thread_state = last_thread_state
                # self.last_whole_trace = last_whole_trace

    def generate_blocked_circle_trace(self, to_pid, to_thread):
        self.blocked_circle_trace = str()
        if not self.all_pid_thread_name_dict or '__pid_thread_name_list__' \
                not in self.all_pid_thread_name_dict:
            flymeprint.error('can not generate blocked circle trace')
            return
        target_index = self.all_pid_thread_name_dict[
            '__pid_thread_name_list__'].index((to_pid, to_thread))
        current_index = 0
        for current_tuple in self.all_pid_thread_name_dict[
            '__pid_thread_name_list__']:
            if current_index < target_index:
                current_index += 1
                continue
            self.blocked_circle_trace += (
                self.all_pid_thread_name_dict[current_tuple[0]][
                    'thread_set'][
                    current_tuple[1]] + '\n')
        self.blocked_circle_trace = \
            self.blocked_circle_trace.rstrip(
                '\n')
