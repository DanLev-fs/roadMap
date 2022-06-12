from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QScrollArea, QDialog
from PyQt5.QtWidgets import QFrame, QWidget, QVBoxLayout, QLabel, QGraphicsScene
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsLineItem, QFontComboBox
from PyQt5.QtWidgets import QButtonGroup, QComboBox, QGraphicsPolygonItem
from PyQt5.QtWidgets import QGraphicsTextItem, QGridLayout, QHBoxLayout, QLabel
from PyQt5.QtWidgets import QMenu, QMessageBox, QSizePolicy,QToolBox, QToolButton
from PyQt5.QtWidgets import QAction, QToolBar, QSpinBox, QFileDialog
from PyQt5.QtCore import QSize, Qt, QEvent, QRect, QPointF,  QSizeF
from PyQt5.QtCore import QLineF, QRectF, pyqtSignal
from PyQt5.QtGui import QPixmap, QPen, QBrush, QPainter, QColor, QImage
from PyQt5.QtGui import QFont, QIcon, QIntValidator, QPainterPath, QPolygonF
import msgpack
import numpy as np
import math
import sys
import forms.resource
import forms.mainWindow as mainWindow
import forms.sizeDialog as sizeDialog

class Items(): # класс для хранения всех предметов на сцене.
			   # Задумываляся для сохранения диаграммы.
			   # Не закончен
	def __init__(self) -> None:
		self.itemsList = []		# Инициализация списка для предметов на сцене

	def addItem(self, item, itemType, itemColor) -> None:	# Добавить предмет (Предмет, item, тип предмета, цвет)
		self.itemsList.append({"%s"%id(item): (item, "item", itemType, itemColor)})

	def addText(self, item, itemText, itemFont, itemSize, itemColor) -> None:	# Добавить тескт (Предмет, text, содержимое текста, шрифт, размер, цвет)
		self.itemsList.append({"%s"%id(item): (item, "text", itemText, itemFont, itemSize, itemColor)})

	def addArrow(self, item, startItem, endItem, itemColor) -> None:	# Добавить стрелку (Предмет, arrow, начальный предмет, конечный предмет, цвет)
		self.itemsList.append({"%s"%id(item): (item, "arrow", startItem, endItem, itemColor)})

	def remove(self, item) -> None:		# Удалить предмет из списка
		self.itemsList.remove(str(id(item)))

	def get(self) -> list:		# Получить все предметы
		return self.itemsList

class Arrow(QGraphicsLineItem):		# Класс генерирующий стрелку
	def __init__(self, startItem, endItem, parent=None):	# Инициализация
		super(Arrow, self).__init__(parent)

		self.arrowHead = QPolygonF()

		self.myStartItem = startItem
		self.myEndItem = endItem
		self.setFlag(QGraphicsItem.ItemIsSelectable, True)
		self.myColor = Qt.black
		self.setPen(QPen(self.myColor, 2, Qt.SolidLine, Qt.RoundCap,
				Qt.RoundJoin))

	def setColor(self, color):	# Установить цвет созданной стрелки
		self.myColor = color

	def startItem(self):	# Получить начальный предмет выбранной стрелки
		return self.myStartItem

	def endItem(self):		# Получить конечный предмет выбранной стрелки
		return self.myEndItem

	def boundingRect(self):		# Возвращает прямоугольник, углы которого являются центрами предметов соединенных стрелкой
		extra = (self.pen().width() + 20) / 2.0
		p1 = self.line().p1()
		p2 = self.line().p2()
		return QRectF(p1, QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-extra, -extra, extra, extra)

	def shape(self):	# Возвращает линию от центра одного предмета до второго соединенных стрелкой
		path = super(Arrow, self).shape()
		path.addPolygon(self.arrowHead)
		return path

	def updatePosition(self):	# Обновляет стрелку при перемещении одного из соединенных предметов 
		line = QLineF(self.mapFromItem(self.myStartItem, 0, 0), self.mapFromItem(self.myEndItem, 0, 0))
		self.setLine(line)

	def paint(self, painter, option, widget=None):		# Метод рисующий стрелку
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

