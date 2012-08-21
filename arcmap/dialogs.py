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
Define custom dialogs here to avoid cluttering up the rest of the code
"""

import os

import gtk
import cairo

import preferences
import visualwidget
import resizewidget
import parallax
import graphics
import tilemap
import datafiles
import background

class HIGTableBuilder(object):
	"""Builds table layouts for HIG-compliant dialogs"""
	def __init__(self):
		self.cols = 3
		self.row = 1
		self.table = gtk.Table(self.row, self.cols, False)
		self.table.set_col_spacing(0, 12)
		self.table.set_border_width(12)

	def updateSize(self):
		self.row = self.row + 1;
		self.table.resize(self.row, self.cols)

	def addSectionHeader(self, labelText):
		self.updateSize()
		label = gtk.Label("<b>" + labelText + "</b>")
		label.set_use_markup(True)
		label.set_alignment(0, 0.5)
		self.table.attach(label, 0, 2, self.row - 1, self.row)

	def addWidget(self, widget):
		self.updateSize()
		self.table.attach(widget, 1, 3, self.row - 1, self.row, xpadding=6,
			ypadding=6)

	def addLabeledWidget(self, labelText, widget):
		self.updateSize()
		label = gtk.Label(labelText)
		label.set_use_underline(True)
		label.set_mnemonic_widget(widget)
		label.set_alignment(0, 0.5)
		self.table.attach(label, 1, 2, self.row - 1, self.row, xpadding=6,
			ypadding=6)
		self.table.attach(widget, 2, 3, self.row - 1, self.row, xpadding=6,
			ypadding=6)
		widget.connect("state-changed", self.__stateChangedCB, label)

	def __stateChangedCB(self, widget, state, label):
		# This is here so that the label will become insensitive if the
		# widget is set to be insensitive
		label.set_sensitive(widget.get_property("sensitive"))

	def getTable(self):
		return self.table


def UnsavedDialog(window, hasFileName = True):
	dialog = gtk.Dialog("", window, gtk.DIALOG_MODAL |
		gtk.DIALOG_DESTROY_WITH_PARENT, None)
	dialog.add_button("Close _Without Saving", gtk.RESPONSE_CLOSE)
	dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
	dialog.set_border_width(6)
	dialog.set_has_separator(False)
	dialog.set_resizable(False)
	dialog.vbox.set_spacing(12)
	dialog.vbox.set_border_width(6)
	hbox = gtk.HBox()
	hbox.set_spacing(12)
	hbox.set_border_width(6)
	image = gtk.Image()
	image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
	hbox.pack_start(image, False, False, 0)
	hbox.pack_end(gtk.Label("Save the changes to the map before closing?"))
	dialog.vbox.pack_start(hbox, False, False, 0)
	dialog.show_all()
	if hasFileName == True:
		dialog.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT)
	else:
		dialog.add_button(gtk.STOCK_SAVE_AS, gtk.RESPONSE_ACCEPT)

	response = dialog.run()
	dialog.destroy()
	return response


class PropertiesDialog(gtk.Dialog):
	""" Dialog for File->Properties """

	def __init__(self, parent, controller):
		"""
		parent = the dialog's parent window
		map = the map whose properties will be displayed
		"""
		gtk.Dialog.__init__(self, "", parent,
			gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_CANCEL,
			gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

		self.notebook = gtk.Notebook()

		self.createGeneralTab(controller)
		self.createSaveTab()

		self.vbox.add(self.notebook)
		self.show_all()

	def createGeneralTab(self, controller):
		builder = HIGTableBuilder()
		builder.addSectionHeader("Level Information")
		self.width = gtk.Label(controller.mapWidth())
		builder.addLabeledWidget("Width:", self.width)
		self.height = gtk.Label(controller.mapHeight())
		builder.addLabeledWidget("Height:", self.height)
		self.layers = gtk.Label(controller.getNumLayers())
		builder.addLabeledWidget("Layers:", self.layers)
		self.notebook.append_page(builder.table, gtk.Label("General"))

	def createSaveTab(self):
		builder = HIGTableBuilder()
		builder.addSectionHeader("File save options")
		self.parallaxCheck = gtk.CheckButton("Export _Backgrounds", True)
		self.parallaxCheck.set_active(True)
		builder.addWidget(self.parallaxCheck)
		self.physicsCheck = gtk.CheckButton("Export p_hysics information", True)
		self.physicsCheck.set_active(True)
		builder.addWidget(self.physicsCheck)
		self.notebook.append_page(builder.table, gtk.Label("Save"))


class StaticShapePropertiesDialog(gtk.Dialog):
	def __init__(self, parent, shape):
		gtk.Dialog.__init__(self, "Shape Properties", parent,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY,
			gtk.RESPONSE_ACCEPT))

		builder = HIGTableBuilder()

		builder.addSectionHeader("Physics")

		frictionAdjustment = gtk.Adjustment(shape.friction, 0.0, 1.0, 0.1)
		self.frictionSpin = gtk.SpinButton(frictionAdjustment, 1.0, 4)
		builder.addLabeledWidget("Coefficient of _Friction:", self.frictionSpin)

		restitutionAdjustment = gtk.Adjustment(shape.restitution, 0.0, 20.0, 0.1)
		self.restitutionSpin = gtk.SpinButton(restitutionAdjustment, 1.0, 4)
		builder.addLabeledWidget("Coefficient of _Restitution:",
			self.restitutionSpin)

		builder.addSectionHeader("Damage")

		damageAdjustment = gtk.Adjustment(shape.damage, 0.0, 32000.0, 1.0)
		self.damageSpin = gtk.SpinButton(damageAdjustment, 1.0, 4)
		builder.addLabeledWidget("_Damage per second:", self.damageSpin)

		self.vbox.pack_start(builder.getTable(), True, False, 0)
		self.vbox.show_all()
		self.set_resizable(False)
		self.set_default_response(gtk.RESPONSE_ACCEPT)

	def getFriction(self):
		return self.frictionSpin.get_value()

	def getRestitution(self):
		return self.restitutionSpin.get_value()

	def getDamage(self):
		return self.damageSpin.get_value()


class NewDialog(gtk.Dialog):
	""" Dialog for File->New """
	def __init__(self, parent):
		"""	parent = the dialog's parent window """
		gtk.Dialog.__init__(self, "New Map", parent,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK,
			gtk.RESPONSE_ACCEPT))

		builder = HIGTableBuilder()

		widthAdjustment = gtk.Adjustment(20, 1, 65535, 1, 10, 0)
		self.widthSpinButton = gtk.SpinButton(widthAdjustment, 1.0, 0)
		self.widthSpinButton.set_snap_to_ticks(True)
		self.widthSpinButton.set_numeric(True)
		self.widthSpinButton.set_alignment(1.0)
		builder.addLabeledWidget("_Width:", self.widthSpinButton)

		heightAdjustment = gtk.Adjustment(15, 1, 65535, 1, 10, 0)
		self.heightSpinButton = gtk.SpinButton(heightAdjustment, 1.0, 0)
		self.heightSpinButton.set_snap_to_ticks(True)
		self.heightSpinButton.set_numeric(True)
		self.heightSpinButton.set_alignment(1.0)
		builder.addLabeledWidget("_Height:", self.heightSpinButton)

		tileAdjustment = gtk.Adjustment(32, 10, 128, 1, 1, 0)
		self.tileSpinButton = gtk.SpinButton(tileAdjustment, 1.0, 0)
		self.tileSpinButton.set_snap_to_ticks(True)
		self.tileSpinButton.set_numeric(True)
		self.tileSpinButton.set_alignment(1.0)
		builder.addLabeledWidget("_Tile Size:", self.tileSpinButton)

		self.vbox.add(builder.getTable())
		self.vbox.show_all()
		self.set_resizable(False)
		self.set_default_response(gtk.RESPONSE_ACCEPT)

	def getWidth(self):
		return self.widthSpinButton.get_value_as_int()

	def getHeight(self):
		return self.heightSpinButton.get_value_as_int()

	def getTileSize(self):
		return self.tileSpinButton.get_value_as_int()


