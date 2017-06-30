import datetime
from com.flyme.anranalyser.flymeutils import flymeprint
from com.flyme.anranalyser.flymeutils import flymeparser

# dropboxPath = '/home/liucong/temp/log/549842/dropbox'
# anrPath = '/home/liucong/temp/log/549842/anr'
# event_log_path_list = ['/home/liucong/temp/log/549842/mtklog/mobilelog
# /APLog_2017_0607_110615']

root_path = '/home/liucong/temp/log/560313/sys_anr'


def main():
    start_time = datetime.datetime.now()
    flymeparser.parseDropbox(root_path)
    end_time = datetime.datetime.now()
    flymeprint.debug(
        'Time took: ' + str((end_time - start_time).seconds) + ' seconds')


if __name__ == '__main__':
    main()
