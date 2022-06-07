from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QScrollArea, QDialog
from PyQt5.QtWidgets import QFrame, QWidget, QVBoxLayout, QLabel, QGraphicsScene
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QFontComboBox
from PyQt5.QtWidgets import QButtonGroup, QComboBox, QGraphicsPolygonItem
from PyQt5.QtWidgets import QGraphicsTextItem, QGridLayout, QHBoxLayout, QLabel
from PyQt5.QtWidgets import QMenu, QMessageBox, QSizePolicy,QToolBox, QToolButton
from PyQt5.QtWidgets import QAction, QToolBar, QSpinBox
from PyQt5.QtCore import QSize, Qt, QEvent, QRect, QPointF,  QSizeF
from PyQt5.QtCore import QLineF, QRectF, pyqtSignal
from PyQt5.QtGui import QPixmap, QPen, QBrush, QPainter, QColor
from PyQt5.QtGui import QFont, QIcon, QIntValidator, QPainterPath, QPolygonF
import forms.resource
import math
import forms.mainWindow as mainWindow
import forms.sizeDialog as sizeDialog
import sys

class Arrow(QGraphicsLineItem):
	def __init__(self, startItem, endItem, parent=None):
		super(Arrow, self).__init__(parent)

		self.arrowHead = QPolygonF()

		self.myStartItem = startItem
		self.myEndItem = endItem
		self.setFlag(QGraphicsItem.ItemIsSelectable, True)
		self.myColor = Qt.black
		self.setPen(QPen(self.myColor, 2, Qt.SolidLine, Qt.RoundCap,
				Qt.RoundJoin))

	def setColor(self, color):
		self.myColor = color

	def startItem(self):
		return self.myStartItem

	def endItem(self):
		return self.myEndItem

	def boundingRect(self):
		extra = (self.pen().width() + 20) / 2.0
		p1 = self.line().p1()
		p2 = self.line().p2()
		return QRectF(p1, QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-extra, -extra, extra, extra)

	def shape(self):
		path = super(Arrow, self).shape()
		path.addPolygon(self.arrowHead)
		return path

	def updatePosition(self):
		line = QLineF(self.mapFromItem(self.myStartItem, 0, 0), self.mapFromItem(self.myEndItem, 0, 0))
		self.setLine(line)

	def paint(self, painter, option, widget=None):
		if (self.myStartItem.collidesWithItem(self.myEndItem)):
			return

		myStartItem = self.myStartItem
		myEndItem = self.myEndItem
		myColor = self.myColor
		myPen = self.pen()
		myPen.setColor(self.myColor)
		arrowSize = 20.0
		painter.setPen(myPen)
		painter.setBrush(self.myColor)

		centerLine = QLineF(myStartItem.pos(), myEndItem.pos())
		endPolygon = myEndItem.polygon()
		p1 = endPolygon.first() + myEndItem.pos()

		intersectPoint = QPointF()
		for i in endPolygon:
			p2 = i + myEndItem.pos()
			polyLine = QLineF(p1, p2)
			intersectType = polyLine.intersect(centerLine, intersectPoint)
			if intersectType == QLineF.BoundedIntersection:
				break
			p1 = p2

		self.setLine(QLineF(intersectPoint, myStartItem.pos()))
		line = self.line()

		angle = math.acos(line.dx() / line.length())
		if line.dy() >= 0:
			angle = (math.pi * 2.0) - angle

		arrowP1 = line.p1() + QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
										math.cos(angle + math.pi / 3) * arrowSize)
		arrowP2 = line.p1() + QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
										math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)

		self.arrowHead.clear()
		for point in [line.p1(), arrowP1, arrowP2]:
			self.arrowHead.append(point)

		painter.drawLine(line)
		painter.drawPolygon(self.arrowHead)
		if self.isSelected():
			painter.setPen(QPen(myColor, 1, Qt.DashLine))
			myLine = QLineF(line)
			myLine.translate(0, 4.0)
			painter.drawLine(myLine)
			myLine.translate(0,-8.0)
			painter.drawLine(myLine)

class DiagramTextItem(QGraphicsTextItem):
	lostFocus = pyqtSignal(QGraphicsTextItem)

	selectedChange = pyqtSignal(QGraphicsItem)

	def __init__(self, parent=None, scene=None):
		super(DiagramTextItem, self).__init__(parent, scene)

		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemIsSelectable)

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemSelectedChange:
			self.selectedChange.emit(self)
		return value

	def focusOutEvent(self, event):
		self.setTextInteractionFlags(Qt.NoTextInteraction)
		self.lostFocus.emit(self)
		super(DiagramTextItem, self).focusOutEvent(event)

	def mouseDoubleClickEvent(self, event):
		if self.textInteractionFlags() == Qt.NoTextInteraction:
			self.setTextInteractionFlags(Qt.TextEditorInteraction)
		super(DiagramTextItem, self).mouseDoubleClickEvent(event)

