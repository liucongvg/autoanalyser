class BaseAnrObj:
    """
    time_and_filepath: a dick, 'anr_time' key for anr time, 'trace_time' key for trace 
    time
    'dropbox_file_name' key for whole current processing dropbox file name
    'anr_trace_file_name' key for whole data anr trace txt file name if exists
    
    mainTrace: a dict, 'trace' key for main thread stack, 'thread_state' key for main 
    thread state
    
    allMain: a dict, 'trace_time' key for dropbox trace time, 'anr_time' key for 
    dropbox anr time, 'content' key for dropbox whole trace only for target pid
    
    content: whole file content
    """

    def __init__(self, time_and_filepath, packageName, anrReason, cpuUsage, pid,
                 mainTrace, allMain, content):
        self.time_and_filepath = time_and_filepath
        self.packageName = packageName
        self.anrReason = anrReason
        self.cpuUsage = cpuUsage
        self.pid = pid
        self.mainTrace = mainTrace
        self.allMain = allMain
        self.content = content