class ResizeDialog(gtk.Dialog):
	""" Dialog for resizing the map """
	def __init__(self, parent, currentWidth, currentHeight, thumbnail):
		gtk.Dialog.__init__(self, "Resize Map", parent,
			gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY,
			gtk.RESPONSE_ACCEPT))

		# This needs to be here so that the gtk.gdk.Window is valid for the
		# thumbnail code below
		self.show_all()

		builder = HIGTableBuilder()

		builder.addSectionHeader("Dimentions")
		builder.addLabeledWidget("Current Width:",
			gtk.Label(str(currentWidth)))
		builder.addLabeledWidget("Current Height:",
			gtk.Label(str(currentHeight)))

		self.currentWidth = currentWidth
		self.currentHeight = currentHeight
		self.newWidthLabel = gtk.Label(str(currentWidth))
		builder.addLabeledWidget("New Width:", self.newWidthLabel)
		self.newHeightLabel = gtk.Label(str(currentHeight))
		builder.addLabeledWidget("New Height:", self.newHeightLabel)

		builder.addSectionHeader("Adjustment")
		negLabel = gtk.Label("Negative values will cause tiles to be\n"
			+"removed from the specified edge")
		negLabel.set_alignment(0.0, 0.0)
		builder.addWidget(negLabel)

		rightAdjustment = gtk.Adjustment(0, -(currentWidth - 1), 65535, 1, 10, 0)
		self.rightSpinButton = gtk.SpinButton(rightAdjustment, 1.0, 0)
		self.rightSpinButton.set_snap_to_ticks(True)
		self.rightSpinButton.set_numeric(True)
		self.rightSpinButton.set_alignment(1.0)
		self.rightSpinButton.connect("value-changed", self.rightChangedCB)

		leftAdjustment = gtk.Adjustment(0, -(currentWidth - 1), 65535, 1, 10, 0)
		self.leftSpinButton = gtk.SpinButton(leftAdjustment, 1.0, 0)
		self.leftSpinButton.set_snap_to_ticks(True)
		self.leftSpinButton.set_numeric(True)
		self.leftSpinButton.set_alignment(1.0)
		self.leftSpinButton.connect("value-changed", self.leftChangedCB)

		topAdjustment = gtk.Adjustment(0, -(currentHeight - 1), 65535, 1, 10, 0)
		self.topSpinButton = gtk.SpinButton(topAdjustment, 1.0, 0)
		self.topSpinButton.set_snap_to_ticks(True)
		self.topSpinButton.set_numeric(True)
		self.topSpinButton.set_alignment(1.0)
		self.topSpinButton.connect("value-changed", self.topChangedCB)

		bottomAdjustment = gtk.Adjustment(0, -(currentHeight - 1), 65535, 1, 10, 0)
		self.bottomSpinButton = gtk.SpinButton(bottomAdjustment, 1.0, 0)
		self.bottomSpinButton.set_snap_to_ticks(True)
		self.bottomSpinButton.set_numeric(True)
		self.bottomSpinButton.set_alignment(1.0)
		self.bottomSpinButton.connect("value-changed", self.bottomChangedCB)

		self.__r = resizewidget.ResizeView(currentWidth, currentHeight,
			thumbnail)

		# The boxes are here to force the cell allocated to the resize widget
		# to remain a certain width and height. They are invisible on the dialog
		# and serve no real purpose other than a hack.
		size = int(max(thumbnail.get_width(), thumbnail.get_height()))
		hBox = gtk.HBox()
		hBox.set_size_request(size, 1)
		vBox = gtk.VBox()
		vBox.set_size_request(1, size)

		table = gtk.Table(4, 4, False)
		table.attach(self.leftSpinButton, 0, 1, 1, 2, xpadding=6, ypadding=6)
		table.attach(self.rightSpinButton, 2, 3, 1, 2, xpadding=6, ypadding=6)
		table.attach(self.topSpinButton, 1, 2, 0, 1, xpadding=6, ypadding=6)
		table.attach(self.bottomSpinButton, 1, 2, 2, 3, xpadding=6, ypadding=6)
		table.attach(self.__r, 1, 2, 1, 2, xoptions=gtk.EXPAND,
			yoptions=gtk.EXPAND, xpadding=6, ypadding=6)
		table.attach(vBox, 3, 4, 1, 2, xpadding=0, ypadding=6)
		table.attach(hBox, 1, 2, 3, 4, xpadding=6, ypadding=0)
		builder.addWidget(table)

		self.vbox.add(builder.getTable())
		self.vbox.show_all()
		self.set_resizable(False)
		self.set_default_response(gtk.RESPONSE_ACCEPT)

	def leftChangedCB(self, widget):
		r = self.rightSpinButton.get_value_as_int()
		l = self.leftSpinButton.get_value_as_int()
		nw = r + l + self.currentWidth
		self.newWidthLabel.set_text(str(nw))
		self.rightSpinButton.get_adjustment().lower = -(self.currentWidth + l - 1)
		self.__r.setLeft(l)

	def rightChangedCB(self, widget):
		r = self.rightSpinButton.get_value_as_int()
		l = self.leftSpinButton.get_value_as_int()
		nw = r + l + self.currentWidth
		self.newWidthLabel.set_text(str(nw))
		self.leftSpinButton.get_adjustment().lower = -(self.currentWidth + r - 1)
		self.__r.setRight(r)

	def topChangedCB(self, widget):
		t = self.topSpinButton.get_value_as_int()
		b = self.bottomSpinButton.get_value_as_int()
		nh = t + b + self.currentHeight
		self.newHeightLabel.set_text(str(nh))
		self.bottomSpinButton.get_adjustment().lower = -(self.currentHeight + t - 1)
		self.__r.setTop(t)

	def bottomChangedCB(self, widget):
		t = self.topSpinButton.get_value_as_int()
		b = self.bottomSpinButton.get_value_as_int()
		nh = t + b + self.currentHeight
		self.newHeightLabel.set_text(str(nh))
		self.topSpinButton.get_adjustment().lower = -(self.currentWidth + b - 1)
		self.__r.setBottom(b)

	def getWidth(self):
		r = self.rightSpinButton.get_value_as_int()
		l = self.leftSpinButton.get_value_as_int()
		return r + l + self.currentWidth

	def getHeight(self):
		t = self.topSpinButton.get_value_as_int()
		b = self.bottomSpinButton.get_value_as_int()
		return t + b + self.currentHeight

	def getXOffset(self):
		return self.leftSpinButton.get_value_as_int()

	def getYOffset(self):
		return self.topSpinButton.get_value_as_int()


