import os
import re
import shutil
from com.flyme.anranalyser.mainstate.Basestate import Basestate


class Blocked(Basestate):
    def __init__(self, anrObj):
        Basestate.__init__(self, anrObj)
        trace = ''
        self.mainConcernedTrace = self.__getMainConcernedTrace();
        for i in self.mainConcernedTrace['__thread_sequece__']:
            trace += (self.mainConcernedTrace[i]['trace'] + '\n')
        self.mainBlockedConcernedTrace = trace

    def generate_merge(self, merge):
        message = self.get_base_info() + '\n\n'
        message += self.mainBlockedConcernedTrace + '\n\n'
        message += self.get_cpuusage()
        self.generate_to_merge_file(message, merge)

    def __getMainConcernedTrace(self):
        mainConcernedTrace = dict()
        match = re.search(
            "(\"(main)\".*?tid=(\d+).*? (\w*)(.|\n)*?)(\n|\r\n){2}?",
            self.anrObj.allMain['content'])
        if not match:
            return mainConcernedTrace
        mainTrace = match.group(1)
        mainName = match.group(2)
        mainLocalTid = match.group(3)
        mainState = match.group(4)
        mainConcernedTrace[mainLocalTid] = {"trace": mainTrace,
                                            "thread_state": mainState,
                                            "thread_name": mainName}
        mainConcernedTrace["__thread_sequece__"] = [mainLocalTid]
        lastLocalThreadTid = mainLocalTid
        while mainConcernedTrace[lastLocalThreadTid][
            "thread_state"] == 'Blocked':
            match = re.search("waiting to lock.*held by thread (\d+)",
                              mainConcernedTrace[lastLocalThreadTid]["trace"])
            if not match:
                return mainConcernedTrace
            lockedTid = match.group(1)

            mainConcernedTrace[lastLocalThreadTid]["locked_tid"] = lockedTid

            match = re.search(
                "\"(.*)\" prio=.*tid=" + lockedTid + " (\w*)(.|\n)*?(("
                                                     "\n|\r\n){2}?)",
                self.anrObj.allMain['content'])
            if not match:
                return mainConcernedTrace
            threadTrace = match.group(0).rstrip(match.group(4))
            threadName = match.group(1)
            threadState = match.group(2)
            if lockedTid in mainConcernedTrace:
                break
            mainConcernedTrace[lockedTid] = {"trace": threadTrace,
                                             "thread_state": threadState,
                                             'thread_name': threadName}
            mainConcernedTrace["__thread_sequece__"].append(lockedTid)
            lastLocalThreadTid = lockedTid

        return mainConcernedTrace

    def generate_bug_and_undetermined_if_needed(self, bug, undetermined,
                                                notbug):
        length = len(self.mainConcernedTrace['__thread_sequece__'])
        lastTid = self.mainConcernedTrace['__thread_sequece__'][length - 1]
        reportBug = False
        last_stack_state = self.mainConcernedTrace[lastTid]['thread_state']
        if last_stack_state == 'Waiting' or last_stack_state == 'Sleeping':
            reportBug = True
        if reportBug:
            Basestate.generate_bug(self, bug)
        else:
            Basestate.generate_undetermined(self, undetermined)
