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
Contains code for the toplevel window
"""


import gtk
import os
import logging
import sys

import preferences
import mapcontroller
import editortools
import tilepalette
import mapgrid
import layers
import dialogs
import datafiles
import undo

programName = "Arctographer"

uiString = """
<ui>
	<menubar name="MenuBar">
		<menu action="File">
			<menuitem action="New"/>
			<menuitem action="Open"/>
			<separator/>
			<menuitem action="Save"/>
			<menuitem action="SaveAs"/>
			<separator/>
			<menuitem action="Properties"/>
			<separator/>
			<menuitem action="Close"/>
			<menuitem action="Quit"/>
		</menu>
		<menu action="Edit">
			<menuitem action="Undo"/>
			<menuitem action="Redo"/>
			<separator/>
			<menuitem action="Resize"/>
			<menuitem action="Background"/>
			<separator/>
			<menuitem action="Preferences"/>
		</menu>
		<menu action="View">
			<menuitem action="ToggleToolbar"/>
			<separator/>
			<menuitem action="ToggleGridMap"/>
			<menuitem action="ToggleGridPalette"/>
			<separator/>
			<menuitem action="ZoomIn"/>
			<menuitem action="ZoomOut"/>
			<menuitem action="ZoomNormal"/>
		</menu>
		<menu action="Help">
			<menuitem action="About"/>
		</menu>
	</menubar>
	<toolbar name="MapTools">
		<toolitem action="TileDraw"/>
		<toolitem action="TileDelete"/>
		<separator/>
		<toolitem action="PhysicsSelect"/>
		<toolitem action="PolygonDraw"/>
		<toolitem action="CircleDraw"/>
	</toolbar>
	<toolbar name="Layers">
		<toolitem action="addLayer"/>
		<toolitem action="removeLayer"/>
		<toolitem action="raiseLayer"/>
		<toolitem action="lowerLayer"/>
	</toolbar>
	<toolbar name="MainBar">
		<toolitem action="New"/>
		<toolitem action="Open"/>
		<toolitem action="Save"/>
		<toolitem action="SaveAs"/>
		<separator/>
		<toolitem action="ZoomIn"/>
		<toolitem action="ZoomOut"/>
		<toolitem action="ZoomNormal"/>
		<separator/>
		<toolitem action="Undo"/>
		<toolitem action="Redo"/>
	</toolbar>
