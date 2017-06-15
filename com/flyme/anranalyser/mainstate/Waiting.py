import re
from com.flyme.anranalyser.mainstate.Basestate import Basestate


class Waiting(Basestate):
    def __init__(self, anrobj):
        Basestate.__init__(self, anrobj)

    def generate_bug_and_undetermined_if_needed(self, bug, undetermined,
                                                notbug):
        main_trace_list = Basestate.get_main_list(self)
        reportBug = False
        if len(main_trace_list) >= 3 and main_trace_list[0][0].find(
                'java.lang.Object.wait!') != -1 and main_trace_list[1][0].find(
            'java.lang.Thread.join') != -1 and main_trace_list[2][0].find(
            self.anrObj.packageName) != -1:
            reportBug = True
        elif len(main_trace_list) >= 2 and main_trace_list[0][0].find(
                'java.lang.Object.wait!') != -1 and main_trace_list[1][0].find(
                self.anrObj.packageName) != -1:
            reportBug = True
        if reportBug:
            Basestate.generate_bug(self, bug)
        else:
            Basestate.generate_undetermined(self, undetermined)
