import os
import shutil
import gzip
import re
from com.flyme.anranalyser.flymeutils.BaseAnrObj import BaseAnrObj
from com.flyme.anranalyser.flymeutils import flymeprint

from com.flyme.anranalyser.mainstate.Blocked import Blocked
from com.flyme.anranalyser.mainstate.Native import Native
from com.flyme.anranalyser.mainstate.Otherstate import Otherstate
from com.flyme.anranalyser.mainstate.Runnable import Runnable
from com.flyme.anranalyser.mainstate.Suspended import Suspended
from com.flyme.anranalyser.mainstate.TimedWaiting import TimedWaiting
from com.flyme.anranalyser.mainstate.Waiting import Waiting
from com.flyme.anranalyser.mainstate.WaitingForGcToComplete import \
    WaitingForGcToComplete
from com.flyme.anranalyser.mainstate.WaitingPerformingGc import \
    WaitingPerformingGc


def parseDropbox(dropbox, anr):
    try:
        listDir = os.listdir(dropbox)
    except Exception as ex:
        flymeprint.errorprint(ex)
        return
    # extract
    extractall = os.path.join(dropbox, 'extractall')
    # use main stack to merge content
    merge = os.path.join(dropbox, 'merge')
    # report bug according to policy
    bug = os.path.join(dropbox, 'bug')
    # undetermined entry which should by analysed manually
    undetermined = os.path.join(dropbox, 'undetermined')
    # notbug directory
    notbug = os.path.join(dropbox, 'notbug')

    if not cleanAndBuildDir(extractall, merge, bug, undetermined, notbug):
        flymeprint.errorprint('can not cleanAndBuildDir')
        return

    state_obj_dict = dict()
    for entry in listDir:
        # only system_app_anr is concerned
        # match = re.match('(system_app_anr|data_app_anr).*\.gz', entry)
        match = re.match('(system_app_anr).*\.gz', entry)
        if not match:
            continue
        print('start process ---> ' + entry)
        fullName = os.path.join(dropbox, entry)
        newEntry = entry.rstrip('.gz')
        fullNew = os.path.join(extractall, newEntry)
        wholeFile = extractGzToDest(fullName, fullNew)
        if wholeFile == '':
            continue

        anrobj = parseContent(wholeFile, fullNew, anr)
        if not is_a_valid_anr_obj(anrobj):
            flymeprint.errorprint(entry + ' ---> 信息不完整')
            continue
        if anrobj.mainTrace["thread_state"] == 'Blocked':
            obj = Blocked(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Native':
            obj = Native(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Runnable':
            obj = Runnable(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Suspended':
            obj = Suspended(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'TimedWaiting':
            obj = TimedWaiting(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'Waiting':
            obj = Waiting(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'WaitingForGcToComplete':
            obj = WaitingForGcToComplete(anrobj)
        elif anrobj.mainTrace["thread_state"] == 'WaitingPerformGc':
            obj = WaitingPerformingGc(anrobj)
        else:
            obj = Otherstate(anrobj)
        append_to_merge_or_match(obj, state_obj_dict)
        print('end process ---> ' + entry)

    generate_report(state_obj_dict.values(), merge, bug, undetermined, notbug)


def append_to_merge_or_match(stateObj, state_obj_dict):
    key = stateObj.get_key()
    if key in state_obj_dict:
        print('duplication')
        state_obj_dict[key].matched_state_list.append(stateObj)
    else:
        state_obj_dict[key] = stateObj


def generate_report(state_obj_list, merge, bug, undetermined, notbug):
    if len(state_obj_list) == 0:
        return
    for i in state_obj_list:
        i.generate_merge(merge)
        i.generate_bug_and_undetermined_if_needed(bug, undetermined, notbug)


def is_a_valid_anr_obj(anrobj):
    if (anrobj.packageName == 'null' or anrobj.pid == 'null'):
        return False
    if ('anr_time' not in anrobj.time_and_filepath or 'trace_time' not in
        anrobj.time_and_filepath or 'dropbox_file_name' not in
        anrobj.time_and_filepath):
        return False
    if (
                    'trace' not in anrobj.mainTrace or 'thread_state' not in
                anrobj.mainTrace):
        return False
    if ('content' not in anrobj.allMain):
        return False
    return True


# def mergeOutput(output, merge):
#    mergedList = list()
#    for outputEntry in os.listdir(output):
#        output_entry = os.path.join(output, outputEntry)
#        fo = open(output_entry, 'r')
#        content = fo.read()
#        entry_mainConcerndTrace = getMainConcernedTrace(content)
#        entry_thread_state = entry_mainConcerndTrace['main']['thread_state']
#        entry_trace = entry_mainConcerndTrace['main']['trace']
#        entry_trace_list = re.findall('at .*?\(', entry_trace)
#        match = re.search('package name:(\n|\r\n)(.*)', content)
#        if not match:
#            print('warning package name not match')
#            continue
#        entry_packageName = match.group(2)
#
#        matched = False
#        for i in mergedList:
#            if entry_packageName in i:
#                state = i[entry_packageName]['thread_state']
#                trace = i[entry_packageName]['trace']
#                if state == entry_thread_state and entry_trace_list_equal(
#                        entry_trace_list, trace):
#                    print("match")
#                    matched = True
#                    break
#
#        if not matched:
#            mergedList.append({entry_packageName: {'thread_state':
# entry_thread_state,
#                                                   'trace': entry_trace_list}})
#            merge_entry = os.path.join(merge, outputEntry)
#            print('Producing ' + merge_entry)
#            shutil.copy(output_entry, merge_entry)


def entry_trace_list_equal(entry_trace_list, list):
    if entry_trace_list.__len__() != list.__len__():
        return False
    for i in range(list.__len__()):
        if (entry_trace_list[i] != list[i]):
            return False
    return True


def cleanAndBuildDir(*dirs):
    try:
        for i in dirs:
            if os.path.exists(i):
                shutil.rmtree(i)
            os.mkdir(i)
    except Exception as ex:
        flymeprint.errorprint(ex)
        return False
    return True


def extractGzToDest(src, dest):
    try:
        gz = gzip.open(src, 'rb')
        wholeFile = gz.read().decode()
        newFile = open(dest, 'w')
        newFile.write(wholeFile)
        newFile.close()
    except Exception as ex:
        flymeprint.errorprint(ex)
        return ''
    return wholeFile


def parseContent(content, filename, anrPath):
    # processName = getProcessName(content)
    packageName = getPackageName(content)
    anrReason = getAnrReason(content)
    # build = getbuild(content)
    cpuUsage = getCpuUsage(content)
    pid = getPid(content)

    anrTime = getDropboxAnrTime(content, packageName)
    if len(anrTime) == 0:
        flymeprint.errorprint('no dropbox anr time')

    traceTime = getTraceTime(content, packageName, pid)
    if len(traceTime) == 0:
        flymeprint.errorprint('no dropbox trace time')

    matchedTime = getMatchedTime(traceTime, anrTime)
    if len(matchedTime) == 0:
        flymeprint.errorprint('dropbox anr time does not match trace time')

    allMain = getWholeMain(content, packageName, pid, matchedTime, anrTime,
                           anrPath)
    # renderThreadTrace = getRenderThreadTrace(allMain['content'])
    # binderTrace = getBinderTrace(allMain['content'])

    mainTrace = getMainTrace(allMain)
    # mainThreadstate = mainTrace["thread_state"]

    time_and_filepath = dict()
    if 'anr_time' in allMain:
        time_and_filepath['anr_time'] = allMain['anr_time']
    if 'trace_time' in allMain:
        time_and_filepath['trace_time'] = allMain['trace_time']
    if 'anr_trace_file_name' in allMain:
        time_and_filepath['anr_trace_file_name'] = allMain[
            'anr_trace_file_name']
    time_and_filepath['dropbox_file_name'] = filename

    anrobj = BaseAnrObj(time_and_filepath, packageName, anrReason, cpuUsage,
                        pid,
                        mainTrace, allMain, content)

    return anrobj


def getMatchedTime(traceTime, anrTime):
    matchedTime = dict()
    for i in anrTime.keys():
        for j in traceTime.keys():
            # if anrTime[i] < 1 * 60 * 60 * 1000 and traceTime[j] > 11 * 60 *
            #  60 * 1000:
            #     if (
            #                                         11 * 60 * 60 * 1000 +
            # 59 * 60 *
            #                             1000 +
            #                             59 * 1000 - traceTime[j] + anrTime[
            # i]) < 3 *
            # 1000:
            #         matchedTime.append(
            #             {'anr_time': anrTime[i], 'trace_time': traceTime[j]})
            #         continue
            if traceTime[j] < 1 * 60 * 60 * 1000 and anrTime[
                i] > 11 * 60 * 60 * 1000:
                if (
                                                    11 * 60 * 60 * 1000 + 59
                                        * 60 *
                                        1000 +
                                        60 * 1000 - anrTime[i] + traceTime[
                            j]) < 3 * 1000:
                    matchedTime['anr_time'] = i
                    matchedTime['trace_time'] = j
                    break
                    # matchedTime.append(
                    #     {'anr_time': anrTime[i], 'trace_time': traceTime[j]})
                    # continue
            else:
                if traceTime[j] - anrTime[i] < 3000:
                    # matchedTime.append(
                    #     {'anr_time': anrTime[i], 'trace_time': traceTime[j]})
                    # continue
                    matchedTime['anr_time'] = i
                    matchedTime['trace_time'] = j
                    break
    return matchedTime


def parse_data_anr(packageName, pid, anrTime, anrPath):
    anrentries = os.listdir(anrPath)
    for i in anrentries:
        match = re.search('traces.*?\.txt', i)
        if match:
            wholeAnrPath = os.path.join(anrPath, i)
            content = open(wholeAnrPath).read()
            traceTime = getTraceTime(content, packageName, pid)
            matchedTime = getMatchedTime(traceTime, anrTime)
            if len(matchedTime) == 0:
                continue
            allMain = getWholeMainFinal(pid, matchedTime, content)
            allMain['anr_trace_file_name'] = wholeAnrPath
            return allMain
    flymeprint.errorprint('no data anr time matches')
    return dict()


def getWholeMain(content, packageName, pid, matchedTime, anrTime, anrPath):
    if len(anrTime) == 0:
        return dict()
    if len(matchedTime) == 0:
        return parse_data_anr(packageName, pid, anrTime, anrPath)
    return getWholeMainFinal(pid, matchedTime, content)


def getWholeMainFinal(pid, matchedTime, content):
    if 'trace_time' not in matchedTime or 'anr_time' not in matchedTime:
        return dict()
    match = re.search(
        '----- pid ' + pid + ' at \d{4}-\d{2}-\d{2} ' + matchedTime[
            'trace_time'] + ' -----' + "((.|\n)*?)" + "----- end " + pid + " -----",
        content)
    if not match:
        return dict()
    allMain = dict()
    allMain['trace_time'] = matchedTime['trace_time']
    allMain['anr_time'] = matchedTime['anr_time']
    allMain['content'] = match.group(1)
    return allMain


def getProcessName(content):
    match = re.match("^Process: (.*)\s", content)
    if not match:
        return "null"
    return match.group(1)


def getPackageName(content):
    match = re.search("Package: (.*) v.*\s", content)
    if not match:
        return "null"
    return match.group(1)


def getAnrReason(content):
    match = re.search("Subject: (.*)\s", content)
    if not match:
        return "null"
    return match.group(1)


def getbuild(content):
    match = re.search("Build: (.*)\s", content)
    if not match:
        return "null"
    return match.group(1)


def getCpuUsage(content):
    # match = re.search("Build.*\s*((.|\n)*?)\s*----- pid.", content)
    match = re.search(
        "(\n|\r\n){2}((.|\n)*?(CPU usage from(.|\n)*?)(\r\n|\n){2}?)",
        content)
    if not match:
        return "null"
    return match.group(4)


def getPid(content):
    match = re.search("(.|\n)*?----- pid ((\d)*)", content)
    if not match:
        return "null"
    return match.group(2)


def getDropboxAnrTime(content, packageName):
    match = re.findall(
        '\d{2}-\d{2} (\d{2}:\d{2}:\d{2}.\d{3}).*?am_anr.*?' + packageName +
        '.*',
        content)
    anrTime = dict()
    for i in match:
        match = re.search('(\d{2}):(\d{2}):(\d{2}).(\d{3})', i)
        hour = match.group(1)
        minute = match.group(2)
        second = match.group(3)
        minisecond = match.group(4)
        wholeMinisecond = int(minisecond) + int(second) * 1000 + int(
            minute) * 60 * 1000 + int(hour) * \
                                  60 * 60 \
                                  * 1000
        anrTime[i] = wholeMinisecond
    return anrTime


def getTraceTime(content, pakcageName, pid):
    traceTime = dict()  # key is string time, value is integer time
    match = re.findall(
        '----- pid ' + pid + ' at \d*-\d*-\d* (\d{2}:\d{2}:\d{2}) -----\s{1,'
                             '2}Cmd line: ' + pakcageName,
        content)
    for i in match:
        match = re.search('(\d{2}):(\d{2}):(\d{2})', i)
        hour = match.group(1)
        minute = match.group(2)
        second = match.group(3)
        wholeMinisecond = int(second) * 1000 + int(minute) * 60 * 1000 + int(
            hour) * 60 * 60 * 1000
        traceTime[i] = wholeMinisecond
    return traceTime


def getRenderThreadTrace(allMain):
    match = re.search("(.|\n)*?(\"RenderThread\" prio=(.|\n)*?)(\n|\r\n){2}?",
                      allMain)
    if not match:
        return "null"
    return match.group(2)


def getBinderTrace(allMain):
    match = re.findall("(\"Binder_\d{1,2}\" prio=(.|\n)*?)(\n|\r\n){2}?",
                       allMain)
    if not match:
        return "null"
    binderList = list()
    for i in match:
        binderList.append(i[0])
    return tuple(binderList)


def getMainConcernedTrace(allMain):
    mainConcernedTrace = dict()
    match = re.search("(\"(main)\".*?tid=(\d+).*? (\w*)(.|\n)*?)(\n|\r\n){2}?",
                      allMain)
    if not match:
        return mainConcernedTrace
    mainTrace = match.group(1)
    mainName = match.group(2)
    mainLocalTid = match.group(3)
    mainState = match.group(4)
    mainConcernedTrace[mainLocalTid] = {"trace": mainTrace,
                                        "thread_state": mainState,
                                        "thread_name": mainName}
    mainConcernedTrace["__thread_sequece__"] = mainLocalTid
    lastLocalThreadTid = mainLocalTid
    while mainConcernedTrace[lastLocalThreadTid]["thread_state"] == 'Blocked':
        match = re.search("waiting to lock.*held by thread (\d+)",
                          mainConcernedTrace[lastLocalThreadTid]["trace"])
        if not match:
            return mainConcernedTrace
        lockedTid = match.group(1)
        mainConcernedTrace[lastLocalThreadTid]["locked_tid"] = lockedTid

        match = re.search(
            "\"(.*)\" prio=.*tid=" + lockedTid + " (\w*)(.|\n)*?((\n|\r\n){"
                                                 "2}?)",
            allMain)
        if not match:
            return mainConcernedTrace
        threadTrace = match.group(0).rstrip(match.group(4))
        threadName = match.group(1)
        threadState = match.group(2)
        mainConcernedTrace[lockedTid] = {"trace": threadTrace,
                                         "thread_state": threadState,
                                         'thread_name': threadName}
        mainConcernedTrace["__thread_sequece__"].append(lockedTid)
        lastLocalThreadTid = lockedTid

    return mainConcernedTrace


def getMainTrace(allMain):
    mainTrace = dict()
    if 'content' not in allMain:
        return mainTrace
    match = re.search("(\"(main)\".*?tid=(\d+).*? (\w*)(.|\n)*?)(\n|\r\n){2}?",
                      allMain['content'])
    if not match:
        return mainTrace
    mainTrace['trace'] = match.group(1)
    mainTrace['thread_state'] = match.group(4)
    return mainTrace


def anrobjtofile(anrObj, fullName):
    newFile = open(fullName, 'w')
    mainConcernedTrace = ''
    for i in anrObj.mainConcernedTrace["__thread_sequece__"]:
        mainConcernedTrace += anrObj.mainConcernedTrace[i]["trace"] + '\n'
    outputMessage = 'package name:\n' + anrObj.packageName + '\n\n' + 'anr ' \
                                                                      'time:\n' \
                    + \
                    anrObj.anrTime + '\n\n' + 'trace time:\n' + \
                    str(anrObj.traceTime) \
                    + '\n\n' + 'anr reason:\n' + \
                    anrObj.anrReason + '\n\n' + 'cpu usage:\n' + \
                    anrObj.cpuUsage \
                    + '\n\n' + \
                    "main concerned stack trace:\n" + mainConcernedTrace + \
                    '\n\n'
    newFile.write(outputMessage)
    newFile.close()
