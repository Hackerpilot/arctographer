################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Sep 23 2009
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
Contains code for previewing graphical user preferences
"""


import cairo
import gtk

import graphics
import shapes
import preferences


class VisualWidget(gtk.DrawingArea):
	"""
	Widget for previewing preferences
	"""
	__gsignals__ = {"expose-event" : "override"}

	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self.__checkerBoard = graphics.getCheckerPattern(16)

		self.shapes = []
		vPoly = shapes.Polygon([
			shapes.Point(10, 10),
			shapes.Point(10, 86),
			shapes.Point(40, 86),
			shapes.Point(86, 10),
		])
		iPoly = shapes.Polygon([
			shapes.Point(106, 10),
			shapes.Point(96, 86),
			shapes.Point(140, 86),
			shapes.Point(120, 50),
			shapes.Point(160, 10),
		])
		circle = shapes.Circle(35)
		circle.setCenter(shapes.Point(200, 48))
		self.shapes.append(vPoly)
		self.shapes.append(iPoly)
		self.shapes.append(circle)

		self.set_size_request(256, 96)

	def update(self):
		"""
		Updates the preview
		"""
		self.queue_draw()

	def do_expose_event(self, event):
		context = self.window.cairo_create()
		context.set_source(self.__checkerBoard)
		context.paint()
		size = self.window.get_size()
		graphics.drawGrid(context, 16, size[0], size[1])
		for shape in self.shapes:
			graphics.drawShape(shape, context, True)


