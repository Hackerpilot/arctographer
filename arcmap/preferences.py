################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Sep 26 2009
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
Application preferences
"""

import os
import logging
import ConfigParser

import graphics
import datafiles

log = logging.getLogger("preferences")


# Zoom levels available for TileGrid instances
zoomLevels = [
	.25,
	.5,
	.75,
	1.0,
	1.5,
	2.0,
	4.0,
]
zoomNormalIndex = zoomLevels.index(1.0)

visual = {
	"handle_size" : 12,
	"valid_outline" : 0x00ff00ff,
	"valid_fill" : 0x00ff0080,
	"invalid_outline" : 0xff0000ff,
	"invalid_fill" : 0xff000080,
	"stipple_length" : 4,
	"stipple_gap" : 2,
}

# Default values for physics. (static geometry)
physics = {
	"default_friction" : 1.0,
	"default_restitution" : 0.0,
}

files = {
	"tileset_prefix" : os.path.join("images", "tiles"),
	"parallax_prefix" : os.path.join("images", "parallax"),
	"data_prefix" : "",
	"use_prefixes" : False
}

def save():
	"""
	Saves the user's preferences to a file named "config.ini"
	"""
	config = ConfigParser.SafeConfigParser()

	config.add_section("Visual")
	config.set("Visual", "handle_size", str(visual["handle_size"]))
	config.set("Visual", "stipple_length", str(visual["stipple_length"]))
	config.set("Visual", "stipple_gap", str(visual["stipple_gap"]))
	config.set("Visual", "valid_outline", "0x%08x" % visual["valid_outline"])
	config.set("Visual", "valid_fill", "0x%08x" % visual["valid_fill"])
	config.set("Visual", "invalid_outline",
		"0x%08x" % visual["invalid_outline"])
	config.set("Visual", "invalid_fill", "0x%08x" % visual["invalid_fill"])

	config.add_section("Physics")
	config.set("Physics", "default_restitution",
		str(physics["default_restitution"]))
	config.set("Physics", "default_friction",
		str(physics["default_friction"]))

	config.add_section("Files")
	config.set("Files", "tileset_prefix", str(files["tileset_prefix"]))
	config.set("Files", "parallax_prefix", str(files["parallax_prefix"]))
	config.set("Files", "data_prefix", str(files["data_prefix"]))
	config.set("Files", "use_prefixes", str(files["use_prefixes"]))

	if os.path.exists(datafiles.userConfigPath()) == False:
		try:
			os.makedirs(datafiles.userConfigPath(), 0700)
		except Exception as e:
			log.error("Creation of user configuration directory failed with" +
				" error: \"%s\'""" % e)
			return
	f = open(os.path.join(datafiles.userConfigPath(), "config.ini"), "w")
	config.write(f)

def load():
	"""
	Loads the user's preferences
	'"""
	path = os.path.join(datafiles.userConfigPath(), "config.ini")
	if os.path.exists(path):
		f = open(path, "r")
		config = ConfigParser.SafeConfigParser()
		config.readfp(f)

		def getIntOption(section, sectionName, name):
			try:
				section[name] = config.getint(sectionName, name)
			except ConfigParser.NoOptionError:
				pass
			except ValueError:
				pass

		def getFloatOption(section, sectionName, name):
			try:
				section[name] = config.getfloat(sectionName, name)
			except ConfigParser.NoOptionError:
				pass

		def getHexOption(section, sectionName, name):
			try:
				section[name] = config.get(sectionName, name)
			except ConfigParser.NoOptionError:
				pass
			try:
				section[name] = int(section[name], 16)
			except ValueError:
				pass

		def getBoolOption(section, sectionName, name):
			try:
				section[name] = config.getboolean(sectionName, name)
			except ConfigParser.NoOptionError:
				pass
			except ValueError:
				pass

		def getStringOption(section, sectionName, name):
			try:
				section[name] = config.get(sectionName, name)
			except ConfigParser.NoOptionError:
				pass

		getIntOption(visual, "Visual", "handle_size")
		getIntOption(visual, "Visual", "stipple_length")
		getIntOption(visual, "Visual", "stipple_gap")
		getHexOption(visual, "Visual", "valid_fill")
		getHexOption(visual, "Visual", "valid_outline")
		getHexOption(visual, "Visual", "invalid_fill")
		getHexOption(visual, "Visual", "invalid_outline")

		getFloatOption(physics, "Physics", "default_friction")
		getFloatOption(physics, "Physics", "default_restitution")

		getStringOption(files, "Files", "tileset_prefix")
		getStringOption(files, "Files", "parallax_prefix")
		getStringOption(files, "Files", "data_prefix")
		getBoolOption(files, "Files", "use_prefixes")

	else:
		log.info("Could not open user configuration file. Using defaults")
