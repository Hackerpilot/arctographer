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
Module for drawing the map to the screen
"""

__docformat__ = "epytext"

import math
import logging
import cairo
import gtk

import dialogs
import mapcontroller
import tilegrid
import editortools
import graphics


class MapGrid(tilegrid.TileGrid, mapcontroller.MapListener):
	""" Handles drawing the map to the screen """

	# This class contains some tricky code. The drawing area is the same size as
	# it appears on the screen. It is not added to a gtk.ScrolledWindow and
	# simply panned around because this would be memory-prohibitave. MapGrid
	# keeps track of its own scroll bars and scroll offset, and translates any
	# coordinates that are sent off to subclasses of EditorTool so that they are
	# able to draw on-screen at the correct positions.
	#
	# MapGrid modifies the transformaiton matrix during its specialRedraw call.


	def __init__(self, controller, statusBar):
		"""
		@type controller: MapController
		@param controller: the map controller
		@type statusBar: gtk.StatusBar
		@param statusBar: status bar to update
		"""
		mapcontroller.MapListener.__init__(self, controller)
		controller.setThumbnailSource(self)

		pixelWidth = controller.mapWidth() * controller.mapTileSize()
		pixelHeight = controller.mapHeight() * controller.mapTileSize()
		tilegrid.TileGrid.__init__(self, pixelWidth, pixelHeight,
			controller.mapTileSize())

		# Access to the parent window's status bar
		self.__statusBar = statusBar
		self.__contextID = self.__statusBar.get_context_id("Map Grid")
		self.__lastMessage = -1

		self.__scrollOffsetX = 0
		self.__scrollOffsetY = 0

		self.__dragScrollPressed = False
		self.__dragScrollX = None
		self.__dragScrollY = None
		self.eventBox.connect("scroll-event", self.scroll)

		# This flag prevents infinite loops between the specialRedraw function
		# and the scrollUpdate function.
		self.__redrawLocked = False

		self.addTool(editortools.TileDrawTool(controller, pixelWidth,
			pixelHeight), editortools.TILE_DRAW_ID)
		self.addTool(editortools.TileDeleteTool(controller, pixelWidth,
			pixelHeight), editortools.TILE_DELETE_ID)
		self.addTool(editortools.PhysicsSelectTool(controller, pixelWidth,
			pixelHeight), editortools.PHYSICS_SELECT_ID)
		self.addTool(editortools.CircleDrawTool(controller, pixelWidth,
			pixelHeight), editortools.CIRCLE_DRAW_ID)
		self.addTool(editortools.PolygonDrawTool(controller, pixelWidth,
			pixelHeight), editortools.POLYGON_DRAW_ID)

		self.createScrollBars()

		self.table = gtk.Table(2, 2, False)
		self.table.attach(self.eventBox, 0, 1, 0, 1,
			xoptions=gtk.EXPAND|gtk.FILL,
			yoptions=gtk.EXPAND|gtk.FILL)
		self.table.attach(self.vScroll, 1, 2, 0, 1, xoptions=gtk.FILL,
			yoptions=gtk.EXPAND|gtk.FILL)
		self.table.attach(self.hScroll, 0, 1, 1, 2,
			xoptions=gtk.EXPAND|gtk.FILL,
			yoptions=gtk.FILL)
		self.table.show_all()

	def createScrollBars(self):
		controller = self.getController()
		ts = controller.mapTileSize()
		width = controller.mapWidth() * ts
		self.hAdjust = gtk.Adjustment(self.__scrollOffsetX, 0, width, ts,
			ts * 4, 0)
		self.hScroll = gtk.HScrollbar(self.hAdjust)
		self.hScroll.connect("value-changed", self.scrollUpdate, False)

		height = controller.mapHeight() * ts
		self.vAdjust = gtk.Adjustment(self.__scrollOffsetY, 0, height, ts,
			ts * 4, 0)
		self.vScroll = gtk.VScrollbar(self.vAdjust)
		self.vScroll.connect("value-changed", self.scrollUpdate, True)

	def getWidget(self):
		return self.table

	def specialRedraw(self, context, ex, ey, ew, eh):

		self.__redrawLocked = True

		# Ensure that the scrolling is handled correctly
		# This sets the size of the scroll bar handles correctly
		self.vAdjust.page_size = eh / self.getZoom()
		self.hAdjust.page_size = ew / self.getZoom()

		# Adjust the scroll offsets so that the maximum amount of map is
		# visible. This mimics the behavior of a drawing area inside of a
		# gtk.ScrolledWindow
		ewz = int(ew / self.getZoom())
		if self.__scrollOffsetX + ewz > self.hAdjust.upper:
			self.__scrollOffsetX = int(max(self.hAdjust.upper - ewz, 0))
			self.hAdjust.value = self.__scrollOffsetX

		ehz = int(eh / self.getZoom())
		if self.__scrollOffsetY + ehz > self.vAdjust.upper:
			self.__scrollOffsetY = int(max(self.vAdjust.upper - ehz, 0))
			self.vAdjust.value = self.__scrollOffsetY

		context.rectangle(0, 0, self.hAdjust.upper - self.__scrollOffsetX,
			self.vAdjust.upper - self.__scrollOffsetY)
		context.set_source(self.checkerPattern)
		context.fill()

		# Draw tile layers
		controller = self.getController()
		ts = int(controller.mapTileSize())

		xStart = self.__scrollOffsetX // ts
		xEnd = (ewz // ts) + xStart + 2
		yStart = self.__scrollOffsetY // ts
		yEnd = (ehz // ts) + yStart + 2

		i = controller.getLayerInfo()

		for z in range(controller.getNumLayers()):
			if i[z][1] == False:
				continue # The layer is not visible
			for x in range(xStart, xEnd):
				for y in range(yStart, yEnd):
					info = controller.getTile(x, y, z)
					if info is not None:
						surface = controller.getTilesetSurface(info[2])
						context.set_source_surface(surface,
							((x - info[0]) * ts) - self.__scrollOffsetX,
							((y - info[1]) * ts) - self.__scrollOffsetY)
						context.rectangle((x * ts) - self.__scrollOffsetX,
							(y * ts) - self.__scrollOffsetY, ts, ts)
						context.fill()


		if self.showGrid == True:
			context.save()
			context.rectangle(0, 0, ts * controller.mapWidth(),
				ts * controller.mapHeight())
			context.clip()
			graphics.drawGrid(context, ts, ewz, ehz,
				self.__scrollOffsetX,
				self.__scrollOffsetY)
			context.restore()

		# Change the transform matrix of the context here so that the classes
		# in editortools don't need to know about self.__scrollOffset*. This
		# only works if specialRedraw is called before the
		context.translate(-self.__scrollOffsetX, -self.__scrollOffsetY)

		self.__redrawLocked = False

	def addTool(self, tool, toolID):
		tilegrid.TileGrid.addTool(self, tool, toolID)
		self.__lastMessage = self.__statusBar.push(self.__contextID,
			self.getToolInstructions())

	def buttonPress(self, widget, event):
		if event.button == 2:
			# Middle-click pans around the map
			self.__dragScrollPressed = True
			self.__dragScrollX = (self.__scrollOffsetX * self.getZoom()) + event.x
			self.__dragScrollY = (self.__scrollOffsetY * self.getZoom()) + event.y
		else:
			tilegrid.TileGrid.buttonPress(self, widget, event)

	def buttonRelease(self, widget, event):
		if event.button == 2:
			self.__dragScrollPressed = False
			self.__dragScrollX = None
			self.__dragScrollY = None
		else:
			tilegrid.TileGrid.buttonRelease(self, widget, event)

	def mouseMotion(self, widget, event):
		# Translate the coordinates according to self.__scrollOffset* so that
		# the editortools aren't affected by them.
		if self.__dragScrollPressed == True:
			dx = (self.__dragScrollX - event.x) / self.getZoom()
			if dx + self.hAdjust.page_size < self.hAdjust.upper:
				self.hAdjust.set_value(dx)
			else:
				self.hAdjust.set_value(self.hAdjust.upper
					- self.hAdjust.page_size)

			dy = (self.__dragScrollY - event.y) / self.getZoom()
			if dy + self.vAdjust.page_size < self.vAdjust.upper:
				self.vAdjust.set_value(dy)
			else:
				self.vAdjust.set_value(self.vAdjust.upper
					- self.vAdjust.page_size)
		else:
			event.x = event.x + (self.__scrollOffsetX * self.getZoom())
			event.y = event.y + (self.__scrollOffsetY * self.getZoom())
			tilegrid.TileGrid.mouseMotion(self, widget, event)

	def scroll(self, window, event):
		"""
		Callback for the scroll wheel/buttons. This is necessary to emulate the
		behavior of gtk.ScrolledWindow
		@type window: gtk.gdk.Window
		@param window: the window
		@type event: gtk.gdk.Event
		@param event: the scroll event
		"""
		if event.direction == gtk.gdk.SCROLL_UP:
			self.vAdjust.set_value(self.vAdjust.value
				- self.vAdjust.step_increment)
		elif event.direction == gtk.gdk.SCROLL_DOWN:
			newVal = self.vAdjust.value + self.vAdjust.step_increment
			if newVal + self.vAdjust.page_size > self.vAdjust.upper:
				self.vAdjust.set_value(self.vAdjust.upper
					- self.vAdjust.page_size)
			else:
				self.vAdjust.set_value(self.vAdjust.value
					+ self.vAdjust.step_increment)
		elif event.direction == gtk.gdk.SCROLL_LEFT:
			self.hAdjust.set_value(self.hAdjust.value
				- self.hAdjust.step_increment)
		elif event.direction == gtk.gdk.SCROLL_RIGHT:
			newVal = self.hAdjust.value + self.hAdjust.step_increment
			if newVal + self.hAdjust.page_size > self.hAdjust.upper:
				self.hAdjust.set_value(self.hAdjust.upper
					- self.hAdjust.page_size)
			else:
				self.hAdjust.set_value(self.hAdjust.value
					+ self.hAdjust.step_increment)

	def toolSelect(self, toolID):
		tilegrid.TileGrid.toolSelect(self, toolID)
		self.__statusBar.pop(self.__lastMessage)
		self.__lastMessage = self.__statusBar.push(self.__contextID,
			self.getToolInstructions())
		self.queue_draw()

	def scrollUpdate(self, adjustment, vertical):
		if vertical:
			self.__scrollOffsetY = int(round(adjustment.get_value()))
		else:
			self.__scrollOffsetX = int(round(adjustment.get_value()))

		# Prevent an infinite loop
		if self.__redrawLocked == False:
			self.queue_draw()

	def getThumbnail(self, largest):
		"""
		@type largest: int
		@param largest: the largest of the dimentions of the returned image
		"""
		controller = self.getController()
		ts = controller.mapTileSize()
		mw = controller.mapWidth()
		mh = controller.mapHeight()
		w = mw * ts
		h = mh * ts
		s = 1.0
		if w > h:
			s = float(largest) / float(w)
		else:
			s = float(largest) / float(h)
		result = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(w * s), int(h * s))
		context = cairo.Context(result)
		context.scale(s, s)

		# Now a trick to get this to work correctly. specialRedraw changes based
		# on the values of self.__scrollOffset*, so make a copy of them here
		tempScrollX = self.__scrollOffsetX
		tempScrollY = self.__scrollOffsetY
		self.__scrollOffsetX = 0
		self.__scrollOffsetY = 0

		self.specialRedraw(context, 0, 0, w, h)

		# Restore them here
		self.__scrollOffsetX = tempScrollX
		self.__scrollOffsetY = tempScrollY


		return result

	############################################################################
	# MapListener code
	############################################################################

	def listenSetVisibilty(self, index, visible):
		self.queue_draw()

	def listenResize(self, width, height, xOffset, yOffset):
		ts = self.getController().mapTileSize()
		self.vAdjust.upper = height * ts
		self.hAdjust.upper = width * ts

	def listenAddLayer(self, layerName):
		self.queue_draw()

	def listenRemoveLayer(self, index):
		self.queue_draw()

	def listenSwapLayers(self, index1, index2):
		self.queue_draw()

	def listenAddTile(self, tile, x, y, z):
		self.queue_draw()

	def listenRemoveTile(self, x, y, z):
		self.queue_draw()

	def listenUndoRedo(self):
		self.queue_draw()

	############################################################################
	# End MapListener code
	############################################################################

