# SPDX-License-Identifier: LGPL-2.1-or-later

# ***************************************************************************
# *   Copyright (c) 2016 sliptonic <shopinthewoods@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD
import os
import traceback


def _caller():
    """internal function to determine the calling module."""
    filename, line, func, text = traceback.extract_stack(limit=3)[0]
    return os.path.splitext(os.path.basename(filename))[0], line, func


class Level:
    """Enumeration of log levels, used for setLevel and getLevel."""

    RESET = -1
    ERROR = 0
    WARNING = 1
    NOTICE = 2
    INFO = 3
    DEBUG = 4

    _names = {
        ERROR: "ERROR",
        WARNING: "WARNING",
        NOTICE: "NOTICE",
        INFO: "INFO",
        DEBUG: "DEBUG",
    }

    @classmethod
    def toString(cls, level):
        return cls._names.get(level, "UNKNOWN")


class ModuleLogger:
    _tracked = False
    _logLevel = None

    def __init__(self, module, initialLogLevel=None):
        self._logLevel = initialLogLevel
        self._module = module

    def getModule(self):
        return self._module

    def _log(self, level, msg):
        """internal function to do the logging"""

        if not self.willLogAt(level):
            return None

        message = "%s.%s: %s" % (self.getModule(), Level.toString(level), msg)
        if _useConsole:
            message += "\n"
            if level == Level.NOTICE:
                FreeCAD.Console.PrintLog(message)
            elif level == Level.WARNING:
                FreeCAD.Console.PrintWarning(message)
            elif level == Level.ERROR:
                FreeCAD.Console.PrintError(message)
            else:
                FreeCAD.Console.PrintMessage(message)
        else:
            print(message)
        return message

    def isTrackingEnabled(self):
        return self._tracked or _trackAll

    def setTrackingEnabled(self, enabled):
        """(enabled)"""
        self._tracked = enabled

    def enableTracking(self):
        self.setTrackingEnabled(True)

    def disableTracking(self):
        self.setTrackingEnabled(False)

    def getLevel(self):
        if self._logLevel is None:
            return _defaultLogLevel
        else:
            return self._logLevel

    def setLevel(self, level):
        if level == Level.RESET:
            self.level = None
        else:
            self.level = level

    def willLogAt(self, level):
        """(level)"""
        return self.getLevel() >= level

    def debug(self, message):
        """(message)"""
        if self.willLogAt(Level.DEBUG):
            module, line, func = _caller()
            return self._log(Level.DEBUG, "({}) - {}".format(line, message))

    def info(self, message):
        """(message)"""
        return self._log(Level.INFO, message)

    def notice(self, message):
        """(message)"""
        return self._log(Level.NOTICE, message)

    def warning(self, message):
        """(message)"""
        return self._log(Level.WARNING, message)

    def error(self, message):
        """(message)"""
        return self._log(Level.ERROR, message)

    def track(self, *args):
        """(....) - call with arguments of current function you want logged if tracking is enabled."""

        if self.isTrackingEnabled():
            module, line, func = _caller()
            message = "%s(%d).%s(%s)" % (
                module,
                line,
                func,
                ", ".join([str(arg) for arg in args]),
            )
            if _useConsole:
                FreeCAD.Console.PrintMessage(message + "\n")
            else:
                print(message)
            return message
        return None


_defaultLogLevel = Level.NOTICE
_useConsole = True
_trackAll = False
_moduleLoggers = {}


def thisModule():
    """returns the module id of the caller, can be used for setLevel, getLevel and trackModule."""
    return _caller()[0]


def logToConsole(yes):
    """(boolean) - if set to True (default behaviour) log messages are printed to the console. Otherwise they are printed to stdout."""
    global _useConsole
    _useConsole = yes


def getLoggerWithLevelOrDebugLogger(level, debug, module=None):
    """(level, debug, module=None)"""

    if module is None:
        module = _caller()[0]

    withLevel = Level.DEBUG if debug else level
    return getModuleLogger(module, withLevel=withLevel, enableTracking=debug)


def getModuleLogger(module=None, withLevel=None, enableTracking=None):
    """(module=None, withLevel=None, enableTracking=None)"""

    if module is None:
        module = _caller()[0]

    logger = _moduleLoggers.get(module, None)
    if logger is None:
        logger = ModuleLogger(module, initialLogLevel=withLevel)
        _moduleLoggers[module] = logger
    elif withLevel is not None:
        logger.setLevel(withLevel)

    if enableTracking is not None:
        logger.setTrackingEnabled(enableTracking)

    return logger


def setLevel(level, module=None):
    """(level, module = None)
    if no module is specified the default log level is set.
    Otherwise the module specific log level is changed (use RESET to clear)."""
    global _defaultLogLevel
    global _moduleLoggers
    if module:
        getModuleLogger(module).setLevel(level)
    else:
        if level == Level.RESET:
            _defaultLogLevel = Level.NOTICE

            for module in _moduleLoggers:
                module.setLevel(Level.RESET)
        else:
            _defaultLogLevel = level


def getLevel(module=None):
    """(module = None) - return the global (None) or module specific log level."""
    if module:
        return getModuleLogger(module).getLevel()

    return _defaultLogLevel


def trackAllModules(boolean):
    """(boolean) - if True all modules will be tracked, otherwise tracking is up to the module setting."""
    global _trackAll
    _trackAll = boolean


def untrackAllModules():
    """In addition to stop tracking all modules it also clears the tracking flag for all individual modules."""
    global _trackAll
    global _moduleLoggers

    _trackAll = False

    for module in _moduleLoggers:
        module.disableTracking()


def trackModule(module=None):
    """(module = None) - start tracking given module, current module if not set."""

    if module is None:
        module, _, _ = _caller()

    getModuleLogger(module).enableTracking()


def untrackModule(module=None):
    """(module = None) - stop tracking given module, current module if not set."""
    global _moduleLoggers

    if module is None:
        module, _, _ = _caller()

    logger = _moduleLoggers.get(module, None)

    if logger is not None:
        logger.disableTracking()
