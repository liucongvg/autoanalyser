import os

from com.flyme.autoanalyser.anranalyser.BaseAnrObj import BaseAnrObj
from com.flyme.autoanalyser.utils import flymeprint
from com.flyme.autoanalyser.utils import flymeparser
from com.flyme.autoanalyser.anranalyser.state.Suspended import Suspended
from com.flyme.autoanalyser.anranalyser.state.Otherstate import Otherstate
from com.flyme.autoanalyser.anranalyser.state.WaitingPerformingGc import \
    WaitingPerformingGc
from com.flyme.autoanalyser.anranalyser.state.WaitingForGcToComplete import \
    WaitingForGcToComplete
from com.flyme.autoanalyser.anranalyser.state.TimedWaiting import TimedWaiting
from com.flyme.autoanalyser.anranalyser.state.Runnable import Runnable
from com.flyme.autoanalyser.anranalyser.state.Native import Native
from com.flyme.autoanalyser.anranalyser.state.Blocked import Blocked
from com.flyme.autoanalyser.anranalyser.state.Waiting import Waiting
from com.flyme.autoanalyser.cache import cachemanager


def start(root_path):
    parse_dropbox(root_path)


def parse_dropbox(root_path):
    cachemanager.root_path = root_path
    try:
        is_dir = os.path.isdir(root_path)
        if not is_dir:
            flymeprint.warning('invalid root dir:' + root_path)
    except Exception as ex:
        flymeprint.warning(ex)
        return
    # anranalyser
    anranalyser = os.path.join(root_path, '__anranalyser__')
    # extract
    extractall = os.path.join(anranalyser, 'extractall')
    # use main stack to merge content
    merge = os.path.join(anranalyser, 'merge')
    # report bug according to policy
    bug = os.path.join(anranalyser, 'bug')
    # undetermined entry which should by analysed manually
    undetermined = os.path.join(anranalyser, 'undetermined')
    # notbug directory
    notbug = os.path.join(anranalyser, 'notbug')

    if not flymeparser.cleanAndBuildDir(extractall, merge, bug, undetermined,
                                        notbug):
        flymeprint.warning('can not cleanAndBuildDir')
        return

    state_obj_dict = dict()
    drop_box_entries = cachemanager.get_dropbox_files()
    if len(drop_box_entries) == 0:
        flymeprint.warning('no dropbox files found')
    data_anr_entries = cachemanager.get_data_anr_trace_files()
    if len(data_anr_entries) == 0:
        flymeprint.warning('no data anr files found')
    event_log_entries = cachemanager.get_event_log_files()
    if len(event_log_entries) == 0:
        flymeprint.warning('no event log files found')
    for dfile in drop_box_entries:
        entry = os.path.basename(dfile)
        flymeprint.debug('start process ---> ' + entry)
        dest_file = os.path.join(extractall, entry.rstrip('.gz'))
        file_content = cachemanager.get_file_content(dfile, dest_file)
        if file_content is None:
            flymeprint.error(dest_file + ' content empty')
            continue

        anrobj = parse_dfile(dfile, root_path)
        if not anrobj:
            continue
        anrobj.time_and_filepath['dropbox_file_name'] = dest_file
        if not is_a_valid_anr_obj(anrobj):
            flymeprint.error(entry + ' ---> incomplete information!!!')
            continue
        repair_pid_if_needed(anrobj)
        if anrobj.mainTrace["thread_state"] == 'Blocked':
            obj = Blocked(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Native':
            obj = Native(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Runnable':
            obj = Runnable(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Suspended':
            obj = Suspended(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'TimedWaiting':
            obj = TimedWaiting(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Waiting':
            obj = Waiting(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'WaitingForGcToComplete':
            obj = WaitingForGcToComplete(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'WaitingPerformGc':
            obj = WaitingPerformingGc(anrobj)
        else:
            obj = Otherstate(anrobj)
        append_to_merge_or_match(obj, state_obj_dict)
        flymeprint.debug('end process ---> ' + entry)

    generate_report(state_obj_dict.values(), merge, bug, undetermined, notbug)


def parse_dfile(dfile, root_path):
    content = cachemanager.get_file_content(dfile)
    if not content:
        return None
    package_name = flymeparser.get_pname_dropbox(content)
    anr_reason = flymeparser.get_subject_dropbox(content)
    cpu_usage = flymeparser.get_cpu_dropbox(content)

    anr_time = flymeparser.get_anr_time_event_log(content, package_name)
    pid = flymeparser.get_anr_pid_event_log(content,
                                            '\d{2}-\d{2} \d{2}:\d{2}:\d{'
                                            '2}.\d{3}',
                                            package_name)
    anr_in_time = flymeparser.get_anr_in_time(content, package_name)
    if len(anr_time) == 0:
        flymeprint.warning(
            'no dropbox anr time, get eventlog anr time for package:' +
            package_name)
        anr_time = get_event_log_anr_time(root_path, package_name)
        if len(anr_time) == 0:
            flymeprint.warning('no eventlog anr time for ' + package_name)
            return None

    trace_time = flymeparser.get_trace_time_for_anr(content, package_name)
    if len(trace_time) == 0:
        flymeprint.warning('no dropbox trace time')

    matched_time = flymeparser.get_matched_time_for_anr(trace_time, anr_time,
                                                        anr_in_time)
    if len(matched_time) == 0 and len(trace_time) != 0:
        flymeprint.warning('no dropbox trace matches')

    whole_trace = get_whole_trace_for_anr(content, package_name,
                                          matched_time, anr_time,
                                          anr_in_time,
                                          root_path)
    # renderThreadTrace = getRenderThreadTrace(whole_trace['content'])
    # binderTrace = getBinderTrace(whole_trace['content'])

    if 'content' not in whole_trace:
        return None
    main_trace = flymeparser.get_trace(whole_trace['content'], 'main')
    # mainThreadstate = main_trace["thread_state"]

    time_and_filepath = dict()
    if 'anr_time' in whole_trace:
        time_and_filepath['anr_time'] = whole_trace['anr_time']
    if 'trace_time' in whole_trace:
        time_and_filepath['trace_time'] = whole_trace['trace_time']
    if 'anr_trace_file_name' in whole_trace:
        time_and_filepath['anr_trace_file_name'] = whole_trace[
            'anr_trace_file_name']
    if 'event_log_path' in whole_trace:
        time_and_filepath['event_log_path'] = whole_trace['event_log_path']
    if 'anr_time_str' in anr_in_time:
        time_and_filepath['anr_in_time_str'] = anr_in_time['anr_time_str']

    anrobj = BaseAnrObj(time_and_filepath, package_name, anr_reason, cpu_usage,
                        pid,
                        main_trace, whole_trace, content)

    return anrobj


def get_whole_trace_for_anr(content, packageName, matchedTime, anrTime,
                            anr_in_time,
                            root_path):
    if len(anrTime) == 0:
        return dict()
    if len(matchedTime) == 0:
        flymeprint.debug('parse data anr trace')
        return parse_data_anr(packageName, anrTime, anr_in_time, root_path)
    return flymeparser.get_whole_trace_final(matchedTime, content)


def parse_data_anr(package_name, anr_time, anr_in_time, root_path):
    for file_name in cachemanager.get_data_anr_trace_files():
        content = cachemanager.get_file_content(file_name)
        if not content:
            continue
        trace_time = flymeparser.get_trace_time_for_anr(content, package_name)
        matched_time = flymeparser.get_matched_time_for_anr(trace_time,
                                                            anr_time,
                                                            anr_in_time)
        if len(matched_time) == 0:
            continue
        whole_trace = flymeparser.get_whole_trace_final(matched_time,
                                                        content)
        whole_trace['anr_trace_file_name'] = file_name
        if 'event_log_path' in anr_time[matched_time['anr_time']]:
            whole_trace['event_log_path'] = anr_time[matched_time['anr_time']][
                'event_log_path']
        return whole_trace
    flymeprint.warning('no data anr time matches')
    return dict()


def get_event_log_anr_time(root_path, package_name):
    anr_time = dict()
    event_log_entries = cachemanager.get_event_log_files()
    for file_name in event_log_entries:
        content = cachemanager.get_am_anr_cache(file_name)
        if not content:
            continue
        anr_time = flymeparser.get_anr_time_event_log(content, package_name)
        for i in anr_time.keys():
            anr_time[i] = {'anr_time': anr_time[i]['anr_time'],
                           'evnet_log_path': file_name}
    return anr_time


def is_a_valid_anr_obj(anrobj):
    if not anrobj.packageName:
        return False
    if ('anr_time' not in anrobj.time_and_filepath or 'trace_time' not in
        anrobj.time_and_filepath or 'dropbox_file_name' not in
        anrobj.time_and_filepath):
        return False
    if (
                    'trace' not in anrobj.mainTrace or 'thread_state' not in
                anrobj.mainTrace):
        return False
    if 'content' not in anrobj.allMain:
        return False
    return True


def repair_pid_if_needed(anrobj):
    pid = anrobj.pid
    repaired = False
    if pid is None or pid == '0':
        flymeprint.warning('pid:' + str(pid) + ', not valid, try to repair')
        anr_time = anrobj.time_and_filepath['anr_time']
        if 'event_log_path' in anrobj.time_and_filepath:
            # find pid in event log
            content = cachemanager.get_am_anr_cache(
                anrobj.time_and_filepath['event_log_path'])
            # match = re.search(
            #    '^\d{2}-\d{2} ' + anr_time + '.*?am_anr.*?\[\d+,(\d+),'
            #                                 '' + anrobj.packageName,
            #    content, re.M)
            pid = flymeparser.get_anr_pid_event_log(content, anr_time,
                                                    anrobj.packageName)
            if pid and pid != '0':
                repaired = True
            else:
                repaired = False
                # if match:
                #    pid = match.group(1)
                #    if not pid or pid == '0':
                #        repaired = False
                #    else:
                #        repaired = True
                #        anrobj.pid = pid
                # else:
                #    repaired = False
        if not repaired:
            trace_time = anrobj.time_and_filepath['trace_time']
            if 'anr_trace_file_name' in anrobj.time_and_filepath:
                # find pid in data anr trace
                content = cachemanager.get_file_content(
                    anrobj.time_and_filepath['anr_trace_file_name'])
                # repaired = flymeparser.fix_anr_obj_with_content(anrobj,
                #  content)
            else:
                # find pid in dropbox trace
                content = anrobj.content
            pid = flymeparser.get_trace_pid(content, trace_time,
                                            anrobj.packageName)
            if pid:
                repaired = True
                anrobj.pid = pid
            else:
                repaired = False
        if not repaired:
            flymeprint.warning('repair pid failed')
        else:
            flymeprint.debug('repair pid successfully ---> pid:' + anrobj.pid)


def append_to_merge_or_match(stateObj, state_obj_dict):
    key = stateObj.get_key()
    if key in state_obj_dict:
        flymeprint.debug('duplication for:' + key)
        state_obj_dict[key].matched_state_list.append(stateObj)
    else:
        state_obj_dict[key] = stateObj


def generate_report(state_obj_list, merge, bug, undetermined, notbug):
    if len(state_obj_list) == 0:
        return
    for i in state_obj_list:
        i.generate_merge(merge)
        i.generate_bug_and_undetermined_if_needed(bug, undetermined, notbug)
