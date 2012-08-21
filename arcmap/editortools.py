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
Code for the GUI tools that allow the user to edit the map. This is used by the
mapgrid module.
"""


import gtk
import cairo

import graphics
import mapcontroller
import shapes
import dialogs
import undo

# Constants for use in the UI code.
TILE_DRAW_ID = 0
TILE_DELETE_ID = 1
PHYSICS_SELECT_ID = 2
CIRCLE_DRAW_ID = 3
POLYGON_DRAW_ID = 4
LIGHT_DRAW_ID = 5
# Add new codes here for new tools


def coordsToTileEdges(ix, iy, ts):
	"""
	Return the ix and iy snapped to the nearest division between tiles
	This is used for physics drawing
	@type ix: int
	@param ix: x-coordinate of mouse
	@type iy: int
	@param iy: y-coordinate of mouse
	@type ts: int
	@param ts: the size (in pixels) of a tile
	"""
	x = round(ix / ts) * ts
	y = round(iy / ts) * ts
	return x, y


def coordsToTiles(x, y, ts):
	"""
	Translates mouse coordinates to tile coordinates
	@type x: int
	@param x: x-coordinate of the mouse
	@type y: int
	@param y: y-cooridnate of the mouse
	@type ts: int
	@param ts: size of a tile in pixels
	"""
	return x // ts, y // ts


def rectangleSelect(x1, y1, x2, y2, ts):
	"""
	Returns the coordinates of a rectangle whose edges are snapped to the
	divisions between tiles. The returned value is in pixel units in the form
	(x, y, w, h)
	@type x1: int
	@param x1: left x-coordinate in tiles
	@type y1: int
	@param y1: top y-coordinate in tiles
	@type x2: int
	@param x2: right x-coordinate in tiles
	@type y2: int
	@param y2: bottom y-coordinate in tiles
	@type ts: int
	@param ts: size of tile in pixels
	"""
	rx = min(x1, x2) * ts
	ry = min(y1, y2) * ts
	rw = (abs(x2 - x1) + 1) * ts
	rh = (abs(y2 - y1) + 1) * ts
	return int(rx), int(ry), int(rw), int(rh)


class EditorTool(mapcontroller.MapListener):
	"""
	Base class for tools used in the map editor. Derive from this class to add
	more functionality to the program
	"""
	def __init__(self, controller, maxX, maxY):
		"""
		@type controller: mapcontroller.MapController
		@param controller: the map controller
		@type maxX: int
		@param maxX: the maximum x-coordinate for the mouse (in pixels)
		@type maxY: int
		@param maxY: the maximum y-coordinate for the mouse (in pixels)
		"""
		self.__x = 0
		self.__y = 0
		self.__maxX = maxX - 1
		self.__maxY = maxY - 1
		self.__instructions = None
		self.__id = -1
		self.__hasPointer = False
		mapcontroller.MapListener.__init__(self, controller)

	def setMaxX(self, maxX):
		self.__maxX = maxX

	def setMaxY(self, maxY):
		self.__maxY = maxY

	def getPointer(self):
		"""
		@rtype: bool
		@return: True if the mouse is over the TileGrid
		"""
		return self.__hasPointer

	def setInstructions(self, text):
		"""
		@type text: string
		@param text: the instructions for using this tool
		"""
		self.__instructions = text

	def getInstructions(self):
		"""
		@rtype: string
		@return: the instructions for using this tool.
		"""
		return self.__instructions

	def getID(self):
		"""
		@rtype: int
		@return: the ID of this tool
		"""
		return self.__id

	def draw(self, context):
		"""
		Draws the tool to the given cairo context
		@type context: cairo.Context
		@param context: the drawing context
		"""
		pass

	def x(self):
		"""
		@rtype: int
		@return: the x-coordinate of the mouse
		"""
		return self.__x

	def y(self):
		"""
		@rtype: int
		@return: the y-coordinate of the mouse
		"""
		return self.__y

	def mouseMotion(self, x, y):
		"""
		@rtype: bool
		@return: True if this event causes a redraw to be necessary.
		"""
		# This line about setting the __hasPointer to True should not be
		# necessary. I don't know why gtk gives a leave notification when the
		# mouse button is pressed or released. It makes no sense.
		self.__hasPointer = True
		self.__x = int(min(max(0, x), self.__maxX))
		self.__y = int(min(max(0, y), self.__maxY))
		return False

	def mouseButtonPress(self, button, time):
		"""
		@type button: int
		@param button: button that was pressed
		@type time: int
		@param time: the time that the button press happened. Necessary for
		    popping up menus
		@rtype: bool
		@return: True if this event causes a redraw to be necessary.
		"""
		self.__hasPointer = True
		return False

	def mouseButtonRelease(self, button, time):
		"""
		@type button: int
		@param button: button that was pressed
		@param time: the time that the button press happened. Necessary for
		    popping up menus
		@rtype: bool
		@return: True if this event causes a redraw to be necessary.
		"""
		self.__hasPointer = True
		return False

	def mouseEnter(self):
		"""
		Called when the mouse enters the area over the TileGrid
		@rtype: bool
		@return: True if the TileGrid should be redrawn
		"""
		self.__hasPointer = True
		return True

	def mouseLeave(self):
		"""
		Called when the mouse leaves the area over the TileGrid
		@rtype: bool
		@return: True if the TileGrid should be redrawn
		"""
		self.__hasPointer = False
		return True

	def keyPress(self, key):
		"""
		TODO: figure out and document the type of key
		@rtype: bool
		@return: True if this event causes a redraw to be necessary.
		"""
		return False

	def draw(self, context):
		pass

	def undo(self):
		pass

	def listenResize(self, width, height, xoffset, yoffset):
		self.__maxX = width * self.getController().mapTileSize() - 1
		self.__maxY = height * self.getController().mapTileSize() - 1


class TileTool(EditorTool):
	def __init__(self, controller, maxX, maxY):
		EditorTool.__init__(self, controller, maxX, maxY)
		self.setInstructions("Error: This is an abstract class")
		self.selectX1 = -1
		self.selectY1 = -1
		self.selectX2 = -1
		self.selectY2 = -1
		self.lastX = -1
		self.lastY = -1
		self.buttonDown = False

	def mouseButtonPress(self, button, time):
		if button != 1:
			return False
		self.selectX1, self.selectY1 = coordsToTiles(self.x(), self.y(),
			self.getController().mapTileSize())
		self.selectY2 = self.selectY1
		self.selectX2 = self.selectX1
		self.lastX = self.selectX1
		self.lastY = self.selectY1
		self.buttonDown = True
		return True

	def mouseButtonRelease(self, button, time):
		if button != 1:
			return False
		x1 = int(min(self.selectX1, self.selectX2))
		y1 = int(min(self.selectY1, self.selectY2))
		x2 = int(max(self.selectX1, self.selectX2))
		y2 = int(max(self.selectY1, self.selectY2))
		self.selectX1 = x1
		self.selectY1 = y1
		self.selectX2 = x2
		self.selectY2 = y2
		self.buttonDown = False
		return True

	def mouseMotion(self, x, y):
		""" See TileGrid.mouseMotion """

		def updateLast(a, b):
			if a == self.lastX and b == self.lastY:
				return False
			else:
				self.lastX = a
				self.lastY = b
				return True

		EditorTool.mouseMotion(self, x, y)
		if self.buttonDown:
			self.selectX2, self.selectY2 = coordsToTiles(self.x(), self.y(),
				self.getController().mapTileSize())
			return updateLast(self.selectX2, self.selectY2)
		else:
			tmpx, tmpy = coordsToTiles(self.x(), self.y(),
				self.getController().mapTileSize())
			return updateLast(tmpx, tmpy)

class TileDeleteTool(TileTool):
	def __init__(self, controller, maxX, maxY):
		TileTool.__init__(self, controller, maxX, maxY)
		self.setInstructions("Click and drag to select tiles to delete")

	def mouseMotion(self, x, y):
		TileTool.mouseMotion(self, x, y)
		return self.buttonDown

	def mouseButtonRelease(self, button, time):
		TileTool.mouseButtonRelease(self, button, time)
		controller = self.getController()
		z = controller.selectedLayer()

		action = undo.TileRemoveAction(controller)

		for x in range(self.selectX1, self.selectX2 + 1):
			for y in range(self.selectY1, self.selectY2 + 1):
				r = self.getController().removeTile(x, y, z)
				action.appendTileRemove((x, y, z), r)

		controller.addUndoAction(action)


	def draw(self, context):
		if self.buttonDown == False:
			return

		ts = self.getController().mapTileSize()
		x, y, w, h = rectangleSelect(self.selectX1, self.selectY1,
			self.selectX2, self.selectY2, ts)
		pattern = graphics.getDeletePattern(ts)
		context.rectangle(x, y, w, h)
		context.set_source(pattern)
		pattern.set_extend(cairo.EXTEND_REPEAT)
		matrix = cairo.Matrix()
		matrix.translate(-x, -y)
		pattern.set_matrix(matrix)
		context.set_source(pattern)
		context.rectangle(x, y, w, h)
		context.fill()


class TileSelectTool(TileTool):
	def __init__(self, controller, index, maxX, maxY):
		TileTool.__init__(self, controller, maxX, maxY)
		self.setInstructions("Left-click to select tiles. Click and drag to"
			+ " select multiple tiles.")
		self.__index = index


	def mouseMotion(self, x, y):
		TileTool.mouseMotion(self, x, y)
		return self.buttonDown

	def mouseButtonRelease(self, button, time):
		TileTool.mouseButtonRelease(self, button, time)
		if button != 1:
			return False
		else:
			self.getController().setSelection(self.__index, self.selectX1,
				self.selectY1, self.selectX2, self.selectY2)
			return False

	def draw(self, context):
		"""
		Draws a rectangle around the selected tiles
		"""
		x, y, w, h = rectangleSelect(self.selectX1, self.selectY1,
			self.selectX2, self.selectY2,
			self.getController().mapTileSize())

		# semi-transparent square
		fc = graphics.getHighlightColor()
		hc = graphics.getBackgroundColor()
		context.set_source_rgba(fc.r, fc.g, fc.b, 0.5)
		context.rectangle(x, y, w, h)
		context.fill()
		context.rectangle(x + 0.5, y + 0.5, w, h)
		context.set_source_rgba(fc.r, fc.g, fc.b, 1.0)
		context.set_line_width(3.0)
		context.stroke()
		context.rectangle(x + 0.5, y + 0.5, w, h)
		context.set_source_rgba(hc.r, hc.g, hc.b, 1.0)
		context.set_line_width(1.0)
		context.stroke()


class TileDrawTool(TileTool):
	def __init__(self, controller, maxX, maxY):
		TileTool.__init__(self, controller, maxX, maxY)
		self.setInstructions("Left-click to draw tiles on the map."
		+ " Right-click to delete them.")

		# Index of the source image
		self.__selectionIndex = None
		# surface for drawing
		self.__brush = None

	def mouseMotion(self, x, y):
		if self.__selectionIndex is None:
			return False
		""" See TileGrid.mouseMotion """
		return TileTool.mouseMotion(self, x, y)

	def mouseButtonPress(self, button, time):
		""" See TileGrid.buttonPress """
		if self.__selectionIndex is None or button != 1:
			return False
		TileTool.mouseButtonPress(self, button, time)
		return True

	def mouseButtonRelease(self, button, time):
		""" See TileGrid.buttonRelease """
		if self.__selectionIndex is None or button != 1:
			return False
		TileTool.mouseButtonRelease(self, button, time)
		self.__setTiles(self.selectX1, self.selectX2, self.selectY1,
			self.selectY2)
		return True

	def __setTiles(self, startX, endX, startY, endY):
		"""
		Sets tiles on the map in the range defined by startX, endX, startY
		and endY
		"""
		if self.__selectionIndex is None:
			return

		# Ensure that start < end
		sX = int(min(startX, endX))
		eX = int(max(startX, endX))
		sY = int(min(startY, endY))
		eY = int(max(startY, endY))

		controller = self.getController()
		z = controller.selectedLayer()
		action = undo.TileAddAction(controller)

		if startX == endX and startY == endY:
			# Do not repeat the pattern. Overflow of the range is allowed if
			# the starts and ends are the same
			tempY = sY
			tempX = sX
			for i in range(self.selectionX1, self.selectionX2 + 1):
				for j in range(self.selectionY1, self.selectionY2 + 1):
					r = controller.addTile(tempX, tempY, z, i, j,
						self.__selectionIndex)
					action.appendTileAdd((tempX, tempY, z),
						(i, j, self.__selectionIndex), r)
					tempY += 1
				tempY = sY
				tempX += 1
		else:
			# Repeat the pattern but do not allow it to overflow the specified
			# area
			sdx = abs(self.selectionX2 - self.selectionX1)
			sdy = abs(self.selectionY2 - self.selectionY1)
			ddx = eX - sX
			ddy = eY - sY
			for i in range(ddx + 1):
				for j in range(ddy + 1):
					ix = (i % (sdx + 1)) + self.selectionX1
					iy = (j % (sdy + 1)) + self.selectionY1
					x = i + sX
					y = j + sY
					r = controller.addTile(x, y, z, ix, iy,
						self.__selectionIndex)
					action.appendTileAdd((x, y, z), (ix, iy,
						self.__selectionIndex),	r)

		controller.addUndoAction(action)

	def draw(self, context):
		if self.__brush is None or self.getPointer() == False:
			return
		ts = self.getController().mapTileSize()
		if self.buttonDown:
			x, y, w, h = rectangleSelect(self.selectX1, self.selectY1,
				self.selectX2, self.selectY2, ts)
			pattern = cairo.SurfacePattern(self.__brush)
			pattern.set_extend(cairo.EXTEND_REPEAT)
			matrix = cairo.Matrix()
			matrix.translate(-x, -y)
			pattern.set_matrix(matrix)
			context.set_source(pattern)
			context.rectangle(x, y, w, h)
			context.fill()
		else:
			x = self.lastX * ts
			y = self.lastY * ts
			context.set_source_surface(self.__brush, x, y)
			w = (abs(self.selectionX2 - self.selectionX1) + 1) * ts
			h = (abs(self.selectionY2 - self.selectionY1) + 1) * ts
			context.rectangle(x, y, w, h)
			context.fill()

	def listenSetSelection(self, index, brush, x1, y1, x2, y2):
		self.__selectionIndex = index
		self.__brush = brush
		self.selectionX1 = int(x1)
		self.selectionY1 = int(y1)
		self.selectionX2 = int(x2)
		self.selectionY2 = int(y2)

	def listenFileClosed(self):
		self.__selectionIndex = None
		self.__brush = None
		self.selectionX1 = self.selectionY1 = 0
		self.selectionX2 = self.selectionY2 = 0


class ShapeTool(EditorTool):
	"""
	Base class for tools that draw physics shapes
	"""
	def __init__(self, controller, maxX, maxY):
		EditorTool.__init__(self, controller, maxX, maxY)
		self.__snapInterval = 1

	def draw(self, context):
		self.getController().drawShapes(context)

	def setSnapInterval(self, snapInterval):
		"""
		@type snapInterval: int
		@param snapInterval: Coordinates will be snapped to multiples of this
			number
		"""
		self.__snapInterval = snapInterval

	def mouseMotion(self, x, y):
		x, y = coordsToTileEdges(x, y, self.__snapInterval)
		EditorTool.mouseMotion(self, x, y)


class PhysicsSelectTool(ShapeTool):
	def __init__(self, controller, maxX, maxY):
		ShapeTool.__init__(self, controller, maxX, maxY)
		self.__selectedShape = None
		self.__dragLastX = -1
		self.__dragLastY = -1
		# Coordinate for the start of a drag operation. This is either the start
		# point for dragging an entire shape, or for dragging a single handle.
		self.__dragStartX = -1
		self.__dragStartY = -1
		self.__dragging = False
		self.__handleIndex = None
		self.setInstructions("Click and drag to move shapes")

	def mouseButtonPress(self, button, time):
		s = self.selectShape(self.x(), self.y())

		def startDrag(shape):
			self.__selectedShape = shape
			self.__dragging = True
			self.__dragLastX, self.__dragLastY = coordsToTileEdges(
				self.x(), self.y(),
				self.getController().mapTileSize() // 2)
			self.__dragStartX = self.__dragLastX
			self.__dragStartY = self.__dragLastY

		def selectHandle():
			for i, p in enumerate(self.__selectedShape.getHandles()):
				if shapes.pointInHandle(shapes.Point(self.x(), self.y()), p):
					self.__handleIndex = i
					self.__dragStartX, self.__dragStartY = coordsToTileEdges(
					self.x(), self.y(), self.getController().mapTileSize())
					break

		if button == 1:
			if self.__selectedShape is not None:
				selectHandle()
				if self.__handleIndex is None:
					startDrag(s)
			else:
				startDrag(s)
		elif button == 3:
			self.__selectedShape = s
			if s is not None:
				self.popupShapeMenu(self.__selectedShape, button, time)
		return True

	def mouseButtonRelease(self, button, time):
		if button == 1:
			if (self.__dragging == True and
				(self.__dragLastX != self.__dragStartX
				or self.__dragLastY != self.__dragStartY)):
				action = undo.ShapeMoveAction(
					self.getController(),
					self.__selectedShape,
					self.__dragLastX - self.__dragStartX,
					self.__dragLastY - self.__dragStartY,
					)
				self.getController().addUndoAction(action)
			if (self.__handleIndex is not None and (
				self.__dragLastX != self.__dragStartX
				or self.__dragLastY != self.__dragStartY)):
				action = undo.ShapeAdjustAction(
					self.getController(),
					self.__selectedShape,
					self.__handleIndex,
					self.__dragStartX,
					self.__dragStartY,
					self.__dragLastX,
					self.__dragLastY,
					)
				self.getController().addUndoAction(action)
			self.__dragging = False
			self.__handleIndex = None


	def mouseMotion(self, x, y):
		ShapeTool.mouseMotion(self, x, y)
		if self.__selectedShape is not None:
			tmpX, tmpY = coordsToTileEdges(self.x(), self.y(),
					self.getController().mapTileSize() // 2)
			if self.__handleIndex is not None:
				if hasattr(self.__selectedShape, "getRadius"):
					self.__selectedShape.setSnapFactor(
						int(self.getController().mapTileSize() // 2))
				self.__selectedShape.adjust(tmpX, tmpY,
					self.__handleIndex)
				self.__dragLastX = tmpX
				self.__dragLastY = tmpY
				return True
			elif self.__dragging:
				dx = self.__dragLastX - tmpX
				dy = self.__dragLastY - tmpY
				if dx != 0 or dy != 0:
					ts = self.getController().mapTileSize()
					self.__selectedShape.shift(-dx, -dy)
					self.__dragLastX = tmpX
					self.__dragLastY = tmpY
					self.getController().notifyModification(True)
					return True
		return False

	def draw(self, context):
		ShapeTool.draw(self, context)
		if self.__selectedShape is not None:
			if self.__selectedShape.friction is None:
				# The friction being None (a completely bogus value) means that
				# the shape was deleted. Because the shape was deleted in a
				# callback function, this code to set __selectedShape to None
				# can't be in the button event handler
				self.__selectedShape = None
				return
			for p in self.__selectedShape.getHandles():
				graphics.drawPointHandle(context, p)
			graphics.drawMoveHandle(context, self.__selectedShape.getCenter())

	def popupShapeMenu(self, shape, button, time):
		"""
		@type shape: shapes.Shape
		@param shape: the shape that this is a context menu for
		@type button: int
		@param button: the button pressed
		@type time: int?
		@param time: the time that this event was triggered
		"""
		menu = gtk.Menu()
		deleteItem = gtk.ImageMenuItem(gtk.STOCK_DELETE)
		deleteItem.connect("activate", self.deleteCB, shape)
		propertiesItem = gtk.ImageMenuItem(gtk.STOCK_PROPERTIES)
		propertiesItem.connect("activate", self.propertiesCB, shape)
		menu.attach(deleteItem, 0, 1, 0, 1)
		menu.attach(propertiesItem, 0, 1, 1, 2)
		menu.show_all()
		menu.popup(None, None, None, button, time)

	def deleteCB(self, menuitem, shape):
		"""
		callback for the delete item in popupShapeMenu
		@type menuitem: gtk.MenuItem
		@param menuitem: ignored
		@type shape: shapes.Shape
		@param shape: the shape to delete
		"""
		self.__selectedShape = None
		action = undo.ShapeDeleteAction(self.getController(), shape)
		self.getController().addUndoAction(action)
		self.getController().removeShape(shape)

	def propertiesCB(self, menuitem, shape):
		"""
		callback for the properties item in popupShapeMenu
		@type menuitem: gtk.MenuItem
		@param menuitem: ignored
		@type shape: shapes.Shape
		@param shape: the shape whose properties should be changed
		"""
		d = dialogs.StaticShapePropertiesDialog(
			self.getController().getToplevel(), shape)
		result = d.run()
		if result == gtk.RESPONSE_ACCEPT:
			shape.friction = d.getFriction()
			shape.damage = d.getDamage()
			shape.restitution = d.getRestitution()
			self.getController().notifyModification(True)
		d.destroy()

	def selectShape(self, x, y):
		"""
		@type x: int
		@param x: x-coordinate to test
		@type y: int
		@param y: y-coordinate to test
		@rtype: shapes.Shape
		@return: the shape selected, or None
		"""
		shapeList = self.getController().getShapes()
		for shape in shapeList:
			if shape.intersects(shapes.Point(x, y)):
				return shape
		return None

	def listenRemoveShape(self, shape):
		if self.__selectedShape == shape:
			self.__selectedShape = None



class CircleDrawTool(ShapeTool):
	def __init__(self, controller, maxX, maxY):
		ShapeTool.__init__(self, controller, maxX, maxY)
		self.__drawing = False
		self.__circle = shapes.Circle(
			int(self.getController().mapTileSize() / 2),
			int(self.getController().mapTileSize() / 2))
		self.setSnapInterval(int(self.getController().mapTileSize() / 2))
		# A good default value, since the radius can't be negative
		self.__oldRadius = -1
		self.setInstructions("Click to set the center point. Click"
			+ " again to set the radius")

	def mouseButtonPress(self, button, time):
		if self.__drawing:
			controller = self.getController()
			action = undo.ShapeAddAction(controller, self.__circle)
			controller.addUndoAction(action)
			controller.addShape(self.__circle)
			self.__circle = shapes.Circle(
				int(controller.mapTileSize() / 2),
				int(controller.mapTileSize() / 2))
			self.__drawing = False
		else:
			if button == 1:
				self.__circle.setCenter(shapes.Point(self.x(), self.y()))
				self.__drawing = True

	def mouseButtonRelease(self, button, time):
		return False

	def mouseMotion(self, x, y):
		ShapeTool.mouseMotion(self, x, y)
		if self.__drawing == True:
			self.__circle.adjust(self.x(), self.y())
			if self.__circle.getRadius() == self.__oldRadius:
				return False
			else:
				self.__oldRadius = self.__circle.getRadius()
				return True

	def draw(self, context):
		if self.__drawing:
			graphics.drawShape(self.__circle, context, True)
		ShapeTool.draw(self, context)

class PolygonDrawTool(ShapeTool):
	def __init__(self, controller, maxX, maxY):
		ShapeTool.__init__(self, controller, maxX, maxY)
		# True if a shape is in the middle of being drawn
		self.__drawing = False
		self.__polygon = shapes.Polygon()
		# These keep the number of redraws down
		self.__lastX = 0
		self.__lastY = 0
		self.setInstructions("Left click to add points, right click to finish.")
		self.setSnapInterval(int(self.getController().mapTileSize() // 2))

	def mouseButtonPress(self, button, time):
		controller = self.getController()
		if button == 1:
			p = coordsToTileEdges(self.x(), self.y(),
				controller.mapTileSize())
			if self.__drawing == True:
				last = self.__polygon.getLastPoint()
				if last is not None and self.x() == last.x and self.y() == last.y \
					and self.__polygon.convex():
					self.__polygon.delExtraPoint()
					self.__polygon.forceCClockwise()
					action = undo.ShapeAddAction(controller, self.__polygon)
					controller.addUndoAction(action)
					controller.addShape(self.__polygon)
					self.__polygon = shapes.Polygon()
					self.__drawing = False
				else:
					self.__polygon.addPoint(shapes.Point(self.x(), self.y()))
			else:
				self.__polygon.addPoint(shapes.Point(self.x(), self.y()))
				self.__drawing = True
		elif button == 3:
			if self.__drawing:
				if self.__polygon.convex():
					self.__drawing = False
					self.__polygon.forceCClockwise()
					action = undo.ShapeAddAction(controller, self.__polygon)
					controller.addUndoAction(action)
					controller.addShape(self.__polygon)
					self.__polygon = shapes.Polygon()
		return True

	def mouseButtonRelease(self, button, time):
		return False

	def mouseMotion(self, x, y):
		ShapeTool.mouseMotion(self, x, y)
		self.__polygon.adjust(self.x(), self.y())
		# Only force a redraw if the snapped mouse coordinates have actually
		# changed.
		if self.x() == self.__lastX and self.y() == self.__lastY:
			self.__lastX = self.x()
			self.__lastY = self.y()
			return False
		else:
			self.__lastX = self.x()
			self.__lastY = self.y()
			return self.__drawing


	def draw(self, context):
		if self.__drawing == True:
			graphics.drawShape(self.__polygon, context, True)
		ShapeTool.draw(self, context)
