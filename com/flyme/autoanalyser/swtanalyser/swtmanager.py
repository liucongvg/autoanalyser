import re
import os
from datetime import datetime

from com.flyme.autoanalyser.utils import flymeparser, flymeprint
from com.flyme.autoanalyser.swtanalyser.Monitor import Monitor
from com.flyme.autoanalyser.swtanalyser.Handler import Handler
from com.flyme.autoanalyser.swtanalyser.SwtObj import SwtObj
from com.flyme.autoanalyser.cache import cachemanager


def start(root_path):
    return parse_swt(root_path)


def parse_swt(root_path):
    cachemanager.root_path = root_path
    watchdog_raw_dict = parse_event_log_for_wd(root_path)
    if not watchdog_raw_dict:
        watchdog_raw_dict = parse_db_watchdog(root_path)
    if not watchdog_raw_dict:
        flymeprint.error('no watchdog keyword found')
        return
    watchdog_formated_dict = parse_watchdog_raw_dict(watchdog_raw_dict)
    is_sf_hang = True
    for time_str in watchdog_formated_dict:
        if '__is_sf_hang__' not in watchdog_formated_dict[time_str] or not \
                watchdog_formated_dict[time_str]['__is_sf_hang__']:
            is_sf_hang = False
    if not is_sf_hang:
        if not watchdog_formated_dict:
            flymeprint.error('parse_wachdog_raw_dict error')
            return
        system_server_trace_time_dict = parse_data_anr_trace(root_path)
        if not system_server_trace_time_dict:
            system_server_trace_time_dict = parse_db_trace(root_path)
        if not system_server_trace_time_dict:
            flymeprint.error('no system_server trace time')
            return
        elif len(system_server_trace_time_dict) <= 1:
            flymeprint.error(
                'only one system_server trace found, not enough to analysis')
            return
        matched_trace_time = get_matched_trace_time(watchdog_formated_dict,
                                                    system_server_trace_time_dict,
                                                    False)
        if not matched_trace_time:
            flymeprint.error('no matched time')
            return
        pm_matched_trace_time = get_pm_matched_trace_time(
            system_server_trace_time_dict, watchdog_formated_dict)
        swtobj_dict = get_swtobj_dict(watchdog_formated_dict,
                                      matched_trace_time,
                                      pm_matched_trace_time)
    else:
        flymeprint.debug('sf hang...')
        swtobj_dict = get_swtobj_dict(watchdog_formated_dict, None, None)
    return generate_report(swtobj_dict, root_path)


def get_pm_matched_trace_time(system_server_trace_time_dict,
                              watchdog_formated_dict):
    have_pm = False
    pm_watchdog_formated_dict = dict()
    for i in watchdog_formated_dict.keys():
        for j in watchdog_formated_dict[i]['checker_list']:
            if j['thread_name'] == 'PackageManager':
                have_pm = True
                pm_watchdog_formated_dict[i] = watchdog_formated_dict[i]
    if have_pm:
        pm_matched_trace_time = get_matched_trace_time(
            pm_watchdog_formated_dict,
            system_server_trace_time_dict,
            True)
    else:
        pm_matched_trace_time = None
    return pm_matched_trace_time


def parse_db_watchdog(root_path):
    flymeprint.debug('parsing db watchdog...')
    cachemanager.root_path = root_path
    db_event_log_files = cachemanager.get_db_event_log_files()
    return parse_event_log_for_wd_by_entries(db_event_log_files)


def generate_report(swtobj_dict, root_path):
    report_dir = os.path.join(root_path, '__swtanalyser__')
    flymeparser.clean_and_build_dir(report_dir)
    result_dict = dict()
    for time_str in swtobj_dict:
        swtobj = swtobj_dict[time_str]
        if swtobj.file_name in result_dict:
            continue
        result_dict[swtobj.file_name] = swtobj.generate_report(report_dir)
    return result_dict


