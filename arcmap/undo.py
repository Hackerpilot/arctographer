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
Module for undoing and redoing actions in the map editor
"""

import copy

# DO NOT ACCESS THESE DIRECTLY
__undoList = []
__redoList = []


def addUndoAction(action):
	"""
	Don't use this directly. Call the addUndoAction function of MapController.
	Doing so will update the status of the undo and redo buttons on the window.
	@type action: UndoAction
	@param action: the action to add to the undo stack
	"""
	global __redoList
	__redoList = []
	__undoList.append(action)


def undo():
	"""
	@rtype: bool
	@return: True if anything was undone, False otherwise
	"""
	if len(__undoList) > 0:
		__undoList[-1].undo()
		__redoList.append(__undoList.pop())
		return True
	else:
		return False


def redo():
	"""
	@rtype: bool
	@return: True if anything was redone, False otherwise
	"""
	if len(__redoList) > 0:
		__redoList[-1].redo()
		__undoList.append(__redoList.pop())
		return True
	else:
		return False


def canUndo():
	"""
	@rtype: bool
	@return: True if there are any actions that can be undone
	"""
	return len(__undoList) > 0


def canRedo():
	"""
	@rtype: bool
	@return: True if there are any actions that can be redone
	"""
	return len(__redoList) > 0


def getRedoDescription():
	"""
	@rtype: str
	@return: a textual description of the next action that can be redone, or
	    None. It's a good idea to call canRedo before this.
	"""
	if canRedo():
		return __redoList[-1].getRedoString()
	else:
		return None


def getUndoDescription():
	"""
	@rtype: str
	@return: a textual description of the next action taht can be redone, or
	    None. It's a good idea to call canUndo before this.
	"""
	if canUndo():
		return __undoList[-1].getUndoString()
	else:
		return None


class UndoAction(object):
	"""
	Base class for undo actions
	"""
	def __init__(self, controller):
		self.__controller = controller
		self.__description = "REPLACE THIS TEXT"

	def getController(self):
		return self.__controller

	def setDescription(self, desc):
		"""
		Only derived classes should call this
		@type desc: str
		@param desc: A description of the action to be taken
		"""
		self.__description = desc

	def undo(self):
		"""
		Undo the action
		"""
		raise NameError("UndoAction.undo is abstract.")

	def redo(self):
		"""
		Redo the action
		"""
		raise NameError("UndoAction.redo is abstract.")

	def getUndoString(self):
		"""
		@rtype: str
		@return: A string describing the action to be done
		"""
		return "Undo " + self.__description

	def getRedoString(self):
		"""
		@rtype: str
		@return: A string describing the action to be done
		"""
		return "Redo " + self.__description


class ShapeMoveAction(UndoAction):
	"""
	UndoAction for moving physics shapes around the map
	"""
	def __init__(self, controller, shape, dx, dy):
		UndoAction.__init__(self, controller)
		self.__shape = shape
		self.__dx = dx
		self.__dy = dy
		self.setDescription("move shape")

	def undo(self):
		self.__shape.shift(-self.__dx, -self.__dy)

	def redo(self):
		self.__shape.shift(self.__dx, self.__dy)


class ShapeDeleteAction(UndoAction):
	"""
	UndoAction for deleting a shape from the map
	"""
	def __init__(self, controller, shape):
		UndoAction.__init__(self, controller)
		self.__shape = shape
		self.setDescription("delete shape")

	def undo(self):
		self.getController().addShape(self.__shape)

	def redo(self):
		self.getController().removeShape(self.__shape)


class ShapeAddAction(UndoAction):
	"""
	UndoAction for adding a shape to the map
	"""
	def __init__(self, controller, shape):
		UndoAction.__init__(self, controller)
		self.__shape = shape
		self.setDescription("add shape")

	def undo(self):
		self.getController().removeShape(self.__shape)

	def redo(self):
		self.getController().addShape(self.__shape)


class ShapeAdjustAction(UndoAction):
	"""
	UndoAction for adjusting the geometry of a shape
	"""
	def __init__(self, controller, shape, index, oldX, oldY, newX, newY):
		"""
		@type controller: mapcontroller.MapController
		@param controller: the map controller
		@type index: int
		@param index: the index of the shape's handle being adjusted
		@type oldX: int
		@param oldX: old x-coordinate of the handle
		@type oldY: int
		@param oldY: old y-coordinate of the handle
		@type newX: int
		@param newX: new x-coordinate of the handle
		@type newY: int
		@param newY: new y-coordinate of the handle
		"""
		UndoAction.__init__(self, controller)
		self.__oldX = oldX
		self.__oldY = oldY
		self.__newX = newX
		self.__newY = newY
		self.__shape = shape
		self.__index = index
		self.setDescription("adjust shape")

	def undo(self):
		self.__shape.adjust(self.__oldX, self.__oldY, self.__index)

	def redo(self):
		self.__shape.adjust(self.__newX, self.__newY, self.__index)


class TileAddAction(UndoAction):
	"""
	Action for adding tiles to the map. Because tiles are often added in chunks,
	the appendTileAdd method must be used. This way the entire chunk can be
	undone at once
	"""
	def __init__(self, controller):
		UndoAction.__init__(self, controller)
		self.setDescription("add tiles")
		self.__addedTiles = {}
		self.__oldTiles = {}

	def appendTileAdd(self, coords, newImageCoords, oldImageCoords):
		"""
		Adds a tile add operation to this undo action
		@type coords: (int, int, int)
		@param coords: x-coordinate, y-coordinate, and layer
		@type newImageCoords: (int, int, int)
		@param newImageCoords: x-coordinate of new tile's image,
			x-coordinate of new tile's image, and image index of new tile's
			image.
		@type oldImageCoords: (int, int, int)
		@param oldImageCoords: x-coordinate of old tile's image,
			x-coordinate of old tile's image, and image index of old tile's
			image.
		"""
		self.__addedTiles[coords] = newImageCoords
		self.__oldTiles[coords] = oldImageCoords

	def undo(self):
		for coord, imageCoord in self.__oldTiles.iteritems():
			x = coord[0]
			y = coord[1]
			z = coord[2]
			controller = self.getController()
			if self.__oldTiles[coord] is None:
				controller.removeTile(x, y, z)
			else:
				ix = imageCoord[0]
				iy = imageCoord[1]
				ii = imageCoord[2]
				controller.addTile(x, y, z, ix, iy, ii)

	def redo(self):
		for coord, imageCoord in self.__addedTiles.iteritems():
			x = coord[0]
			y = coord[1]
			z = coord[2]
			controller = self.getController()
			ix = imageCoord[0]
			iy = imageCoord[1]
			ii = imageCoord[2]
			controller.addTile(x, y, z, ix, iy, ii)


class TileRemoveAction(UndoAction):
	"""
	Action for removing tiles from the map
	"""
	def __init__(self, controller):
		UndoAction.__init__(self, controller)
		self.setDescription("remove tiles")
		self.__oldTiles = {}

	def appendTileRemove(self, coords, oldImageCoords):
		"""
		Adds a tile remove operation to this undo action
		@type coords: (int, int, int)
		@param coords: x-coordinate, y-coordinate, and layer
		@type oldImageCoords: (int, int, int)
		@param oldImageCoords: x-coordinate of old tile's image,
		    x-coordinate of old tile's image, and image index of old tile's
			image
		"""
		if coords in self.__oldTiles:
			return
		self.__oldTiles[coords] = oldImageCoords

	def undo(self):
		for coord, imageCoord in self.__oldTiles.iteritems():
			x = coord[0]
			y = coord[1]
			z = coord[2]
			controller = self.getController()
			if self.__oldTiles[coord] is not None:
				ix = imageCoord[0]
				iy = imageCoord[1]
				ii = imageCoord[2]
				controller.addTile(x, y, z, ix, iy, ii)

	def redo(self):
		controller = self.getController()
		for coord in self.__oldTiles:
			x = coord[0]
			y = coord[1]
			z = coord[2]
			controller.removeTile(x, y, z)

class ResizeAction(UndoAction):
	def __init__(self, controller, newWidth, newHeight, xOffset, yOffset,
		oldWidth, oldHeight):

		UndoAction.__init__(self, controller)
		self.setDescription("resize map")
		self.__newWidth = newWidth
		self.__newHeight = newHeight
		self.__xOffset = xOffset
		self.__yOffset = yOffset
		self.__oldWidth = oldWidth
		self.__oldHeight = oldHeight

		self.__tileRemove = TileRemoveAction(controller)

		def addTileRange(x1, x2, y1, y2):
			for x in range(x1, x2):
				for y in range(y1, y2):
					for z in range(controller.mapLayers()):
						r = controller.getTile(x, y, z)
						if r is not None:
							self.__tileRemove.appendTileRemove((x, y, z), r)

		# Left edge
		if xOffset < 0:
			addTileRange(0, -xOffset, 0, oldHeight)

		# Top edge
		if yOffset < 0:
			addTileRange(0, oldWidth, 0, -yOffset)

		# Right edge
		rightStart = oldWidth - (oldWidth - newWidth + xOffset)
		addTileRange(rightStart, oldWidth, 0, oldHeight)

		# Bottom edge
		bottomStart = oldHeight - (oldHeight - newHeight + yOffset)
		addTileRange(0, oldWidth, bottomStart, oldHeight)

	def undo(self):
		self.getController().resize(self.__oldWidth, self.__oldHeight,
			-self.__xOffset, -self.__yOffset)
		self.__tileRemove.undo()

	def redo(self):
		self.__tileRemove.redo()
		self.getController().resize(self.__newWidth, self.__newHeight,
			self.__xOffset, self.__yOffset)

class LayerRemoveAction(UndoAction):
	def __init__(self, controller, index):
		"""
		@type index: int
		@param index: the index of the layer to remove
		"""
		UndoAction.__init__(self, controller)
		self.setDescription("remove layer")
		self.__index = index
		self.__layer = controller.removeLayer(index)

	def undo(self):
		self.getController().addLayerLiteral(self.__layer, self.__index)

	def redo(self):
		self.getController().removeLayer(self.__index)

class LayerAddAction(UndoAction):
	def __init__(self, controller, layerName):
		"""
		@type layerName: string
		@param layerName: the name of the new layer
		"""
		UndoAction.__init__(self, controller)
		self.__index = controller.addLayer(layerName, True)
		self.__layerName = layerName

	def undo(self):
		self.getController().removeLayer(self.__index)

	def redo(self):
		self.getController().addLayer(self.__layerName, True)
