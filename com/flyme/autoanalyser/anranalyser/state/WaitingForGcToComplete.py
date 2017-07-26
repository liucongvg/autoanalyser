import re

from com.flyme.autoanalyser.anranalyser.state.Basestate import Basestate


class WaitingForGcToComplete(Basestate):
    def __init__(self, anrobj):
        Basestate.__init__(self, anrobj)

    def generate_bug_and_undetermined_if_needed(self, bug, undetermined,
                                                notbug):
        match = re.search(
            '\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{3} ' + self.anrObj.pid + ' \d+ '
                                                                       'E '
                                                                       'AndroidRuntime: java.lang.OutOfMemoryError: Failed to allocate a.*? until OOM',
            self.anrObj.content)
        if match:
            Basestate.generate_bug(self, bug)
        else:
            Basestate.generate_undetermined(self, undetermined)
