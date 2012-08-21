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

"""
Functions for getting paths for data files
"""

import os
import sys
import platform
import preferences
try:
	import _winreg
except ImportError:
	# Non-windows operating system. We don't need _winreg imported
	pass

# Small optimization to speed up calls to programDataPath
_programDataPath = None

def programDataPath():
	# Don't create a local _programDataPath
	global _programDataPath
	if _programDataPath is not None:
		return _programDataPath

	"""
	@rtype: str
	@return: the directory for the program's read-only data
	Mac OS-X support is non-existant
	"""
	if platform.system() == "Windows":
		try:
			key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\Arctographer")
		except WindowsError:
			path = "."
		else:
			path = _winreg.QueryValueEx(key, "Path")[0]
		_programDataPath = path
		return path
	elif platform.system() == "Linux":
		possibilities = [
			"/usr/share/arctographer",
			"/usr/share/games/arctographer",
			"/usr/local/share/arctographer",
			"/usr/local/share/games/arctographer",
			os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir)
		]
		for p in possibilities:
			if os.path.exists(p):
				_programDataPath = p
				return p
	else:
		raise Exception("Unsupported operating system")

def userConfigPath():
	"""
	Mac OS-X support is non-existant
	@rtype: str
	@return: the directory for storting user configuration files
	"""
	if platform.system() == "Windows":
		path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Artographer-0.3")
		return path
	elif platform.system() == "Linux":
		path = os.path.join(os.path.expanduser("~"), ".config", "arctographer")
		return path
	else:
		raise Exception("Unsupported operating system")


def getIconPath(iconName):
	"""
	Gets the path that icons are stored in
	"""
	return os.path.join(programDataPath(), "icons", iconName)

def getTilesetPath(fileName, save=False):
	"""
	Gets the path for a tileset
	@type fileName: str
	@param fileName: the name of the file
	@type save: bool
	@param save: Is the result being used to save a file path?
	"""
	if preferences.files["use_prefixes"]:
		if save:
			save = False
			return os.path.join(preferences.files["tileset_prefix"],
				os.path.basename(fileName))
		else:
			save = False
			return os.path.join(preferences.files["data_prefix"],
				preferences.files["tileset_prefix"],
				os.path.basename(fileName))
	else:
		save = False
		return fileName

def getParallaxPath(fileName, save=False):
	"""
	Gets a path for a parallax background
	@type save: bool
	@param save: Is the result being used to save a file path?
	"""
	if preferences.files["use_prefixes"]:
		if save:
			save = False
			return os.path.join(preferences.files["parallax_prefix"],
				os.path.basename(fileName))
		else:
			save = False
			return os.path.join(preferences.files["data_prefix"],
				preferences.files["parallax_prefix"],
				os.path.basename(fileName))
	else:
		save = False
		return fileName


class FileNotFoundError(Exception):
	def __init__(self, fileName):
		self.__fileName = fileName

	def __str__(self):
		return (("Could not find the file \"%s\". Please check your file "
			+"preferences and make sure that the file exists.")
			% self.__fileName)

