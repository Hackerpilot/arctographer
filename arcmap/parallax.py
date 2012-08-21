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
Contains custom widget for previewing parallax backgrounds.
"""

import gtk
import cairo

import graphics
import tilemap

class ParallaxViewer(gtk.DrawingArea):
	"""
	Widget for drawing parallax backgrounds to the screen
	"""

	__gsignals__ = {"expose-event": "override"}

	def __init__(self, width, height, scale):
		"""
		@type width: int
		@param width: width of preview in pixels
		@type height: int
		@param height: height of preview in pixels
		@type scale: int
		@param scale: scale factor for the preview.
		"""
		gtk.DrawingArea.__init__(self)
		# List of cairo.ImageSurface
		self.__layers = []
		# List of tilemap.Parallax
		self.__backgrounds = []
		# X-offset for preview
		self.__x = 0
		# Y-offset for preview
		self.__y = 0
		# Width of preview in pixels
		self.__width = width
		# Height of preview in pixels
		self.__height = height
		# Scaling applied to preview
		self.__scaleFactor = scale
		# Buffer to draw on
		self.__drawBuffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, width,
			height)
		# Background color
		self.__backColor = graphics.RGBA(0.0, 0.0, 0.0, 1.0)

		self.set_size_request(int(self.__width * self.__scaleFactor),
			int(self.__height * self.__scaleFactor))
		self.__redrawBuffer()

	def do_expose_event(self, event):
		windowContext = self.window.cairo_create()
		windowContext.rectangle(event.area.x, event.area.y, event.area.width,
			event.area.height)
		windowContext.clip()
		windowContext.scale(self.__scaleFactor, self.__scaleFactor)
		windowContext.set_source_surface(self.__drawBuffer)
		windowContext.paint()

	def addBackground(self, parallax):
		"""
		Adds a background to the preview
		@type parallax: tilemap.Parallax
		@param parallax: the background to add
		"""
		self.__layers.append(graphics.loadImage(parallax.fileName))
		self.__backgrounds.append(parallax)
		self.__redrawBuffer()
		self.queue_draw()

	def setX(self, x):
		"""
		@type x: int
		@param x: the new x-coordinate for the preview
		"""
		self.__x = x
		self.__redrawBuffer()
		self.queue_draw()

	def setY(self, y):
		"""
		@type y: int
		@param y: the y-coordinate for the preview
		"""
		self.__y = y
		self.__redrawBuffer()
		self.queue_draw()

	def setColor(self, color):
		"""
		@type color: graphics.RGBA
		@param color: the color to draw on the background below all the other
		    layers
		"""
		self.__backColor = color
		self.__redrawBuffer()
		self.queue_draw()

	def setWidth(self, width):
		"""
		@type width: int
		@param width: the new width of the preview
		"""
		self.__width = width
		self.__sizeChanged()

	def setHeight(self, height):
		"""
		@type height: int
		@param height: the new height of the preview
		"""
		self.__height = height
		self.__sizeChanged()

	def setScale(self, scale):
		"""
		@type scale: float
		@param scale: the new scale factor for the preview
		"""
		self.__scaleFactor = scale
		self.__sizeChanged()

	def setVisible(self, index, vis):
		"""
		@type index: int
		@param index: index of the layer to set (in)visible
		@type vis: bool
		@param vis: True to set the layer visible, False to set invisible
		"""
		self.__backgrounds[index].visible = vis
		self.__redrawBuffer()
		self.queue_draw()

	def swapLayers(self, index1, index2):
		"""
		Swaps two layers in the display order
		@type index1: int
		@param index1: the first layer
		@type index2: int
		@param index2: the second layer
		"""
		tb = self.__backgrounds[index1]
		self.__backgrounds[index1] = self.__backgrounds[index2]
		self.__backgrounds[index2] = tb

		tl = self.__layers[index1]
		self.__layers[index1] = self.__layers[index2]
		self.__layers[index2] = tl

		self.__redrawBuffer()
		self.queue_draw()

	def deleteLayer(self, index):
		"""
		@type index: int
		@param index: the index of the layer to delete
		"""
		del self.__backgrounds[index]
		del self.__layers[index]
		self.__redrawBuffer()
		self.queue_draw()

	def __sizeChanged(self):
		"""
		Called to recalculate things when the size of the widget changes
		"""
		self.set_size_request(int(self.__width * self.__scaleFactor),
			int(self.__height * self.__scaleFactor))
		self.__drawBuffer = cairo.ImageSurface(cairo.FORMAT_ARGB32,
			self.__width, self.__height)
		self.__redrawBuffer()
		self.queue_draw()

	def __redrawBuffer(self):
		"""
		Redraws the window
		"""
		context = cairo.Context(self.__drawBuffer)
		self.__backColor.contextColor(context)
		context.paint()
		for index, layerSurface in enumerate(self.__layers):
			back = self.__backgrounds[index]
			if back.visible == False:
				continue

			def calcBaseTimes(coord, scroll, scrollSpeed, tile, dimention,
				viewDimention):
				if scroll == True:
					coord = int(coord * scrollSpeed)
				else:
					coord = 0
				if tile == True:
					if coord > 0:
						coord = -(coord % dimention)
					else:
						coord = -coord % dimention
					times = (viewDimention // dimention) + 2
				else:
					times = 1
				return coord, times

			x, xTimes = calcBaseTimes(self.__x, back.hScroll, back.hScrollSpeed,
				back.hTile, layerSurface.get_width(), self.__width)
			y, yTimes = calcBaseTimes(-self.__y, back.vScroll,
				back.vScrollSpeed, back.vTile, layerSurface.get_height(),
				self.__height)

			for i in range(xTimes):
				if x <= 0:
					dstX = x + (layerSurface.get_width() * i)
				else:
					if self.__width > layerSurface.get_width():
						dstX = x + (layerSurface.get_width() * -(i - 1))
					else:
						dstX = x + (layerSurface.get_width() * -i)
				for j in range(yTimes):
					if y <= 0:
						dstY = y + (layerSurface.get_height() * j)
					else:
						if self.__height > layerSurface.get_height():
							dstY = y + (layerSurface.get_height() * -(j - 1))
						else:
							dstY = y + (layerSurface.get_height() * -j)
					context.set_source_surface(layerSurface, dstX, dstY)
					context.rectangle(dstX, dstY, layerSurface.get_width(),
						layerSurface.get_height())
					context.fill()