def get_swtobj_dict(watchdog_formated_dict, matched_trace_time,
                    pm_matched_trace_time):
    swtobj_dict = dict()
    for time_str in watchdog_formated_dict:
        pid = watchdog_formated_dict[time_str]['pid']
        is_sf_hang = False
        if watchdog_formated_dict[time_str]['__is_sf_hang__']:
            handler_list = list()
            monitor_list = list()
            is_sf_hang = True
        else:
            whole_trace_dict = get_whole_trace_dict(time_str,
                                                    matched_trace_time)
            if pm_matched_trace_time:
                pm_whole_trace_dict = get_whole_trace_dict(time_str,
                                                           pm_matched_trace_time)
                pm_whole_previous_trace = pm_whole_trace_dict['previous_trace']
                pm_whole_later_trace = pm_whole_trace_dict['later_trace']
            if not whole_trace_dict:
                flymeprint.error('empty whole_trace_dict')
                continue
            whole_previous_trace = whole_trace_dict['previous_trace']
            whole_later_trace = whole_trace_dict['later_trace']
            # swtobj_dict[time_str] = dict()
            # swtobj_dict[time_str]['event_log'] = watchdog_formated_dict[
            # time_str][
            #    'event_log']
            checker_list = watchdog_formated_dict[time_str]['checker_list']
            # swtobj_dict[time_str]['monitor_list'] = list()
            # swtobj_dict[time_str]['handler_list'] = list()
            monitor_list = list()
            handler_list = list()
            for checker in checker_list:
                checker_name = checker['checker_name']
                thread_name = checker['thread_name']
                event_log = checker['event_log']
                if checker['checker_type'] == 'handler':
                    if (
                                thread_name == 'PackageManager') and \
                            pm_matched_trace_time:
                        handler = Handler(
                            watchdog_formated_dict[time_str]['time_struct'],
                            pid,
                            checker_name, thread_name, event_log,
                            pm_whole_previous_trace,
                            pm_whole_later_trace)
                    else:
                        handler = Handler(
                            watchdog_formated_dict[time_str]['time_struct'],
                            pid,
                            checker_name, thread_name, event_log,
                            whole_previous_trace,
                            whole_later_trace)
                        # swtobj_dict[time_str]['handler_list'].append(handler)
                    handler_list.append(handler)
                elif checker['checker_type'] == 'monitor':
                    class_name = checker['checker_class_name']
                    monitor = Monitor(
                        watchdog_formated_dict[time_str]['time_struct'], pid,
                        class_name, checker_name, thread_name,
                        event_log, whole_previous_trace,
                        whole_later_trace)
                    # swtobj_dict[time_str]['monitor_list'].append(monitor)
                    monitor_list.append(monitor)
                else:
                    continue
        swtobj = SwtObj(pid, time_str,
                        watchdog_formated_dict[time_str]['event_log'],
                        watchdog_formated_dict[time_str]['file_name'],
                        handler_list, monitor_list, is_sf_hang)
        swtobj_dict[time_str] = swtobj
    return swtobj_dict


