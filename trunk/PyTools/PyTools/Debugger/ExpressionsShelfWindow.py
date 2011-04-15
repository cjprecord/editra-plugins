# -*- coding: utf-8 -*-
# Name: ExpressionsShelfWindow.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window for debugger expressions"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import wx
import copy

# Editra Libraries
import ed_glob
from profiler import Profile_Get, Profile_Set

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.PyToolsUtils import RunProcInThread
from PyTools.Debugger.ExpressionDialog import ExpressionDialog
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.ExpressionsList import ExpressionsList
from PyTools.Debugger.RpdbDebugger import RpdbDebugger

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class ExpressionsShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(ExpressionsShelfWindow, self).__init__(parent)

        # Attributes
        ctrlbar = self.setup(ExpressionsList(self))
        ctrlbar.AddStretchSpacer()
        self.ignoredwarnings = {}
        self.executebtn = self.AddPlateButton(_("Execute"), ed_glob.ID_BIN_FILE, wx.ALIGN_LEFT)
        self.executebtn.ToolTip = wx.ToolTip(_("Execute"))
        self.expressions = ToolConfig.GetConfigValue(ToolConfig.TLC_EXPRESSIONS)

        self.layout("Clear", self.OnClear)
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_DELETE), wx.ART_MENU)
        self.taskbtn.SetBitmap(bmp)
        self._listCtrl.PopulateRows(self.expressions)

        # Debugger Attributes
        RpdbDebugger().restoreexpressions = self.RestoreExpressions
        RpdbDebugger().saveandrestoreexpressions = self.SaveAndRestoreExpressions
        RpdbDebugger().clearexpressionvalues = self._listCtrl.clearexpressionvalues

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnExecute, self.executebtn)

    def Unsubscription(self):
        """Cleanup callbacks when window is destroyed"""
        RpdbDebugger().restoreexpressions = lambda:None
        RpdbDebugger().saveandrestoreexpressions = lambda:None
        RpdbDebugger().clearexpressionvalues = lambda:None

    def OnThemeChanged(self, msg):
        """Update Icons"""
        super(VariablesShelfWindow, self).OnThemeChanged(msg)
        for btn, bmp in ((self.executebtn, ed_glob.ID_BIN_FILE),
                         (self.taskbtn, ed_glob.ID_DELETE)):
            bitmap = wx.ArtProvider.GetBitmap(str(bmp), wx.ART_MENU)
            btn.SetBitmap(bitmap)

    def DeleteExpression(self, expression):
        if not expression in self.expressions:
            return None
        del self.expressions[expression]
        self.SaveExpressions()

    def SetExpression(self, expression, enabled):
        self.expressions[expression] = enabled
        self.SaveExpressions()

    def RestoreExpressions(self):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(self.expressions)
        self._listCtrl.RefreshRows()

    def SaveExpressions(self):
        """Store expressions to the users persistent configuration"""
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[ToolConfig.TLC_EXPRESSIONS] = copy.deepcopy(self.expressions)
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)

    def SaveAndRestoreExpressions(self):
        self.SaveExpressions()
        self.RestoreExpressions()

    def OnClear(self, evt):
        """Clear the expressions"""
        self.expressions = {}
        self.SaveAndRestoreExpressions()

    def OnExecute(self, event):
        """Execute an expression"""
        desc = _("This code will be executed at the debuggee:")
        expr_dialog = ExpressionDialog(self, u"", _("Enter Code to Execute"),
                                       desc, None, (200, 200))
        pos = self.GetPositionTuple()
        expr_dialog.SetPosition((pos[0] + 50, pos[1] + 50))
        if expr_dialog.ShowModal() == wx.ID_OK:
            _expr = expr_dialog.get_expression()
            worker = RunProcInThread("DbgExec", self._oncodeexecuted,
                                     RpdbDebugger().execute, _expr)
            worker.start()
        expr_dialog.Destroy()

    def _oncodeexecuted(self, res):
        """Expression execution callback"""
        if not res:
            return
        if len(res) == 2:
            warning, error = res
        else:
            error = res
            warning = None

        PyToolsUtils.error_dialog(self, error)
        if warning and not warning in self.ignoredwarnings:
            dlg = wx.MessageDialog(self,
                                   _("Would you like to ignore this warning for the rest of this session?\n\n%s") % warning,\
                                   _("Ignore Warning"),
                                   wx.YES_NO|wx.YES_DEFAULT|wx.ICON_WARNING)
            if dlg.ShowModal() == wx.ID_YES:
                self.ignoredwarnings[warning] = True
            dlg.Destroy()
