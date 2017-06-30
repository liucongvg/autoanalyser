import re
import os
import shutil


class Basestate:
    def __init__(self, anrObj):
        self.anrObj = anrObj
        self.matched_state_list = list()

    def get_main_list(self):
        return re.findall('^  at (.*?)(\n|\r\n)',
                          self.anrObj.mainTrace['trace'], re.M)

    def get_key(self):
        return self.__get_key_inner(self.anrObj.mainTrace)

    def __get_key_inner(self, mainTrace):
        key = mainTrace['thread_state'] + ' '
        main_trace_list = re.findall('^  at (.*?)\(.*?\)(\n|\r\n)',
                                     mainTrace['trace'], re.M)
        match_count = 0
        for i in main_trace_list:
            key += (i[0] + ' ')
            match_count += 1
            if match_count >= 3:
                break
        return key

    # def get_output_content(self):
    #        mainConcernedTrace = ''
    #        for i in self.anrObj.mainConcernedTrace["__thread_sequece__"]:
    #            mainConcernedTrace += self.anrObj.mainConcernedTrace[i][
    # "trace"] + '\n'
    #        outputMessage = 'produced from:\n' + self.anrObj.filename +
    # '\n\n' +
    # 'package ' \
    #
    # 'name:\n' + \
    #                        self.anrObj.packageName + '\n\n' + 'anr ' \
    #                                                           'time:\n' \
    #                        + \
    #                        self.anrObj.anrTime + '\n\n' + 'trace time:\n' + \
    #                        self.anrObj.traceTime \
    #                        + '\n\n' + 'anr reason:\n' + \
    #                        self.anrObj.anrReason + '\n\n' + 'cpu usage:\n' + \
    #                        self.anrObj.cpuUsage \
    #                        + '\n\n' + \
    #                        "main concerned stack trace:\n" +
    # mainConcernedTrace + \
    #                        '\n\n'
    #        return outputMessage

    def is_match(self, state):
        if not ('trace' in self.anrObj.mainTrace):
            return False
        l_state = self.anrObj.mainTrace['thread_state']
        l_trace = self.anrObj.mainTrace['trace']
        r_state = state.anrObj.mainTrace['thread_state']
        r_trace = state.anrObj.mainTrace['trace']
        return self.__is_main_matched(l_state, l_trace, r_state, r_trace)

    def __is_main_matched(self, l_state, l_trace, r_state, r_trace):
        if l_state != r_state:
            return False
        l_list = re.findall('^  at (.*?)\s', l_trace, re.M)
        r_list = re.findall('^  at (.*?)\s', r_trace, re.M)
        # if len(l_list) != len(r_list):
        #    return False
        if len(l_list) >= len(r_list):
            range = len(r_list)
        else:
            range = len(l_list)
        match_times = 0;
        for i in range:
            if l_list[i] != r_list[i]:
                return False
            if (++match_times >= 3):
                return True
        return True

    def generate_merge(self, merge):
        message = self.get_base_info() + '\n\n' + self.get_main_trace() \
                  + '\n\n' + self.get_cpuusage()
        self.generate_to_merge_file(message, merge)

    def generate_to_merge_file(self, message, merge):
        self.filename = os.path.basename(
            self.anrObj.time_and_filepath['dropbox_file_name'])
        self.merge_filename = os.path.join(merge, self.filename)
        fd = open(self.merge_filename, 'w', encoding='utf-8')
        fd.write(message)
        fd.close()

    def generate_bug_and_undetermined_if_needed(self, bug, undetermined,
                                                notbug):
        self.generate_undetermined(undetermined)

    def generate_bug(self, bug):
        shutil.copy(self.merge_filename, os.path.join(bug, self.filename))

    def generate_undetermined(self, undetermined):
        shutil.copy(self.merge_filename,
                    os.path.join(undetermined, self.filename))

    def generate_notbug(self, notbug):
        shutil.copy(self.merge_filename, os.path.join(notbug, self.filename))

    def __get_generate_from(self):
        message = 'Generated from:\n'
        if 'anr_trace_file_name' in self.anrObj.time_and_filepath:
            message += 'dropbox file:\n' + self.anrObj.time_and_filepath[
                'dropbox_file_name'] + '\n'
            message += 'anr trace tile:\n' + self.anrObj.time_and_filepath[
                'anr_trace_file_name'] + '\n'
            return message
        message += self.anrObj.time_and_filepath['dropbox_file_name']
        return message

    def __get_package_name(self):
        return 'Package name:\n' + self.anrObj.packageName

    def __get_repeat_time(self):
        return 'Repeated times:\n' + str(len(self.matched_state_list))

    def __get_event_log_anr_time(self):
        return 'Event log anr time:\n' + self.anrObj.time_and_filepath[
            'anr_time']

    def __get_trace_time(self):
        return 'Trace anr time:\n' + self.anrObj.time_and_filepath['trace_time']

    def __get_anr_in_time(self):
        if 'anr_in_time_str' not in self.anrObj.time_and_filepath:
            return 'ANR in time:\nnull'
        return 'ANR in time:\n' + self.anrObj.time_and_filepath[
            'anr_in_time_str']

    def get_base_info(self):
        return self.__get_generate_from() + '\n\n' + self.__get_package_name(

        ) + '\n\n' \
               + \
               self.__get_repeat_time() + '\n\n' + \
               self.__get_event_log_anr_time() + \
               '\n\n' \
               + self.__get_trace_time() + '\n\n' + self.__get_anr_in_time()

    def get_main_trace(self):
        return 'Main concerned trace:\n' + self.anrObj.mainTrace['trace']

    def get_cpuusage(self):
        return 'Cpu usage:\n' + self.anrObj.cpuUsage
