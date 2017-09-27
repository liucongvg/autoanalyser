import datetime
import sys
import os

from com.flyme.autoanalyser.exceptionanalyser import jemanager, nemanager
from com.flyme.autoanalyser.oucanalyser import oucmanager
from com.flyme.autoanalyser.swtanalyser import swtmanager
from com.flyme.autoanalyser.anranalyser import anrmanager

# dropboxPath = '/home/liucong/temp/log/549842/dropbox'
# anrPath = '/home/liucong/temp/log/549842/anr'
# event_log_path_list = ['/home/liucong/temp/log/549842/mtklog/mobilelog
# /APLog_2017_0607_110615']
from com.flyme.autoanalyser.utils import flymeprint


def main():
    start_time = datetime.datetime.now()
    if (len(sys.argv) != 3) and (len(sys.argv) != 4):
        flymeprint.error(
            'invalid arguments! two or three parameter needed!\n--anr '
            'root_dir or '
            '--android_reboot root_dir or --ouc_excel excel_filename ['
            'dest_path]')
        return
    if os.path.isabs(sys.argv[0]):
        cdir = os.path.dirname(sys.argv[0])
        os.chdir(cdir)
    else:
        cdir = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
        os.chdir(cdir)
    flymeprint.debug('current dir:' + cdir)
    root_path = sys.argv[2]
    flymeprint.debug('root dir:' + root_path)
    if sys.argv[1] == '--anr':
        anrmanager.start(root_path)
    elif sys.argv[1] == '--android_reboot':
        if swtmanager.start(root_path)['is_swt']:
            pass
        elif jemanager.start(root_path)['is_je']:
            pass
        elif nemanager.start(root_path)['is_ne']:
            pass
        else:
            flymeprint.warning('unkonwn reboot type...')
    elif sys.argv[1] == '--ouc_excel':
        if len(sys.argv) == 4:
            dest_dir = sys.argv[3]
        else:
            dest_dir = None
        oucmanager.start(sys.argv[2], dest_dir)
    else:
        flymeprint.error('use --anr or --android_reboot or --ouc_excel')
        return
    end_time = datetime.datetime.now()
    flymeprint.debug(
        'Time took: ' + str((end_time - start_time).seconds) + ' seconds')


if __name__ == '__main__':
    main()
