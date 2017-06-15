import datetime
from com.flyme.anranalyser.flymeutils import flymeparser

dropboxPath = '/home/liucong/temp/log/550716/M92QACPHRSUTT/dropbox'
anrPath = '/home/liucong/temp/log/550716/M92QACPHRSUTT/anr'
event_log_path_list = ['/home/liucong/temp/log/550716/M92QACPHRSUTT/mtklog/mobilelog/APLog_2017_0609_175615']


def main():
    start_time = datetime.datetime.now()
    flymeparser.parseDropbox(dropboxPath, anrPath, event_log_path_list)
    end_time = datetime.datetime.now()
    print('Time took: ' + str((end_time - start_time).seconds) + ' seconds')


if __name__ == '__main__':
    main()
