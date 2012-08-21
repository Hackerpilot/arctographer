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
Contains a custom widget for previewing a resize operation
"""

import cairo
import gtk

import graphics


class ResizeView(gtk.DrawingArea):
	"""
	Widget for previewing a resize operation.
	"""

	__gsignals__ = {"expose-event" : "override"}

	def __init__(self, tileWidth, tileHeight , thumb):
		"""
		@type tileWidth: int
		@param tileWidth: current width of map in tiles
		@type tileHeight: int
		@param tileHeight: current height of map in tiles
		@type thumb: cairo.ImageSurface
		@param thumb: thumbnail image of the map
		"""
		gtk.DrawingArea.__init__(self)
		self.__tWidth = thumb.get_width()
		self.__tHeight = thumb.get_height()
		self.__pixelSize = int(max(thumb.get_width(), thumb.get_height()))
		self.__oldWidth = tileWidth
		self.__oldHeight = tileHeight
		self.__thumb = thumb
		self.__newWidth = tileWidth
		self.__newHeight = tileHeight
		self.__scaleFactor = 1.0
		self.__top = 0
		self.__bottom = 0
		self.__left = 0
		self.__right = 0
		self.__checkerBoard = graphics.getCheckerPattern(16)
		self.set_size_request(thumb.get_width(), thumb.get_height())

	def setTop(self, top):
		self.__top = top
		self.__newHeight = self.__oldHeight + self.__top + self.__bottom
		self.__setDimentions()

	def setBottom(self, bottom):
		self.__bottom = bottom
		self.__newHeight = self.__oldHeight + self.__top + self.__bottom
		self.__setDimentions()

	def setLeft(self, left):
		self.__left = left
		self.__newWidth = self.__oldWidth + self.__left + self.__right
		self.__setDimentions()

	def setRight(self, right):
		self.__right = right
		self.__newWidth = self.__oldWidth + self.__left + self.__right
		self.__setDimentions()

	def do_expose_event(self, event):
		"""
		Redraws the widget
		"""
		context = self.window.cairo_create()
		context.set_source(self.__checkerBoard)
		context.paint()
		context.scale(self.__scaleFactor, self.__scaleFactor)
		tileWidth = float(self.__tHeight) / float(self.__oldHeight)
		context.set_source_surface(self.__thumb, self.__left * tileWidth,
			self.__top * tileWidth)
		context.rectangle(self.__left * tileWidth,
			self.__top * tileWidth, self.__tWidth, self.__tHeight)
		context.fill()

	def __setDimentions(self):
		# Sets the dimentions of the widget and causes a redraw with the proper
		# scaling applied. The math here is magical. Don't mess with it
		w = self.__pixelSize
		h = self.__pixelSize
		# gd = greater dimention
		gd = max(self.__oldWidth, self.__oldHeight)
		if self.__newWidth > self.__newHeight:
			h = self.__pixelSize * (float(self.__newHeight) / float(self.__newWidth))
			self.__scaleFactor = gd / float(self.__newWidth)
		else:
			w = self.__pixelSize * (float(self.__newWidth) / float(self.__newHeight))
			self.__scaleFactor = gd / float(self.__newHeight)
		self.set_size_request(int(w), int(h))
		self.queue_draw()


