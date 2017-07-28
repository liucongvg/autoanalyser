from com.flyme.autoanalyser.utils import flymeparser, flymeprint
import os

root_path = None

whole_file_cache = dict()
am_anr_cache = dict()
event_log_watchdog_cache = dict()

cached_1 = False
dropbox_files = list()
data_anr_trace_files = list()
event_log_files = list()

cached_2 = False
db_event_log_dict = dict()
db_trace_dict = dict()
db_process_and_threads_dict = dict()
db_binderif_dict = dict()


def get_file_content(src_file, dest_file=None):
    if src_file in whole_file_cache:
        return whole_file_cache[src_file]
    if src_file.endswith('.gz'):
        content = flymeparser.extractGz(src_file, dest_file)
    else:
        content = open(src_file, encoding='utf-8').read()
    whole_file_cache[src_file] = content
    return content


def get_am_anr_cache(file_name):
    if file_name in am_anr_cache:
        return am_anr_cache[file_name]
    content = get_file_content(file_name)
    if not content:
        return None
    am_anr_list = flymeparser.get_am_anr_list(content)
    if not am_anr_list:
        return None
    content = str()
    last_index = len(am_anr_list) - 1
    for i in range(len(am_anr_list)):
        if i == last_index:
            content += am_anr_list[i]
        else:
            content += (am_anr_list[i] + '\n')
    am_anr_cache[file_name] = content
    return content


def get_dropbox_files():
    if not cached_1:
        cache_all_file_entries()
    return dropbox_files


def get_data_anr_trace_files():
    if not cached_1:
        cache_all_file_entries()
    return data_anr_trace_files


def get_event_log_files():
    if not cached_1:
        cache_all_file_entries()
    return event_log_files


def cache_all_concerned_db_file_entries():
    # clear and extract db
    global cached_2
    cached_2 = True
    for current_root_dir, current_dir_entries, current_file_entries in os.walk(
            root_path):
        for dir in current_dir_entries:
            if flymeparser.is_fname_match(dir,
                                          'db\.fatal\.\d{2}\.SWT\.dbg\.DEC'):
                flymeparser.clean_files(os.path.join(current_root_dir, dir))
        for file in current_file_entries:
            if flymeparser.is_fname_match(file, 'db\.fatal\.\d{2}\.SWT\.dbg'):
                try:
                    flymeparser.extract_db(os.path.join(current_root_dir, file))
                except Exception as ex:
                    flymeprint.error(ex)
    # cache
    for current_root_dir, current_dir_entries, current_file_entries in os.walk(
            root_path):
        for file in current_file_entries:
            if not flymeparser.is_swt_dir(os.path.basename(current_root_dir)):
                continue
            pid = flymeparser.get_ss_pid_by_swtdir(current_root_dir)
            if flymeparser.is_fname_match(file, 'SYS_ANDROID_EVENT_LOG'):
                db_event_log_dict[pid] = os.path.join(current_root_dir, file)
                # db_event_log_files.append(os.path.join(current_root_dir,
                # file))
            if flymeparser.is_fname_match(file, 'SWT_JBT_TRACES'):
                db_trace_dict[pid] = os.path.join(current_root_dir, file)
                # db_trace_files.append(os.path.join(current_root_dir, file))
            if flymeparser.is_fname_match(file, 'SYS_PROCESSES_AND_THREADS'):
                # db_process_and_threads_files.append(
                #    os.path.join(current_root_dir, file))
                db_process_and_threads_dict[pid] = os.path.join(
                    current_root_dir, file)
            if flymeparser.is_fname_match(file, 'SYS_BINDER_INFO'):
                # db_binderif_files.append(os.path.join(current_root_dir, file))
                db_binderif_dict[pid] = os.path.join(current_root_dir, file)
    return


def get_db_event_log_files():
    return get_db_event_log_dict().values()


def get_db_event_log_dict():
    if not cached_2:
        cache_all_concerned_db_file_entries()
    return db_event_log_dict


def get_db_trace_files():
    return get_db_trace_dict().values()


def get_db_trace_dict():
    if not cached_2:
        cache_all_concerned_db_file_entries()
    return db_trace_dict


def get_db_pt_files():
    return get_db_pt_dict().values()


def get_db_pt_dict():
    if not cached_2:
        cache_all_concerned_db_file_entries()
    return db_process_and_threads_dict


def get_db_bi_files():
    return get_db_bi_dict().values()


def get_db_bi_dict():
    if not cached_2:
        cache_all_concerned_db_file_entries()
    return db_binderif_dict


def cache_all_file_entries():
    global cached_1
    cached_1 = True
    for current_root_dir, current_dir_entries, current_file_entries in os.walk(
            root_path):
        for file_name in current_file_entries:
            # match = re.match('system_app_anr.*\.gz', file_name)
            if flymeparser.is_fname_match(file_name, 'system_app_anr.*\.gz'):
                dropbox_files.append(os.path.join(current_root_dir, file_name))
            # match = re.match('traces.*?\.txt', file_name)
            if flymeparser.is_fname_match(file_name, 'traces.*?\.txt'):
                data_anr_trace_files.append(
                    os.path.join(current_root_dir, file_name))
            # match = re.match('events.*', file_name)
            if flymeparser.is_fname_match(file_name, 'events.*'):
                event_log_files.append(
                    os.path.join(current_root_dir, file_name))
