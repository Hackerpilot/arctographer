################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran
# Date: Oct 25 2009
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

import logging
import json

import background
import graphics
import datafiles

log = logging.getLogger("backgroundio")

class BackgroundWriter(object):
	def __init__(self, background):
		self.__dictionary = {}
		self.__dictionary["bgColor"] = "#%08x" % background.getBGColor().toU32()
		self.__dictionary["parallaxes"] = []
		for index, parallax in enumerate(background.getParallaxes()):
			self.__dictionary["parallaxes"].append(self.__writeParallax(
				parallax, index))

	def __writeParallax(self, parallax, index):
		dictionary = {}
		dictionary["index"] = index
		dictionary["fileName"] = datafiles.getParallaxPath(parallax.fileName,
			True)
		dictionary["vTile"] = parallax.vTile
		dictionary["hTile"] = parallax.hTile
		dictionary["vScroll"] = parallax.vScroll
		dictionary["hScroll"] = parallax.hScroll
		dictionary["vScrollSpeed"] = parallax.vScrollSpeed
		dictionary["hScrollSpeed"] = parallax.hScrollSpeed
		dictionary["visible"] = parallax.visible
		return dictionary

	def writed(self):
		return self.__dictionary

	def writef(self, fileName):
		try:
			f = open(fileName, "w")
		except IOError as e:
			log.error(e)
		json.dump(self.__dictionary, f, indent=0)
		f.close()


class BackgroundReader(object):
	def __init__(self):
		self.__background = None


	def readd(self, dictionary):
		"""
		@type dictionary: {}
		@param dictionary: dictionary parsed from JSON describing the background
		@rtype: background.Background
		@return: the parsed background
		"""
		bg = background.Background()

		if "bgColor" in dictionary:
			try:
				bgColor = int(dictionary["bgColor"][1:], 16)
			except ValueError:
				log.error("Invalid background color specified.")
				bgColor = 0x00000000
		else:
			bgColor = 0x00000000
			log.error("No background color specified. Defaulting to Black.")
		color = graphics.RGBA()
		color.fromU32(bgColor)
		bg.setBGColor(color)

		if "parallaxes" in dictionary:
			parallaxList = []
			for parallax in dictionary["parallaxes"]:
				p, index = self.__readParallax(parallax)
				if index == -1: # index not specified
					parallaxList.append(p)
				else:
					while(index + 1 > len(parallaxList)):
						parallaxList.append(None)
					parallaxList[index] = p
			if None in parallaxList:
				log.warning("Parallax indicies are not consecutive. Maybe something's missing?")
			newList = [i for i in parallaxList if i != None]
			bg.setParallaxes(newList)
		else:
			log.info("No parallaxes specified")

		return bg

	def readf(self, fileName):
		"""
		@type fileName: str
		@param fileName: the path to the file to read from
		@rtype: background.Background
		@return: the parsed background
		"""
		try:
			f = open(fileName, "r")
		except IOError as e:
			log.error(e)
			return None

		try:
			d = json.load(f)
		except Exception as e:
			log.error(e)
			return None
		else:
			return self.readd(d)

	def __readParallax(self, dictionary):
		p = background.ParallaxLayer()

		index = -1

		if "index" in dictionary:
			if type(dictionary["index"]) == int:
				index = dictionary["index"]
			else:
				log.error("The index of a parallax layer must be an integer.")
		else:
			log.error("Layer index not specified. This may lead to file corruption.")

		if "fileName" in dictionary:
			p.fileName = datafiles.getParallaxPath(
				dictionary["fileName"])
		else:
			log.error("No file name specified in file for parallax")

		if "vTile" in dictionary:
			if type(dictionary["vTile"]) == bool:
				p.vTile = dictionary["vTile"]
			else:
				log.error("vTile for a parallax background must be \"true\" or \"false\". Defaulting to false.")
		else:
			log.error("Vertical tiling not specified for parallax. Defaulting to false.")
			p.vTile = False

		if "hTile" in dictionary:
			p.hTile = bool(dictionary["hTile"])
		else:
			log.error("Horizontal tiling not specified for parallax. Defaulting to false.")
			p.hTile = False

		if "vScroll" in dictionary:
			p.vScroll = bool(dictionary["vScroll"])
		else:
			log.error("No vertical scroll specified for parallax. Defaulting to false.")
			p.vScroll = False

		if "hScroll" in dictionary:
			p.hScroll = bool(dictionary["hScroll"])
		else:
			log.error("No horizontal scroll specified for parallax. Defaulting to false.")
			p.hScroll = False

		if "vScrollSpeed" in dictionary:
			# The others are easy because a bool conversion never throws an
			# exception
			try:
				p.vScrollSpeed = float(dictionary["vScrollSpeed"])
			except ValueError:
				log.error("Could not convert %s to a decimal number for parallax vertical scroll speed. Defaulting to 1.0" %
					dictionary["vScrollSpeed"])
				p.vScrollSpeed = 1.0
		else:
			log.error("No vertical scroll speed specified for parallax. Defaulting to 1.0")
			p.vScrollSpeed = 1.0

		if "hScrollSpeed" in dictionary:
			try:
				p.hScrollSpeed = float(dictionary["hScrollSpeed"])
			except ValueError:
				log.error("Could not convert %s to a decimal number for parallax horizontal scroll speed. Defaulting to 1.0" %
					dictionary["hScrollSpeed"])
				p.hScrollSpeed = 1.0
		else:
			log.error("No horizontal scroll speed specified for parallax. Defaulting to 1.0")
			p.hScrollSpeed = 1.0

		if "visible" in dictionary:
			p.visible = bool(dictionary["visible"])
		else:
			log.error("No visibility specified for parallax. Defaulting to true.")
			p.visibile = True

		return p, index

