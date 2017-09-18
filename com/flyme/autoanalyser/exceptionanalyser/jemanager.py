from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.exceptionanalyser.JE import JE
from com.flyme.autoanalyser.utils import flymeparser, flymeprint
import os

target_dir = '__jeanalyser__'


def start(root_path):
    whole_target_dir = os.path.join(root_path, target_dir)
    flymeparser.clean_and_build_dir(whole_target_dir)
    je_dict = parse_je(root_path, whole_target_dir)
    if not je_dict:
        flymeprint.error('error parsing je')
    return je_dict


def parse_je(root_path, report_dir):
    flymeprint.debug('parsing je...')
    cachemanager.root_path = root_path
    exp_main_files = cachemanager.get_db_exp_main_files()
    res_dict = dict()
    index = 0
    for file_name in exp_main_files:
        content = cachemanager.get_file_content(file_name)
        je_trace = flymeparser.get_je_trace(content)
        je = JE(je_trace, file_name)
        index += 1
        je.generate_report(report_dir, 'je_' + str(index) + '.txt')
        res_dict[file_name] = je.get_brief_trace()
    return res_dict
