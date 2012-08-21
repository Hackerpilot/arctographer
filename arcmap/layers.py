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
Module for managing the map's layers
"""

__docformat__ = "epytext"

import logging

import gtk

import mapcontroller
import undo

log = logging.getLogger("layers")


class LayerView(mapcontroller.MapListener):
	def __init__(self, controller):
		"""
		@type controller: MapController
		@param controller: the map controller
		"""
		mapcontroller.MapListener.__init__(self, controller)

		self.treeModel = gtk.ListStore(str, bool)

		self.treeView = gtk.TreeView(self.treeModel)
		self.treeView.set_headers_visible(True)
		self.treeView.columns_autosize()

		textRenderCell = gtk.CellRendererText()
		textRenderCell.set_property("editable", True)
		textRenderCell.connect("edited", self.layerNameCB, self.treeModel)

		toggleRenderCell = gtk.CellRendererToggle()
		toggleRenderCell.set_property("activatable", True)
		toggleRenderCell.connect("toggled", self.toggleCB, self.treeModel)

		selection = self.treeView.get_selection()
		selection.connect("changed", self.layerSelectCB)

		column0 = gtk.TreeViewColumn("Layer", textRenderCell, text=0)
		column1 = gtk.TreeViewColumn("Visible", toggleRenderCell)
		column1.add_attribute(toggleRenderCell, "active", True)

		self.treeView.append_column(column1)
		self.treeView.append_column(column0)

		self.scrolledWindow = gtk.ScrolledWindow()
		self.scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.scrolledWindow.add(self.treeView)

		# Prevent the LayerView from responding to callbacks caused by its own
		# actions
		self.__locked = False

	def comIndex(self, index):
		"""
		Converts from a tree model index to a map index, and vice-versa
		@type index: int
		@param index: an index
		@rtype: int
		@return: an index in the form other than what was passed in
		"""
		return len(self.treeModel) - index - 1

	def getWidget(self):
		return self.scrolledWindow

	def getCurrent(self):
		"""
		@rtype: gtk.TreeIter
		@return: an iterator associated with the currently selected layer
		"""
		selection = self.treeView.get_selection()
		if selection is not None:
			return selection.get_selected()[1]
		else:
			return None

	def addLayer(self, layerName = "New Layer"):
		"""
		Adds a new layer to the map
		@type layerName: string
		@param layerName: the name for the new layer
		"""
		self.__locked = True
		self.treeModel.prepend((layerName, True))
		action = undo.LayerAddAction(self.getController(), layerName)
		self.getController().addUndoAction(action)
		layerName = "New Layer"
		self.__locked = False

	# Any appearance of magic in the get_path, get_iter and the random array
	# indicies on them is purely coincidental. Honest.

	def removeLayer(self):
		"""
		Removes the currently selected layer
		"""
		iter = self.getCurrent()
		if iter is None:
			return
		self.__locked = True
		# Remove the current layer
		index = self.treeModel.get_path(iter)[0]
		action = undo.LayerRemoveAction(self.getController(),
			self.comIndex(index))
		self.getController().addUndoAction(action)
		self.treeModel.remove(iter)
		self.__locked = False

	def raiseLayer(self):
		"""
		Raises the currently selected layer
		"""
		cIter = self.getCurrent()
		if cIter is None or int(self.treeModel.get_path(cIter)[0]) == 0:
			return
		else:
			current = self.treeModel.get_path(cIter)[0]
			pIter = self.treeModel.get_iter(int(current) - 1)
			previous = self.treeModel.get_path(pIter)[0]
			self.treeModel.swap(cIter, pIter)
			self.getController().swapLayers(self.comIndex(int(current)),
				self.comIndex(int(previous)))

	def lowerLayer(self):
		"""
		Lowers the currently selected layer
		"""
		iter = self.getCurrent()
		if iter is None:
			return
		else:
			next = self.treeModel.iter_next(iter)
			if next is not None:
				index = self.treeModel.get_path(iter)[0]
				nextIndex = self.treeModel.get_path(next)[0]
				self.treeModel.swap(iter, next)
				self.getController().swapLayers(self.comIndex(index),
					self.comIndex(int(nextIndex)))

	def layerNameCB(self, cell, path, newText, model):
		"""
		Callback for a change in the layer name text
		"""
		p = int(path)
		model[p][0] = newText
		self.getController().setLayerName(self.comIndex(p), newText)

	def toggleCB(self, cell, path, model):
		"""
		Callback for a change in a layer visibility
		"""
		p = int(path)
		model[p][1] = not model[p][1]
		self.getController().setMapLayerVisibility(self.comIndex(p),
			model[p][1])

	def layerSelectCB(self, treeSelection):
		iter = self.getCurrent()
		if iter is not None:
			index = int(self.treeModel.get_path(iter)[0])
			self.getController().selectLayer(self.comIndex(index))

	############################################################################
	# MapListener code
	############################################################################

	def listenFileOpened(self):
		self.treeView.set_sensitive(True)
		for i in self.getController().getLayerInfo():
			self.treeModel.prepend(i)
		self.treeView.get_selection().select_path(0)

	def listenFileClosed(self):
		self.treeView.set_sensitive(False)
		self.treeModel.clear()

	def listenAddLayer(self, layerName):
		if self.__locked == False:
			self.treeModel.prepend((layerName, True))

	def listenRemoveLayer(self, index):
		if self.__locked == False:
			ci = self.comIndex(index)
			self.treeModel.remove(self.treeModel.get_iter(ci))

	############################################################################
	# End MapListener code
	############################################################################
