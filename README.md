# flyme-stability
使用方法如下：
在main.py中会看到如下三个变量
dropboxPath = '/home/liucong/temp/log/550716/M92QACPHRSUTT/dropbox'
anrPath = '/home/liucong/temp/log/550716/M92QACPHRSUTT/anr'
event_log_path_list = ['/home/liucong/temp/log/550716/M92QACPHRSUTT/mtklog/mobilelog/APLog_2017_0609_175615']

其中dropboxPath是dropbox所在文件夹，anrPath是trace所在的文件夹，event_log_path_list是eventlog所在文件夹列表（因为可能会有多分，所以类型为列表），运行时直接更改这三个变量即可。
如此分三个变量可操作性不强，后续会改进。
