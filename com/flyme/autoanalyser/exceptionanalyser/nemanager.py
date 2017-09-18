from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.exceptionanalyser.NE import NE
from com.flyme.autoanalyser.utils import flymeparser, flymeprint
import os

target_dir = '__neanalyser__'


def start(root_path):
    whole_target_dir = os.path.join(root_path, target_dir)
    flymeparser.clean_and_build_dir(whole_target_dir)
    ne_dict = parse_ne(root_path, whole_target_dir)
    if not ne_dict:
        flymeprint.error('error parsing ne')
    return ne_dict


def parse_ne(root_path, report_dir):
    flymeprint.debug('parsing ne...')
    cachemanager.root_path = root_path
    exp_main_files = cachemanager.get_db_exp_main_files()
    res_dict = dict()
    index = 0
    for file_name in exp_main_files:
        content = cachemanager.get_file_content(file_name)
        ne_trace = flymeparser.get_ne_trace(content)
        ne = NE(ne_trace, file_name)
        index += 1
        ne.generate_report(report_dir, 'ne_' + str(index) + '.txt')
        res_dict[file_name] = ne.get_brief_trace()
    return res_dict
