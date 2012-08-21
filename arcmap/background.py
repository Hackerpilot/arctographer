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
Module for parallax backgrounds
"""

import graphics
import copy


class Background(object):
	"""
	Level background information
	"""

	def __init__(self):
		self.parallaxes = []
		self.bgColor = graphics.RGBA()

	def getParallaxes(self):
		"""
		@rtype: ParallaxLayer[]
		@return: the parallax layers of the background
		"""
		return copy.deepcopy(self.parallaxes)

	def setParallaxes(self, parallaxes):
		"""
		@type parallaxes: ParallaxLayer[]
		@param parallaxes: the layers for the background
		"""
		self.parallaxes = parallaxes

	def getBGColor(self):
		"""
		@rtype: graphics.RGBA
		@return: the map's background color
		"""
		return copy.copy(self.bgColor)

	def setBGColor(self, color):
		"""
		@type color: graphics.RGBA
		@param color: the new background color
		"""
		self.bgColor = color


class ParallaxLayer(object):
	"""
	Parallax layer for the background
	"""

	def __init__(self):
		# Name of the file for the parallax background
		self.fileName = None
		# True if the background should be vertically tiled
		self.vTile = False
		# True if the background should be horizontally tiled
		self.hTile = False
		# True if the background should scroll vertically
		self.vScroll = False
		# True if the background should scroll horizontally
		self.hScroll = False
		# Rate at which the background scrolls vertically
		self.vScrollSpeed = 1.0
		# Rate at which the background scrolls horizontally
		self.hScrollSpeed = 1.0
		# Layer visibilty - can be turned off
		self.visible = True