def get_whole_trace_dict(time_str, matched_trace_time):
    whole_trace_dict = dict()
    if time_str not in matched_trace_time:
        return whole_trace_dict
    whole_previous_content = matched_trace_time[time_str]['previous_content']
    whole_later_content = matched_trace_time[time_str]['later_content']
    if 'best_previous_time_str' in matched_trace_time[time_str]:
        previous_matched_time_str = matched_trace_time[time_str][
            'best_previous_time_str']
    else:
        previous_matched_time_str = matched_trace_time[time_str][
            'best_alternative_previous_time_str']
    previous_trace_content = flymeparser.get_whole_trace_str(
        whole_previous_content,
        'system_server',
        previous_matched_time_str)
    if 'best_later_time_str' in matched_trace_time[time_str]:
        later_matched_time_str = matched_trace_time[time_str][
            'best_later_time_str']
    else:
        later_matched_time_str = matched_trace_time[time_str][
            'best_alternative_later_time_str']
    later_trace_content = flymeparser.get_whole_trace_str(whole_later_content,
                                                          'system_server',
                                                          later_matched_time_str)
    if 'best_alternative_previous_head' in matched_trace_time[time_str]:
        best_previous_head = matched_trace_time[time_str][
            'best_alternative_previous_head']
    else:
        best_previous_head = matched_trace_time[time_str]['best_previous_head']
    if 'best_alternative_later_head' in matched_trace_time[time_str]:
        best_later_head = matched_trace_time[time_str][
            'best_alternative_later_head']
    else:
        best_later_head = matched_trace_time[time_str]['best_later_head']
    whole_trace_dict['previous_trace'] = {'time': previous_matched_time_str,
                                          'content': previous_trace_content,
                                          'is_valid':
                                              matched_trace_time[time_str][
                                                  'is_previous_valid'],
                                          'i_r': matched_trace_time[time_str][
                                              'p_i_r'], 'file_name':
                                              matched_trace_time[time_str][
                                                  'previous_file_name'],
                                          'head': best_previous_head}
    whole_trace_dict['later_trace'] = {'time': later_matched_time_str,
                                       'content': later_trace_content,
                                       'is_valid': matched_trace_time[time_str][
                                           'is_later_valid'],
                                       'i_r': matched_trace_time[time_str][
                                           'l_i_r'],
                                       'file_name': matched_trace_time[
                                           time_str]['later_file_name'],
                                       'head': best_later_head}
    return whole_trace_dict


def parse_event_log_for_wd_by_entries(event_log_entries):
    if not event_log_entries:
        flymeprint.warning('no event log files found')
    watchdog_raw_dict = dict()
    for file_name in event_log_entries:
        content = cachemanager.get_file_content(file_name)
        if not content:
            continue
        # watchdog_list = re.findall(
        #    '(^\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3}.*?I watchdog: .*)', content,
        #    re.M)
        watchdog_list = flymeparser.get_watchdog_list(content)
        if watchdog_list:
            watchdog_raw_dict[file_name] = watchdog_list
    return watchdog_raw_dict


def parse_event_log_for_wd(root_path):
    flymeprint.debug('parsing event log...')
    event_log_entries = cachemanager.get_event_log_files()
    return parse_event_log_for_wd_by_entries(event_log_entries)


def parse_watchdog_raw_dict(watchdog_lists):
    watchdog_formated_dict = dict()
    for file_name in watchdog_lists.keys():
        max_time_str = None
        prev_content = None
        for content in watchdog_lists[file_name]:
            time_str = flymeparser.get_watchdog_time_event_log(content)
            if max_time_str is None:
                max_time_str = time_str
                prev_content = content
            elif time_str > max_time_str:
                max_time_str = time_str
                watchdog_lists[file_name].remove(prev_content)
                prev_content = content
        for content in watchdog_lists[file_name]:
            # matched_list = re.search('(^\d{2}-\d{2} (\d{2}):(\d{2}):(\d{
            # 2}))\.(\d{
            # 3})',
            #                  content, re.M)
            # if not matched_list:
            #    continue
            # flymeparser.get_anr_time_event_log()
            # time_str = matched_list.group(1)
            time_str = flymeparser.get_watchdog_time_event_log(content)
            watchdog_ss_pid = flymeparser.get_wd_ss_pid(content)
            if not time_str:
                continue
            if time_str in watchdog_formated_dict:
                continue
            watchdog_formated_dict[time_str] = dict()
            watchdog_formated_dict[time_str]['checker_list'] = list()
            watchdog_formated_dict[time_str]['file_name'] = file_name
            watchdog_formated_dict[time_str]['event_log'] = content
            time_struct = datetime.strptime(time_str, '%m-%d %H:%M:%S')
            watchdog_formated_dict[time_str]['time_struct'] = time_struct
            watchdog_formated_dict[time_str][
                'pid'] = watchdog_ss_pid
            # matched_list = re.findall(
            #    '(Blocked in handler on (?P<handler_name>.*?) \(('
            #    '?P<thread_name>.*?)\))',
            #    content)
            if flymeparser.is_sf_hang(content):
                watchdog_formated_dict[time_str]['__is_sf_hang__'] = True
                continue
            watchdog_formated_dict[time_str]['__is_sf_hang__'] = False
            matched_list = flymeparser.get_watchdog_hlist_event_log(content)
            if matched_list:
                for i in matched_list:
                    watchdog_formated_dict[time_str]['checker_list'].append(
                        {'checker_type':
                             'handler',
                         'event_log': i[0],
                         'checker_name': i[1],
                         'thread_name': i[2]})
        # matched_list = re.findall(
        #    '(Blocked in monitor (?P<class_name>.*?) on ('
        #    '?P<checker_name>.*?) '
        #    '\((?P<thread_name>.*?)\))',
        #    content)
        matched_list = flymeparser.get_watchdog_mlist_event_log(content)
        if matched_list:
            for i in matched_list:
                watchdog_formated_dict[time_str]['checker_list'].append(
                    {'checker_type':
                         'monitor',
                     'event_log': i[0],
                     'checker_class_name':
                         i[1],
                     'checker_name': i[2],
                     'thread_name': i[3]})
    if len(watchdog_formated_dict) == 0:
        flymeprint.error('no watchdog found in event log')
    return watchdog_formated_dict