class BackgroundLayerDialog(gtk.Dialog):
	def __init__(self, parent, parallax):

		if parallax is not None:
			self.parallax = parallax
		else:
			self.parallax = background.ParallaxLayer()

		if self.parallax.fileName is None:
			fileName = "New Background"
		else:
			fileName = self.parallax.fileName

		gtk.Dialog.__init__(self, os.path.basename(fileName), parent,
			gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY,
			gtk.RESPONSE_ACCEPT))

		builder = HIGTableBuilder()

		builder.addSectionHeader("Appearance")

		fFilter = graphics.getFileFilter()
		self.fileChooser = gtk.FileChooserDialog("Choose Background Image",
			self, gtk.FILE_CHOOSER_ACTION_OPEN,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
			gtk.STOCK_OPEN, gtk.RESPONSE_ACCEPT))
		self.fileChooser.add_filter(fFilter)

		self.fileButton = gtk.FileChooserButton(self.fileChooser)
		if self.parallax.fileName is not None:
			self.fileChooser.set_filename(self.parallax.fileName)
		self.fileButton.set_width_chars(6)

		# Set the default directory of the file chooser based on the file prefix
		# setting from the preferences. This should save a few clicks.
		path = datafiles.getParallaxPath("")
		print path
		if path != "":
			print "set_current_folder"
			self.fileChooser.set_current_folder(path)

		builder.addLabeledWidget("_Image", self.fileButton)

		builder.addSectionHeader("Repeat")

		self.tileHorizontally = gtk.CheckButton("Repeat Horizontally", True)
		self.tileHorizontally.set_active(self.parallax.hTile)
		builder.addWidget(self.tileHorizontally)

		self.tileVertically = gtk.CheckButton("Repeat Vertically", True)
		self.tileVertically.set_active(self.parallax.vTile)
		builder.addWidget(self.tileVertically)

		builder.addSectionHeader("Scrolling")

		self.scrollHorizontally = gtk.CheckButton("Scroll Horizontally", True)
		self.scrollHorizontally.connect("toggled",
			self.scrollHorizontallyChanged)
		builder.addWidget(self.scrollHorizontally)

		self.scrollHorizontallySpeed = gtk.SpinButton(
			gtk.Adjustment(self.parallax.hScrollSpeed, 0, 20.0, 0.1, 1.0,
			0.0), 0.1, 2)
		builder.addLabeledWidget("Horizontal Scroll Speed",
			self.scrollHorizontallySpeed)

		self.scrollVertically = gtk.CheckButton("Scroll Vertically", True)
		self.scrollVertically.connect("toggled",
			self.scrollVerticallyChanged)
		builder.addWidget(self.scrollVertically)

		self.scrollVerticallySpeed = gtk.SpinButton(
			gtk.Adjustment(self.parallax.vScrollSpeed, 0, 20.0, 0.1, 1.0,
			0.0), 0.1, 2)
		builder.addLabeledWidget("Vertical Scroll Speed",
			self.scrollVerticallySpeed)


		self.scrollHorizontally.set_active(self.parallax.hScroll)
		self.scrollHorizontallySpeed.set_sensitive(self.parallax.hScroll)
		self.scrollVertically.set_active(self.parallax.vScroll)
		self.scrollVerticallySpeed.set_sensitive(self.parallax.vScroll)

		self.vbox.add(builder.getTable())
		self.show_all()
		self.set_resizable(False)

	def scrollHorizontallyChanged(self, button):
		self.scrollHorizontallySpeed.set_sensitive(button.get_active())

	def scrollVerticallyChanged(self, button):
		self.scrollVerticallySpeed.set_sensitive(button.get_active())

