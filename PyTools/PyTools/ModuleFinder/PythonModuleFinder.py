# -*- coding: utf-8 -*-
# Name: PythonModuleFinder.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Pylint module for Python data """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import os
import pkg_resources

# Local Imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.ProcessCreator import ProcessCreator
from PyTools.ModuleFinder.AbstractModuleFinder import AbstractModuleFinder

# Editra Libraries
import util
import ebmlib

_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Error Ids
ERROR_NO_FINDMODULE, \
ERROR_UNKNOWN = range(0, 2)

INFO_USED_PATH, \
INFO_COMMAND_LINE, \
INFO_DIRVARS = range(0, 3)

#-----------------------------------------------------------------------------#

class PythonModuleFinder(AbstractModuleFinder):
    def __init__(self, variabledict, moduletofind):
        super(PythonModuleFinder, self).__init__(variabledict, moduletofind)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.pythonpath = variabledict.get("PYTHONPATH")

    def RunModuleFind(self):
        """Run Module Finder
        @note: runs on background thread
        """
        results = FindResults()
        flag, localpythonpath = ToolConfig.GetPythonExecutablePath("PyFind")

        if not flag:
            # No configured Python
            results.Errors.add(localpythonpath)
            return results

        # No findmodule found in plugin
        if not pkg_resources.resource_exists("PyTools.ModuleFinder", "findmodule.py"):
            results.Errors.add(ERROR_NO_FINDMODULE)
            return results

        findmodule_script = pkg_resources.resource_filename("PyTools.ModuleFinder", "findmodule.py")

        # Start find module
        finder_cmd = [localpythonpath, findmodule_script, self.moduletofind]
        processcreator = ProcessCreator("PyFind", ".", finder_cmd, self.pythonpath)
        process = processcreator.createprocess()
        stdoutdata, stderrdata = process.communicate()
        processcreator.restorepath()

        util.Log("[PyFind][info] stdout %s" % stdoutdata)
        util.Log("[PyFind][info] stderr %s" % stderrdata)
        util.Log("[PyFind][info] PyFind command finished running")
        try:
            stdoutrows = eval(stdoutdata.rstrip('\r\n'))
            if self.pythonpath:
                results.Info.append((INFO_USED_PATH, u", ".join(self.pythonpath)))
            results.Info.append((INFO_COMMAND_LINE, " ".join(finder_cmd)))
            if self.dirvarfile:
                results.Info.append((INFO_DIRVARS, self.dirvarfile))
            results.SetResults(stdoutrows)
            return results
        except Exception, ex:
            msg = repr(ex)
            util.Log("[PyFind][info] Error: %s" % msg)
            results.Errors.add(msg)
            return results
        results.Errors.add(ERROR_UNKNOWN)
        return results

#-----------------------------------------------------------------------------#

class FindResults(object):
    """Container class for find results"""
    def __init__(self):
        super(FindResults, self).__init__()

        # Attributes
        self._results = set() # List of tuples
        self._errors = set() # Set of errors
        self._info = list() # Info messages tuple(MSG_ID, string data)

    Results = property(lambda self: self._results)
    Errors = property(lambda self: self._errors)
    Info = property(lambda self: self._info)

    def SetResults(self, data):
        """Set the results"""
        tmpdata = [ f.lower() for f in data ]
        tmpdata = list(set(tmpdata))
        finaldata = list()
        for fname in tmpdata:
            for rname in data:
                if rname.lower() == fname:
                    finaldata.append(rname)
                    break
        self.Results.update(finaldata)