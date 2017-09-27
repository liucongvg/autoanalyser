from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.exceptionanalyser.JE import JE
from com.flyme.autoanalyser.utils import flymeparser, flymeprint
import os

target_dir = '__jeanalyser__'


def start(root_path):
    whole_target_dir = os.path.join(root_path, target_dir)
    je_dict = parse_je(root_path, whole_target_dir)
    if not je_dict:
        flymeprint.error('error parsing je')
    return je_dict


def parse_je(root_path, report_dir):
    flymeprint.debug('try je...')
    cachemanager.root_path = root_path
    res_dict = dict()
    index = 0
    if cachemanager.mtk_db_only:
        res_dict['is_je'] = True
        flymeparser.clean_and_build_dir(report_dir)
        res_dict['brief_trace'] = dict()
        exp_main_files = cachemanager.get_db_exp_main_files()
        for file_name in exp_main_files:
            content = cachemanager.get_file_content(file_name)
            je_trace = flymeparser.get_je_db_trace(content)
            je = JE(je_trace, file_name)
            index += 1
            je.generate_report(report_dir, 'je_' + str(index) + '.txt')
            res_dict['brief_trace'][file_name] = je.get_brief_trace()
    else:
        main_files = cachemanager.get_main_log_files()
        is_je = False
        time_list = list()
        for main_file in main_files:
            flymeprint.debug('parsing: ' + main_file)
            content = cachemanager.get_file_content(main_file)
            je_dict = flymeparser.parse_ss_je(content)
            if not je_dict:
                continue
            if je_dict['time'] in time_list:
                continue
            time_list.append(je_dict['time'])
            is_je = True
            flymeprint.debug('je detected...')
            flymeparser.clean_and_build_dir(report_dir)
            je = JE(je_dict['trace'], main_file)
            index += 1
            je.generate_report(report_dir, 'je_' + str(index) + '.txt')
            # res_dict['brief_trace'][main_file] = je.get_brief_trace()
            break
        if not is_je:
            flymeprint.debug('not je...')
        res_dict['is_je'] = is_je
    return res_dict