def parse_data_anr_entries(data_anr_entries):
    flymeprint.debug('parsing data anr trace...')
    if not data_anr_entries:
        flymeprint.error('no data anr files found')
    trace_time_dict = dict()
    for file_name in data_anr_entries:
        # fo = open(file_name, encoding='utf-8')
        # content = fo.read()
        # fo.close()
        content = cachemanager.get_file_content(file_name)
        if not content:
            continue
        # match = re.findall(
        #    '^----- pid ' + '\d+' + ' at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{
        # 2}) '
        #                            '-----\nCmd line: ' + 'system_server',
        #    content, re.M)
        matched_list = flymeparser.get_trace_time_pid_for_wd(content)
        if not matched_list:
            continue
        for entry in matched_list:
            head = entry[0]
            pid = entry[1]
            time_str = entry[2]
            trace_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            trace_time_dict[time_str] = {'time_struct': trace_time,
                                         'file_name': file_name,
                                         'content': content,
                                         'pid': pid, 'head': head}

    if len(trace_time_dict) == 0 and len(data_anr_entries) != 0:
        flymeprint.error('no system_server trace matches')
    return trace_time_dict


def parse_data_anr_trace(root_path):
    trace_files = cachemanager.get_data_anr_trace_files()
    return parse_data_anr_entries(trace_files)


def parse_db_trace(root_path):
    flymeprint.debug('parsing db trace...')
    trace_files = cachemanager.get_db_trace_files()
    return parse_data_anr_entries(trace_files)


def get_pid_matched_ss_trace_dict(pid, system_server_trace_time_dict):
    trace_dict = dict()
    for time_str in system_server_trace_time_dict:
        if pid == system_server_trace_time_dict[time_str]['pid']:
            trace_dict[time_str] = system_server_trace_time_dict[time_str]
    return trace_dict


