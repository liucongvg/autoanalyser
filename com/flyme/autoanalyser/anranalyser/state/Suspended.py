from com.flyme.autoanalyser.anranalyser.state.Basestate import Basestate


class Suspended(Basestate):
    def __init__(self, anrObj):
        Basestate.__init__(self, anrObj)
