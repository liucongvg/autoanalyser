import hashlib
import os
import zipfile

from com.flyme.autoanalyser.cache import cachemanager
from com.flyme.autoanalyser.swtanalyser import swtmanager
from com.flyme.autoanalyser.utils import flymeparser, flymeprint
import datetime

try:
    import pandas
    import requests
    import pymysql
except Exception as ex:
    flymeprint.error(ex)


def start(excel_fn, dest_dir=None):
    if not dest_dir:
        dest_dir = '/home/liucong/temp/ouc/' + str(
            datetime.datetime.now().timestamp())
    parse_excel(excel_fn, dest_dir)


def parse_excel(excel_fn, ouc_dest_dir):
    try:
        db = pymysql.connect(host='localhost', user='flyme_stability',
                             password='123456', db='flyme_stability_1')
        table_name = 'pro7_urge_1'
        cursor = db.cursor()
        cursor.execute(
            'create table if not exists pro7_urge_1(download_uri varchar(256) '
            'not null,zip_md5 varchar(40) not null,db_md5 varchar(40) not '
            'null,primary key(db_md5),db_dir varchar(1024),fdevice varchar('
            '30),fpackage_name '
            'varchar(50),fflyme_ver varchar(80),'
            'index index_fpackage_name('
            'fpackage_name),fimei varchar(50),index index_fimei(fimei),'
            'fos_version varchar(10),'
            'froot varchar(10),fcountry varchar(10),fnetwork varchar(10),'
            'fcrashtime varchar(40),fupload_time varchar(40),inside_id '
            'varchar(40),stat_date varchar(20), exception_class varchar(20), '
            'index index_exception_class(exception_class),subject varchar('
            '512),index index_subject(subject),brief_trace varchar(512),'
            'index index_brief_trace(brief_trace),whole_trace varchar(8192),'
            'exception_log_time varchar(100))')
        db.commit()
        df = pandas.read_excel(excel_fn)
        try:
            loop_count = 0
            it = df.iterrows()
            while (True):
                entry_tuple = it.__next__()
                row = entry_tuple[1]
                flymeprint.debug('downloading ' + row[0])
                zip_file_tuple = flymeparser.download_log(row[0], ouc_dest_dir)
                zip_file = zip_file_tuple[0]
                md5sum = zip_file_tuple[1]
                try:
                    extract_log_to_db(cursor, table_name, row, zip_file, md5sum)
                    db.commit()
                except Exception as ex:
                    flymeprint.warning(ex)
                finally:
                    cachemanager.free_cache()
                    # loop_count += 1
                    # if loop_count == 10:
                    #    break
        except StopIteration as stop_ex:
            flymeprint.debug('parse excel done')
            # ouc_dest_dir = '/home/liucong/temp/ouc/1503385916.620414'
    except Exception as ex:
        flymeprint.error(ex)
    finally:
        if not db:
            db.close()