class DiagramTextItem(QGraphicsTextItem):	# Класс для создания текста
	lostFocus = pyqtSignal(QGraphicsTextItem)	# Просто установни сигралов для завершения
	selectedChange = pyqtSignal(QGraphicsItem)	# редактирования и выбора предмета в сцене

	def __init__(self, parent=None, scene=None):	# Инициализация
		super(DiagramTextItem, self).__init__(parent, scene)

		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemIsSelectable)

	def itemChange(self, change, value):	# Выбор предмета. Проверяет если выбран этот предмет, то устанавливает рамку выбора
		if change == QGraphicsItem.ItemSelectedChange:
			self.selectedChange.emit(self)
		return value

	def focusOutEvent(self, event):		# Потеря фокуса предмета
		self.setTextInteractionFlags(Qt.NoTextInteraction)
		self.lostFocus.emit(self)
		super(DiagramTextItem, self).focusOutEvent(event)

	def mouseDoubleClickEvent(self, event):		# Редактирование при двойном клике по тексту
		if self.textInteractionFlags() == Qt.NoTextInteraction:
			self.setTextInteractionFlags(Qt.TextEditorInteraction)
		super(DiagramTextItem, self).mouseDoubleClickEvent(event)

class DiagramItem(QGraphicsPolygonItem):	# Класс предметов 
	Step, Conditional, StartEnd, Io = range(4)	# Типы предметов

	def __init__(self, diagramType, contextMenu, parent=None):	# Инициализация
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

	def removeArrow(self, arrow):	# Удаление стрелки
		try:
			self.arrows.remove(arrow)
		except ValueError:
			pass

	def removeArrows(self):		# Удаление всех стрелок связвнных с этим предметом, при удалении самого предмета
		for arrow in self.arrows[:]:
			arrow.startItem().removeArrow(arrow)
			arrow.endItem().removeArrow(arrow)
			self.scene().removeItem(arrow)

	def addArrow(self, arrow):	# Добавить стрелку ко списку всех стрелок предмета
		self.arrows.append(arrow)

	def image(self):	# Иконки
		pixmap = QPixmap(250, 250)
		pixmap.fill(Qt.transparent)
		painter = QPainter(pixmap)
		painter.setPen(QPen(Qt.black, 8))
		painter.translate(125, 125)
		painter.drawPolyline(self.myPolygon)
		return pixmap

	def contextMenuEvent(self, event):	# Вызов контекстного меню правым кликом мыши
		self.scene().clearSelection()
		self.setSelected(True)
		self.contextMenu.exec_(event.screenPos())

	def itemChange(self, change, value):	# Вызов обновления стрелки при перемещении предмета
		if change == QGraphicsItem.ItemPositionChange:
			for arrow in self.arrows:
				arrow.updatePosition()

		return value