class DiagramItem(QGraphicsPolygonItem):
	Step, Conditional, StartEnd, Io = range(4)

	def __init__(self, diagramType, contextMenu, parent=None):
		super(DiagramItem, self).__init__(parent)

		self.arrows = []

		self.diagramType = diagramType
		self.contextMenu = contextMenu

		path = QPainterPath()
		if self.diagramType == self.StartEnd:
			path.moveTo(200, 50)
			path.arcTo(150, 0, 50, 50, 0, 90)
			path.arcTo(50, 0, 50, 50, 90, 90)
			path.arcTo(50, 50, 50, 50, 180, 90)
			path.arcTo(150, 50, 50, 50, 270, 90)
			path.lineTo(200, 25)
			self.myPolygon = path.toFillPolygon()
		elif self.diagramType == self.Conditional:
			self.myPolygon = QPolygonF([
					QPointF(-100, 0), QPointF(0, 100),
					QPointF(100, 0), QPointF(0, -100),
					QPointF(-100, 0)])
		elif self.diagramType == self.Step:
			self.myPolygon = QPolygonF([
					QPointF(-100, -100), QPointF(100, -100),
					QPointF(100, 100), QPointF(-100, 100),
					QPointF(-100, -100)])
		else:
			self.myPolygon = QPolygonF([
					QPointF(-120, -80), QPointF(-70, 80),
					QPointF(120, 80), QPointF(70, -80),
					QPointF(-120, -80)])

		self.setPolygon(self.myPolygon)
		self.setFlag(QGraphicsItem.ItemIsMovable, True)
		self.setFlag(QGraphicsItem.ItemIsSelectable, True)

	def removeArrow(self, arrow):
		try:
			self.arrows.remove(arrow)
		except ValueError:
			pass

	def removeArrows(self):
		for arrow in self.arrows[:]:
			arrow.startItem().removeArrow(arrow)
			arrow.endItem().removeArrow(arrow)
			self.scene().removeItem(arrow)

	def addArrow(self, arrow):
		self.arrows.append(arrow)

	def image(self):
		pixmap = QPixmap(250, 250)
		pixmap.fill(Qt.transparent)
		painter = QPainter(pixmap)
		painter.setPen(QPen(Qt.black, 8))
		painter.translate(125, 125)
		painter.drawPolyline(self.myPolygon)
		return pixmap

	def contextMenuEvent(self, event):
		self.scene().clearSelection()
		self.setSelected(True)
		self.myContextMenu.exec_(event.screenPos())

	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemPositionChange:
			for arrow in self.arrows:
				arrow.updatePosition()

		return value

