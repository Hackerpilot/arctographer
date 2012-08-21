################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Sep 29 2009
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
File input and output for the TileMap class.
"""

import os.path
import logging
import json

import preferences
import tilemap
import graphics
import datafiles

log = logging.getLogger("mapio")


class MapWriter(object):
	def __init__(self, tileMap):
		self.__dictionary = {"layers": [], "images": []}
		self.__map = tileMap
		self.writeInfo(self.__map.width, self.__map.height, self.__map.tileSize)
		self.writeLayers(self.__map.layers)
		self.writeImages(self.__map.images)

	def writeInfo(self, width, height, tileSize):
		self.__dictionary["width"] = width
		self.__dictionary["height"] = height
		self.__dictionary["tileSize"] = tileSize

	def writeLayers(self, layers):
		for index, layer in enumerate(layers):
			self.__writeLayer(layer, index)

	def writeImages(self, images):
		for index, fileName in enumerate(images):
			self.__dictionary["images"].append({"index": index,
				"fileName": datafiles.getTilesetPath(fileName, True)})

	def __writeLayer(self, layer, index):
		layerDictionary = {"index": index, "name": layer.name,
			"visible": layer.visible, "tiles": []}
		for x, column in enumerate(layer.tiles):
			for y, tile in enumerate(column):
				if tile is not None:
					ix, iy, index = tile.getImageInfo()
					layerDictionary["tiles"].append({"x": x, "y": y, "ix": ix,
						"iy": iy, "ii": index})
		self.__dictionary["layers"].append(layerDictionary)

	def writef(self, fileName):
		try:
			f = open(fileName, "w")
		except IOError as e:
			log.warning(e)
		json.dump(self.__dictionary, f, indent=4)
		f.close()

	def writed(self):
		return self.__dictionary



class MapReader:
	"""
	Base class for map readers
	"""
	def __init__(self):
		self.map = tilemap.TileMap()

	def readf(self, fileName):
		try:
			f = open(fileName, "r")
		except IOException as e:
			log.error(e)
			f.close()
			return None

		try:
			d = json.load(f)
		except Exception as e:
			log.error(str(e))
			return None
		else:
			return self.readd(d)

	def readd(self, d):
		"""
		@type d: {}
		@param d: the tilemap structure in the form of a Python dictionary
		"""
		if "width" in d:
			if type(d["width"]) == int:
				self.map.width = d["width"]
			else:
				raise MapLoadException("Map's width must be an integer")
		else:
			raise MapLoadException("Width not specified for map file")

		if "height" in d:
			self.map.height = d["height"]
		else:
			log.error("Hight not specified for map file")
			return None

		if "tileSize" in d:
			self.map.tileSize = d["tileSize"]
		else:
			log.error("Tile size not specified in map file")
			return None

		if "images" in d:
			for image in d["images"]:
				self.__readImage(image)
		else:
			log.error("No image files specified in map file")
			return None

		if "layers" in d:
			if len(d["layers"]) == 0:
				self.map.addLayer("New Layer", True)
			else:
				for layer in d["layers"]:
					self.__readLayer(layer)
		else:
			log.error("No layers specified in map file")
			return None

		return self.map

	def __readImage(self, image):
		if "index" in image:
			if type(image["index"]) == int:
				index = image["index"]
			else:
				raise MapLoadException("Map indicies must be integers")
		else:
			raise MapLoadException("No index specified for image")

		if "fileName" in image:
			if type(image["fileName"]) == str or type(image["fileName"]) == unicode:
				fileName = datafiles.getTilesetPath(image["fileName"])
			else:
				raise MapLoadException("The file name for an image must be a string")
		else:
			raise MapLoadException("No file name specified for image")

		self.map.addImage(fileName, index)

	def __readLayer(self, layer):
		if "name" in layer:
			if type(layer["name"]) == str or type(layer["name"]) == unicode:
				name = layer["name"]
			else:
				raise MapLoadException("The name of the layer must be a string")
		else:
			name = "Unnamed Layer"
			log.error("No name specified for layer. Defaulting to \"Unnamed Layer\"")

		if "visible" in layer:
			if type(layer["visible"]) == bool:
				visible = layer["visible"]
			else:
				raise MapLoadException("The visibility of a map layer must be true or false")
		else:
			visible = True
			log.error("No visibility specified for layer. Defaulting to True")

		self.map.addLayer(name, visible)

		for tile in layer["tiles"]:
			if "x" in tile:
				if type(tile["x"]) == int:
					x = tile["x"]
				else:
					raise MapLoadException("Tile coordinates must be integers")
			else:
				raise MapLoadException("No x-coordinate specified for tile")

			if "y" in tile:
				if type(tile["y"]) == int:
					y = tile["y"]
				else:
					raise MapLoadException("Tile coordinates must be integers")
			else:
				raise MapLoadException("No y-coordinate specified for tile")

			if "ix" in tile:
				if type(tile["ix"]) == int:
					ix = tile["ix"]
				else:
					raise MapLoadException("Tile coordinates must be integers")
			else:
				raise MapLoadException("No image x-coordinate specified for tile")

			if "iy" in tile:
				if type(tile["iy"]) == int:
					iy = tile["iy"]
				else:
					raise MapLoadException("Tile coordinates must be integers")
			else:
				raise MapLoadException("No image y-coordinate specified for tile")

			if "ii" in tile:
				if type(tile["ii"]) == int:
					ii = tile["ii"]
				else:
					raise MapLoadException("Tile coordinates must be integers")
			else:
				raise MapLoadException("No image index specified for tile")

			t = tilemap.Tile(ii, ix, iy)
			self.map.addTile(t, x, y, layer["index"])


class MapLoadException(Exception):
	def __init__(self, message):
		self.msg = message

	def __str__(self):
		return self.msg
