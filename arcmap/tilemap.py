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
Contains classes to represent the tile map.
"""


__docformat__ = "epytext"

import copy
import logging

import mapio

import graphics

log = logging.getLogger("tilemap")

class TileMap:
	def __init__(self):
		# Measured in tiles
		self.width = 0
		# Measured in tiles
		self.height = 0
		# Measured in pixels
		self.tileSize = 32
		# Map's layers
		self.layers = []
		# Image files used
		self.images = []

	def resize(self, width, height, xOffset, yOffset):
		"""
		Resizes the map
		@type width: int
		@param width: The new width
		@type height: int
		@param height: The new height
		@type xOffset: int
		@param xOffset: the number of tiles that the existing tiles sholuld be
		    shifted right. This number can be negative.
		@type yOffset: int
		@param yOffset: the number of tiles that the existing tiles should be
			shifted down. This number can be negative.
		"""
		if width == self.width and height == self.height:
			return
		for l in self.layers:
			l.resize(width, height, xOffset, yOffset)
		self.width = width
		self.height = height

	def getTile(self, x, y, layer):
		"""
		@rtype: (int, int, int)
		@return: the image x-coordinate, y-coordinate, and index, or None if
			there was no tile at the specified coordinates
		"""
		if layer > len(self.layers):
			return None
		else:
			t = self.layers[layer].getTile(x, y)
			if t is not None:
				return t.getImageInfo()
			else:
				return None

	def addTile(self, t, x, y, z):
		"""
		Adds a tile to the map
		@type t: Tile
		@param t: The tile
		@type x: int
		@param x: x-coordinate
		@type y: int
		@param y: y-coordinate
		@type z: int
		@param z: layer index
		@rtype: (int, int, int)
		@return: The x-coordinate, y-coordinate, and index of the image of the
		    tile that used to be at the coordinates (x, y), or None if there
			was no tile there before
		"""
		if x > self.width or y > self.height:
			# Don't issue a warning here because the size of the tilegrid
			# window is often greater than that of the map
			return
		while z > len(self.layers) - 1:
			self.layers.append(Layer(self.width, self.height))
		return self.layers[z].addTile(t, x, y)

	def removeTile(self, x, y, z):
		"""
		Removes a tile from the map
		@type x: int
		@param x: x-coordinate
		@type y: int
		@param y: y-coordinate
		@type z: int
		@param z: layer index
		@rtype: (int, int, int)
		@return: The x-coordinate, y-coordinate, and index of the image of the
		    tile that used to be at the coordinates (x, y, z), or None if there
			was no tile there before
		"""
		if z > len(self.layers):
			return None
		else:
			if x >= self.width or y >= self.height:
				log.error("removeTile: x and y must be less than the width and"
					+ "height")
				return
			else:
				return self.layers[z].removeTile(x, y)

	def addLayer(self, name, visible, z = -1):
		"""
		Brief Description
		@type name: string
		@param name: Placeholder
		@type visible: bool
		@param visible: whether or not the layer is visible
		@type z: int
		@param z: index of the new layer
		"""
		if z != -1:
			while z > len(self.layers) - 1:
				self.layers.append(Layer(self.width, self.height))
			self.layers[z].name = name
			self.layers[z].visible = visible
		else:
			self.layers.append(Layer(self.width, self.height))
			self.layers[-1].name = name
			self.layers[-1].visible = visible
		z = -1

	def addLayerLiteral(self, layer, index):
		self.layers = self.layers[:index] + [layer] + self.layers[index:]

	def removeLayer(self, index):
		"""
		Brief Description
		@type index: int
		@param index: Placeholder
		@rtype: Layer
		@return: the removed layer, or None
		"""
		if index > len(self.layers) - 1:
			loge("Tried to remove a non-existant layer")
			return None
		else:
			l = self.layers[index]
			self.layers.remove(self.layers[index])
			return l

	def swapLayers(self, index1, index2):
		"""
		Brief Description
		@type index1: int
		@param index1: Placeholder
		@type index2: int
		@param index2: Placeholder
		"""
		if index1 > len(self.layers) -1 or index2 > len(self.layers) - 1:
			loge("TileMap.swapLayers: Swap indicies out of range.")
		else:
			temp = self.layers[index1]
			self.layers[index1] = self.layers[index2]
			self.layers[index2] = temp

	def addImage(self, fileName, index):
		"""
		@type fileName: string
		@param fileName: file name of the image to add
		@type index: int
		@param index: index of the image
		"""
		while index > len(self.images) - 1:
			self.images.append(None)
		self.images[index] = fileName

	@staticmethod
	def createMap(tileSize, width, height):
		"""
		@type tileSize: placeholder
		@param tileSize: placeholder
		@type width: placeholder
		@param width: placeholder
		@type height: placeholder
		@param height: placeholder
		"""
		m = TileMap()
		m.width = width
		m.height = height
		m.tileSize = tileSize
		m.addLayer("New Layer", True)
		return m


class Layer:
	def __init__(self, width, height):
		self.tiles = [[None for i in range(height)] for j in range(width)]
		self.name = "New Layer"
		self.visible = True

	def addTile(self, tile, x, y):
		"""
		Brief Description
		@type tile: Tile
		@param tile: Placeholder
		@type x: int
		@param x: Placeholder
		@type y: int
		@param y: Placeholder
		@rtype: (int, int, int)
		@return: The x-coordinate, y-coordinate, and index of the image of the
			tile that used to be at the coordinates (x, y), or None if there
			was no tile there before
		"""
		if(x < len(self.tiles) and y < len(self.tiles[x]) and
			self.tiles[x][y] is not None):
			r = self.tiles[x][y].getImageInfo()
			self.tiles[x][y] = tile
			return r
		else:
			self.tiles[x][y] = tile
			return None

	def getTile(self, x, y):
		if x < len(self.tiles) and y < len(self.tiles[x]):
			return self.tiles[x][y]
		else:
			return None

	def removeTile(self, x, y):
		"""
		Brief Description
		@type x: int
		@param x: Placeholder
		@type y: int
		@param y: Placeholder
		@rtype: (int, int, int)
		@return: The x-coordinate, y-coordinate, and index of the image of the
			tile that used to be at the coordinates (x, y), or None if there
			was no tile there before
		"""
		if self.tiles[x][y] is not None:
			r = self.tiles[x][y].getImageInfo()
			self.tiles[x][y] = None
			return r
		else:
			return None

	def resize(self, width, height, xOffset, yOffset):
		"""
		@type width: int
		@param width: the new width of the map
		@type height: int
		@param height: the new height of the map
		@type xOffset: int
		@param xOffset: the difference between the old 0 x-coordinate and the
			new one. Can be positive or negative
		"""
		if width <= 0 or height <= 0:
			log.error("Tried to resize the map to have a zero or negative"+
			"dimention")
			return
		newTiles = [[None for i in range(height)] for j in range(width)]
		for x, column in enumerate(self.tiles):
			for y, tile in enumerate(column):
				newX = x + xOffset
				newY = y + yOffset
				if newX < width and newY < height and newX >= 0 and newY >= 0:
					newTiles[newX][newY] = self.tiles[x][y]
		self.tiles = newTiles


class Tile(object):
	def __init__(self, index, ix, iy):
		"""
		Brief Description
		@type index: int
		@param index: Image index
		@type ix: int
		@param ix: Image x-coordinate
		@type iy: int
		@param iy: Image y-coordinate
		"""
		self.__ix = ix
		self.__iy = iy
		self.__index = index

	def getImageInfo(self):
		"""
		@rtype: (int, int, int)
		@return: the image x-coordinate, y-coordinate, and index
		"""
		return self.__ix, self.__iy, self.__index

	def setImageInfo(self, index, ix, iy):
		"""
		@type index: int
		@param index: image index
		@type ix: int
		@param ix: x-coordinate of image
		@type iy: int
		@param iy: y-coordinate of image
		"""
		self._ix = ix
		self._iy = iy
		self._index = index