class DiagramScene(QGraphicsScene):
	InsertItem, InsertLine, InsertText, MoveItem  = range(4)

	itemInserted = pyqtSignal(DiagramItem)
	textInserted = pyqtSignal(QGraphicsTextItem)
	itemSelected = pyqtSignal(QGraphicsItem)

	def __init__(self, parent=None):
		super(DiagramScene, self).__init__(parent)

		self.myItemMenu = None
		self.myMode = self.MoveItem
		self.myItemType = DiagramItem.Step
		self.line = None
		self.textItem = None
		self.myItemColor = Qt.white
		self.myTextColor = Qt.black
		self.myLineColor = Qt.black
		self.myFont = QFont()

	def setLineColor(self, color):
		self.myLineColor = color
		if self.isItemChange(Arrow):
			item = self.selectedItems()[0]
			item.setColor(self.myLineColor)
			self.update()

	def setTextColor(self, color):
		self.myTextColor = color
		if self.isItemChange(DiagramTextItem):
			item = self.selectedItems()[0]
			item.setDefaultTextColor(self.myTextColor)

	def setItemColor(self, color):
		self.myItemColor = color
		if self.isItemChange(DiagramItem):
			item = self.selectedItems()[0]
			item.setBrush(self.myItemColor)

	def setFont(self, font):
		self.myFont = font
		if self.isItemChange(DiagramTextItem):
			item = self.selectedItems()[0]
			item.setFont(self.myFont)

	def setMode(self, mode):
		self.myMode = mode

	def setItemType(self, type):
		self.myItemType = type

	def editorLostFocus(self, item):
		cursor = item.textCursor()
		cursor.clearSelection()
		item.setTextCursor(cursor)

		#if item.toPlainText():
		#	self.removeItem(item)
		#	item.deleteLater()

	def mousePressEvent(self, mouseEvent):
		if (mouseEvent.button() != Qt.LeftButton):
			return

		if self.myMode == self.InsertItem:
			item = DiagramItem(self.myItemType, self.myItemMenu)
			item.setBrush(self.myItemColor)
			self.addItem(item)
			item.setPos(mouseEvent.scenePos())
			self.itemInserted.emit(item)
		elif self.myMode == self.InsertLine:
			self.line = QGraphicsLineItem(QLineF(mouseEvent.scenePos(),
					mouseEvent.scenePos()))
			self.line.setPen(QPen(self.myLineColor, 2))
			self.addItem(self.line)
		elif self.myMode == self.InsertText:
			textItem = DiagramTextItem()
			textItem.setFont(self.myFont)
			textItem.setTextInteractionFlags(Qt.TextEditorInteraction)
			textItem.setZValue(1000.0)
			textItem.lostFocus.connect(self.editorLostFocus)
			textItem.selectedChange.connect(self.itemSelected)
			self.addItem(textItem)
			textItem.setDefaultTextColor(self.myTextColor)
			textItem.setPos(mouseEvent.scenePos())
			self.textInserted.emit(textItem)

		super(DiagramScene, self).mousePressEvent(mouseEvent)

	def mouseMoveEvent(self, mouseEvent):
		if self.myMode == self.InsertLine and self.line:
			newLine = QLineF(self.line.line().p1(), mouseEvent.scenePos())
			self.line.setLine(newLine)
		elif self.myMode == self.MoveItem:
			super(DiagramScene, self).mouseMoveEvent(mouseEvent)

	def mouseReleaseEvent(self, mouseEvent):
		if self.line and self.myMode == self.InsertLine:
			startItems = self.items(self.line.line().p1())
			if len(startItems) and startItems[0] == self.line:
				startItems.pop(0)
			endItems = self.items(self.line.line().p2())
			if len(endItems) and endItems[0] == self.line:
				endItems.pop(0)

			self.removeItem(self.line)
			self.line = None

			if len(startItems) and len(endItems) and \
					isinstance(startItems[0], DiagramItem) and \
					isinstance(endItems[0], DiagramItem) and \
					startItems[0] != endItems[0]:
				startItem = startItems[0]
				endItem = endItems[0]
				arrow = Arrow(startItem, endItem)
				arrow.setColor(self.myLineColor)
				startItem.addArrow(arrow)
				endItem.addArrow(arrow)
				arrow.setZValue(-1000.0)
				self.addItem(arrow)
				arrow.updatePosition()

		self.line = None
		super(DiagramScene, self).mouseReleaseEvent(mouseEvent)

	def isItemChange(self, type):
		for item in self.selectedItems():
			if isinstance(item, type):
				return True
		return False

