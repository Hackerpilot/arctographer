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
Contains the TileGrid class
"""


__docformat__ = "epytext"

import logging
import gtk
import cairo
import preferences
import mapcontroller
import graphics

class TileGrid(gtk.DrawingArea):
	"""
	Base class for MapGrid and TilePalette. Handles functionality common
	to both such as drawing grids, handling mouse events, etc
	"""
	__gsignals__ = {"expose-event": "override"}

	def __init__(self, width, height, tileSize):
		gtk.DrawingArea.__init__(self)

		self.showGrid = False
		self.__scaleFactor = 1.0
		self.__zoomLevel = preferences.zoomNormalIndex
		self.__tileSize = tileSize
		self.__tools = []
		self.__selectedTool = 0
		self.__width = 0
		self.__height = 0
		self.checkerPattern = graphics.getCheckerPattern(tileSize)

		# DrawingArea can't get events of its own for whatever reason.
		# Sticking it in an EventBox works around this
		self.eventBox = gtk.EventBox()
		self.eventBox.connect("button-press-event", self.buttonPress)
		self.eventBox.connect("button-release-event", self.buttonRelease)
		self.eventBox.connect("motion-notify-event", self.mouseMotion)
		self.eventBox.connect("leave-notify-event", self.mouseLeave)
		self.eventBox.connect("enter-notify-event", self.mouseEnter)
		self.eventBox.connect("key-press-event", self.keyPress)
		self.eventBox.add(self)

		self.eventBox.set_events(gtk.gdk.POINTER_MOTION_MASK |
			gtk.gdk.POINTER_MOTION_HINT_MASK |
			gtk.gdk.BUTTON_PRESS_MASK |
			gtk.gdk.SCROLL_MASK |
			gtk.gdk.KEY_PRESS_MASK |
			gtk.gdk.BUTTON_RELEASE_MASK |
			gtk.gdk.LEAVE_NOTIFY_MASK |
			gtk.gdk.ENTER_NOTIFY_MASK)
		self.eventBox.show_all()

	def setSize(self, width, height):
		"""
		Sets the size of the tile grid
		@type width: int
		@param width: width of the grid in pixels
		@type height: int
		@param height: height of the grid in pixels
		"""
		self.__width = width
		self.__height = height
		self.set_size_request(self.__width, self.__height)

	def getWidget(self):
		return self.eventBox

	def do_expose_event(self, event):
		windowContext = self.window.cairo_create()
		windowContext.rectangle(event.area.x, event.area.y, event.area.width,
			event.area.height)
		windowContext.clip()
		windowContext.scale(self.__scaleFactor, self.__scaleFactor)
		self.specialRedraw(windowContext, event.area.x, event.area.y,
			event.area.width, event.area.height)
		if len(self.__tools) > 0:
			self.__tools[self.__selectedTool].draw(windowContext)

	def addTool(self, tool, toolID):
		while len(self.__tools) < toolID + 1:
			self.__tools.append(None)
		self.__tools[toolID] = tool

	def toolSelect(self, toolID):
		self.__selectedTool = toolID

	def getToolInstructions(self):
		return self.__tools[self.__selectedTool].getInstructions()

	def buttonPress(self, widget, event):
		if len(self.__tools) > 0:
			r = self.__tools[self.__selectedTool].mouseButtonPress(event.button,
				event.time)
			if r:
				self.queue_draw()

	def buttonRelease(self, widget, event):
		if len(self.__tools) > 0:
			r = self.__tools[self.__selectedTool].mouseButtonRelease(
				event.button, event.time)
			if r:
				self.queue_draw()

	def mouseMotion(self, widget, event):
		x, y = self.translateCoords(event.x, event.y)
		if len(self.__tools) > 0:
			r = self.__tools[self.__selectedTool].mouseMotion(x, y)
			if r:
				self.queue_draw()

	def mouseEnter(self, widget, event):
		r = self.__tools[self.__selectedTool].mouseEnter()
		if r:
			self.queue_draw()

	def mouseLeave(self, widget, event):
		r = self.__tools[self.__selectedTool].mouseLeave()
		if r:
			self.queue_draw()


	def keyPress(self, widget, event):
		if len(self.__tools) > 0:
			r = self.__tools[self.__selectedTool].keyPress(event.keyval)
			if r:
				self.redrawBuffer()
				self.queue_draw()

	def __validateZoom(self):
		self.__zoomLevel = min(max(self.__zoomLevel, 0),
			len(preferences.zoomLevels) - 1)

	def zoomIn(self):
		"""
		Zoom in
		"""
		self.__zoomLevel += 1
		self.__setZoom()

	def zoomOut(self):
		"""
		Zooms out
		"""
		self.__zoomLevel -= 1
		self.__setZoom()

	def zoomNormal(self):
		"""
		Reset the zoom level to 100%
		"""
		self.__zoomLevel = preferences.zoomNormalIndex
		self.__setZoom()

	def __setZoom(self):
		""" Set the zoom level"""
		self.__validateZoom()
		self.__scaleFactor = preferences.zoomLevels[self.__zoomLevel]
		self.queue_draw()

	def getZoom(self):
		return self.__scaleFactor

	def specialRedraw(self, context, ex, ey, ew, eh):
		""" Override this in derived classes """
		pass

	def translateCoords(self, x, y):
		"""
		Translates the coordinates x and y based on the zoom level given in sf
		For example, at a zoom level of 2 an x-coordinate of 50 screen pixels
		would actually be at 25 map pixels.
		"""
		sfinverse = 1.0 / self.__scaleFactor
		return round(x * sfinverse), round(y * sfinverse)

	def toggleGrid(self):
		""" Turns the grid on or off """
		self.showGrid = not self.showGrid
		self.queue_draw()
