import datetime
from com.flyme.anranalyser.flymeutils import flymeparser

dropboxPath = '/home/liucong/temp/log/dropbox'
anrPath = '/home/liucong/temp/log/anr'

def main():
    start_time = datetime.datetime.now()
    flymeparser.parseDropbox(dropboxPath, anrPath)
    end_time = datetime.datetime.now()
    print('Time took: ' + str((end_time - start_time).seconds) + ' seconds')

main()
