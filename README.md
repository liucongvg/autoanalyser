# flyme-stability
使用方法如下：
在main.py中会看到如下变量

root_path = '....'

root_path即为下载log解压后的根目录,使用时替换为相应路径即可


生成的信息会在root_path下的__anranalyser__中
1.extractall：表示解压.gz得到的最原始的dropbox信息
2.bug：表示确定要提bug的项
3.notbug：表示确定不提bug的项
4.merge：表示merge（即去重）extractall后的项
5.undetermined：表示不确定的项，需要自己再分析