class BackgroundDialog(gtk.Dialog):
	def __init__(self, parent, parallaxes, bgColor):
		gtk.Dialog.__init__(self, "Backgrounds", parent,
			gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_APPLY,
			gtk.RESPONSE_ACCEPT))

		self.bgColor = bgColor
		self.parallaxes = parallaxes

		# Default width and height.
		# TODO: tweak this so that it works on the netbook
		previewWidth = 1024
		previewHeight = 768
		previewScale = 1.0

		# Left side of dialog: contains the preview and sliders
		vs = gtk.VScale(gtk.Adjustment(0, -2000, 2000, 1, 10, 10))
		vs.set_digits(0)
		vs.set_draw_value(False)
		hs = gtk.HScale(gtk.Adjustment(0, -5000, 5000, 1, 10, 10))
		hs.set_draw_value(False)
		hs.set_digits(0)
		t = gtk.Table(2, 2)
		self.__preview = parallax.ParallaxViewer(previewWidth, previewHeight,
			previewScale)
		vs.connect("value-changed", self.previewYChanged)
		hs.connect("value-changed", self.previewXChanged)
		t.attach(self.__preview, 0, 1, 0, 1)
		t.attach(vs, 1, 2, 0, 1)
		t.attach(hs, 0, 1, 1, 2)

		# Right side of dialog: contains preview size spin buttons, background
		# color selector, and list of layers.

		# Top portion
		builder = HIGTableBuilder()
		builder.addSectionHeader("Background")
		self.colorButton = gtk.ColorButton(self.bgColor.getGdk())
		self.colorButton.connect("color-set", self.colorSet)
		builder.addLabeledWidget("Color:", self.colorButton)
		self.__preview.setColor(self.bgColor)

		builder.addSectionHeader("Preview")
		previewWSpin = gtk.SpinButton(gtk.Adjustment(previewWidth, 0, 1024, 1,
			10, 0), 10, 0)
		previewWSpin.connect("value-changed", self.previewWidthChanged)
		builder.addLabeledWidget("Width:", previewWSpin)

		previewHSpin = gtk.SpinButton(gtk.Adjustment(previewHeight, 0, 768, 1,
			10, 0), 10, 0)
		previewHSpin.connect("value-changed", self.previewHeightChanged)
		builder.addLabeledWidget("Height:", previewHSpin)

		previewScale = gtk.SpinButton(gtk.Adjustment(previewScale, 0.1, 2.0,
			0.1, 0.0), 10, 2)
		previewScale.connect("value-changed", self.previewScaleChanged)
		builder.addLabeledWidget("Zoom", previewScale)

		# List view
		self.treeModel = gtk.ListStore(bool, str)
		self.treeView = gtk.TreeView(self.treeModel)
		cto = gtk.CellRendererToggle()
		cto.set_property("activatable", True)
		cto.connect("toggled", self.visibilityToggle)
		self.treeView.append_column(gtk.TreeViewColumn("Visible", cto, active=0))
		cte = gtk.CellRendererText()
		self.treeView.append_column(gtk.TreeViewColumn("Background", cte,
			text=1))

		# Add current parallax information to the tree view
		if self.parallaxes is not None:
			for p in self.parallaxes:
				self.treeModel.prepend([p.visible,
					os.path.basename(p.fileName)])
				self.__preview.addBackground(p)

		# This has the same effect as clicking the edit button
		self.treeView.connect("row-activated", self.rowActivated)

		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.ORIENTATION_HORIZONTAL)
		toolbar.set_style(gtk.TOOLBAR_ICONS)
		toolbar.set_show_arrow(False)

		newButton = gtk.ToolButton(gtk.STOCK_NEW)
		newButton.connect("clicked", self.newClicked)
		toolbar.insert(newButton, -1)

		deleteButton = gtk.ToolButton(gtk.STOCK_DELETE)
		deleteButton.connect("clicked", self.deleteClicked)
		toolbar.insert(deleteButton, -1)

		upButton = gtk.ToolButton(gtk.STOCK_GO_UP)
		upButton.connect("clicked", self.upClicked)
		toolbar.insert(upButton, -1)

		downButton = gtk.ToolButton(gtk.STOCK_GO_DOWN)
		downButton.connect("clicked", self.downClicked)
		toolbar.insert(downButton, -1)

		editButton = gtk.ToolButton(gtk.STOCK_EDIT)
		editButton.connect("clicked", self.editClicked)
		toolbar.insert(editButton, -1)

		vBox = gtk.VBox()
		vBox.pack_start(builder.getTable(), False, False)
		vBox.pack_end(toolbar, False, True)
		vBox.pack_end(self.treeView)

		hBox = gtk.HBox()
		hBox.pack_start(t)
		hBox.pack_end(vBox)
		self.vbox.add(hBox)
		self.set_resizable(False)
		self.show_all()

	def previewWidthChanged(self, adjustment):
		self.__preview.setWidth(int(adjustment.get_value()))

	def previewHeightChanged(self, adjustment):
		self.__preview.setHeight(int(adjustment.get_value()))

	def previewScaleChanged(self, adjustment):
		self.__preview.setScale(adjustment.get_value())

	def previewXChanged(self, adjustment):
		self.__preview.setX(int(adjustment.get_value()))

	def previewYChanged(self, adjustment):
		self.__preview.setY(int(adjustment.get_value()))

	def colorSet(self, colorButton):
		self.bgColor = graphics.RGBA()
		self.bgColor.setGdk(colorButton.get_color())
		self.__preview.setColor(self.bgColor)

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

	def comIndex(self, index):
		return len(self.treeModel) - index - 1

	def newClicked(self, button):
		p = self.__showEditDialog(None)
		if p is not None and p.fileName is not None:
			self.parallaxes.append(p)
			self.treeModel.prepend([True, os.path.basename(p.fileName)])
			self.__preview.addBackground(p)

	def deleteClicked(self, button):
		iter = self.getCurrent()
		if iter is None:
			return
		# Remove the current layer
		index = self.treeModel.get_path(iter)[0]
		self.__preview.deleteLayer(self.comIndex(index))
		self.treeModel.remove(iter)
		del self.parallaxes[self.comIndex(index)]

	def upClicked(self, button):
		cIter = self.getCurrent()
		if cIter is None or int(self.treeModel.get_path(cIter)[0]) == 0:
			return
		else:
			current = self.treeModel.get_path(cIter)[0]
			pIter = self.treeModel.get_iter(int(current) - 1)
			previous = self.treeModel.get_path(pIter)[0]
			self.treeModel.swap(cIter, pIter)
			self.__preview.swapLayers(self.comIndex(int(current)),
				self.comIndex(int(previous)))

	def downClicked(self, button):
		iter = self.getCurrent()
		if iter is None:
			return
		else:
			next = self.treeModel.iter_next(iter)
			if next is not None:
				index = self.treeModel.get_path(iter)[0]
				nextIndex = self.treeModel.get_path(next)[0]
				self.treeModel.swap(iter, next)
				self.__preview.swapLayers(self.comIndex(index),
					self.comIndex(int(nextIndex)))

	def editClicked(self, button):
		iter = self.getCurrent()
		if iter is None:
			return
		else:
			index = self.treeModel.get_path(iter)[0]
			self.__showEditDialog(self.parallaxes[self.comIndex(index)])

	def rowActivated(self, treeview, path, column):
		self.__showEditDialog(self.parallaxes[self.comIndex(path[0])])

	def visibilityToggle(self, cell, path):
		p = int(path)
		self.treeModel[p][0] = not self.treeModel[p][0]
		self.__preview.setVisible(self.comIndex(p), self.treeModel[p][0])

	def __showEditDialog(self, parallax):
		d = BackgroundLayerDialog(self, parallax)
		result = d.run()
		if result == gtk.RESPONSE_ACCEPT:
			parallax = d.parallax
			parallax.hScroll = d.scrollHorizontally.get_active()
			parallax.vScroll = d.scrollVertically.get_active()
			parallax.hTile = d.tileHorizontally.get_active()
			parallax.vTile = d.tileVertically.get_active()
			parallax.vScrollSpeed = d.scrollVerticallySpeed.get_value()
			parallax.hScrollSpeed = d.scrollHorizontallySpeed.get_value()
			parallax.fileName = d.fileChooser.get_filename()
			d.destroy()
			return parallax
		else:
			d.destroy()
			return None