class DiagramScene(QGraphicsScene):		# Класс сцены
	InsertItem, InsertLine, InsertText, MoveItem  = range(4)	# Текущее действие

	itemInserted = pyqtSignal(DiagramItem)			#
	textInserted = pyqtSignal(QGraphicsTextItem)	# Сигналы
	itemSelected = pyqtSignal(QGraphicsItem)		#

	def __init__(self, itemsInterface: Items, itemMenu, parent=None):	# Инициализация
		super(DiagramScene, self).__init__(parent)

		self.itemsInterface = itemsInterface
		self.myItemMenu = itemMenu
		self.myMode = self.MoveItem
		self.myItemType = DiagramItem.Step
		self.line = None
		self.textItem = None
		self.myItemColor = Qt.white
		self.myTextColor = Qt.black
		self.myLineColor = Qt.black
		self.myFont = QFont()

	def setLineColor(self, color):	# Изменение цвета стрелки
		self.myLineColor = color
		if self.isItemChange(Arrow):
			item = self.selectedItems()[0]
			item.setColor(self.myLineColor)
			self.update()

	def setTextColor(self, color):	# Изменение цвета текста
		self.myTextColor = color
		if self.isItemChange(DiagramTextItem):
			item = self.selectedItems()[0]
			item.setDefaultTextColor(self.myTextColor)

	def setItemColor(self, color):	# Изменение цвета предмета
		self.myItemColor = color
		if self.isItemChange(DiagramItem):
			item = self.selectedItems()[0]
			item.setBrush(self.myItemColor)

	def setFont(self, font):	# Изменение шрифта
		self.myFont = font
		if self.isItemChange(DiagramTextItem):
			item = self.selectedItems()[0]
			item.setFont(self.myFont)

	def setMode(self, mode):	# Установка текущего действия
		self.myMode = mode

	def setItemType(self, type):	# Установка типа предмета для добавления
		self.myItemType = type

	def editorLostFocus(self, item):	# Завершение редактирования текста + проверка на отсутствие текста
		cursor = item.textCursor()
		cursor.clearSelection()
		item.setTextCursor(cursor)

		if item.toPlainText() == "":
			self.removeItem(item)
			item.deleteLater()

	def mousePressEvent(self, mouseEvent):	# Добавление предмета | Эвент левого щелчка мыши 
		if (mouseEvent.button() != Qt.LeftButton):	# Если не выбран предмет эвент остановаливается
			return

		if mouseEvent.scenePos().x() > self.sceneRect().right():	# Проверка на попыку создания предмета за пределами сцены
			return
		if mouseEvent.scenePos().x() < self.sceneRect().left():
			return
		if mouseEvent.scenePos().y() > self.sceneRect().bottom():
			return
		if mouseEvent.scenePos().y() < self.sceneRect().top():
			return

		if self.myMode == self.InsertItem:	# Добавление предмета
			item = DiagramItem(self.myItemType, self.myItemMenu)
			item.setBrush(self.myItemColor)
			self.addItem(item)
			item.setPos(mouseEvent.scenePos())
			self.itemsInterface.addItem(item, self.myItemType, self.myItemColor)
			self.itemInserted.emit(item)
		elif self.myMode == self.InsertLine:	# Начало стрелки
			self.line = QGraphicsLineItem(QLineF(mouseEvent.scenePos(),
					mouseEvent.scenePos()))
			self.line.setPen(QPen(self.myLineColor, 2))
			self.addItem(self.line)
		elif self.myMode == self.InsertText:	# Добавление теста
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

	def mouseMoveEvent(self, mouseEvent):	# Эвент перемещения мыши с зажатой левой клавишей
		if self.myMode == self.InsertLine and self.line:	# Создание линии для последующей генерации стрелки
			newLine = QLineF(self.line.line().p1(), mouseEvent.scenePos())
			self.line.setLine(newLine)
		elif self.myMode == self.MoveItem:	# Проверка на вынос предмета за пределы сцены. Не работает полностью
			height = self.sceneRect().height()
			width = self.sceneRect().width()
			pos = mouseEvent.scenePos()
			if pos.x() < 0:
				self.selectedItems()[0].setPos(0, pos.y())
			elif pos.x() > width:
				self.selectedItems()[0].setPos(width, pos.y())
			if pos.y() < 0:
				self.selectedItems()[0].setPos(pos.x(), 0)
			elif pos.y() > height:
				self.selectedItems()[0].setPos(pos.x(), height)
			super(DiagramScene, self).mouseMoveEvent(mouseEvent)

	def mouseReleaseEvent(self, mouseEvent):	# Эвент срабатывающий при отжатии левой кнопки мыши
		if self.line and self.myMode == self.InsertLine:	# Если включен режим создания стрелки
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
					startItems[0] != endItems[0]:					# Если со стартовым и конечном предметом норм и это не один предмет, создаем стрелку
				startItem = startItems[0]
				endItem = endItems[0]
				arrow = Arrow(startItem, endItem)
				arrow.setColor(self.myLineColor)
				startItem.addArrow(arrow)
				endItem.addArrow(arrow)
				arrow.setZValue(-1000.0)
				self.addItem(arrow)
				arrow.updatePosition()
				self.itemsInterface.addArrow(arrow, id(startItem), id(endItem), self.myLineColor)

		self.line = None
		super(DiagramScene, self).mouseReleaseEvent(mouseEvent)

	def isItemChange(self, type):	# Проверка соответствия выбранного предмета нужному типу
		for item in self.selectedItems():
			if isinstance(item, type):
				return True
		return False

