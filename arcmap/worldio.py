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
Module for reading physics info from files or Python dictionaries
"""

import os
import json
import logging

import blazeworld
import shapes

log = logging.getLogger("worldio")

class WorldReader(object):
	"""
	Class for reading maps from JSON formatted text
	"""
	def __init__(self):
		pass

	def readf(self, fileName):
		"""
		Read a blaze world from a JSON file
		@type fileName: str
		@param fileName: the path to the file to read from
		"""
		if os.path.exists(fileName):
			f = open(fileName)
			try:
				d = json.load(f)
			except Exception as e:
				log.error(e)
				f.close()
				return None
			else:
				return self.readd(d)
				f.close()

	def readd(self, d):
		"""
		Reads a blaze world from a dictionary that was generated from a
		JSON file
		@type d: {}
		@param d: the dictionary for the world
		@rtype: BlazeWorld
		@return: the world loaded from the file
		"""
		world = blazeworld.BlazeWorld()
		if "gravityX" in d:
			if type(d["gravityX"]) == float or type(d["gravityX"]) == int:
				world.gravityX = float(d["gravityX"])
			else:
				log.error("Gravity X-component must be a number. Defaulting to 0")
				world.gravityX = 0.0
		else:
			log.error("Gravity X-component not specified in file. Defaulting to 0")
			world.gravityX = 0.0

		if "gravityY" in d:
			if type(d["gravityY"]) == float or type(d["gravityY"]) == int:
				world.gravityY = d["gravityY"]
			else:
				log.error("Gravity Y coordinate must be a number. Defaulting to -9.8")
				world.gravityY = -9.8
		else:
			log.error("Gravity Y-component not specified in file. Defaulting to -9.8")
			world.gravityY = -9.8

		if "shapes" in d:
			for shape in d["shapes"]:
				world.addShape(self.__parseShape(shape))
		else:
			log.error("No shapes attribute specified in the file")

		return world

	def __parseShape(self, shape):
		if "type" in shape:
			if shape["type"] == "circle":
				return self.__parseCircle(shape)
			elif shape["type"] == "polygon":
				return self.__parsePolygon(shape)
			else:
				log.error("Invalid shape type specified in file")
				return None

	def __parsePolygon(self, polygon):
		p = shapes.Polygon()
		p.delExtraPoint()
		if "points" in polygon:
			for point in polygon["points"]:
				p.addPoint(shapes.Point(point["x"], point["y"]))
		else:
			log.error("Polygon specified with no points")
		if "damage" in polygon:
			p.damage = polygon["damage"]
		if "friction" in polygon:
			p.friction = polygon["friction"]
		if "restitution" in polygon:
			p.restitution = polygon["restitution"]
		return p

	def __parsePoint(self, point):
		if "x" in point:
			if type(point["x"]) == float:
				x = point["x"]
			else:
				raise WorldError("Could not parse point's x-coordinate")
		else:
			raise WorldError("No x-coordinate found in point")

		if "y"in point:
			if type(point["x"]) == float or type(point["y"]) == int:
				y = float(point["y"])
			else:
				raise WorldError("Could not parse point's y-coordinate'")
		else:
			raise WorldError("No y-coordinate found in point")

	def __parseCircle(self, circle):
		c = shapes.Circle(0.0)
		if "center" in circle:
			c.setCenter(shapes.Point(circle["center"]["x"],
				circle["center"]["y"]))
		else:
			log.error("Circle specified with no center")
		if "radius" in circle:
			c.setRadius(circle["radius"])
		else:
			log.error("Circle specified with no radius")
		if "damage" in circle:
			c.damage = circle["damage"]
		if "friction" in circle:
			c.friction = circle["friction"]
		if "restitution" in circle:
			c.restitution = circle["restitution"]
		return c


class WorldWriter(object):
	def __init__(self, world):
		self.__world = world

	def writed(self):
		"""
		Writes the world to a dictionary that can be inserted to a dictionary
		or list that is then exported as a JSON file
		@type world: BlazeWorld
		@param world: the world to write
		@rtype: {}
		@return: A dictionary representing the blaze world
		"""
		d = {"shapes": [], "gravityX": self.__world.gravityX,
			"gravityY": self.__world.gravityY}
		for shape in self.__world.getShapes():
			d["shapes"].append(self.__writeShape(shape))
		return d

	def writef(self, fileName):
		"""
		Writes the world to a JSON file
		@type world: BlazeWorld
		@param world: the world to write
		@type fileName: str
		@param fileName: the path to the file to write to
		"""
		f = open(fileName, "w")
		json.dump(self.writed(self.__world), f)
		f.close()

	def __writeShape(self, shape):
		o = {"damage": shape.damage, "friction": shape.friction,
			"restitution": shape.restitution}
		if hasattr(shape, "getRadius"):
			o["type"] = "circle"
			o["center"] = {"x": shape.getCenter().x, "y": shape.getCenter().y}
			o["radius"] = shape.getRadius()
		else:
			o["type"] = "polygon"
			o["points"] = []
			for point in shape.getPoints():
				o["points"].append({"x": point.x, "y": point.y})
		return o


class WorldError(Exception):
	def __init__(self, message):
		self.msg = message

	def __str__(self):
		return self.msg
