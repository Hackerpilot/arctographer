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
Code for graphical operations such as tile and shape drawing.
"""


import os
import math
import logging

import gobject
import gtk
import cairo

import shapes
import preferences

log = logging.getLogger("graphics")

def getBackgroundColor():
	"""
	@rtype: RGBA
	@return: a color representation of the background color from the gtk theme
	"""
	style = gtk.rc_get_style_by_paths(gtk.settings_get_default(),
		"GtkTextView", "GtkTextView", gtk.TextView)
	c = RGBA()
	c.setGdk(style.bg[gtk.STATE_NORMAL])
	return c


def getForegroundColor():
	"""
	@rtype: RGBA
	@return: the foreground color from the gtk theme
	"""
	style = gtk.rc_get_style_by_paths(gtk.settings_get_default(),
		"GtkTextView", "GtkTextView", gtk.TextView)
	c = RGBA()
	c.setGdk(style.text[gtk.STATE_NORMAL])
	return c


def getHighlightColor():
	style = gtk.rc_get_style_by_paths(gtk.settings_get_default(),
		"GtkTextView", "GtkTextView", gtk.TextView)
	c = RGBA()
	c.setGdk(style.bg[gtk.STATE_SELECTED])
	return c


def getFileFilter():
	"""
	@rtype: gtk.FileFilter
	@return: A file filter for open dialogs allowing only image formats
	"""
	fFilter = gtk.FileFilter()
	fFilter.add_mime_type("image/png") # Preffered
	fFilter.add_mime_type("image/x-ms-bmp") # Also works
	fFilter.add_mime_type("image/jpeg") # a bad idea for pixel-art...
	fFilter.add_mime_type("image/x-pcx")
	fFilter.add_mime_type("image/x-tga")
	fFilter.add_mime_type("image/gif") # TODO: Test this with an animation
	fFilter.set_name("Images")
	return fFilter


def loadImage(fileName):
	"""
	This function is used so that images in any format supported by gdk can be
	loaded.
	@type fileName: string
	@param fileName: name of file to load
	@rtype: cairo.ImageSurface
	@return: An image surface containing the contents of the file
	"""
	if not os.path.exists(fileName):
		log.error("Could not open " + fileName)
		return None
	else:
		pixbuf = gtk.gdk.pixbuf_new_from_file(fileName)
		x = pixbuf.get_width()
		y = pixbuf.get_height()
		surface = cairo.ImageSurface(0,x,y)
		ct = cairo.Context(surface)
		ct2 = gtk.gdk.CairoContext(ct)
		ct2.set_source_pixbuf(pixbuf,0,0)
		ct2.paint()
		return surface


class RGBA(object):
	def __init__(self, r = 0.0, g = 0.0, b = 0.0, a = 1.0):
		"""
		@type r: float
		@param r: red
		@type g: float
		@param g: green
		@type b: float
		@param b: blue
		@type a: float
		@param a: alpha
		"""
		self.r = r
		self.g = g
		self.b = b
		self.a = a

		# Silly Python
		r = 0.0
		g = 0.0
		b = 0.0
		a = 1.0

	def toU32(self):
		"""
		@return: a 32-bit unsigned integer representing the color
		"""
		return ((int(self.r * 255) << 24) + (int(self.g * 255) << 16)
			+ (int(self.b * 255) << 8) + (int(self.a * 255)))

	def fromU32(self, u):
		if isinstance(u, int) or isinstance(u, long):
			self.r = (u >> 24) / 255.0
			self.g = ((u & 0x00ff0000) >> 16) / 255.0
			self.b = ((u & 0x0000ff00) >> 8) / 255.0
			self.a = (u & 0x000000ff) / 255.0
		else:
			log.warning("Invalid argument to RGBA.fromU32, %s" % u)


	def setGdk(self, color):
		"""
		Sets this based on a gtk.gdk.Color
		"""
		self.r = color.red / 65535.0
		self.g = color.green / 65535.0
		self.b = color.blue / 65535.0
		self.a = 1.0

	def getGdk(self):
		"""
		@rtype: a gtk.gdk.Color
		@return: this color in gdk format
		"""
		# 2**16 = 65536
		return gtk.gdk.Color(int(self.r * 65535), int(self.g * 65535),
			int(self.b * 65535))

	def contextColor(self, context):
		context.set_source_rgba(self.r, self.g, self.b, self.a)


def getCheckerPattern(ts):
	"""
	@type ts: int
	@param ts: size of the checker pattern in pixels
	@rtype: cairo.SurfacePattern
	@return: the new pattern
	"""
	# tso = tile size over ...
	tso4 = ts / 4
	tso2 = ts / 2
	checkerboard = cairo.ImageSurface(cairo.FORMAT_ARGB32, tso2, tso2)
	checkerContext = cairo.Context(checkerboard)

	checkerContext.set_source_rgba(0.5, 0.5, 0.5, 1)
	checkerContext.rectangle(0, 0, tso2, tso2)
	checkerContext.fill()

	checkerContext.set_source_rgba(0.25, 0.25, 0.25, 1)
	checkerContext.rectangle(tso4, 0, tso4, tso4)
	checkerContext.fill()
	checkerContext.rectangle(0, tso4, tso4, tso4)
	checkerContext.fill()

	checkerPattern = cairo.SurfacePattern(checkerboard)
	checkerPattern.set_extend(cairo.EXTEND_REPEAT)
	return checkerPattern


def drawGrid(context, tileSize, width, height, xOffset = 0, yOffset = 0):
	"""
	Draw a grid with cells the same size as tiles on a cairo context
	@type context: cairo.Context
	@param context: the destination context
	@type tileSize: int
	@param tileSize: the size of the grid cells
	"""
	context.save()
	context.set_source_rgba(0.0, 0.0, 0.0, 1.0)
	context.set_dash((preferences.visual["stipple_length"],
		preferences.visual["stipple_gap"]))
	context.set_line_width(1)
	for i in range(-1, width // tileSize + 2):
		x = i * tileSize + .5 - (xOffset % tileSize)
		context.move_to(x, 0)
		context.line_to(x, height)
		context.stroke()
	for i in range(-1, height // tileSize + 2):
		y =  i * tileSize + .5 - (yOffset % tileSize)
		context.move_to(0, y)
		context.line_to(width, y)
		context.stroke()
	context.restore()

	xOffset = 0
	yOffset = 0


def drawShape(shape, context, handles = False):
	outlineColor = RGBA()
	outlineColor.fromU32(preferences.visual["valid_outline"])
	fillColor = RGBA()
	fillColor.fromU32(preferences.visual["valid_fill"])
	if hasattr(shape, "getRadius"):
		drawCircle(context, shape, outlineColor,
			fillColor, handles)
	else:
		if shape.convex() == False:
			outlineColor.fromU32(preferences.visual["invalid_outline"])
			fillColor.fromU32(preferences.visual["invalid_fill"])
		drawPolygon(context, shape, outlineColor, fillColor, handles)
	handles = False


def drawPolygon(context, shape, outlineColor, fillColor, handles = False):
	"""
	@type context: cairo.Context
	@param context: context to draw on
	@type shape: shapes.Shape
	@param shape: the shape to draw
	@type outlineColor: RGBA
	@param outlineColor: color for the outline
	@type fillColor: RGBA
	@param fillColor: color for the filled shape
	@type handles: bool
	@param handles: True if handles should be drawn on the points
	"""
	outlineColor.contextColor(context)
	points = shape.getPoints()
	context.set_line_width(2.0)
	context.move_to(points[0].x, points[0].y)
	for point in shape.getPoints():
		# 0.5 to align the points to pixels
		context.line_to(point.x, point.y)
	context.close_path()
	context.stroke_preserve()
	fillColor.contextColor(context)
	context.fill()

	if handles:
		for point in points:
			drawPointHandle(context, point)
	handles = False


def drawCircle(context, shape, outlineColor, fillColor,	handles = False):
	"""
	@type context: cairo.Context
	@param context: context to draw to
	@type shape: shapes.Shape
	@param shape: the shape to draw
	@type outlineColor: RGBA
	@param outlineColor: color for the outline
	@type fillColor: RGBA
	@param fillColor: color for the filled shape
	@type handles: bool
	@param handles: True if the handles should be drawn, false otherwise
	"""
	outlineColor.contextColor(context)
	context.set_line_width(2.0)
	c = shape.getCenter()
	context.arc(c.x, c.y, shape.getRadius(), 0, math.pi * 2)
	context.stroke_preserve()
	fillColor.contextColor(context)
	context.fill()

	if handles:
		for point in shape.getHandles():
			drawPointHandle(context, point)


def drawPointHandle(context, p, lineWidth = 1.0):
	"""
	@type context: cairo.Context
	@param context: destination context
	@type p: shapes.Point
	@param p: the point to draw
	"""
	size = preferences.visual["handle_size"]
	x = p.x - int(size / 2.0)
	y = p.y - int(size / 2.0)
	context.rectangle(x + 0.5, y + 0.5, size, size)
	context.set_source_rgba(0.0, 0.0, 0.0, 1.0)
	context.set_line_width(lineWidth)
	context.stroke()
	context.rectangle(x + 1.5, y + 1.5, size, size)
	context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
	context.set_line_width(lineWidth)
	context.stroke()
	size = -1
	lineWidth = 1.0


def drawMoveHandle(context, p):
	"""
	Draws a movement handle (A four-pointed arrow)
	@type context: cairo.Context
	@param context: the context to draw on
	@type p: shapes.Point
	@param p: the point to draw the handle around
	"""
	size = preferences.visual["handle_size"]

	context.set_line_width(size / 4)
	context.set_source_rgba(0.0, 0.0, 0.0, 1.0)

	context.move_to(p.x - (size / 2) - 0.5, p.y)
	context.line_to(p.x + (size / 2) + 0.5, p.y)
	context.stroke()

	context.move_to(p.x, p.y - (size / 2) - 0.5)
	context.line_to(p.x, p.y + (size / 2) + 0.5)
	context.stroke()

	arrowSize = size / 2.5

	# Right arrow
	context.move_to(p.x + (size / 2), p.y - arrowSize)
	context.line_to(p.x + (size / 2) + arrowSize, p.y)
	context.line_to(p.x + (size / 2), p.y + arrowSize)
	context.close_path()
	context.fill()

	# Left arrow
	context.move_to(p.x - (size / 2), p.y - arrowSize)
	context.line_to(p.x - (size / 2) - arrowSize, p.y)
	context.line_to(p.x - (size / 2), p.y + arrowSize)
	context.close_path()
	context.fill()

	# Bottom arrow
	context.move_to(p.x + arrowSize, p.y + (size / 2))
	context.line_to(p.x, p.y + (size / 2) + arrowSize)
	context.line_to(p.x - arrowSize, p.y + (size / 2))
	context.close_path()
	context.fill()

	# Top arrow
	context.move_to(p.x + arrowSize, p.y - (size / 2))
	context.line_to(p.x, p.y - (size / 2) - arrowSize)
	context.line_to(p.x - arrowSize, p.y - (size / 2))
	context.close_path()
	context.fill()

	# reset default argument
	size = -1


def getDeleteCirclePattern(size):
	"""
	@type size: int
	@param size: Size of the circle
	@rtype: cairo.SurfacePattern
	@return: a red circle with a line through it.
	"""
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
	context = cairo.Context(surface)
	context.set_source_rgba(1.0, 0.0, 0.0, 1.0)
	context.arc(size / 2, size / 2, size / 2 * .8 , 0, math.pi * 2)
	context.set_line_width(size / 8)
	context.stroke_preserve()
	context.clip()
	context.move_to(0, 0)
	context.line_to(size, size)
	context.stroke()
	return cairo.SurfacePattern(surface)


def getDeletePattern(size):
	"""
	@type size: int
	@param size: the size of the x
	@rtype: cairo.SurfacePattern
	@return: a red x
	"""
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
	context = cairo.Context(surface)
	context.set_source_rgba(1.0, 0.0, 0.0, 1.0)
	lineWidth = size / 8
	context.move_to(lineWidth, lineWidth)
	context.line_to(size - lineWidth, size - lineWidth)
	context.move_to(lineWidth, size - lineWidth)
	context.line_to(size - lineWidth, lineWidth)
	context.stroke()
	return cairo.SurfacePattern(surface)