class Ui(QtWidgets.QMainWindow):
	InsertTextButton = 10

	def __init__(self):
		super(Ui, self).__init__()
		self.ui = mainWindow.Ui_MainWindow()
		self.ui.setupUi(self)
		self.createActions()
		self.createItems()
		self.createToolbars()
		self.scene = DiagramScene()
		self.scene.setSceneRect(QRectF(0, 0, 5000, 5000))
		self.scene.itemInserted.connect(self.itemInserted)
		self.scene.textInserted.connect(self.textInserted)
		self.scene.itemSelected.connect(self.itemSelected)
		self.ui.canvas.setScene(self.scene)

	def createItems(self):
		self.buttonGroup = QButtonGroup()
		self.buttonGroup.setExclusive(False)
		self.buttonGroup.buttonClicked[int].connect(self.buttonGroupClicked)

		layout = QGridLayout()
		layout.addWidget(self.createCellWidget("Conditional", DiagramItem.Conditional),
				0, 0)
		layout.addWidget(self.createCellWidget("Process", DiagramItem.Step), 0,
				1)
		layout.addWidget(self.createCellWidget("Input/Output", DiagramItem.Io),
				1, 0)

		textButton = QToolButton()
		textButton.setCheckable(True)
		self.buttonGroup.addButton(textButton, self.InsertTextButton)
		textButton.setIcon(QIcon(QPixmap(':/icons/img/textpointer.png').scaled(30, 30)))
		textButton.setIconSize(QSize(50, 50))

		textLayout = QGridLayout()
		textLayout.addWidget(textButton, 0, 0, Qt.AlignHCenter)
		textLayout.addWidget(QLabel("Text"), 1, 0, Qt.AlignCenter)
		textWidget = QWidget()
		textWidget.setLayout(textLayout)
		layout.addWidget(textWidget, 1, 1)

		layout.setRowStretch(3, 10)
		layout.setColumnStretch(2, 10)

		itemWidget = QWidget()
		itemWidget.setLayout(layout)

		self.ui.toolBox.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Ignored))
		self.ui.toolBox.setMinimumWidth(itemWidget.sizeHint().width())
		self.ui.toolBox.addItem(itemWidget, "Items")

	def createToolbars(self):
		self.editToolBar = QToolBar(self)
		self.editToolBar.setObjectName("Edit")
		self.editToolBar.addAction(self.deleteAction)
		self.editToolBar.addAction(self.toFrontAction)
		self.editToolBar.addAction(self.sendBackAction)

		self.fontCombo = QFontComboBox()
		self.fontCombo.currentFontChanged.connect(self.currentFontChanged)

		self.fontSizeCombo = QComboBox()
		self.fontSizeCombo.setEditable(True)
		for i in range(8, 30, 2):
			self.fontSizeCombo.addItem(str(i))
		validator = QIntValidator(2, 64, self)
		self.fontSizeCombo.setValidator(validator)
		self.fontSizeCombo.currentIndexChanged.connect(self.fontSizeChanged)

		self.fontColorToolButton = QToolButton()
		self.fontColorToolButton.setPopupMode(QToolButton.MenuButtonPopup)
		self.fontColorToolButton.setMenu(
				self.createColorMenu(self.textColorChanged, Qt.black))
		self.textAction = self.fontColorToolButton.menu().defaultAction()
		self.fontColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/textpointer.png',
						Qt.black))
		self.fontColorToolButton.setAutoFillBackground(True)
		self.fontColorToolButton.clicked.connect(self.textButtonTriggered)

		self.fillColorToolButton = QToolButton()
		self.fillColorToolButton.setPopupMode(QToolButton.MenuButtonPopup)
		self.fillColorToolButton.setMenu(
				self.createColorMenu(self.itemColorChanged, Qt.white))
		self.fillAction = self.fillColorToolButton.menu().defaultAction()
		self.fillColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/floodfill.png',
						Qt.white))
		self.fillColorToolButton.clicked.connect(self.fillButtonTriggered)

		self.lineColorToolButton = QToolButton()
		self.lineColorToolButton.setPopupMode(QToolButton.MenuButtonPopup)
		self.lineColorToolButton.setMenu(
				self.createColorMenu(self.lineColorChanged, Qt.black))
		self.lineAction = self.lineColorToolButton.menu().defaultAction()
		self.lineColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/linecolor.png',
						Qt.black))
		self.lineColorToolButton.clicked.connect(self.lineButtonTriggered)

		self.textToolBar = QToolBar(self)
		self.textToolBar.setObjectName("Font")
		self.textToolBar.addWidget(self.fontCombo)
		self.textToolBar.addWidget(self.fontSizeCombo)
		self.textToolBar.addAction(self.boldAction)
		self.textToolBar.addAction(self.italicAction)
		self.textToolBar.addAction(self.underlineAction)

		self.colorToolBar = QToolBar(self)
		self.colorToolBar.setObjectName("Color")
		self.colorToolBar.addWidget(self.fontColorToolButton)
		self.colorToolBar.addWidget(self.fillColorToolButton)
		self.colorToolBar.addWidget(self.lineColorToolButton)

		pointerButton = QToolButton()
		pointerButton.setCheckable(True)
		pointerButton.setChecked(True)
		pointerButton.setIcon(QIcon(':/icons/img/pointer.png'))
		linePointerButton = QToolButton()
		linePointerButton.setCheckable(True)
		linePointerButton.setIcon(QIcon(':/icons/img/linepointer.png'))

		self.pointerTypeGroup = QButtonGroup()
		self.pointerTypeGroup.addButton(pointerButton, DiagramScene.MoveItem)
		self.pointerTypeGroup.addButton(linePointerButton,
				DiagramScene.InsertLine)
		self.pointerTypeGroup.buttonClicked[int].connect(self.pointerGroupClicked)

		self.pointerToolbar = QToolBar(self)
		self.pointerToolbar.setObjectName("Pointer type")
		self.pointerToolbar.addWidget(pointerButton)
		self.pointerToolbar.addWidget(linePointerButton)

		sceneScalePlus = QToolButton()
		sceneScalePlus.setText("+")
		sceneScalePlus.clicked.connect(self.sceneScalePlus)
		self.sceneScaleBox = QSpinBox()
		self.sceneScaleBox.setMaximum(200)
		self.sceneScaleBox.setMinimum(50)
		self.sceneScaleBox.setValue(100)
		sceneScaleMinus = QToolButton()
		sceneScaleMinus.setText("-")
		sceneScaleMinus.clicked.connect(self.sceneScaleMinus)

		self.sceneScaleToolBar = QToolBar()
		self.sceneScaleToolBar.setObjectName("Scale")
		self.sceneScaleToolBar.addWidget(self.sceneScaleBox)
		self.sceneScaleToolBar.addWidget(sceneScalePlus)
		self.sceneScaleToolBar.addWidget(sceneScaleMinus)

		self.addToolBar(Qt.LeftToolBarArea, self.editToolBar)
		self.addToolBar(self.textToolBar)
		self.addToolBar(Qt.LeftToolBarArea, self.colorToolBar)
		self.addToolBar(Qt.LeftToolBarArea, self.pointerToolbar)
		self.addToolBar(self.sceneScaleToolBar)

	def createActions(self):
		self.toFrontAction = QAction(
				QIcon(':/icons/img/bringtofront.png'), "Bring to &Front",
				self, shortcut="Ctrl+F", statusTip="Bring item to front",
				triggered=self.bringToFront)

		self.sendBackAction = QAction(
				QIcon(':/icons/img/sendtoback.png'), "Send to &Back", self,
				shortcut="Ctrl+B", statusTip="Send item to back",
				triggered=self.sendToBack)

		self.deleteAction = QAction(QIcon(':/icons/img/delete.png'),
				"&Delete", self, shortcut="Delete",
				statusTip="Delete item from diagram",
				triggered=self.deleteItem)

		self.exitAction = QAction("E&xit", self, shortcut="Ctrl+X",
				statusTip="Quit Scenediagram example", triggered=self.close)

		self.boldAction = QAction(QIcon(':/icons/img/bold.png'),
				"Bold", self, checkable=True, shortcut="Ctrl+B",
				triggered=self.handleFontChange)

		self.italicAction = QAction(QIcon(':/icons/img/italic.png'),
				"Italic", self, checkable=True, shortcut="Ctrl+I",
				triggered=self.handleFontChange)

		self.underlineAction = QAction(
				QIcon(':/icons/img/underline.png'), "Underline", self,
				checkable=True, shortcut="Ctrl+U",
				triggered=self.handleFontChange)

	def createColorMenu(self, slot, defaultColor):
		colors = [Qt.black, Qt.white, Qt.red, Qt.blue, Qt.yellow]
		names = ["black", "white", "red", "blue", "yellow"]

		colorMenu = QMenu(self)
		for color, name in zip(colors, names):
			action = QAction(self.createColorIcon(color), name, self,
					triggered=slot)
			action.setData(QColor(color)) 
			colorMenu.addAction(action)
			if color == defaultColor:
				colorMenu.setDefaultAction(action)
		return colorMenu

	def createColorIcon(self, color):
		pixmap = QPixmap(20, 20)
		painter = QPainter(pixmap)
		painter.setPen(Qt.NoPen)
		painter.fillRect(QRect(0, 0, 20, 20), color)
		painter.end()

		return QIcon(pixmap)

	def handleFontChange(self):
		font = self.fontCombo.currentFont()
		font.setPointSize(self.fontSizeCombo.currentText().toInt()[0])
		if self.boldAction.isChecked():
			font.setWeight(QFont.Bold)
		else:
			font.setWeight(QFont.Normal)
		font.setItalic(self.italicAction.isChecked())
		font.setUnderline(self.underlineAction.isChecked())

		self.scene.setFont(font)

	def deleteItem(self):
		for item in self.scene.selectedItems():
			if isinstance(item, DiagramItem):
				item.removeArrows()
			self.scene.removeItem(item)

	def sceneScale(self, scaleValue, value):
		if value in range(50, 201):
			self.sceneScaleBox.setValue(value)
			self.ui.canvas.scale(scaleValue, scaleValue)

	def sceneScalePlus(self):
		value = self.sceneScaleBox.value()
		value += 25
		self.sceneScale(1.25, value)
	
	def sceneScaleMinus(self):
		value = self.sceneScaleBox.value()
		value -= 25
		self.sceneScale(0.75, value)
	
	def pointerGroupClicked(self, i):
		self.scene.setMode(self.pointerTypeGroup.checkedId())

	def bringToFront(self):
		if not self.scene.selectedItems():
			return

		selectedItem = self.scene.selectedItems()[0]
		overlapItems = selectedItem.collidingItems()

		zValue = 0
		for item in overlapItems:
			if (item.zValue() >= zValue and isinstance(item, DiagramItem)):
				zValue = item.zValue() + 0.1
		selectedItem.setZValue(zValue)

	def sendToBack(self):
		if not self.scene.selectedItems():
			return

		selectedItem = self.scene.selectedItems()[0]
		overlapItems = selectedItem.collidingItems()

		zValue = 0
		for item in overlapItems:
			if (item.zValue() <= zValue and isinstance(item, DiagramItem)):
				zValue = item.zValue() - 0.1
		selectedItem.setZValue(zValue)

	def currentFontChanged(self, font):
		self.handleFontChange()

	def fontSizeChanged(self, font):
		self.handleFontChange()

	def textColorChanged(self):
		self.textAction = self.sender()
		self.fontColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/textpointer.png',
						QColor(self.textAction.data())))
		self.textButtonTriggered()

	def createCellWidget(self, text, diagramType):
		item = DiagramItem(diagramType, None)
		icon = QIcon(item.image())

		button = QToolButton()
		button.setIcon(icon)
		button.setIconSize(QSize(50, 50))
		button.setCheckable(True)
		self.buttonGroup.addButton(button, diagramType)

		layout = QGridLayout()
		layout.addWidget(button, 0, 0, Qt.AlignHCenter)
		layout.addWidget(QLabel(text), 1, 0, Qt.AlignCenter)

		widget = QWidget()
		widget.setLayout(layout)

		return widget

	def itemColorChanged(self):
		self.fillAction = self.sender()
		self.fillColorToolButton.setIcon(
				self.createColorToolButtonIcon( ':/icons/img/floodfill.png',
						QColor(self.fillAction.data())))
		self.fillButtonTriggered()

	def lineColorChanged(self):
		self.lineAction = self.sender()
		self.lineColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/linecolor.png',
						QColor(self.lineAction.data())))
		self.lineButtonTriggered()

	def textButtonTriggered(self):
		self.scene.setTextColor(QColor(self.textAction.data()))

	def fillButtonTriggered(self):
		self.scene.setItemColor(QColor(self.fillAction.data()))

	def lineButtonTriggered(self):
		self.scene.setLineColor(QColor(self.lineAction.data()))

	def buttonGroupClicked(self, id):
		buttons = self.buttonGroup.buttons()
		for button in buttons:
			if self.buttonGroup.button(id) != button:
				button.setChecked(False)

		if id == self.InsertTextButton:
			self.scene.setMode(DiagramScene.InsertText)
		else:
			self.scene.setItemType(id)
			self.scene.setMode(DiagramScene.InsertItem)
	
	def itemInserted(self, item):
		self.pointerTypeGroup.button(DiagramScene.MoveItem).setChecked(True)
		self.scene.setMode(self.pointerTypeGroup.checkedId())		
		self.buttonGroup.button(item.diagramType).setChecked(False)

	def textInserted(self, item):
		self.buttonGroup.button(self.InsertTextButton).setChecked(False)
		self.scene.setMode(self.pointerTypeGroup.checkedId())

	def itemSelected(self, item):
		font = item.font()
		color = item.defaultTextColor()
		self.fontCombo.setCurrentFont(font)
		self.fontSizeCombo.setEditText(str(font.pointSize()))
		self.boldAction.setChecked(font.weight() == QFont.Bold)
		self.italicAction.setChecked(font.italic())
		self.underlineAction.setChecked(font.underline())

	def createColorToolButtonIcon(self, imageFile, color):
		pixmap = QPixmap(50, 80)
		pixmap.fill(Qt.transparent)
		painter = QPainter(pixmap)
		image = QPixmap(imageFile)
		target = QRect(0, 0, 50, 60)
		source = QRect(0, 0, 42, 42)
		painter.fillRect(QRect(0, 60, 50, 80), color)
		painter.drawPixmap(target, image, source)
		painter.end()

		return QIcon(pixmap)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Ui()
	window.show()
	sys.exit(app.exec_())