def extract_log_to_db(cursor, table_name, row, zip_file, zip_md5sum):
    # zip_list = os.listdir(dest_dir)
    # for zip_file in zip_list:
    #    if os.path.isdir(os.path.join(dest_dir, zip_file)):
    #        continue
    #    fname = os.path.join(dest_dir, zip_file)
    fname = zip_file
    dname = fname + '_'
    zf = zipfile.ZipFile(fname, 'r')
    os.makedirs(dname, exist_ok=True)
    zf.extractall(dname)
    for root, dirs, files in os.walk(dname):
        for entry in dirs:
            if flymeparser.is_fname_match(entry, 'db\..*?dbg\.DEC'):
                flymeparser.clean_files(os.path.join(root, entry))
        for entry in files:
            if flymeparser.is_fname_match(entry, 'db\..*dbg'):
                to_extract = os.path.join(root, entry)
                flymeparser.extract_db(to_extract)
                fd = open(to_extract, mode='rb')
                db_md5_sum = hashlib.md5(fd.read()).hexdigest()
                db_dir = os.path.join(root, entry + '.DEC')
                whole_trace = ''
                brief_trace = ''
                fd = open(os.path.join(db_dir, '__exp_main.txt'),
                          encoding='utf-8')
                exp_main_content = fd.read()
                exception_class = flymeparser.get_exclass(exp_main_content)
                subject = flymeparser.get_sj(exp_main_content)
                exception_log_time = flymeparser.get_exlt(exp_main_content)
                if exception_class == 'SWT':
                    flymeprint.debug('exception class:SWT')
                    watchdog_raw_dict = swtmanager.parse_db_watchdog(root)
                    is_valid_swt = False
                    is_valid_trace = False
                    is_trace_matched = False
                    if watchdog_raw_dict:
                        is_valid_swt = True
                        watchdog_formated_dict = \
                            swtmanager.parse_watchdog_raw_dict(
                                watchdog_raw_dict)
                        system_server_trace_time_dict = \
                            swtmanager.parse_db_trace(
                                root)
                        if system_server_trace_time_dict:
                            is_valid_trace = True
                            matched_trace_time = \
                                swtmanager.get_matched_trace_time(
                                    watchdog_formated_dict,
                                    system_server_trace_time_dict,
                                    False)
                            if matched_trace_time:
                                is_trace_matched = True
                                pm_matched_trace_time = \
                                    swtmanager.get_pm_matched_trace_time(
                                        system_server_trace_time_dict,
                                        watchdog_formated_dict)
                                swtobj_dict = swtmanager.get_swtobj_dict(
                                    watchdog_formated_dict, matched_trace_time,
                                    pm_matched_trace_time)
                                for key in swtobj_dict.keys():
                                    swt = swtobj_dict[key]
                                    if (len(swt.handler_list) == 0) and (
                                                len(swt.monitor_list) == 0):
                                        brief_trace = swt.event_log
                                        whole_trace = swt.event_log
                                    else:
                                        for item in swt.handler_list:
                                            # if item.later_trace['is_valid']:
                                            #    current_trace = \
                                            #
                                            # flymeparser.get_swt_report_trace(
                                            #            item.later_trace[
                                            #                'content'],
                                            #            item.thread_name)
                                            #    if not current_trace:
                                            #        flymeprint.warning(
                                            #            'current trace empty')
                                            #        break
                                            #    else:
                                            #        whole_trace += (
                                            #            current_trace + '\n')
                                            #        brief_trace += (
                                            #
                                            # flymeparser.get_brief_trace(
                                            #                current_trace,
                                            #                False) +
                                            #            '\n')
                                            #        # whole_trace += (
                                            #        #    item.later_trace[
                                            #        #        'content'] + '\n')
                                            #        # brief_trace += (
                                            #        #
                                            #        #
                                            # flymeparser.get_brief_trace(
                                            #        #        item.later_trace[
                                            #        #            'content'] +
                                            #        #  '\n'))
                                            # else:
                                            #    whole_trace +=
                                            # item.later_trace[
                                            #        'i_r']
                                            #    brief_trace = whole_trace
                                            #    break
                                            wbdict = \
                                                get_checker_whole_brief_trace(
                                                    item)
                                            whole_trace += wbdict['whole_trace']
                                            brief_trace += wbdict['brief_trace']
                                            if wbdict['should_break']:
                                                break
                                        for item in swt.monitor_list:
                                            wbdict = \
                                                get_checker_whole_brief_trace(
                                                    item)
                                            whole_trace += wbdict['whole_trace']
                                            brief_trace += wbdict['brief_trace']
                                            if wbdict['should_break']:
                                                break
                                    break
                            else:
                                is_trace_matched = False
                                flymeprint.error('no trace matched')
                                reason = 'no matched trace found for swt time'
                                whole_trace = reason
                                brief_trace = reason
                        else:
                            is_valid_trace = False
                            flymeprint.error('no valid trace')
                            reason = 'no system_server trace found'
                            whole_trace = reason
                            brief_trace = reason
                    else:
                        is_valid_swt = False
                        flymeprint.debug('not swt')
                        reason = 'no watchdog keyword found in event log'
                        whole_trace = reason
                        brief_trace = reason
                elif exception_class == 'Java (JE)':
                    flymeprint.debug('exception class:Java (JE)')
                    whole_trace = flymeparser.get_je_trace(exp_main_content)
                    brief_trace = flymeparser.get_brief_trace(whole_trace, True)
                elif exception_class == 'Native (NE)':
                    whole_trace = flymeparser.get_ne_trace(exp_main_content)
                    brief_trace = flymeparser.get_brief_ne_trace(whole_trace)
                    flymeprint.debug('exception class:Native (NE)')
                else:
                    flymeprint.debug(
                        'exception class:' + exception_class + ',ignored...')
                    reason = 'ignored exception class'
                    whole_trace = reason
                    brief_trace = reason
                if os.path.exists(db_dir):
                    additional_dict = {'db_dir': db_dir, 'zip_md5': zip_md5sum,
                                       'db_md5': db_md5_sum,
                                       'whole_trace': whole_trace.replace('\'',
                                                                          '\'\''),
                                       'brief_trace': brief_trace.replace('\'',
                                                                          '\'\''),
                                       'exception_class': exception_class,
                                       'subject': subject,
                                       'exception_log_time': exception_log_time}
                    try:
                        flymeparser.insert_to_database(cursor, table_name, row,
                                                       additional_dict)
                    except Exception as ex:
                        flymeprint.warning(ex)
                else:
                    flymeprint.error('db dir not match with db file')
                fd.close()


def get_checker_whole_brief_trace(item):
    whole_trace = ''
    brief_trace = ''
    should_break = False
    if item.later_trace['is_valid']:
        current_trace = \
            flymeparser.get_swt_report_trace(
                item.later_trace[
                    'content'],
                item.thread_name)
        if not current_trace:
            flymeprint.warning(
                'current trace empty')
            should_break = True
        else:
            whole_trace += (
                current_trace + '\n')
            brief_trace += (
                flymeparser.get_brief_trace(
                    current_trace,
                    False) +
                '\n')
            # whole_trace += (
            #    item.later_trace[
            #        'content'] + '\n')
            # brief_trace += (
            #
            # flymeparser.get_brief_trace(
            #        item.later_trace[
            #            'content'] +
            #  '\n'))
    else:
        whole_trace = item.later_trace[
            'i_r']
        brief_trace = whole_trace
        should_break = True
    return {'whole_trace': whole_trace, 'brief_trace': brief_trace,
            'should_break': should_break}