def get_matched_trace_time(watchdog_formated_dict,
                           system_server_trace_time_dict, is_pm):
    flymeprint.debug('getting best-matched time...')
    if is_pm:
        middle_t = 300
        pre_trunc = 600
    else:
        middle_t = 30
        pre_trunc = 120
    later_trunc = 120
    matched_time = dict()
    if len(system_server_trace_time_dict) < 2:
        flymeprint.error('system_server trace less than 2')
        return matched_time
    for watchdog_time_str in watchdog_formated_dict.keys():
        pid = watchdog_formated_dict[watchdog_time_str]['pid']
        ss_pid_matched_trace_dict = get_pid_matched_ss_trace_dict(pid,
                                                                  system_server_trace_time_dict)
        if not ss_pid_matched_trace_dict:
            flymeprint.warning('pid:' + pid + ' no trace')
            continue
        system_server_trace_time_list = ss_pid_matched_trace_dict.keys()

        best_previous_time_str = min(system_server_trace_time_list)
        best_previous_item = ss_pid_matched_trace_dict.pop(
            best_previous_time_str)
        best_previous_time_struct = best_previous_item['time_struct']
        best_previous_time_count = best_previous_time_struct.timestamp()
        best_previous_file_name = best_previous_item['file_name']
        best_previous_content = best_previous_item['content']
        best_previou_time_head = best_previous_item['head']
        if not system_server_trace_time_list:
            flymeprint.error('only one system trace found')
            continue
        best_later_time_str = max(system_server_trace_time_list)
        best_later_item = ss_pid_matched_trace_dict.pop(best_later_time_str)
        max_time_struct = best_later_time_struct = best_later_item[
            'time_struct']
        best_later_time_count = best_later_time_struct.timestamp()
        best_later_file_name = best_later_item['file_name']
        best_later_content = best_later_item['content']
        best_later_time_head = best_later_item['head']

        matched_time[watchdog_time_str] = dict()
        no_best_previous_time = True
        no_best_later_time = True
        no_best_time = True
        no_alternative_time = True
        new_time_struct = watchdog_formated_dict[watchdog_time_str][
            'time_struct'].replace(year=max_time_struct.year)
        watchdog_formated_dict[watchdog_time_str][
            'time_struct'] = new_time_struct
        new_time_count = new_time_struct.timestamp()
        if new_time_count > best_previous_time_count:
            no_alternative_time = False
        if new_time_count - best_previous_time_count >= middle_t:
            no_best_previous_time = False
        if new_time_count <= best_later_time_count:
            no_best_later_time = False
        if no_alternative_time:
            flymeprint.error(
                'watchdog time and trace time not match ---> ' +
                watchdog_time_str)
            continue
        if no_best_previous_time:
            flymeprint.warning(
                'no best previous time ---> ' + watchdog_time_str)
        if no_best_later_time:
            flymeprint.warning('no best later time ---> ' + watchdog_time_str)
        if (not no_best_previous_time) and (not no_best_later_time):
            no_best_time = False

        watchdog_time_struct = watchdog_formated_dict[watchdog_time_str][
            'time_struct']
        watchdog_time_count = watchdog_time_struct.timestamp()
        for system_server_time_str in ss_pid_matched_trace_dict.keys():
            system_server_trace_time_struct = ss_pid_matched_trace_dict[
                system_server_time_str]['time_struct']
            system_server_time_count = \
                system_server_trace_time_struct.timestamp()
            current_time_interval = watchdog_time_count - \
                                    system_server_time_count
            previous_time_interval = watchdog_time_count - \
                                     best_previous_time_count
            later_time_interval = watchdog_time_count - best_later_time_count
            current_file_name = \
                ss_pid_matched_trace_dict[system_server_time_str][
                    'file_name']
            current_content = \
                ss_pid_matched_trace_dict[system_server_time_str]['content']
            current_head = ss_pid_matched_trace_dict[system_server_time_str][
                'head']
            if no_best_time:
                change_best_previous = False
                change_best_later = False
                if no_best_previous_time:
                    if (current_time_interval > 0) and (
                                previous_time_interval < current_time_interval):
                        change_best_previous = True
                else:
                    if (current_time_interval - middle_t >= 0) and (
                                previous_time_interval > current_time_interval):
                        change_best_previous = True
                if change_best_previous:
                    best_previous_time_str = system_server_time_str
                    best_previous_time_count = system_server_time_count
                    best_previous_file_name = current_file_name
                    best_previous_content = current_content
                    best_previous_time_struct = system_server_trace_time_struct
                    best_previou_time_head = current_head
                if no_best_later_time:
                    if current_time_interval < later_time_interval:
                        change_best_later = True
                else:
                    if (current_time_interval <= 0) and (
                                current_time_interval > later_time_interval):
                        change_best_later = True
                if change_best_later:
                    best_later_time_str = system_server_time_str
                    best_later_time_count = system_server_time_count
                    best_later_file_name = current_file_name
                    best_later_content = current_content
                    best_later_time_struct = system_server_trace_time_struct
                    best_later_time_head = current_head
            else:
                if (current_time_interval - middle_t >= 0) and (
                            current_time_interval < previous_time_interval):
                    best_previous_time_str = system_server_time_str
                    best_previous_time_count = system_server_time_count
                    best_previous_file_name = current_file_name
                    best_previous_content = current_content
                    best_previous_time_struct = system_server_trace_time_struct
                    best_previou_time_head = current_head
                if (current_time_interval <= 0) and (
                            current_time_interval > later_time_interval):
                    best_later_time_str = system_server_time_str
                    best_later_time_count = system_server_time_count
                    best_later_file_name = current_file_name
                    best_later_content = current_content
                    best_later_time_struct = system_server_trace_time_struct
                    best_later_time_head = current_head
        if no_best_time:
            matched_time[watchdog_time_str][
                'best_alternative_previous_time_str'] = best_previous_time_str
            matched_time[watchdog_time_str][
                'best_alternative_later_time_str'] = best_later_time_str
            matched_time[watchdog_time_str][
                'best_alternative_previous_time_struct'] = \
                best_previous_time_struct
            matched_time[watchdog_time_str][
                'best_alternative_later_time_struct'] = \
                best_later_time_struct
            matched_time[watchdog_time_str][
                'best_alternative_previous_head'] = best_previou_time_head
            matched_time[watchdog_time_str][
                'best_alternative_later_head'] = best_later_time_head
        else:
            matched_time[watchdog_time_str][
                'best_previous_time_str'] = best_previous_time_str
            matched_time[watchdog_time_str][
                'best_later_time_str'] = best_later_time_str
            matched_time[watchdog_time_str][
                'best_previous_time_struct'] = best_previous_time_struct
            matched_time[watchdog_time_str][
                'best_later_time_struct'] = best_later_time_struct
            matched_time[watchdog_time_str][
                'best_previous_head'] = best_previou_time_head
            matched_time[watchdog_time_str][
                'best_later_head'] = best_later_time_head
        current_prev_trunc = watchdog_time_struct.timestamp() - \
                             best_previous_time_struct.timestamp()
        current_later_trunc = best_later_time_struct.timestamp() - \
                              watchdog_time_struct.timestamp()
        is_previous_valid = True
        is_later_valid = True
        p_ivalid_reason = None
        l_ivalid_reason = None
        if current_prev_trunc > pre_trunc:
            p_ivalid_reason = 'trace is ' + str(
                int(current_prev_trunc)) + 's long to ' \
                                           'watchdog ' \
                                           'time,' \
                                           'no need to ' \
                                           'print'
            is_previous_valid = False
        if current_later_trunc > later_trunc:
            is_later_valid = False
            l_ivalid_reason = 'trace is ' + str(
                int(current_later_trunc)) + 's long ' \
                                            'after ' \
                                            '' \
                                            '' \
                                            'watchdog ' \
                                            'time,' \
                                            'no need ' \
                                            'to print'
        matched_time[watchdog_time_str][
            'previous_file_name'] = best_previous_file_name
        matched_time[watchdog_time_str][
            'previous_content'] = best_previous_content
        matched_time[watchdog_time_str]['is_previous_valid'] = is_previous_valid
        matched_time[watchdog_time_str][
            'later_file_name'] = best_later_file_name
        matched_time[watchdog_time_str]['later_content'] = best_later_content
        matched_time[watchdog_time_str]['is_later_valid'] = is_later_valid
        matched_time[watchdog_time_str]['p_i_r'] = p_ivalid_reason
        matched_time[watchdog_time_str]['l_i_r'] = l_ivalid_reason
    return matched_time
