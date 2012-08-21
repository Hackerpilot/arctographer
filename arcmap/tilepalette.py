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
This module contains classes that allow the user to select tiles from tile sets
"""

__docformat__ = "epytext"

import logging
import os

import gtk
import cairo

import mapcontroller
import tilegrid
import editortools
import graphics

class PaletteManager(mapcontroller.MapListener):
	"""
	Manages TilePalette instances.
	Outside code should use the widget returned from getWidget
	"""

	def __init__(self, controller):
		"""
		@type controller: MapController
		@param controller: the map controller
		"""
		mapcontroller.MapListener.__init__(self, controller)

		# Palettes are displayed in a notebook
		self.tileNotebook = gtk.Notebook()
		self.tileNotebook.set_scrollable(True)

		# Keep references to these around so that they can have the grid toggled
		self.__palettes = []

		# Code for allowing new tile sets to be opened
		# This is an open button that goes in the rightmost tab of the notebook
		self.openButton = gtk.Button()
		self.openButton.set_image(gtk.image_new_from_stock(gtk.STOCK_OPEN,
			gtk.ICON_SIZE_MENU))
		self.openButton.set_relief(gtk.RELIEF_NONE)
		self.openButton.connect("clicked", self.tilePalleteOpen)
		self.openButton.set_sensitive(False)

		# Create an empty scrolled window as a placeholder for the open button
		# tab. TODO: think of a better widget for this?
		scrolledWindow = gtk.ScrolledWindow()
		scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.tileNotebook.append_page(scrolledWindow, self.openButton)

	def listenFileOpened(self):
		"""
		Gets the PaletteManager ready for use. This is called when a file
		is opened
		sel = the selection to use
		"""
		self.openButton.set_sensitive(True)

	def listenFileClosed(self):
		"""
		The inverse of initialize. This is called when the map file is closed.
		"""
		self.openButton.set_sensitive(False)
		self.closeAll()

	def listenAddTileSet(self, fileName):
		self.addTileSet(fileName)

	def getWidget(self):
		"""
		@rtype: gtk.Widget
		@return: Return the widget that should be added to the toplevel window
		"""
		self.tileNotebook.show_all()
		return self.tileNotebook

	def toggleGrid(self):
		for palette in self.__palettes:
			palette.toggleGrid()

	def closeTilePalette(self, widget, tilePalette):
		""" Closes a tab in the notebook """
		index = self.tileNotebook.page_num(tilePalette)
		self.tileNotebook.remove_page(index)

	def tilePalleteOpen(self, widget):
		""" This is called when self.openButton is clicked """
		#~ Create the dialog
		dialog = gtk.FileChooserDialog("Open Tileset",
			self.tileNotebook.get_toplevel(), gtk.FILE_CHOOSER_ACTION_OPEN,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
			gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))

		# Only allow images to be opened
		# These should be installed...
		# TODO: Query GDK for this?
		filter = graphics.getFileFilter()
		dialog.add_filter(filter)

		response = dialog.run()
		if response == gtk.RESPONSE_ACCEPT:
			self.addTileSet(dialog.get_filename())
		dialog.destroy()

	def closeAll(self):
		"""Closes all the palettes """
		# Except for page 0, that has the open button on it.
		for i in range(self.tileNotebook.get_n_pages() - 1):
			self.tileNotebook.remove_page(i)
		self.__palettes = []

	def addTileSet(self, fileName = None):
		""" Opens the file specified in fileName in a TilePalette """
		# Add the label and close buttons to the tab
		tabCloseButton = gtk.Button()
		tabCloseButton.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE,
			gtk.ICON_SIZE_MENU))
		tabCloseButton.set_relief(gtk.RELIEF_NONE)
		tabLabel = gtk.Label(os.path.basename(fileName)[0:6] + "..." )
		tabBox = gtk.HBox()
		tabBox.pack_start(tabLabel)
		tabBox.pack_end(tabCloseButton)
		tabBox.show_all()
		# Create the tile palette and add it to a scrolled window
		palette = TilePalette(self.getController(), fileName)
		self.__palettes.append(palette)
		scrolledWindow = gtk.ScrolledWindow(None, None)
		scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolledWindow.add_with_viewport(palette.getWidget())
		self.tileNotebook.prepend_page(scrolledWindow, tabBox)
		tabCloseButton.connect("clicked", self.closeTilePalette,
			scrolledWindow)
		self.tileNotebook.show_all()
		# Show the newly-opened file
		self.tileNotebook.set_current_page(0)


class TilePalette(tilegrid.TileGrid, mapcontroller.MapListener):
	"""
	Class for allowing images to be used as tile sets. Handles selection
	and other related tasks
	"""

	def __init__(self, controller, fileName):
		"""
		@type fileName: str
		@param fileName: the name of the file to open
		"""
		mapcontroller.MapListener.__init__(self, controller)
		self.index = controller.openTileSet(fileName)
		surface = self.getController().getTilesetSurface(self.index)
		width = surface.get_width()
		height = surface.get_height()

		ts = controller.mapTileSize()

		tilegrid.TileGrid.__init__(self, width, height, ts)
		self.toggleGrid()

		self.addTool(editortools.TileSelectTool(controller, self.index,
			width, height), 0)

		self.fileName = fileName
		self.showGrid = True
		self.setSize(width, height)
		self.queue_draw()

	def specialRedraw(self, context, ex, ey, ew, eh):
		""" See TileGrid.specialRedraw """
		surface = self.getController().getTilesetSurface(self.index)
		context.rectangle(0, 0, surface.get_width(), surface.get_height())
		context.set_source(self.checkerPattern)
		context.fill()
		context.set_source_surface(surface, 0, 0)
		context.paint()
		if self.showGrid:
			context.save()
			context.rectangle(0, 0, surface.get_width(), surface.get_height())
			context.clip()
			graphics.drawGrid(context, self.getController().mapTileSize(),
				surface.get_width(), surface.get_height())
