################################################################################
# Authors: Brian Schott (Sir Alaran)
# Copyright: Brian Schott (Sir Alaran)
# Date: Oct 20 2009
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
Module for rigid-body collision detection storage
"""

class BlazeWorld(object):
	def __init__(self):
		# List of shapes that compose the world
		self.__shapes = []
		# Units are meters per second per second
		self.gravityX = 0
		# Units are meters per second per second
		self.gravityY = -9.8

	def addShape(self, s):
		"""
		Brief Description
		@type s: Shape
		@param s: Placeholder
		"""
		self.__shapes.append(s)

	def delShape(self, s):
		"""
		@type s: shapes.Shape
		@param s: the shape to remove
		"""
		if s in self.__shapes:
			self.__shapes.remove(s)

	def getShapes(self):
		"""
		@rtype: Shape[]
		@return: a reference to the shapes
		"""
		return self.__shapes

	def resize(self, width, height, xOffset, yOffset):
		"""
		@type width: int
		@param width: new width in pixels
		@type height: int
		@param height: new height in pixels
		@type xOffset: int
		@param xOffset: x-offset in pixels
		@type yOffset: int
		@param yOffset: y-offset in pixels
		"""
		for s in self.__shapes:
			s.shift(xOffset, yOffset)

			# Remove the shape if it is now outside the world's bounding box
			# leave this commented until undo is implemented for it.
#			if shapes.isInsideRectangle(s, 0, 0, width, height)
#				self.shapes.remove(s)