</ui>
"""


class MainWindow(mapcontroller.MapListener):
	""" Toplevel window for the map editor """
	def __init__(self, fileName = None):
		"""
		@type fileName: str
		@param fileName: the name of the file to try to open the program with
		"""
		controller = mapcontroller.MapController()
		mapcontroller.MapListener.__init__(self, controller)
		self.mapGrid = None
		self.__createGUI()

		failureReason = controller.open(fileName)
		if failureReason is not None and fileName is not None:
			dialog = gtk.MessageDialog(self.window,
				gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
				gtk.MESSAGE_ERROR,
				gtk.BUTTONS_OK,
				"Error opening the file %s:" % fileName)
			dialog.format_secondary_markup(failureReason)
			dialog.run()
			dialog.destroy()
		controller.setToplevel(self.window)
		fileName = None

	def __createGUI(self):
		"""
		Assembles the widgets together onto the window
		"""
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title(programName)
		self.window.connect("destroy", self.destroy)
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("key-press-event", self.keyPress)

		self.uimanager = gtk.UIManager()
		accelGroup = self.uimanager.get_accel_group()
		self.window.add_accel_group(accelGroup)
		actionGroup = gtk.ActionGroup("ActionGroup")

		self.paletteManager = None

		# File menu
		actionGroup.add_actions([
			("New", gtk.STOCK_NEW, "_New", "<Control>N",
				"Create a new file", self.file_new),
			("Open", gtk.STOCK_OPEN, "_Open", "<Control>O", "Open a saved map",
				self.file_open),
			("Save", gtk.STOCK_SAVE, "_Save", "<Control>S",
				"Save the current file", self.file_save),
			("SaveAs", gtk.STOCK_SAVE_AS, "Save _As...", "<Control><Shift>S",
				"Save the current file under a different name",
				self.file_saveAs),
			("Properties", gtk.STOCK_PROPERTIES, "Properties", "<Alt>Return",
				"Modify the properties of the map", self.file_properties),
			("Close", gtk.STOCK_CLOSE, "_Close", "<Control>W",
				"Close the current file", self.file_close),
			("Quit", gtk.STOCK_QUIT, "_Quit", "<Control>Q", "Quit the program",
				self.file_quit),
			("File", None, "_File"),
			("Edit", None, "_Edit"),
			("View", None, "_View"),
			("Help", None, "_Help"),
		])

		# Edit menu
		actionGroup.add_actions([
			("Resize", None, "R_esize", None, "Resize the map",
				self.edit_resize),
			("Preferences", gtk.STOCK_PREFERENCES, "_Preferences", None,
				"Application Preferences", self.edit_preferences),
			("Undo", gtk.STOCK_UNDO, "_Undo", "<Control>Z",
				"Undo the last change", self.edit_undo),
			("Redo", gtk.STOCK_REDO, "_Redo", "<Control>Y",
				"Redo the last change", self.edit_redo),
			("Background", None, "_Background", "<Control>B",
				"Change background information for the map",
				self.edit_background)
		])

		# View menu
		actionGroup.add_actions([
			("ZoomIn", gtk.STOCK_ZOOM_IN, "Zoom _In", None, "Zoom In",
				self.view_zoomIn),
			("ZoomOut", gtk.STOCK_ZOOM_OUT, "Zoom _Out", None, "Zoom Out",
				self.view_zoomOut),
			("ZoomNormal", gtk.STOCK_ZOOM_100, "_Normal Size", "<Control>0",
				"Normal Size", self.view_zoomNormal)
		])

		# Help menu
		actionGroup.add_actions([("About", gtk.STOCK_ABOUT, "_About", None,
			"Information about the program.", self.help_about)])

		# Layer view
		actionGroup.add_actions([
			("addLayer", gtk.STOCK_NEW, None, None,
				"Add a new layer to the map", self.addLayer),
			("removeLayer", gtk.STOCK_DELETE, None, None,
				"Remove the current layer from the map", self.removeLayer),
			("raiseLayer", gtk.STOCK_GO_UP, None, None,
				"Raise the current layer", self.raiseLayer),
			("lowerLayer", gtk.STOCK_GO_DOWN, None, None,
				"Lower the current layer", self.lowerLayer)
		])
		actionGroup.add_toggle_actions([
			("ToggleGridMap", None, "Show Grid on _Map", "<Control>G",
				"Show a grid overlaid on the map", self.view_toggleGridMap),
			("ToggleGridPalette", None, "Show Grid on _Palette",
				"<Control><Shift>G", "Show a grid overlaid on the tile palette",
				self.view_toggleGridPalette),
			("ToggleToolbar", None, "Show _Toolbar", None, "Show the toolbar",
				self.view_toggleToolbar)
		])

		# Side toolbar
		actionGroup.add_radio_actions([
			("TileDraw", None, None, "<Control>T", "Draw tiles on the map",
				editortools.TILE_DRAW_ID),
			("TileDelete", None, None, "<Contorol><Shift>T", "Remove tiles "+
				"from the map", editortools.TILE_DELETE_ID),
			("PhysicsSelect", None, None, "<Control>P",
				"Select and edit shapes", editortools.PHYSICS_SELECT_ID),
			("PolygonDraw", None, None, "<Control>P", "Draw polygons"
				+ " on the map",  editortools.POLYGON_DRAW_ID),
			("CircleDraw", None, None, "<Control>C", "Draw circles"
				+ " on the map", editortools.CIRCLE_DRAW_ID),
			("LightDraw", None, None, None, "Place lights on the map",
				editortools.LIGHT_DRAW_ID)
			], editortools.TILE_DRAW_ID, self.toolSelect)

		self.uimanager.insert_action_group(actionGroup, 0)
		self.uimanager.add_ui_from_string(uiString)
		self.widgets = [
			"/MenuBar/File/Properties", "/MenuBar/File/Save",
			"/MenuBar/File/SaveAs",	"/MenuBar/File/Close",
			"/MenuBar/Edit/Undo",
			"/MenuBar/Edit/Redo", "/MenuBar/Edit/Resize",
			"/MenuBar/Edit/Background",
			"/MenuBar/View/ToggleGridMap", "/MenuBar/View/ToggleGridPalette",
			"/MenuBar/View/ZoomIn",
			"/MenuBar/View/ZoomOut", "/MenuBar/View/ZoomNormal",
			"/MainBar/Save", "/MainBar/SaveAs", "/MainBar/ZoomIn",
			"/MainBar/ZoomOut", "/MainBar/ZoomNormal", "/MainBar/Undo",
			"/MainBar/Redo", "/MapTools", "/Layers"
		]

		# Set the check box correctly
		self.uimanager.get_widget("/MenuBar/View/ToggleToolbar").set_active(True)
		self.uimanager.get_widget("/MenuBar/View/ToggleGridPalette").set_active(True)

		vbox = gtk.VBox(False, 0)
		self.window.add(vbox)

		vPaned = gtk.VPaned()
		self.paletteManager = tilepalette.PaletteManager(self.getController())
		vPaned.pack1(self.paletteManager.getWidget(), True, False)
		vPaned.pack2(self.createTreeView(), True, False)
		vPaned.set_size_request(200, -1)

		self.mapBox = gtk.HBox(False, 0)
		self.mapBox.pack_start(self.__createToolbar(), False, False, 0)

		hpaned = gtk.HPaned()
		hpaned.pack1(self.mapBox, True, False)
		hpaned.pack2(vPaned, False, False)

		vbox.pack_start(self.uimanager.get_widget("/MenuBar"), False, False, 0)
		vbox.pack_start(self.uimanager.get_widget("/MainBar"), False, False, 0)

		self.statusBar = gtk.Statusbar()
		id = self.statusBar.get_context_id("Main Window")
		self.statusBar.push(id, "Open an existing file (Control+O) or create a new one (Control+N)")
		vbox.pack_end(self.statusBar, False, False, 0)
		vbox.pack_end(hpaned, True, True, 2)

		self.__setWidgetsInsensitive()

		self.window.set_size_request(900, 540)
		self.setTitle()
		self.window.show_all()

	def setTitle(self):
		"""
		Sets the window title.
		"""
		name = self.getController().getFileName()
		titleString = ""
		if self.getController().unsaved():
				titleString = titleString + "*"
		if name is None:
			# Split to allow for translation later...
			titleString = titleString + "Unsaved Map"
		else:
			titleString = titleString + os.path.basename(name)
		self.window.set_title(titleString)

	def __createToolbar(self):
		"""
		Creates the toolbar on the left of the screen that holds the tools
		defined in editortools
		"""
		bar = self.uimanager.get_widget("/MapTools")
		bar.set_border_width(0)
		bar.set_orientation(gtk.ORIENTATION_VERTICAL)

		tileButton = self.uimanager.get_widget("/MapTools/TileDraw")
		tileImage = gtk.image_new_from_file(datafiles.getIconPath(
			"tileDraw.png"))
		tileImage.show()
		tileButton.set_icon_widget(tileImage)

		deleteButton = self.uimanager.get_widget("/MapTools/TileDelete")
		deleteImage = gtk.image_new_from_file(datafiles.getIconPath(
			"tileDelete.png"))
		deleteImage.show()
		deleteButton.set_icon_widget(deleteImage)

		selectButton = self.uimanager.get_widget("/MapTools/PhysicsSelect")
		selectImage = gtk.image_new_from_file(datafiles.getIconPath(
			"physicsSelect.png"))
		selectImage.show()
		selectButton.set_icon_widget(selectImage)

		staticButton = self.uimanager.get_widget("/MapTools/PolygonDraw")
		staticImage = gtk.image_new_from_file(datafiles.getIconPath(
			"staticPolyDraw.png"))
		staticImage.show()
		staticButton.set_icon_widget(staticImage)

		staticCButton = self.uimanager.get_widget("/MapTools/CircleDraw")
		staticCImage = gtk.image_new_from_file(datafiles.getIconPath(
			"staticCircleDraw.png"))
		staticCImage.show()
		staticCButton.set_icon_widget(staticCImage)

		bar.set_sensitive(False)
		return bar

	def createTreeView(self):
		"""
		Creates the tree view and its associated buttons
		"""
		self.layerView = layers.LayerView(self.getController())
		vBox = gtk.VBox()
		toolbar = self.uimanager.get_widget("/Layers")
		toolbar.set_sensitive(False)
		vBox.pack_end(toolbar, False, False)
		vBox.pack_start(self.layerView.getWidget(), True, True)
		return vBox

	def delete_event(self, widget, event, data = None):
		return (self.closeCheck() == False)

	def destroy(self, widget, data = None):
		gtk.main_quit()

	def file_new(self, widget, data = None):
		dialog = dialogs.NewDialog(self.window)
		response = dialog.run()
		dialog.destroy()
		if response == gtk.RESPONSE_ACCEPT:
			width = dialog.getWidth()
			height = dialog.getHeight()
			tileSize = dialog.getTileSize()
			self.getController().new(tileSize, width, height)

	def file_open(self, window, data = None):
		openDialog = gtk.FileChooserDialog("Open", self.window,
			gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL,
			gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
		filter = gtk.FileFilter()
		filter.add_pattern("application/json")
		filter.add_pattern("*.json")
		filter.set_name("JSON Files")
		openDialog.add_filter(filter)
		response = openDialog.run()
		if response == gtk.RESPONSE_ACCEPT:
			fileName = openDialog.get_filename()
			self.getController().open(fileName)
			self.setTitle()
		openDialog.destroy()

	def file_save(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		if self.getController().getFileName() is None:
			self.promptSave()
		else:
			self.getController().save()
		self.setTitle()

	def file_saveAs(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		self.promptSave()

	def file_properties(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		d = dialogs.PropertiesDialog(self.window, self.getController())
		response = d.run()
		if response != gtk.STOCK_CANCEL:
			self.getController().saveWorld = d.physicsCheck.get_active()
			self.getController().saveBackground = d.parallaxCheck.get_active()
		d.destroy()

	def promptSave(self):
		"""
		@rtype: bool
		@return: Returns True if the user saved, False otherwise
		"""
		saveDialog = gtk.FileChooserDialog("Save As", self.window,
			gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL,
			gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
		saveDialog.set_do_overwrite_confirmation(True)

		jsonFilter = gtk.FileFilter()
		jsonFilter.add_mime_type("application/json")
		jsonFilter.add_pattern("*.json")
		jsonFilter.set_name("JSON Files")

		saveDialog.add_filter(jsonFilter)
		response = saveDialog.run()
		if response == gtk.RESPONSE_ACCEPT:
			self.getController().setFileName(saveDialog.get_filename())
			self.getController().save()
			saveDialog.destroy()
			self.setTitle()
			return True
		else:
			saveDialog.destroy()
			return False

	def closeCheck(self):
		"""
		Checks to see if the user wants to quit and if he/she wants to save the
		changes to the map.
		@rtype: bool
		@return: False if the user hit "Cancel", True if the file should be
		    closed
		"""
		if self.getController().unsaved():
			response = dialogs.UnsavedDialog(self.window)
			if response == gtk.RESPONSE_CANCEL:
				# Cancel
				return False
			elif response == gtk.RESPONSE_ACCEPT:
				# Save first, then quit
				if self.getController().getFileName() is None:
					return self.promptSave()
				else:
					self.getController().save()
					return True
			elif response == gtk.RESPONSE_CLOSE:
				# Close without saving
				return True
		else:
			return True

	def file_quit(self, widget, data = None):
		if self.closeCheck():
			gtk.main_quit()

	def file_close(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		if self.closeCheck():
			self.getController().close()

	def edit_resize(self, window, data = None):
		controller = self.getController()
		if controller.hasMap() == False:
			return

		dialog = dialogs.ResizeDialog(self.window,
			controller.mapWidth(),
			controller.mapHeight(),
			controller.getThumbnail(96))
		response = dialog.run()
		if response == gtk.RESPONSE_ACCEPT:
			width = dialog.getWidth()
			height = dialog.getHeight()
			xOffset = dialog.getXOffset()
			yOffset = dialog.getYOffset()
			action = undo.ResizeAction(controller, width, height,
				xOffset, yOffset, controller.mapWidth(),
				controller.mapHeight())
			controller.addUndoAction(action)
			controller.resize(width, height, xOffset, yOffset)

		dialog.destroy()

	def edit_undo(self, window, data = None):
		controller = self.getController()
		if controller.hasMap() == False:
			return
		controller.undo()

	def edit_redo(self, window, data = None):
		controller = self.getController()
		if controller.hasMap() == False:
			return
		controller.redo()

	def edit_preferences(self, window, data = None):
		dialog = dialogs.PreferencesDialog(self.window)
		dialog.run()
		dialog.destroy()
		preferences.save()

	def edit_background(self, window, data = None):
		if self.getController().hasMap() == False:
			return

		d = dialogs.BackgroundDialog(self.window,
			self.getController().getParallaxes(),
			self.getController().getBGColor())
		result = d.run()
		if result == gtk.RESPONSE_ACCEPT:
			self.getController().setParallaxes(d.parallaxes)
			self.getController().setBGColor(d.bgColor)

		d.destroy()

	def view_toggleGridMap(self, widget, data = None):
		"""
		We installed this function so you could turn the grid on, and off.
		NOT SO YOU COULD HOLD GRIDSWITCH RAVES!
		"""
		if self.getController().hasMap() == False:
			return
		self.mapGrid.toggleGrid()

	def view_toggleGridPalette(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		if self.paletteManager is not None:
			self.paletteManager.toggleGrid()

	def view_toggleToolbar(self, widget, data = None):
		toolbar = self.uimanager.get_widget("/MainBar")
		if widget.get_active():
			toolbar.show()
		else:
			toolbar.hide()
		pass

	def view_zoomIn(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		self.mapGrid.zoomIn()
		self.setTitle()

	def view_zoomOut(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		self.mapGrid.zoomOut()
		self.setTitle()

	def view_zoomNormal(self, widget, data = None):
		if self.getController().hasMap() == False:
			return
		self.mapGrid.zoomNormal()
		self.setTitle()

	def help_about(self, window, data = None):
		"""
		The answer to the age-old question "Who's responsible for this mess?"
		"""
		dialog = gtk.AboutDialog()
		dialog.set_license("""