class PreferencesDialog(gtk.Dialog):
	def __init__(self, parent):
		gtk.Dialog.__init__(self, "Preferences", parent,
			gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

		self.notebook = gtk.Notebook()
		self.notebook.set_scrollable(True)

		self.createVisualTab()
		self.createFilesTab()
		self.createPhysicsTab()
		self.vbox.add(self.notebook)
		self.show_all()
		self.set_resizable(False)


	def createVisualTab(self):
		builder = HIGTableBuilder()
		builder.addSectionHeader("Grid")

		self.lengthSpin = gtk.SpinButton(gtk.Adjustment(
			preferences.visual["stipple_length"], 0, 50, 1,
			1, 0), 1, 0)
		self.lengthSpin.connect("value-changed", self.visualSpinChange,
			"stipple_length")
		builder.addLabeledWidget("_Line length:", self.lengthSpin)

		self.gapSpin = gtk.SpinButton(gtk.Adjustment(
			preferences.visual["stipple_gap"], 0, 50, 1,
			1, 0), 1, 0)
		self.gapSpin.connect("value-changed", self.visualSpinChange,
			"stipple_gap")
		builder.addLabeledWidget("_Gap length:", self.gapSpin)

		builder.addSectionHeader("Shapes")

		self.handleSpin = gtk.SpinButton(gtk.Adjustment(
			preferences.visual["handle_size"], 6, 20, 1, 1, 0), 1, 0)
		self.handleSpin.connect("value-changed", self.visualSpinChange,
			"handle_size")
		builder.addLabeledWidget("Handle _Size:", self.handleSpin)

		ioColor = graphics.RGBA()
		ioColor.fromU32(preferences.visual["invalid_outline"])
		ioButton = gtk.ColorButton(ioColor.getGdk())
		ioButton.set_use_alpha(True)
		ioButton.set_alpha(int(ioColor.a * 65535)) # convert to unsigned 16-bit
		ioButton.connect("color-set", self.colorSet, "invalid_outline")
		builder.addLabeledWidget("_Invalid Shape Outline Color:", ioButton)

		ifColor = graphics.RGBA()
		ifColor.fromU32(preferences.visual["invalid_fill"])
		ifButton = gtk.ColorButton(ifColor.getGdk())
		ifButton.set_use_alpha(True)
		ifButton.set_alpha(int(ifColor.a * 65535))
		ifButton.connect("color-set", self.colorSet, "invalid_fill")
		builder.addLabeledWidget("I_nvalid Shape Fill Color:", ifButton)

		voColor = graphics.RGBA()
		voColor.fromU32(preferences.visual["valid_outline"])
		voButton = gtk.ColorButton(voColor.getGdk())
		voButton.set_use_alpha(True)
		voButton.set_alpha(int(voColor.a * 65535))
		voButton.connect("color-set", self.colorSet, "valid_outline")
		builder.addLabeledWidget("_Valid Shape Outline Color:", voButton)

		vfColor = graphics.RGBA()
		vfColor.fromU32(preferences.visual["valid_fill"])
		vfButton = gtk.ColorButton(vfColor.getGdk())
		vfButton.set_use_alpha(True)
		vfButton.set_alpha(int(vfColor.a * 65535))
		vfButton.connect("color-set", self.colorSet, "valid_fill")
		builder.addLabeledWidget("V_alid Shape Fill Color:", vfButton)

		builder.addSectionHeader("Preview")
		self.visualWidget = visualwidget.VisualWidget()
		builder.addWidget(self.visualWidget)

		vbox = gtk.VBox()
		vbox.set_border_width(0)
		vbox.pack_start(builder.table, False, False)
		self.notebook.append_page(vbox, gtk.Label("Visual"))

	def colorSet(self, colorButton, key):
		color = graphics.RGBA()
		color.setGdk(colorButton.get_color())
		color.a = colorButton.get_alpha() / 65535.0
		preferences.visual[key] = color.toU32()
		self.visualWidget.update()
		# Add something about updating the preview here.

	def visualSpinChange(self, adjustment, key):
		preferences.visual[key] = adjustment.get_value_as_int()
		self.visualWidget.update()

	def createFilesTab(self):
		builder = HIGTableBuilder()
		builder.addSectionHeader("File location settings")

		self.usePrefixes = gtk.CheckButton("Use Prefixes")
		self.usePrefixes.set_active(preferences.files["use_prefixes"])
		self.usePrefixes.connect("toggled", self.prefixToggled)
		builder.addWidget(self.usePrefixes)

		self.tilesetEntry = gtk.Entry()
		self.tilesetEntry.set_text(preferences.files["tileset_prefix"])
		self.tilesetEntry.connect("changed", self.entryEdited, "tileset_prefix")
		builder.addLabeledWidget("Tileset Prefix:", self.tilesetEntry)

		self.parallaxEntry = gtk.Entry()
		self.parallaxEntry.set_text(preferences.files["parallax_prefix"])
		self.parallaxEntry.connect("changed", self.entryEdited,
			"parallax_prefix")
		builder.addLabeledWidget("Parallax Prefix:", self.parallaxEntry)

		self.dataDirEntry = gtk.Entry()
		self.dataDirEntry.set_text(preferences.files["data_prefix"])
		self.dataDirEntry.connect("changed", self.entryEdited, "data_prefix")
		builder.addLabeledWidget("Default Data Directory:", self.dataDirEntry)

		builder.addSectionHeader("Preview (Save):")

		self.tilePreviewSave = gtk.Entry()
		self.tilePreviewSave.set_editable(False)
		self.parallaxPreviewSave = gtk.Entry()
		self.parallaxPreviewSave.set_editable(False)
		builder.addWidget(self.tilePreviewSave)
		builder.addWidget(self.parallaxPreviewSave)

		builder.addSectionHeader("Preview (Load):")

		self.tilePreviewLoad = gtk.Entry()
		self.tilePreviewLoad.set_editable(False)
		self.parallaxPreviewLoad = gtk.Entry()
		self.parallaxPreviewLoad.set_editable(False)
		builder.addWidget(self.tilePreviewLoad)
		builder.addWidget(self.parallaxPreviewLoad)

		# Call the update functions manually to set up the dialog
		self.prefixToggled(self.usePrefixes)
		self.entryEdited(self.parallaxEntry, "parallax_prefix")

		vbox = gtk.VBox()
		vbox.set_border_width(0)
		vbox.pack_start(builder.table, False, False)
		self.notebook.append_page(vbox, gtk.Label("Files"))

	def prefixToggled(self, button):
		self.tilesetEntry.set_sensitive(button.get_active())
		self.parallaxEntry.set_sensitive(button.get_active())
		self.dataDirEntry.set_sensitive(button.get_active())
		self.tilePreviewSave.set_sensitive(button.get_active())
		self.tilePreviewLoad.set_sensitive(button.get_active())
		self.parallaxPreviewSave.set_sensitive(button.get_active())
		self.parallaxPreviewLoad.set_sensitive(button.get_active())
		preferences.files["use_prefixes"] = button.get_active()

	def entryEdited(self, entry, key):
		preferences.files[key] = entry.get_text()
		self.setPreviewText()

	def setPreviewText(self):
		self.tilePreviewSave.set_text(datafiles.getTilesetPath("tiles.png",
			True))
		self.parallaxPreviewSave.set_text(datafiles.getParallaxPath(
			"parallax.png", True))
		self.tilePreviewLoad.set_text(datafiles.getTilesetPath("tiles.png"))
		self.parallaxPreviewLoad.set_text(datafiles.getParallaxPath(
			"parallax.png"))

	def createPhysicsTab(self):
		builder = HIGTableBuilder()
		builder.addSectionHeader("Default Physics Parameters")

		frictionAdjustment = gtk.Adjustment(
			preferences.physics["default_friction"], 0.0, 1.0, 0.1)
		frictionSpin = gtk.SpinButton(frictionAdjustment, 1.0, 4)
		frictionSpin.connect("value-changed", self.physicsSpinChange,
			"default_friction")
		builder.addLabeledWidget("Coefficient of _Friction:", frictionSpin)

		restitutionAdjustment = gtk.Adjustment(
			preferences.physics["default_restitution"], 0.0, 20.0, 0.1)
		restitutionSpin = gtk.SpinButton(restitutionAdjustment, 1.0, 4)
		restitutionSpin.connect("value-changed", self.physicsSpinChange,
			"default_restitution")
		builder.addLabeledWidget("Coefficient of _Restitution:",
			restitutionSpin)

		vbox = gtk.VBox()
		vbox.set_border_width(0)
		vbox.pack_start(builder.table, False, False)
		self.notebook.append_page(vbox, gtk.Label("Physics"))

	def physicsSpinChange(self, adjustment, key):
		preferences.physics[key] = adjustment.get_value()
