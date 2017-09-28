# flyme-stability

Note:本脚本适用于python3.4及以上版本

使用方法如下：(--android_reboot用于分析system_server进程的重启，--anr用于分析anr,--ouc_excel用于下载excel中的log并提取相关信息加入到数据库；root_path为log和trace等的根目录)
python3.4 __main__.py --android_reboot root_dir
or
python3.4 __main__.py --anr root_dir
or
python3.4 __main__.py --ouc_excel excel_path \[dest_path\](dest_path可不填,默认为/home/liucong/temp/ouc/)

Note:系统monkey产生anr后，一般会选两台发生anr较多的机子分析,由于加入了如果没有抓取到对应时间点的main
log就不提bug的情况，所以建议每次只跑一台机器的log(如：跑完monkey后，产生了两台机器的log，对应文件夹分别为a和b，将a和b放入文件夹c中，最好不要直接将c文件夹的路径传给脚本,而是应该分别将a和b的路径传给脚本，一共执行两次)


分析anr后生成的信息会在root_path下的__anranalyser__中
1.extractall：表示解压.gz得到的最原始的dropbox信息
2.bug：表示确定要提bug的项
3.notbug：表示确定不提bug的项
4.merge：表示merge（即去重）extractall后的项
5.undetermined：表示不确定的项，需要自己再分析

分析system_server进程重启后生成的信息会在root_path下的__swtanalyser__或者__jeanalyser__或者__neanalyser__中，对于swt，文件以'发生时间_swt.txt'命名，解析后的生成文件内容为发生swt前后最合适的时间点对应thread的trace信息，如果卡在binder通信，会根据db文件找到binder对端相应thread的trace，并会在文件头部生产产生重启的原因和可能的最终直接导致重启的线程的堆栈等信息。对于je，文件以je_1.txt, je_2.txt...以此类推来命名，以整个je的堆栈信息为主。对于ne，文件以ne_1.txt, ne_2.txt...以此类推累命名，以整个ne的堆栈信息为主。目前暂时只覆盖到swt, je, ne三种重启的情况，后续会逐步添加相关策略，添加其它情况导致的重启。