MapEditor is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MapEditor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with """ + programName + ". If not, see <http://www.gnu.org/licenses/>.")
		dialog.set_authors(["Brian Schott (Sir Alaran)"])
		dialog.set_documenters(["Brian Schott (Sir Alaran)"])
		dialog.set_website("http://www.hackerpilot.org/map_editor.php")
		dialog.set_program_name(programName)
		dialog.set_version("0.3 Beta")
		dialog.run()
		dialog.destroy()

	def toolSelect(self, action, ignored):
		""" Handles tool selection on the map toolbar """
		self.mapGrid.toolSelect(action.get_current_value())

	def addLayer(self, window, data = None):
		""" Adds a layer to the map """
		self.layerView.addLayer()

	def removeLayer(self, window, data = None):
		""" Removes a layer from the map """
		self.layerView.removeLayer()

	def raiseLayer(self, window, data = None):
		""" Raises the currently selected layer in the map """
		self.layerView.raiseLayer()

	def lowerLayer(self, window, data = None):
		""" Lowers the currently selected layer in the map """
		self.layerView.lowerLayer()

	def keyPress(self, window, event):
		if self.mapGrid is not None:
			self.mapGrid.keyPress(window, event)

	def listenModified(self, modified):
		self.setTitle()

	def __setWidgetsInsensitive(self):
		for w in self.widgets:
			self.uimanager.get_widget(w).set_sensitive(False)

	def listenFileClosed(self):
		self.__setWidgetsInsensitive()
		self.setTitle()
		self.mapBox.remove(self.mapGrid.getWidget())
		self.setTitle()

	def listenFileOpened(self):
		# Activate the widgets
		for w in self.widgets:
			self.uimanager.get_widget(w).set_sensitive(True)

		# Deactivate the Undo/Redo buttons until something is actually undone
		self.uimanager.get_action("/MenuBar/Edit/Undo").set_sensitive(
			False)
		self.uimanager.get_action("/MenuBar/Edit/Redo").set_sensitive(
			False)

		self.mapGrid = mapgrid.MapGrid(self.getController(), self.statusBar)
		self.mapBox.pack_end(self.mapGrid.getWidget())
		self.setTitle()

	def listenUndoRedo(self):
		self.uimanager.get_action("/MenuBar/Edit/Undo").set_sensitive(
			undo.canUndo())
		self.uimanager.get_action("/MenuBar/Edit/Redo").set_sensitive(
			undo.canRedo())
