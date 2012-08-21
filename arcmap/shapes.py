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
Contains various geometry related classes and functions
"""


import math
import preferences

class Point:
	"""
	This may just end up being replaced by a tuple
	"""
	def __init__(self, x, y):
		"""
		Brief Description
		@type x: int
		@param x: Placeholder
		@type y: int
		@param y: Placeholder
		"""
		self.x = x
		self.y = y


class Shape:
	"""
	Base class for shapes
	"""
	def __init__(self):
		self.__center = None
		self.friction = 1.0
		self.restitution = 0.0
		self.damage = 0.0

	def adjust(self, x, y, i = -1):
		"""
		Adjusts the geometry of the shape
		@type x: int
		@param x: the new x-coordinate for the point
		@type y: int
		@param y: the new y-coordinate for the point
		@type i: int
		@param i: the index of the point being moved
		"""
		i = -1
		raise NameError("Shape::adjust must be overridden in a subclass")


	def boundingBox(self):
		"""
		@rtype: (int, int, int, int)
		@return: a bounding box int the form x, y, x2, y2 where x2 is the
		    x-coordinate of the right edge, y2 as the bottom edge, and so on.
		"""
		raise NameError("Shape::boundingBox must be overridden in a subclass")

	def getCenter(self):
		"""
		@rtype: Point
		@return: The center of the shape
		"""
		return self.__center

	def setCenter(self, center):
		self.__center = center

	def intersects(self, p):
		"""
		@type p: Point
		@param p: point to test
		@rtype: bool
		@return: True if p intersects the shape, False otherwise
		"""
		raise NameError("Shape::intersects must be overridden in a subclass")

	def shift(self, xoffset, yoffset):
		"""
		Moves the shape around by x and y
		"""
		raise NameError("Shape::shift must be overridden in a subclass")

	def getHandles(self):
		"""
		@rtype: Point[]
		@return: List of points that define the center of handles for resizing
		   the shape
		"""
		raise NameError("Shape::getHandles must be overridden in a subclass")


class Polygon(Shape):

	def __init__(self, points = None):
		"""
		@type points: point[]
		@param points: the points that make up the polygon
		"""
		Shape.__init__(self)
		self.__points = points
		self.__concave = False
		if points is not None:
			if len(self.__points) < 3:
				log.warning("Polygon constructed with fewer than three points."+
					" This will not end well.")
			else:
				self.__concave = self.__calcConcave()
				self.calcCenter()
		else:
			self.__points = [Point(0, 0)]

		points = None

	def addPoint(self, p):
		"""
		Brief Description
		@type p: Point
		@param p: the point to add
		"""
		self.__points.append(p)
		self.__concave = self.__calcConcave()
		self.calcCenter()

	def getPoints(self):
		"""
		@rtype: Point[]
		@return: A copy of the polygon's points
		"""
		return self.__points[:]

	def getLastPoint(self):
		if len(self.__points) > 2:
			return self.__points[-2]
		else:
			return None

	def delExtraPoint(self):
		del self.__points[-1]

	def forceCClockwise(self):
		"""
		Rearranges the points of the shape so that they are in counter-clockwise
		order.
		"""
		# Python makes this too easy.
		self.__points.sort(key=lambda p: math.atan2(p.x - self.getCenter().x,
			p.y - self.getCenter().y), reverse=True)

	def calcCenter(self):
		"""
		Recalculates the center of the shape. This center is simply the average
		of the x and y coordinates of all the points
		"""
		l = len(self.__points)
		if l == 0:
			return
		totalx = 0
		totaly = 0
		for p in self.__points:
			totalx += p.x
			totaly += p.y
		center = Point(totalx / float(l), totaly / float(l))
		self.setCenter(center)

	def convex(self):
		"""
		@rtype: bool
		@return: True if the shape is convex
		"""
		if len(self.__points) <= 2:
			return False
		else:
			return not self.__concave

	def concave(self):
		"""
		@rtype: bool
		@return: True if the shape is convex
		"""
		# Separated from the calculating function so that the query is fast
		return self.__concave

	def __calcConcave(self):
		if len(self.__points) <= 2:
			# This shape isn't even valid
			return True
		elif len(self.__points) == 3:
			# Triangles are always convex
			return False
		# I think I adapted this from something I snatched from Wikipedia...
		# Basically the cross products of the vectors will all point up or all
		# point down if the turns made at each vertex are in the same direction
		positiveFlag = negativeFlag = False
		for i in range(len(self.__points)):
			j = (i + 1) % len(self.__points)
			k = (i + 2) % len(self.__points)
			z  = ((self.__points[j].x - self.__points[i].x)
				* (self.__points[k].y - self.__points[j].y))
			z = z - ((self.__points[j].y - self.__points[i].y)
				* (self.__points[k].x - self.__points[j].x))
			if z < 0:
				positiveFlag = True
			elif z > 0:
				negativeFlag = True
			if positiveFlag and negativeFlag:
				return True
		return False

	def adjust(self, x, y, i = -1):
		self.__points[i].x = x
		self.__points[i].y = y
		self.__concave = self.__calcConcave()
		self.calcCenter()
		i = -1

	def intersects(self, p):
		# First create a list of vectors that are the right-hand normals of the
		# vectors that point from point n to point n+1
		rightVectors = []
		for i in range(len(self.__points) - 1):
			dx = self.__points[i + 1].x - self.__points[i].x
			dy = self.__points[i + 1].y - self.__points[i].y
			rightVectors.append(Point(dy, -dx))
		# Last point back to the first
		dx = self.__points[0].x - self.__points[-1].x
		dy = self.__points[0].y - self.__points[-1].y
		rightVectors.append(Point(dy, -dx))

		for i, v in enumerate(rightVectors):
			# Calculate the vector pointing from the vertex to the test point,
			# then multiply the components by the right-hand normal.
			x = (p.x - self.__points[i].x) * v.x
			y = (p.y - self.__points[i].y) * v.y

			# If the sum of the components is positive, the point is on the
			# positive side of the normal vector, and thus outside the shape
			if (x + y) >= 0:
				return False
		return True

	def shift(self, xoffset, yoffset):
		for p in self.__points:
			p.x = p.x + xoffset
			p.y = p.y + yoffset
		self.calcCenter()

	def getHandles(self):
		return self.getPoints()


class Circle(Shape):

	def __init__(self, radius, snap = -1):
		Shape.__init__(self)
		self.__radius = radius
		self.__snapFactor = snap
		snap = -1

	def adjust(self, x, y, i = -1):
		c = self.getCenter()
		newRadius = math.sqrt((c.x - x)**2 + (c.y - y)**2)
		if self.__snapFactor != -1:
			newRadius = round(newRadius / self.__snapFactor) \
				* self.__snapFactor
			self.__radius = int(max(self.__snapFactor, newRadius))

	def setSnapFactor(self, snap):
		self.__snapFactor = snap

	def boundingBox(self):
		c = self.getCenter()
		return (c.x - self.__radius, c.x + self.__radius, self.__radius * 2,
			self.__radius * 2)

	def getRadius(self):
		"""
		@rtype: int
		@return: the radius of the circle
		"""
		return self.__radius

	def setRadius(self, r):
		"""
		@type r: int
		@param r: the new radius of the circle
		"""
		self.__radius = r

	def intersects(self, p):
		c = self.getCenter()
		dx = p.x - c.x
		dy = p.y - c.y
		if ((dx ** 2.0) + (dy ** 2.0)) < (self.__radius ** 2.0):
			return True
		else:
			return False

	def shift(self, xoffset, yoffset):
		c = self.getCenter()
		self.setCenter(Point(c.x + xoffset, c.y + yoffset))

	def getHandles(self):
		c = self.getCenter()
		return [Point(c.x - self.__radius, c.y),
			Point(c.x + self.__radius, c.y),
			Point(c.x, c.y - self.__radius),
			Point(c.x, c.y + self.__radius)]


def pointInHandle(p, h):
	"""
	@type p: Point
	@param p: the point to test
	@type h: Point
	@param h: the center of the handle
	@rtype: bool
	@return: True if the point is inside the handle, False if not
	"""
	s = preferences.visual["handle_size"]
	if p.x < h.x - s:
		return False
	if p.x > h.x + s:
		return False
	if p.y < h.y - s:
		return False
	if p.y > h.y + s:
		return False
	return True


def isInsideRectangle(shape, x, y, w, h):
	rx1, ry1, rx2, ry2 = shape.boundingBox()

	if rx2 < x:
		return False
	if ry2 < y:
		return False
	if rx1 > x + w:
		return False
	if ry1 > y + h:
		return False
	return True


def unittest():
	"""
	Simple sanity check on the intersects code
	"""
	p = Polygon([
		Point(1, 1),
		Point(4, 2),
		Point(2, 4)
	])
	assert p.intersects(Point(2, 2)) == True
	assert p.intersects(Point(2, 1)) == False

	p = Polygon([
		Point(1, 1),
		Point(3, 1),
		Point(1, 3),
		Point(3, 3)
	])
	assert p.intersects(Point(2, 2)) == True
	assert p.intersects(Point(0, 0)) == False

if __name__ == "__main__":
	unittest()
