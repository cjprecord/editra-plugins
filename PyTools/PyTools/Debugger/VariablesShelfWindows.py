# -*- coding: utf-8 -*-
# Name: VariablesShelfWindows.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id $"
__revision__ = "$Revision $"

#-----------------------------------------------------------------------------#
# Imports
import threading
import wx

# Editra Libraries
import util
import eclib
import ed_msg

# Local imports
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.VariablesLists import VariablesList
from PyTools.Debugger import RPDBDEBUGGER
import rpdb2

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class BaseVariablesShelfWindow(BaseShelfWindow):
    def __init__(self, parent, listtype, filterlevel):
        """Initialize the window"""
        super(BaseVariablesShelfWindow, self).__init__(parent)
        self.listtype = listtype
        ctrlbar = self.setup(VariablesList(self, listtype, filterlevel))
        self.layout("Unused", self.OnGo)
        
        # attributes
        self.filterlevel = filterlevel
        self.lock = threading.RLock()
        self.jobs = []
        self.n_workers = 0
        self.key = None

    def UpdateVariablesList(self, variables):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(variables)
        self._listCtrl.Refresh()

    def Unsubscription(self):
        pass

    def OnGo(self, event):
        pass
        
    def update_namespace(self, key, expressionlist):
        old_key = self.key
        old_expressionlist = self._listCtrl.get_expression_list()

        if key == old_key:
            expressionlist = old_expressionlist

        self.key = key

        if expressionlist is None:
            expressionlist = [(self.listtype, True)]

        self.post(expressionlist, self.filterlevel)

        return (old_key, old_expressionlist)

    def post(self, expressionlist, filter_level):
        self.jobs.insert(0, (expressionlist, filter_level))

        if self.n_workers == 0:
            pass
            #self.job_post(self.job_update_namespace, ())
        
    def job_update_namespace(self):
        while len(self.jobs) > 0:
            self.lock.acquire()
            self.n_workers += 1
            self.lock.release()
            
            try:
                del self.jobs[1:]
                (expressionlist, filter_level) = self.jobs.pop()
                rl = self.get_namespace(expressionlist, filter_level)
                wx.CallAfter(self.do_update_namespace, rl)

            except (rpdb2.ThreadDone, rpdb2.NoThreads):
                wx.CallAfter(self._listCtrl.Clear())

            self.lock.acquire()
            self.n_workers -= 1
            self.lock.release()

class LocalVariablesShelfWindow(BaseVariablesShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(LocalVariablesShelfWindow, self).__init__(parent, u"locals()", "Medium")

        # Attributes
        RPDBDEBUGGER.clearlocalvariables = self._listCtrl.Clear
        RPDBDEBUGGER.updatelocalvariables = self.update_namespace
        
class GlobalVariablesShelfWindow(BaseVariablesShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(GlobalVariablesShelfWindow, self).__init__(parent, u"globals()", "Medium")

        # Attributes
        RPDBDEBUGGER.clearglobalvariables = self._listCtrl.Clear
        RPDBDEBUGGER.updateglobalvariables = self.update_namespace
        
class ExceptionsShelfWindow(BaseVariablesShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(ExceptionsShelfWindow, self).__init__(parent, u"rpdb_exception_info", "Medium")

        # Attributes
        RPDBDEBUGGER.clearexceptions = self._listCtrl.Clear
        RPDBDEBUGGER.updateexceptions = self.update_namespace
        