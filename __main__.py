import datetime
import sys
from com.flyme.autoanalyser.swtanalyser import swtmanager
from com.flyme.autoanalyser.anranalyser import anrmanager

# dropboxPath = '/home/liucong/temp/log/549842/dropbox'
# anrPath = '/home/liucong/temp/log/549842/anr'
# event_log_path_list = ['/home/liucong/temp/log/549842/mtklog/mobilelog
# /APLog_2017_0607_110615']
from com.flyme.autoanalyser.utils import flymeprint


# root_path = '/home/liucong/temp/log/486145'


# root_path = '/home/liucong/temp/log/558525'


def main():
    start_time = datetime.datetime.now()
    if len(sys.argv) != 3:
        flymeprint.error(
            'invalid arguments! two parameter needed!\n--anr root_dir or '
            '--swt root_dir')
        return
    root_path = sys.argv[2]
    if sys.argv[1] == '--anr':
        anrmanager.start(root_path)
    elif sys.argv[1] == '--swt':
        swtmanager.start(root_path)
    else:
        flymeprint.error('use --anr or --swt')
        return
    end_time = datetime.datetime.now()
    flymeprint.debug(
        'Time took: ' + str((end_time - start_time).seconds) + ' seconds')


if __name__ == '__main__':
    main()