class Ui(QtWidgets.QMainWindow):	# Класс основного окна
	InsertTextButton = 10	# Номер кнопки для текста

	def __init__(self):		# Инициализация
		super(Ui, self).__init__()
		self.ui = mainWindow.Ui_MainWindow()
		self.ui.setupUi(self)	# Создание интерфейса
		self.ui.statusbar.showMessage("Здравствуйте")
		self.createActions()	# 
		self.createItems()		# Дополнение и настройка интерфейса
		self.createToolbars()	# 
		self.itemMenu()			# 
		self.Items = Items()
		self.createScene(5000, 5000)	# Создание дефолной сцены с размером 5000 на 5000
		#self.ui.save.triggered.connect(self.save)
		self.ui.export.triggered.connect(self.exportPNG)	#
		self.ui.exit.triggered.connect(self.close)			# Подключения тригеров к кнопкам
		self.ui.create.triggered.connect(self.createDialog)	#
		self.scaleUpFactor = np.sqrt(2.0)	# Константа для увеличения

	def createScene(self, heigth, width):	# Метод создания сцены с заданными параметрами
		self.scene = DiagramScene(self.Items, self.ui.itemMenu)
		self.scene.setSceneRect(QRectF(0, 0, heigth, width))
		pen = QPen()										#
		pen.setColor(Qt.black)								#
		pen.setWidth(10)									#
		self.scene.addLine(0, 0, 0, heigth, pen)			# Создание границ
		self.scene.addLine(0, 0, width, 0, pen)				#
		self.scene.addLine(heigth, width, 0, width, pen)	#
		self.scene.addLine(heigth, width, width, 0, pen)	#
		self.scene.itemInserted.connect(self.itemInserted)
		self.scene.textInserted.connect(self.textInserted)
		self.scene.itemSelected.connect(self.itemSelected)
		self.ui.canvas.setScene(self.scene)

	def createDialog(self):		# Диалог создания новой сцены с новыми параметрами
		edites = QDialog()
		ui = sizeDialog.Ui_canvasSize()
		ui.setupUi(edites)
		if (edites.exec_() == QDialog.Accepted):
			heigth = ui.higthBox.value()
			width = ui.widthBox.value()
			self.createScene(heigth, width)

	def _get_max_min_pos(self):		# Получение максималтной и минимальной позиции предметов
		listX = []
		listY = []
		for item in self.scene.items():
			if item.x() == 0 and item.y() == 0:
				continue
			if item.isSelected():
				item.setSelected(False)
			listX.append(item.x())
			listY.append(item.y())
		topLeft = QPointF(min(listX)-250, max(listY)+250)
		botomRight = QPointF(max(listX)+250, min(listY)-250)
		return topLeft, botomRight

	def exportPNG(self):	# Метод экспорта в png
		if len(self.scene.items()) == 0:
			self.ui.statusbar.showMessage("Ошибка! Пустая диаграмма")
			return
		self.ui.statusbar.showMessage("Экпортирую, подождите немного")
		rect = self._get_max_min_pos()
		area = QRectF()
		area.setTopLeft(rect[0])
		area.setBottomRight(rect[1])
		image = QImage(self.scene.sceneRect().size().toSize(), QImage.Format_ARGB32_Premultiplied)
		painter = QPainter(image)
		self.scene.render(painter, QRectF(image.rect()), area.normalized())
		painter.end()
		name = QFileDialog.getSaveFileName(self, 'Выберите куда сохранить', 'scene.png', filter="PNG (*.png)")
		image.save(name[0])
		self.ui.statusbar.showMessage("Готово, экспорт завершен!")

	def save(self):		# Метод сохранения. Недоделан
		print("save me")
		lstItems = []
		for item in self.Items.get():
			id = list(item.keys())[0]
			item = list(item.values())[0]
			if item[1] == "item":
				pos = [item[0].x(), item[0].y()]
				itemType = item[2]
				itemColor = QColor.getRgb(QColor(item[3]))
				lstItems.append({"%s"%id: (pos, itemType, itemColor)})
			elif item[1] == "text":
				pass
			elif item[1] == "arrow":
				start = item[2]
				end = item[3]
				itemColor = QColor.getRgb(QColor(item[4]))
				lstItems.append({"%s"%id: (start, end, itemColor)})
		print(lstItems)

	def itemMenu(self):		# Создания кнопок в меню предмотов
		self.ui.itemMenu.addAction(self.deleteAction)
		self.ui.itemMenu.addSeparator()
		self.ui.itemMenu.addAction(self.toFrontAction)
		self.ui.itemMenu.addAction(self.sendBackAction)

	def createItems(self):	# Создание меню с педметами и фонами
		self.buttonGroup = QButtonGroup()
		self.buttonGroup.setExclusive(False)
		self.buttonGroup.buttonClicked[int].connect(self.buttonGroupClicked)

		layout = QGridLayout()
		layout.addWidget(self.createCellWidget("Условие", DiagramItem.Conditional), 0, 0)
		layout.addWidget(self.createCellWidget("Процесс", DiagramItem.Step), 0, 1)
		layout.addWidget(self.createCellWidget("Ввод/Вывод", DiagramItem.Io), 1, 0)

		textButton = QToolButton()
		textButton.setCheckable(True)
		self.buttonGroup.addButton(textButton, self.InsertTextButton)
		textButton.setIcon(QIcon(QPixmap(':/icons/img/textpointer.png').scaled(30, 30)))
		textButton.setIconSize(QSize(50, 50))

		textLayout = QGridLayout()
		textLayout.addWidget(textButton, 0, 0, Qt.AlignHCenter)
		textLayout.addWidget(QLabel("Текст"), 1, 0, Qt.AlignCenter)
		textWidget = QWidget()
		textWidget.setLayout(textLayout)
		layout.addWidget(textWidget, 1, 1)

		layout.setRowStretch(3, 10)
		layout.setColumnStretch(2, 10)

		itemWidget = QWidget()
		itemWidget.setLayout(layout)

		self.backgroundButtonGroup = QButtonGroup()
		self.backgroundButtonGroup.buttonClicked.connect(self.backgroundButtonGroupClicked)

		backgroundLayout = QGridLayout()
		backgroundLayout.addWidget(self.createBackgroundCellWidget("Синяя сетка",
				':/bg/img/background1.png'), 0, 0)
		backgroundLayout.addWidget(self.createBackgroundCellWidget("Белая сетка",
				':/bg/img/background2.png'), 0, 1)
		backgroundLayout.addWidget(self.createBackgroundCellWidget("Серая сетка",
				':/bg/img/background3.png'), 1, 0)
		backgroundLayout.addWidget(self.createBackgroundCellWidget("Без сетки",
				':/bg/img/background4.png'), 1, 1)

		backgroundLayout.setRowStretch(2, 10)
		backgroundLayout.setColumnStretch(2, 10)

		backgroundWidget = QWidget()
		backgroundWidget.setLayout(backgroundLayout)

		self.ui.toolBox.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Ignored))
		self.ui.toolBox.setMinimumWidth(itemWidget.sizeHint().width())
		self.ui.toolBox.addItem(itemWidget, "Предметы")
		self.ui.toolBox.addItem(backgroundWidget, "Фон")

	def createToolbars(self):	# Создание патели инструментов со шрифтами, зумом и всем таким
		self.editToolBar = QToolBar(self)
		self.editToolBar.setObjectName("Edit")
		self.editToolBar.addAction(self.deleteAction)
		self.editToolBar.addAction(self.toFrontAction)
		self.editToolBar.addAction(self.sendBackAction)

		self.fontCombo = QFontComboBox()
		self.fontCombo.currentFontChanged.connect(self.currentFontChanged)
		self.fontCombo.setStatusTip("Шрифт")

		self.fontSizeCombo = QComboBox()
		self.fontSizeCombo.setEditable(True)
		for i in range(8, 30, 2):
			self.fontSizeCombo.addItem(str(i))
		validator = QIntValidator(2, 64, self)
		self.fontSizeCombo.setValidator(validator)
		self.fontSizeCombo.currentIndexChanged.connect(self.fontSizeChanged)
		self.fontSizeCombo.setStatusTip("Размер шрифта")

		self.fontColorToolButton = QToolButton()
		self.fontColorToolButton.setPopupMode(QToolButton.MenuButtonPopup)
		self.fontColorToolButton.setMenu(
				self.createColorMenu(self.textColorChanged, Qt.black))
		self.fontColorToolButton.setStatusTip("Цвет текста")

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
		self.fillColorToolButton.setStatusTip("Цвет предметов")

		self.lineColorToolButton = QToolButton()
		self.lineColorToolButton.setPopupMode(QToolButton.MenuButtonPopup)
		self.lineColorToolButton.setMenu(
				self.createColorMenu(self.lineColorChanged, Qt.black))
		self.lineAction = self.lineColorToolButton.menu().defaultAction()
		self.lineColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/linecolor.png',
						Qt.black))
		self.lineColorToolButton.clicked.connect(self.lineButtonTriggered)
		self.lineColorToolButton.setStatusTip("Цвет стрелки")

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
		pointerButton.setStatusTip("Курсор")
		linePointerButton = QToolButton()
		linePointerButton.setCheckable(True)
		linePointerButton.setIcon(QIcon(':/icons/img/linepointer.png'))
		linePointerButton.setStatusTip("Стрелка")

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
		sceneScalePlus.setStatusTip("Увеличить диаграмму")
		sceneScaleMinus = QToolButton()
		sceneScaleMinus.setText("-")
		sceneScaleMinus.clicked.connect(self.sceneScaleMinus)
		sceneScaleMinus.setStatusTip("Уменьшить диаграмму")

		self.sceneScaleToolBar = QToolBar()
		self.sceneScaleToolBar.setObjectName("Scale")
		self.sceneScaleToolBar.addWidget(sceneScalePlus)
		self.sceneScaleToolBar.addWidget(sceneScaleMinus)

		self.addToolBar(Qt.LeftToolBarArea, self.editToolBar)
		self.addToolBar(self.textToolBar)
		self.addToolBar(Qt.LeftToolBarArea, self.colorToolBar)
		self.addToolBar(Qt.LeftToolBarArea, self.pointerToolbar)
		self.addToolBar(self.sceneScaleToolBar)
		self.setContextMenuPolicy(Qt.NoContextMenu)

	def createActions(self):	# Создание действий, подсказок, комбинаций кнопок для кнопок
		self.toFrontAction = QAction(
				QIcon(':/icons/img/bringtofront.png'), "На передний план",
				self, shortcut="Ctrl+F", statusTip="Поместить предмет на передний план",
				triggered=self.bringToFront)

		self.sendBackAction = QAction(
				QIcon(':/icons/img/sendtoback.png'), "На задний план", self,
				shortcut="Ctrl+B", statusTip="Отправить предмет на задний план",
				triggered=self.sendToBack)

		self.deleteAction = QAction(QIcon(':/icons/img/delete.png'),
				"Удалить", self, shortcut="Delete",
				statusTip="Удалить элемент с диаграммы",
				triggered=self.deleteItem)

		self.boldAction = QAction(QIcon(':/icons/img/bold.png'),
				"Жирный шрифт", self, checkable=True, shortcut="Ctrl+B",
				statusTip="Жирный шрифт", triggered=self.handleFontChange)

		self.italicAction = QAction(QIcon(':/icons/img/italic.png'),
				"Курсив", self, checkable=True, shortcut="Ctrl+I",
				statusTip="Курсив", triggered=self.handleFontChange)

		self.underlineAction = QAction(
				QIcon(':/icons/img/underline.png'), "Подчеркнутый", self,
				checkable=True, shortcut="Ctrl+U", statusTip="Подчеркнутый",
				triggered=self.handleFontChange)

	def createColorMenu(self, slot, defaultColor):	# Создание меню с выбором цвета
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

	def createBackgroundCellWidget(self, text, image):	# Генерация кнопок фона
		button = QToolButton()
		button.setText(text)
		button.setIcon(QIcon(image))
		button.setIconSize(QSize(50, 50))
		button.setCheckable(True)
		self.backgroundButtonGroup.addButton(button)

		layout = QGridLayout()
		layout.addWidget(button, 0, 0, Qt.AlignHCenter)
		layout.addWidget(QLabel(text), 1, 0, Qt.AlignCenter)

		widget = QWidget()
		widget.setLayout(layout)

		return widget

	def createCellWidget(self, text, diagramType):	# Генерация кнопок предметов
		item = DiagramItem(diagramType, self.itemMenu)
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

	def createColorIcon(self, color):	# Генерация кнопок с цветом
		pixmap = QPixmap(20, 20)
		painter = QPainter(pixmap)
		painter.setPen(Qt.NoPen)
		painter.fillRect(QRect(0, 0, 20, 20), color)
		painter.end()

		return QIcon(pixmap)

	def handleFontChange(self):	# Для шрифтов
		font = self.fontCombo.currentFont()
		font.setPointSize(int(self.fontSizeCombo.currentText()))
		if self.boldAction.isChecked():
			font.setWeight(QFont.Bold)
		else:
			font.setWeight(QFont.Normal)
		font.setItalic(self.italicAction.isChecked())
		font.setUnderline(self.underlineAction.isChecked())

		self.scene.setFont(font)

	def deleteItem(self):	# Удаление предметов
		for item in self.scene.selectedItems():
			if isinstance(item, DiagramItem):
				item.removeArrows()
			self.scene.removeItem(item)

	def sceneScalePlus(self):	# Увеличение сцены
		self.ui.canvas.scale(self.scaleUpFactor, self.scaleUpFactor)
	
	def sceneScaleMinus(self):	# Уменьшение сцены
		self.ui.canvas.scale(1.0/self.scaleUpFactor, 1.0/self.scaleUpFactor)
	
	def pointerGroupClicked(self, i):	# Изменение режимов создание стрелки и курсор
		self.scene.setMode(self.pointerTypeGroup.checkedId())

	def bringToFront(self):		# Переместить на передний план
		if not self.scene.selectedItems():
			return

		selectedItem = self.scene.selectedItems()[0]
		overlapItems = selectedItem.collidingItems()

		zValue = 0
		for item in overlapItems:
			if (item.zValue() >= zValue and isinstance(item, DiagramItem)):
				zValue = item.zValue() + 0.1
		selectedItem.setZValue(zValue)

	def sendToBack(self):	# Переместить на задний план
		if not self.scene.selectedItems():
			return

		selectedItem = self.scene.selectedItems()[0]
		overlapItems = selectedItem.collidingItems()

		zValue = 0
		for item in overlapItems:
			if (item.zValue() <= zValue and isinstance(item, DiagramItem)):
				zValue = item.zValue() - 0.1
		selectedItem.setZValue(zValue)

	def currentFontChanged(self, font):	# Метод исполняемый при изменении шрифта
		self.handleFontChange()

	def fontSizeChanged(self, font):	# Метод исполняемый при изменении размера шрифта
		self.handleFontChange()

	def textColorChanged(self):		# Обновление кнопки изменения цвета текста и изменение цвета теста
		self.textAction = self.sender()
		self.fontColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/textpointer.png',
						QColor(self.textAction.data())))
		self.textButtonTriggered()

	def itemColorChanged(self):		# Обновление кнопки изменения цвета предмета и изменение цвета предмета
		self.fillAction = self.sender()
		self.fillColorToolButton.setIcon(
				self.createColorToolButtonIcon( ':/icons/img/floodfill.png',
						QColor(self.fillAction.data())))
		self.fillButtonTriggered()

	def lineColorChanged(self):		# Обновление кнопки изменения цвета стрелки и изменение цвета стрелки
		self.lineAction = self.sender()
		self.lineColorToolButton.setIcon(
				self.createColorToolButtonIcon(':/icons/img/linecolor.png',
						QColor(self.lineAction.data())))
		self.lineButtonTriggered()

	def createColorToolButtonIcon(self, imageFile, color):	# Изменение цвета кнопки смены цвета
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

	def textButtonTriggered(self):	# Изменение цвета теста
		self.scene.setTextColor(QColor(self.textAction.data()))

	def fillButtonTriggered(self):	# Изменение цвета предмета
		self.scene.setItemColor(QColor(self.fillAction.data()))

	def lineButtonTriggered(self):	# Изменение цвета стрелки
		self.scene.setLineColor(QColor(self.lineAction.data()))

	def buttonGroupClicked(self, id):	# Установка нужного режима при нажатии кнопки предмета
		buttons = self.buttonGroup.buttons()
		for button in buttons:
			if self.buttonGroup.button(id) != button:
				button.setChecked(False)

		if id == self.InsertTextButton:
			self.scene.setMode(DiagramScene.InsertText)
		else:
			self.scene.setItemType(id)
			self.scene.setMode(DiagramScene.InsertItem)
	
	def itemInserted(self, item):	# Снятие выбора с кнопки при создании предмета
		self.pointerTypeGroup.button(DiagramScene.MoveItem).setChecked(True)
		self.scene.setMode(self.pointerTypeGroup.checkedId())		
		self.buttonGroup.button(item.diagramType).setChecked(False)

	def textInserted(self, item):	# Снятие выбора с кнопки при создании текста
		self.buttonGroup.button(self.InsertTextButton).setChecked(False)
		self.scene.setMode(self.pointerTypeGroup.checkedId())

	def itemSelected(self, item):	# Установка всех списков, кнопок на панели инструментов связаных с текстом
		font = item.font()			# на параметры выбранного текста
		self.fontCombo.setCurrentFont(font)
		self.fontSizeCombo.setEditText(str(font.pointSize()))
		self.boldAction.setChecked(font.weight() == QFont.Bold)
		self.italicAction.setChecked(font.italic())
		self.underlineAction.setChecked(font.underline())

	def backgroundButtonGroupClicked(self, button):		# Изменение фона
		buttons = self.backgroundButtonGroup.buttons()
		for buttonL in buttons:
			if buttonL != button:
				buttonL.setChecked(False)

		text = button.text()
		if text == "Синяя сетка":
			self.scene.setBackgroundBrush(QBrush(QPixmap(':/bg/img/background1.png')))
		elif text == "Белая сетка":
			self.scene.setBackgroundBrush(QBrush(QPixmap(':/bg/img/background2.png')))
		elif text == "Серая сетка":
			self.scene.setBackgroundBrush(QBrush(QPixmap(':/bg/img/background3.png')))
		else:
			self.scene.setBackgroundBrush(QBrush(QPixmap(':/bg/img/background4.png')))

		self.scene.update()
		self.ui.canvas.update()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Ui()
	window.show()
	sys.exit(app.exec_())