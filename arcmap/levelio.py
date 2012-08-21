################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Oct 20 2009
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

import os
import logging
import json

import mapio
import worldio
import backgroundio


def write(fileName, tileMap, world, background):
	if tileMap is not None:
		mw = mapio.MapWriter(tileMap)
		md = mw.writed()
	else:
		md = None

	if world is not None:
		ww = worldio.WorldWriter(world)
		wd = ww.writed()
	else:
		wd = None

	if background is not None:
		bw = backgroundio.BackgroundWriter(background)
		bd = bw.writed()
	else:
		bd = None

	dictionary = {"background": bd, "tileMap": md, "blazeWorld": wd}

	try:
		f = open(fileName, "w")
	except IOError as e:
		log.error(e)
	else:
		json.dump(dictionary, f, indent=4)
		f.close()


def read(fileName):
	"""
	@type fileName: str
	@param fileName: the path of the file to load from
	@rtype: (background, BlazeWorld, TileMap)
	@return: the background (or None), the blaze world (or none), and the tile
		map (or none)
	This function will raise a LoadError on failure to signal the caller that
	something went wrong.
	"""
	background = None
	world = None
	tilemap = None

	try:
		f = open(fileName, "r")
	except IOError as e:
		err = LoadError(str(e))
		raise err

	try:
		dictionary = json.load(f)
	except Exception as e:
		err = LoadError(str(e))
		raise err

	if "background" in dictionary and dictionary["background"] is not None:
		bgReader = backgroundio.BackgroundReader()
		background = bgReader.readd(dictionary["background"])

	if "tileMap" in dictionary and dictionary["tileMap"] is not None:
		mapReader = mapio.MapReader()
		try:
			tilemap = mapReader.readd(dictionary["tileMap"])
		except mapio.MapLoadException as e:
			err = LoadError(str(e))
			raise err
	else:
		raise LoadError("No tileMap specified in level")

	if "blazeWorld" in dictionary and dictionary["blazeWorld"] is not None:
		blazeReader = worldio.WorldReader()
		world = blazeReader.readd(dictionary["blazeWorld"])

	return background, world, tilemap


class LoadError(Exception):
	def __init__(self, message):
		self.msg = message

	def __str__(self):
		return self.msg

