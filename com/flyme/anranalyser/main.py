import datetime
from com.flyme.anranalyser.flymeutils import flymeparser

dropboxPath = '/home/liucong/temp/log/544309/22/dropbox'
# dropboxPath = '/home/liucong/temp/log/dropbox'
anrPath = '/home/liucong/temp/log/544309/22/anr'


def main():
    start_time = datetime.datetime.now()
    flymeparser.parseDropbox(dropboxPath, anrPath)
    end_time = datetime.datetime.now()
    print('Time took: ' + str((end_time - start_time).seconds) + ' seconds')


if __name__ == '__main__':
    main()
