import re
from com.flyme.anranalyser.mainstate.Basestate import Basestate


class Native(Basestate):
    def __init__(self, anrObj):
        Basestate.__init__(self, anrObj)

    def generate_merge(self, merge):
        trace = self.anrObj.mainTrace['trace']
        list = re.findall('at (.*?)(\n|\r\n)', trace)
        if len(list) == 0 or list[0][
            0].strip() != 'android.view.ThreadedRenderer.nFence(Native method)':
            Basestate.generate_merge(self, merge)
            return
        else:
            match = re.search(
                "(\"(RenderThread)\".*?tid=(\d+).*? (\w*)(.|\n)*?)(\n|\r\n){"
                "2}?",
                self.anrObj.allMain['content'])
            if not match:
                Basestate.generate_merge(self, merge)
                return
            render_thread_trace = match.group(1)
            message = self.get_base_info() + '\n\n' + self.get_main_trace() \
                      + '\n' + render_thread_trace + '\n\n' + \
                      self.get_cpuusage()
            Basestate.generate_to_merge_file(self, message, merge)

    def generate_bug_and_undetermined_if_needed(self, bug, undetermined,
                                                notbug):
        main_list = Basestate.get_main_list(self)
        if len(main_list) >= 1 and main_list[0][0].find(
                'android.os.MessageQueue.nativePollOnce(Native method)') != -1:
            Basestate.generate_notbug(self, notbug)
        else:
            Basestate.generate_undetermined(self, undetermined)
