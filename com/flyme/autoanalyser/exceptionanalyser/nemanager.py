from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.exceptionanalyser.NE import NE
from com.flyme.autoanalyser.utils import flymeparser, flymeprint
import os

target_dir = '__neanalyser__'


def start(root_path):
    whole_target_dir = os.path.join(root_path, target_dir)
    ne_dict = parse_ne(root_path, whole_target_dir)
    if not ne_dict:
        flymeprint.error('error parsing ne')
    return ne_dict


def parse_ne(root_path, report_dir):
    flymeprint.debug('try ne...')
    cachemanager.root_path = root_path
    exp_main_files = cachemanager.get_db_exp_main_files()
    res_dict = dict()
    index = 0
    if cachemanager.mtk_db_only:
        res_dict['is_ne'] = True
        res_dict['brief_trace'] = dict()
        flymeparser.clean_and_build_dir(report_dir)
        for file_name in exp_main_files:
            content = cachemanager.get_file_content(file_name)
            ne_trace = flymeparser.get_ne_trace(content)
            ne = NE(ne_trace, file_name)
            index += 1
            ne.generate_report(report_dir, 'ne_' + str(index) + '.txt')
            res_dict['brief_trace'][file_name] = ne.get_brief_trace()
    else:
        main_files = cachemanager.get_main_log_files()
        is_ne = False
        time_list = list()
        for main_file in main_files:
            flymeprint.debug('parsing ' + main_file)
            content = cachemanager.get_file_content(main_file)
            ne_dict = flymeparser.parse_ne(content)
            if not ne_dict:
                continue
            if ne_dict['time'] in time_list:
                continue
            time_list.append(ne_dict['time'])
            is_ne = True
            flymeparser.clean_and_build_dir(report_dir)
            flymeprint.debug('ne detected...')
            ne = NE(ne_dict['trace'], main_file)
            index += 1
            ne.generate_report(report_dir, 'ne_' + str(index) + '.txt')
            break
        if not is_ne:
            flymeprint.debug('not ne...')
        res_dict['is_ne'] = is_ne
    return res_dict
