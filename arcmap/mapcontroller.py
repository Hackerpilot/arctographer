################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Sep 22 2009
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
Contains the MapController and MapListener classes.
"""

__docformat__ = "epytext"

import os
import logging
import copy

import gtk
import cairo

import tilemap
import blazeworld
import background
import graphics
import undo
import datafiles
import levelio

log = logging.getLogger("mapcontroller")


class MapListener:
	"""
	Base class for anything that wants to be notified about state changes
	in the map
	"""

	def __init__(self, controller):
		"""
		@type controller: MapController
		@param controller: The controller that this will listen to
		"""
		self.__controller = controller
		self.__controller.addListener(self)

	def getController(self):
		"""
		@rtype: MapController
		@return: the controller that this is a listener for
		"""
		return self.__controller

	def listenSetVisibilty(self, index, visible):
		"""
		@type index: int
		@param index: the index of the layer to set visible/invisible
		@type visible: bool
		@param visible: True if the layer should be visible, False otherwise
		"""
		pass

	def listenResize(self, width, height, xoffset, yoffset):
		"""
		Respond to a map resize
		@type width: int
		@param width: The new width in tiles
		@type height: int
		@param height: The new height in tiles
		@type xoffset: int
		@param xoffset: The number of tiles that the existing map contents
		    should be shifted right
		@type yoffset: int
		@param yoffset: The number of tiles that the existing map contents
		    should be shifted down
		"""
		pass

	def listenAddLayer(self, layerName):
		"""
		@type layerName: string
		@param layerName: name of the new layer
		"""
		pass

	def listenAddTile(self, source, x, y, z):
		"""
		@type source: cairo.ImageSurface
		@param source: source surface for drawing
		@type x: int
		@param x: x-coordinate in tiles
		@type y: int
		@param y: y-coordinate in tiles
		@type z: int
		@param z: layer index of the tile to delete
		"""
		pass

	def listenRemoveTile(self, x, y, z):
		"""
		@type x: int
		@param x: x-coordinate of tile to delete
		@type y: int
		@param y: y-coordinate of tile to delete
		@type z: int
		@param z: layer index of the tile to delete
		"""
		pass

	def listenRemoveLayer(self, index):
		"""
		Notify the listener that a layer has been removed
		@type index: int
		@param index: the index of the removed layer
		"""
		pass

	def listenSwapLayers(self, index1, index2):
		"""
		Notify listener that two layers have changed places
		@type index1: int
		@param index1: index of first layer
		@type index2: int
		@param index2: index of second layer
		"""
		pass

	def listenSelectLayer(self, index):
		"""
		Update the listener to a change in layer selection
		@type index: int
		@param index: index of the layer that was selected
		"""
		pass

	def listenModified(self, modified):
		"""
		Notify the listener if the map has unsaved changes or not
		@type modified: bool
		@param modified: Whether or not the map is changed
		"""
		pass

	def listenFileClosed(self):
		"""
		Called when the map being edited is closed. Used to make buttons
		insensitive, free resources, etc.
		"""
		pass

	def listenFileOpened(self):
		"""
		Called when a map is opened or created. Used to make buttons sensitive,
		or whatever else.
		"""
		pass

	def listenSetSelection(self, index, brush, x1, y1, x2, y2):
		"""
		@type index: int
		@param index: index of the image
		@type brush: cairo.ImageSurface
		@param brush: pixel data to use
		@type x1: int
		@param x1: left coordinate of selection in tiles
		@type y1: int
		@param y1: top coordinate of selection in tiles
		@type x2: int
		@param x2: right coordinate of selection in tiles
		@type y2: int
		@param y2: bottom coordinate of selection in tiles
		"""
		pass

	def listenAddTileSet(self, fileName):
		"""
		@type fileName: string
		@param fileName: name of the file that was
		"""
		pass

	def listenUndoRedo(self):
		"""
		Update due to an undo action or a redo action
		"""
		pass

	def listenAddShape(self, shape):
		"""
		Notify the listener that a shape was added
		@type shape: shapes.Shape
		@param shape: the shape added
		"""
		pass

	def listenRemoveShape(self, shape):
		"""
		Notify the listener that a shape was removed
		@type shape: shapes.Shape
		@param shape: the shape added
		"""


class MapController:
	"""
	MapController is the command and control center for the program. It manages
	communication between the other modules and controls the tilemap.
	"""
	def __init__(self):

		# List of MapListener
		self.__listeners = []
		# List of tile images
		self.__images = []
		# Name that the file will be saved under
		self.__fileName = None
		# Does the map have unsaved changes?
		self.__modified = False
		# Currently selected layer
		self.__selectedLayer = None
		# Tile map
		self.__map = None
		# Physics world
		self.__world = None
		# Background info
		self.__background = None
		# Source of resize thumbnail
		self.__thumbnailSource = None
		# Toplevel widget
		self.__toplevel = None
		# True to save background info
		self.saveBackground = True
		# True to save physics world
		self.saveWorld = True

	def setThumbnailSource(self, source):
		self.__thumbnailSource = source

	def getThumbnail(self, largest):
		if self.__thumbnailSource is not None:
			return self.__thumbnailSource.getThumbnail(largest)
		else:
			return None

	def getParallaxes(self):
		if self.__background is None:
			return None
		else:
			return self.__background.getParallaxes()

	def setParallaxes(self, parallaxes):
		self.__background.setParallaxes(parallaxes)
		self.notifyModification(True)

	def getBGColor(self):
		"""
		@rtype: graphics.RGBA
		@return: Map's background color
		"""
		if self.__background is not None:
			return self.__background.getBGColor()
		else:
			return None

	def setBGColor(self, color):
		"""
		@type color: graphics.RGBA
		@param color: the new color
		"""
		self.__background.setBGColor(color)
		self.notifyModification(True)

	def getShapes(self):
		return self.__world.getShapes()

	def setShapes(self, shapes):
		self.__world.setShapes(shapes)

	def addShape(self, shape):
		"""
		@type shape: shapes.Shape
		@param shape: the shape to add to the map
		"""
		self.__world.addShape(shape)
		for listener in self.__listeners:
			listener.listenAddShape(shape)
		self.notifyModification(True)

	def removeShape(self, shape):
		"""
		@type shape: shapes.Shape
		@param shape: the shape to remove
		"""
		self.__world.delShape(shape)
		for listener in self.__listeners:
			listener.listenRemoveShape(shape)
		self.notifyModification(True)

	def hasMap(self):
		"""
		@rtype: bool
		@return: True if there is a map to edit
		"""
		return (self.__map is not None)

	def open(self, fileName):
		"""
		Opens a file
		@type fileName: str
		@param fileName: the path of the file to open
		@rtype: str
		@return: Returns a string saying why the file could not be opened, or
		    None
		"""
		# Only one map can be used at a time
		self.close()
		self.__fileName = fileName
		if fileName is not None and os.path.exists(fileName):
			try:
				self.__background, self.__world, self.__map = levelio.read(
					fileName)
			except datafiles.FileNotFoundError as e:
				self.__fileName = None
				return str(e)
			except levelio.LoadError as e:
				self.__fileName = None
				return str(e)

			if self.__background is None:
				# Create an empty one
				self.__background = background.Background()

			if self.__world is None:
				# Same here
				self.__world = blazeworld.BlazeWorld()

			for index, fileName in enumerate(self.__map.images):
				for listener in self.__listeners:
					listener.listenAddTileSet(fileName)
			for listener in self.__listeners:
				listener.listenFileOpened()
				listener.listenSelectLayer(self.__selectedLayer)
			return None
		else:
			self.__fileName = None
			return "Could not find the file \"%s\"" % fileName

	def close(self):
		# Ignore this call if there is no map currently loaded
		if self.__map is None:
			return
		self.__map = None
		self.__background = None
		self.__world = None
		self.__images = []
		self.__modified = False
		self.__selectedLayer = None
		self.__fileName = None
		self.__selectedLayer = None
		for listener in self.__listeners:
			listener.listenFileClosed()

	def new(self, tileSize, width, height):
		"""
		Creates a new map of the given width, height, and tile dimentions
		@type tileSize: int
		@param tileSize: size of a tile in pixels
		@type width: int
		@param width: width of map in tiles
		@type height: int
		@param height: height of map in tiles
		"""
		self.close()
		self.__map = tilemap.TileMap.createMap(tileSize, width, height)
		self.__world = blazeworld.BlazeWorld()
		self.__background = background.Background()
		self.__selectedLayer = len(self.__map.layers) - 1
		for listener in self.__listeners:
			listener.listenFileOpened()
			listener.listenSelectLayer(self.__selectedLayer)

	def save(self):
		levelio.write(self.__fileName, self.__map,
			self.__world if self.saveWorld == True else None,
			self.__background if self.saveBackground == True else None)
		self.notifyModification(False)

	def mapTileSize(self):
		assert(self.hasMap())
		return self.__map.tileSize

	def mapWidth(self):
		return self.__map.width

	def mapHeight(self):
		return self.__map.height

	def mapLayers(self):
		return len(self.__map.layers)

	def resize(self, width, height, xOffset, yOffset):
		self.__map.resize(width, height, xOffset, yOffset)
		self.__world.resize(width * self.mapTileSize(),
			height * self.mapTileSize(), xOffset * self.mapTileSize(),
			yOffset * self.mapTileSize())
		for listener in self.__listeners:
			listener.listenResize(width, height, xOffset, yOffset)
		self.notifyModification(True)

	def getTile(self, x, y, z):
		"""
		@type x: int
		@param x: x-coordinate of tile
		@type y: int
		@param y: y-coordinate of tile
		@type z: int
		@param z: layer of tile
		@rtype: (int, int, int)
		@return: the image x-coordinate, y-coordinate, and index
		"""
		return self.__map.getTile(x, y, z)

	def selectLayer(self, index):
		"""
		@type index: int
		@param index: index of layer to select
		"""
		self.__selectedLayer = index
		for listener in self.__listeners:
			listener.listenSelectLayer(index)

	def selectedLayer(self):
		"""
		@rtype: int
		@return: the currently selected layer
		"""
		return self.__selectedLayer

	def mapLayerVisibility(self, index):
		"""
		@rtype: bool
		@return: True if the layer at index is visible
		"""
		return self.__map.layers[index].visible

	def setMapLayerVisibility(self, index, v):
		self.__map.layers[index].visible = v
		for listener in self.__listeners:
			listener.listenSetVisibilty(index, v)
		self.notifyModification(True)

	def setLayerName(self, index, name):
		self.__map.layers[index].name = name
		self.notifyModification(True)

	def getFileName(self):
		"""
		@rtype: string
		@return: the name of the file currently loaded
		"""
		return self.__fileName

	def setFileName(self, fileName):
		self.__fileName = fileName

	def addListener(self, listener):
		"""
		Adds a listener into the listener list
		@type listener: MapListener
		@param listener: Placeholder
		"""
		self.__listeners.append(listener)

	def openTileSet(self, fileName):
		"""
		Opens an image file and adds it to the list of open images
		@type fileName: string
		@param fileName: the name of the file to open
		@rtype: int
		@return: the opened image's index
		"""
		image = graphics.loadImage(fileName)
		if image is not None:
			self.__images.append(image)
			index = len(self.__images) - 1
			self.__map.addImage(fileName, index)
			return index
		else:
			return None

	def drawShapes(self, context):
		"""
		Draws the shapes in the map to the given context
		@type context: cairo.Context
		@param context: context to draw on
		"""
		for shape in self.__world.getShapes():
			graphics.drawShape(shape, context)

	def addLayer(self, layerName, visible):
		"""
		@type layerName: string
		@param layerName: name for the new layer
		@type visible: bool
		@param visible: True if the layer is visible
		"""
		self.__map.addLayer(layerName, True)
		# select the new layer. This also ensures that a layer is selected on
		# map load.
		self.__selectedLayer = len(self.__map.layers) - 1
		for listener in self.__listeners:
			listener.listenAddLayer(layerName)
			listener.listenSelectLayer(len(self.__map.layers))
		self.notifyModification(True)
		return self.__selectedLayer

	def addLayerLiteral(self, layer, index):
		"""
		This wouldn't have such a dumb name if Python supported function
		oveloading.
		@type layer: tilemap.Layer
		@param layer: the layer to add
		@type index: int
		@param index: the index to add the layer at
		"""
		self.__map.addLayerLiteral(layer, index)
		for listener in self.__listeners:
			listener.listenAddLayer(layer.name)
		self.notifyModification(True)

	def removeLayer(self, index):
		"""
		@type index: int
		@param index: the index of the layer to remove
		@rtype: tilemap.Layer
		@return: The removed layer (for undo)
		"""
		l = self.__map.removeLayer(index)
		for listener in self.__listeners:
			listener.listenRemoveLayer(index)
		self.notifyModification(True)
		return l

	def swapLayers(self, firstIndex, secondIndex):
		"""
		@type firstIndex: int
		@param firstIndex: first layer index
		@type secondIndex: int
		@param secondIndex: second layer index
		"""
		self.__map.swapLayers(firstIndex, secondIndex)
		for listener in self.__listeners:
			listener.listenSwapLayers(firstIndex, secondIndex)
		self.notifyModification(True)

	def getNumLayers(self):
		"""
		@rtype: int
		@return: the number of layers in the map
		"""
		return len(self.__map.layers)

	def setSelection(self, index, x1, y1, x2, y2):
		"""
		Sets the tile selection. x1 must be less than x2. y1 must be less than
		y2.
		@type index: int
		@param index: index of tile set
		@type x1: int
		@param x1: left edge, in tiles
		@type y1: int
		@param y1: top edge, in tiles
		@type x2: int
		@param x2: right edge, in tiles
		@type y2: int
		@param y2: bottom edge, in tiles
		"""
		ts = self.__map.tileSize
		brushSurface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
			int((abs(x2 - x1) + 1) * ts), int((abs(y2 - y1) + 1) * ts))
		context = cairo.Context(brushSurface)
		context.set_source_surface(self.__images[index], -(x1 * ts), -(y1 * ts))
		context.set_operator(cairo.OPERATOR_SOURCE)
		context.paint()
		for listener in self.__listeners:
			listener.listenSetSelection(index, brushSurface, x1, y1, x2, y2)

	def addTile(self, x, y, z, ix, iy, ii):
		"""
		Adds a tile to the currently selected layer.
		@type x: int
		@param x: x-coordinate of tile
		@type y: int
		@param y: y-coordinate of tile
		@type z: int
		@param z: layer of the tile
		@type ix: int
		@param ix: x-coordinate of the image for the tile
		@type iy: int
		@param iy: y-coordinate of the image for the tile
		@type ii: int
		@param ii: image index
		@rtype: (int, int, int)
		@return: The x-coordinate, y-coordinate, and index of the image of the
			tile that used to be at the coordinates (x, y, z), or None if there
			was no tile there before
		"""
		t = tilemap.Tile(ii, ix, iy)
		r = self.__map.addTile(t, x, y, z)
		for listener in self.__listeners:
			listener.listenAddTile(t, x, y, z)
		self.notifyModification(True)
		return r

	def removeTile(self, x, y, z):
		"""
		Removes a tile from the selected layer
		@type x: int
		@param x: the x-coordinate of the tile to remove
		@type y: int
		@param y: the y-coordinate of the tile to remove
		@rtype: (int, int, int)
		@return: The x-coordinate, y-coordinate, and index of the image of the
			tile that used to be at the coordinates (x, y, z), or None if there
			was no tile there before
		"""
		if z == -1:
			z = self.__selectedLayer
		r = self.__map.removeTile(x, y, z)
		for listener in self.__listeners:
			listener.listenRemoveTile(x, y, z)
		self.notifyModification(True)
		return r

	def getTile(self, x, y, z):
		return self.__map.getTile(x, y, z)

	def getLayerInfo(self):
		"""
		@rtype: [(string, bool)]
		@return: names of layers and whether or not they are visible
		"""
		info = []
		for l in self.__map.layers:
			info.append((l.name, l.visible))
		return info

	def getTilesetSurface(self, index):
		"""
		@type index: int
		@param index: the index of the cairo.ImageSurface to get
		"""
		try:
			return self.__images[index]
		except IndexError:
			return None

	def unsaved(self):
		"""
		@rtype: bool
		@return: true if the map has unsaved changes, false otherwise
		"""
		if self.__map is None:
			return False
		elif self.__modified == False:
			return False
		else:
			return True

	def notifyModification(self, modified):
		"""
		Notify the controller (and all of its listeners) of a modification to
		the map.
		@type modified: bool
		@param modified: True if the map has been modified, False if it no
			longer has unsaved changes
		"""
		self.__modified = modified
		for listener in self.__listeners:
			listener.listenModified(self.__modified)

	def setToplevel(self, widget):
		self.__toplevel = widget

	def getToplevel(self):
		"""
		This function is here so that dialogs can get a reference to the main
		window to calculate their position.
		"""
		return self.__toplevel

	def undo(self):
		undo.undo()
		self.notifyModification(undo.canUndo())
		for listener in self.__listeners:
			listener.listenUndoRedo()

	def redo(self):
		undo.redo()
		self.notifyModification(True)
		for listener in self.__listeners:
			listener.listenUndoRedo()

	def addUndoAction(self, action):
		undo.addUndoAction(action)
		self.notifyModification(True)
		for listener in self.__listeners:
			listener.listenUndoRedo()
