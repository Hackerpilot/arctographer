#! /usr/bin/env python

################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Sep 24 2009
# License:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################


from __future__ import print_function

import logging
import getopt
import sys
if sys.hexversion < 0x020600f0:
	print("Please upgrade to Python 2.6. It is necessary for JSON file I/O")

import pygtk
import gtk

import arcmap.window
import arcmap.preferences

def setLogging(l, f):
	logging.basicConfig(level=l, format="%(levelname)5s %(name)8s %(lineno)4d: %(message)s",
		datefmt="%d %b %Y", filename=f, filemode="w")

def printUsage():
	print(
"""Usage: {0} (options) file
Options:
    -h, --help              Print this message
    -d, --debug=level       Set debug logging level
                            Can be debug, info, warn, error or
                            critical
    -lf, --logfile=file     Set log file""".format(sys.argv[0]))

def getDebugLevel(string):
	d = {
	"debug" : logging.DEBUG,
	"info" : logging.INFO,
	"warn" : logging.WARN,
	"error" : logging.ERROR,
	"critical" : logging.CRITICAL
	}
	if string not in d:
		return logging.WARN
	else:
		return d[string]

def main():
	# Setup the logging first
	try:
		options, arguments = getopt.getopt(sys.argv[1:], "hd:l:",
			["help", "debug=", "logfile="])
	except getopt.GetoptError, err:
		print(str(err))
		printUsage()
		sys.exit(2)

	logFile = None
	fileName = None
	debugLevel = logging.NOTSET

	for o, a in options:
		if o in ("-h", "--help"):
			printUsage()
			return
		elif o in ("-d", "--debug"):
			debugLevel = getDebugLevel(a)
		elif o in ("-l", "--logfile"):
			logFile = a
		else:
			print("unhandled option")
			return

	setLogging(debugLevel, logFile)

	if len(sys.argv) > 1:
		fileName = sys.argv[1]

	arcmap.preferences.load()
	w = arcmap.window.MainWindow(fileName)
	gtk.main()

if __name__ == "__main__":
	main()

