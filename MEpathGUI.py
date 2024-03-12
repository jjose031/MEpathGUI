

# MePathGUI version 1.2.0
# Mar 12, 2024

# by Jason Josephson
# Thank you to pythonguis.com and all the answers on stack.
# Please forgive the amateur writing of this code and help me learn by reporting
# bugs and giving feedback.

import re, sys
from math import floor
import numpy as np
import qdarktheme
import matplotlib.pyplot as plt
import matplotlib.font_manager
from matplotlib import use
use('Qt5Agg')
from operator import itemgetter
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.patches import Circle
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage, AnnotationBbox)
from matplotlib.cbook import get_sample_data
import pandas as pd
from PyQt5.QtGui import QDrag, QColor, QRegExpValidator, QIcon, QFont
from PyQt5.QtCore import QSize, Qt, QMimeData, QPoint, pyqtSignal, QRegExp
from PyQt5.QtWidgets import QSpacerItem, QDialog, QTabWidget, QGroupBox, QSizePolicy, QGraphicsScene, QDoubleSpinBox, QFileDialog, QSpinBox, QColorDialog, QScrollArea, QApplication, QGridLayout, QLabel, QLineEdit, QVBoxLayout, QWidget, QCheckBox, QPushButton, QComboBox

possibleFonts = sorted([x.split('\\')[-1].split('.')[0] for x in matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')], key = str.lower)

df = pd.DataFrame([], columns = ['type', 'name', 'xvalue', 'yvalue', 'namefont' ,'namefontsize' ,'namefontcolour' ,'namefontdx' ,'namefontdy' ,'yfont' ,'yfontsize' ,'yfontcolour' ,'yfontdx' ,'yfontdy' ,'linecolour' ,'linestyle' ,'partner1name' ,'partner2name', 'visibleline', 'visiblename', 'visibleenergy'])

defaults = {'namefont':'Arial', 'namefontsize':14, 'namefontcolour':'black', 'namefontdx':0, 'namefontdy':0.5, 'yfont':'Arial', 'yfontsize':14, 'yfontcolour':'black', 'yfontdx':0, 'yfontdy':-0.75, 'linecolourspecies':'black', 'linecolourconnection': 'black', 'linestylespecies':'solid', 'linestyleconnection':'dashed'}

graphSettings = {'title':'', 'figure width':1000, 'figure height':600, 'x gridlines':False, 'y gridlines':False, 'width':1, 'spacing':1, 'title font':'Arial', 'title font size':16, 'title font colour':'black', 'x-axis range auto':True, 'x-axis range min':0, 'x-axis range max':5, 'x-axis visible':False, 'x-axis title':'', 'x-axis label size':12, 'x-axis label colour':'black', 'x-axis title size':14, 'x-axis title font':'Arial', 'x-axis title colour':'black', 'y-axis range auto':True, 'y-axis range min':-20, 'y-axis range max':20, 'y-axis visible':True, 'y-axis title':'Energy (kcal/mol)', 'y-axis title size':14, 'y-axis title font':'Arial', 'y-axis title colour':'black', 'y-axis label size':12, 'y-axis label colour':'black', 'y-axis ticks visible':True, 'x-axis ticks visible':False}

redrawn = False

def newRow(type, name = None, xvalue = None, yvalue = None, partner1name = None, partner2name = None):
    global df
    if type.lower().strip() == 'species':
        new = pd.DataFrame([['species', name, xvalue, yvalue, defaults['namefont'], defaults['namefontsize'], defaults['namefontcolour'], defaults['namefontdx'], defaults['namefontdy'], defaults['yfont'], defaults['yfontsize'], defaults['yfontcolour'], defaults['yfontdx'], defaults['yfontdy'], defaults['linecolourspecies'], defaults['linestylespecies'], None, None, 2, 2, 2]], columns=['type', 'name', 'xvalue', 'yvalue', 'namefont', 'namefontsize', 'namefontcolour', 'namefontdx', 'namefontdy', 'yfont', 'yfontsize', 'yfontcolour', 'yfontdx', 'yfontdy', 'linecolour', 'linestyle', 'partner1name', 'partner2name', 'visibleline', 'visiblename', 'visibleenergy'])
        new.index = [name]
    elif type.lower().strip() == 'connection':
        spartner1, spartner2 = sorted([partner1name, partner2name])
        new = pd.DataFrame([['connection', None, None, None, None, None, None, None, None, None, None, None, None, None, defaults['linecolourconnection'], defaults['linestyleconnection'], spartner1, spartner2, 2, 0, 0]], columns=['type', 'name', 'xvalue', 'yvalue', 'namefont', 'namefontsize', 'namefontcolour', 'namefontdx', 'namefontdy', 'yfont', 'yfontsize', 'yfontcolour', 'yfontdx', 'yfontdy', 'linecolour', 'linestyle', 'partner1name', 'partner2name', 'visibleline', 'visiblename', 'visibleenergy'])
        new.index = [f'{spartner1}⌬{spartner2}']

    return pd.concat([df, new])

class DragButton(QPushButton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pressPos = None
        self.pressPos2 = None

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)
            #pixmap = QPixmap(self.size())
            #self.render(pixmap)
            #drag.setPixmap(pixmap)
            drag.exec(Qt.MoveAction)
            window.redraw(self.text())

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.pressPos = e.pos()
        elif e.button() == Qt.RightButton:
            self.pressPos2 = e.pos()

    def mouseReleaseEvent(self, e):
        global df

        if (self.pressPos2 is not None and e.button() == Qt.RightButton and e.pos() in self.rect()):
            self.toggle()
            for button in window.buttonlist:
                if button.isChecked() and button is not self:
                    name1 = re.split(r' \| ', self.text())[0]
                    name2 = re.split(r' \| ', button.text())[0]
                    sname1, sname2 = sorted([name1, name2])
                    try:
                        df.loc[f'{sname1}⌬{sname2}']
                    except KeyError:
                        df = newRow('connection', partner1name = name1, partner2name = name2)
                    else:
                        df = df.drop([f'{sname1}⌬{sname2}'], axis = 0)
                    window.makeGrid()
                    if redrawn:
                        window.redraw(f'{window.name} | {window.energy}')
                    self.toggle()
                    button.toggle()
                    break


        if (self.pressPos is not None and e.button() == Qt.LeftButton and e.pos() in self.rect()):
                self.clicked.emit()
                window.redraw(self.text())

        self.pressPos = None
        self.pressPos2 = None

    def mouseDoubleClickEvent(self, e):
        global df

        if e.buttons() == Qt.MiddleButton:
            for i in reversed(range(window.slayout.count())):
                window.slayout.itemAt(i).widget().setParent(None)
            name = re.split(r' \| ', self.text())[0]
            df = df.drop([name], axis = 0)
            for item in list(df[df['type'] == 'connection'].index):
                if name in re.split('⌬', item):
                    df = df.drop([item], axis = 0)
            self.close()
            window.makeGrid()

        if e.buttons() == Qt.LeftButton:
            self.msg = EditSpeciesWindow()
            name, energy = re.split(r' \| ', self.text())
            self.msg.cur = name
            self.msg.widget.setText(name)
            self.msg.widget.selectAll()
            self.msg.widget2.setText(energy)
            self.msg.button.clicked.connect(self.dfEdit)
            self.msg.setModal(True)
            self.msg.show()

    def dfEdit(self):
        global df
        name = re.split(r' \| ', self.text())[0]

        old = df.loc[name].copy()

        old['name'] = self.msg.widget.text()
        old['yvalue'] = float(self.msg.widget2.text())
        old.name = self.msg.widget.text()

        for idx, item in enumerate(df[df['type'] == 'connection'].index):
            if name in re.split('⌬', item):
                if name == re.split('⌬', item)[0]:
                    otherName = re.split('⌬', item)[1]
                else:
                    otherName = re.split('⌬', item)[0]
                df.drop([item], axis = 0, inplace = True)
                df = newRow('connection', partner1name = otherName, partner2name = self.msg.widget.text())
                break

        df.drop([name], axis = 0, inplace = True)
        df = pd.concat([df,pd.DataFrame(old).transpose()])

        self.msg.close()
        window.makeGrid()
        window.redraw(f'{self.msg.widget.text()} | {self.msg.widget2.text()}')

class ColorButton(QPushButton):

    colorChanged = pyqtSignal(object)

    def __init__(self, *args, color=None, **kwargs):
        super(ColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self._default = color
        self.pressed.connect(self.onColorPicker)

        self.setColor(self._default)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        self.setStyleSheet("")
        dlg = QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.setColor(self._default)

        return super(ColorButton, self).mousePressEvent(e)

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=graphSettings['figure width'], height=graphSettings['figure height'], dpi=100):
        self.dpi = dpi
        self.fig = Figure(figsize=(width, height), dpi=self.dpi)
        super(MplCanvas, self).__init__(self.fig)
        self.axes = self.fig.add_subplot(111)

        FigureCanvasQTAgg.__init__(self, self.fig)
        self.setParent(parent)

        #FigureCanvasQTAgg.setSizePolicy(self,
                #QSizePolicy.Expanding,
                #QSizePolicy.Expanding)
        #FigureCanvasQTAgg.updateGeometry(self)
        self.plot()

    def plot(self):
        global df, graphSettings
        self.axes.cla()

        self.fig = Figure(figsize = (graphSettings['figure width'], graphSettings['figure height']), dpi = self.dpi)

        for ix in df[df['type'] == 'species'].index:
            x1 = (graphSettings['width'] + graphSettings['spacing']) * df.loc[ix, 'xvalue']
            x2 = x1 + graphSettings['width']
            y = df.loc[ix, 'yvalue']
            colour = df.loc[ix, 'linecolour']
            style = df.loc[ix, 'linestyle']
            if df.loc[ix, 'visibleline']:
                self.axes.plot([x1, x2], [y, y], color = colour, linestyle = style)
            if df.loc[ix, 'visiblename']:
                nameFont = df.loc[ix, 'namefont']
                nameXPos = (x1 + x2)/2 + df.loc[ix, 'namefontdx']
                nameYPos = y + df.loc[ix, 'namefontdy']
                nameTxt = df.loc[ix, 'name']
                nameColour = df.loc[ix, 'namefontcolour']
                nameSize = df.loc[ix, 'namefontsize']
                self.axes.text(nameXPos, nameYPos, nameTxt, color=nameColour, size=nameSize, family = nameFont, horizontalalignment='center')
            if df.loc[ix, 'visibleenergy']:
                enFont = df.loc[ix, 'yfont']
                enXPos = (x1 + x2)/2 + df.loc[ix, 'yfontdx']
                enYPos = y + df.loc[ix, 'yfontdy']
                enTxt = df.loc[ix, 'yvalue']
                enColour = df.loc[ix, 'yfontcolour']
                enSize = df.loc[ix, 'yfontsize']
                self.axes.text(enXPos, enYPos, enTxt, color=enColour, fontsize=enSize, family = enFont, horizontalalignment='center')

        for ix in df[df['type'] == 'connection'].index:
            partner1, partner2 = df.loc[df.loc[ix, 'partner1name']], df.loc[df.loc[ix, 'partner2name']]
            spartner1, spartner2 = sorted([[partner1, partner1['xvalue']], [partner2, partner2['xvalue']]], key = lambda s: s[1])
            x1 = (graphSettings['width'] + graphSettings['spacing']) * spartner1[1] + graphSettings['width']
            x2 = (graphSettings['width'] + graphSettings['spacing']) * spartner2[1]
            y1 = spartner1[0]['yvalue']
            y2 = spartner2[0]['yvalue']
            colour = df.loc[ix, 'linecolour']
            style = df.loc[ix, 'linestyle']
            if df.loc[ix, 'visibleline']:
                self.axes.plot([x1, x2], [y1, y2], color = colour, linestyle = style)

        self.axes.set_title(graphSettings['title'], family = graphSettings['title font'], fontsize = graphSettings['title font size'], color = graphSettings['title font colour'])

        if not graphSettings['y-axis range auto']:
            self.axes.set_ylim(top = graphSettings['y-axis range max'], bottom = graphSettings['y-axis range min'])
        if not graphSettings['x-axis range auto']:
            self.axes.set_xlim(right = graphSettings['x-axis range max'], left = graphSettings['x-axis range min'])

        if graphSettings['y-axis visible']:
            self.axes.set_ylabel(graphSettings['y-axis title'], family = graphSettings['y-axis title font'], color = graphSettings['y-axis title colour'], fontsize = graphSettings['y-axis title size'])
            if graphSettings['y-axis ticks visible']:
                self.axes.tick_params(left = True, axis = 'y', labelcolor = graphSettings['y-axis label colour'], labelsize = graphSettings['y-axis label size'])
            else:
                self.axes.tick_params(left = False, axis = 'y')
                self.axes.set(yticklabels = [])
        else:
            self.axes.set_ylabel(None)
            self.axes.tick_params(left = False, axis = 'y')
            self.axes.set(yticklabels = [])

        if graphSettings['x-axis visible']:
            self.axes.set_xlabel(graphSettings['x-axis title'], family = graphSettings['x-axis title font'], color = graphSettings['x-axis title colour'], fontsize = graphSettings['x-axis title size'])
            if graphSettings['x-axis ticks visible']:
                self.axes.tick_params(bottom = True, axis = 'x', labelcolor = graphSettings['x-axis label colour'], labelsize = graphSettings['x-axis label size'])
            else:
                self.axes.tick_params(bottom = False, axis = 'x')
                self.axes.set(xticklabels = [])
        else:
            self.axes.set_xlabel(None)
            self.axes.tick_params(bottom = False, axis = 'x')
            self.axes.set(xticklabels = [])

        if graphSettings['x gridlines']:
            self.axes.grid(axis = 'x')
        if graphSettings['y gridlines']:
            self.axes.grid(axis = 'y')

        for key in graphSettings:
            if 'imageGraph' in key:
                if graphSettings[key]['visible']:

                    path = graphSettings[key]['name']
                    scale = float(graphSettings[key]['scale'])
                    xpos = float(graphSettings[key]['x'])
                    ypos = float(graphSettings[key]['y'])

                    fn = get_sample_data(path, asfileobj=False)
                    arr_img = plt.imread(fn, format='png')
                    imagebox = OffsetImage(arr_img, zoom=scale)
                    imagebox.image.axes = self.axes
                    ab = AnnotationBbox(imagebox, (xpos,ypos), xycoords='data', boxcoords="offset points", pad=0, frameon = False)
                    self.axes.add_artist(ab)


        self.draw()

class MainWindow(QWidget):

    def __init__(self, *args, **kwargs):
        global df, graphSettings
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

        self.setGeometry(50, 50, 900, 900)
        self.setWindowIcon(QIcon('icon2.png'))
        self.setWindowTitle('MEpathGUI')

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        #self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.button = QPushButton("New species")
        self.button.clicked.connect(self.showdialog)
        self.button.setFont(QFont('Arial', 12))
        #self.button.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.createConnection = QPushButton("New Connection")
        self.createConnection.clicked.connect(self.connectionWindow)
        self.createConnection.setFont(QFont('Arial', 12))
        #self.createConnection.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.blayout = QGridLayout()

        self.dragdrop = QWidget()
        self.dragdrop.setLayout(self.blayout)
        self.dragdrop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.dragdrop)
        self.scroll.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.slayout = QGridLayout()

        self.speciesField = QWidget()
        self.speciesField.setLayout(self.slayout)

        self.save = QPushButton('SAVE\nIMAGE')
        self.save.clicked.connect(self.file_save)
        self.save.setShortcut('Ctrl+S')
        self.save.setFont(QFont('Arial', 13))
        self.save.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.exporter = QPushButton('EXPORT\nCSV')
        self.exporter.clicked.connect(self.exportcsv)
        self.exporter.setFont(QFont('Arial', 13))
        self.exporter.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.importer = QPushButton('IMPORT\nCSV')
        self.importer.clicked.connect(self.importcsv)
        self.importer.setFont(QFont('Arial', 13))
        self.importer.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.imggraphadd = QPushButton('ADD IMAGE')
        self.imggraphadd.clicked.connect(lambda: self.imageGraph(new = True))
        self.imggraphadd.setFont(QFont('Arial', 12))

        self.wwidth = QSpinBox()
        self.wwidth.setValue(graphSettings['width'])
        self.wwidth.valueChanged.connect(lambda a: self.changeGraph('width', a))

        self.spacing = QSpinBox()
        self.spacing.setValue(graphSettings['spacing'])
        self.spacing.valueChanged.connect(lambda a: self.changeGraph('spacing', a))

        self.title = QLineEdit()
        self.title.setPlaceholderText('Graph title')
        self.title.editingFinished.connect(lambda: self.changeGraph('title', self.title.text()))

        self.titleFont = QComboBox()
        self.titleFont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        self.titleFont.setCurrentText(graphSettings['title font'])
        self.titleFont.currentIndexChanged.connect(lambda a: self.changeGraph('title font', self.titleFont.itemText(a)))

        self.titlesize = QSpinBox()
        self.titlesize.setValue(graphSettings['title font size'])
        self.titlesize.valueChanged.connect(lambda a: self.changeGraph('title font size', a))

        self.titlecolour = ColorButton('Colour')
        self.titlecolour.setColor(graphSettings['title font colour'])
        self.titlecolour.colorChanged.connect(lambda a: self.changeGraph('title font colour', a))

        self.yaxisrangeauto = QCheckBox("y-axis auto range")
        self.yaxisrangeauto.setChecked(graphSettings['y-axis range auto'])
        self.yaxisrangeauto.stateChanged.connect(lambda a: self.changeGraph('y-axis range auto', a))
        self.yaxisrangeauto.stateChanged.connect(lambda a: self.autorange((self.yaxismin, self.yaxismax), a))

        self.yaxismin = QDoubleSpinBox()
        self.yaxismin.setEnabled(not graphSettings['y-axis range auto'])
        self.yaxismin.setMinimum(-2147483647)
        self.yaxismin.setMaximum(2147483647)
        self.yaxismin.setValue(graphSettings['y-axis range min'])
        self.yaxismin.valueChanged.connect(lambda a: self.changeGraph('y-axis range min', a))

        self.yaxismax = QDoubleSpinBox()
        self.yaxismax.setEnabled(not graphSettings['y-axis range auto'])
        self.yaxismax.setMaximum(2147483647)
        self.yaxismax.setMinimum(-2147483647)
        self.yaxismax.setValue(graphSettings['y-axis range max'])
        self.yaxismax.valueChanged.connect(lambda a: self.changeGraph('y-axis range max', a))

        self.yaxistitle = QLineEdit()
        self.yaxistitle.setPlaceholderText('y-Axis title')
        self.yaxistitle.setText(graphSettings['y-axis title'])
        self.yaxistitle.editingFinished.connect(lambda: self.changeGraph('y-axis title', self.yaxistitle.text()))

        self.ytitlefont = QComboBox()
        self.ytitlefont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        self.ytitlefont.setCurrentText(graphSettings['y-axis title font'])
        self.ytitlefont.currentIndexChanged.connect(lambda a: self.changeGraph('y-axis title font', self.ytitlefont.itemText(a)))

        self.ytitlesize = QSpinBox()
        self.ytitlesize.setValue(graphSettings['y-axis title size'])
        self.ytitlesize.valueChanged.connect(lambda a: self.changeGraph('y-axis title size', a))

        self.ytitlecolour = ColorButton('Colour')
        self.ytitlecolour.setColor(graphSettings['y-axis title colour'])
        self.ytitlecolour.colorChanged.connect(lambda a: self.changeGraph('y-axis title colour', a))

        self.ylabelsize = QSpinBox()
        self.ylabelsize.setValue(graphSettings['y-axis label size'])
        self.ylabelsize.valueChanged.connect(lambda a: self.changeGraph('y-axis label size', a))

        self.ylabelcolour = ColorButton('Colour')
        self.ylabelcolour.setColor(graphSettings['y-axis label colour'])
        self.ylabelcolour.colorChanged.connect(lambda a: self.changeGraph('y-axis label colour', a))

        self.yvisible = QCheckBox('y-axis visible')
        self.yvisible.setChecked(graphSettings['y-axis visible'])
        self.yvisible.stateChanged.connect(lambda a: self.changeGraph('y-axis visible', a))
        self.yvisible.stateChanged.connect(lambda a: self.autorange([self.yticksvisible], a))

        self.yticksvisible = QCheckBox('y-axis ticks visible')
        self.yticksvisible.setChecked(graphSettings['y-axis ticks visible'])
        self.yticksvisible.stateChanged.connect(lambda a: self.changeGraph('y-axis ticks visible', a))

        self.xaxisrangeauto = QCheckBox("x-axis auto range")
        self.xaxisrangeauto.setChecked(graphSettings['x-axis range auto'])
        self.xaxisrangeauto.stateChanged.connect(lambda a: self.changeGraph('x-axis range auto', a))
        self.xaxisrangeauto.stateChanged.connect(lambda a: self.autorange((self.xaxismin, self.xaxismax), a))

        self.xaxismin = QDoubleSpinBox()
        self.xaxismin.setEnabled(not graphSettings['x-axis range auto'])
        self.xaxismin.setMinimum(-2147483647)
        self.xaxismin.setMaximum(2147483647)
        self.xaxismin.setValue(graphSettings['x-axis range min'])
        self.xaxismin.valueChanged.connect(lambda a: self.changeGraph('x-axis range min', a))

        self.xaxismax = QDoubleSpinBox()
        self.xaxismax.setEnabled(not graphSettings['x-axis range auto'])
        self.xaxismax.setMaximum(2147483647)
        self.xaxismax.setMinimum(-2147483647)
        self.xaxismax.setValue(graphSettings['x-axis range max'])
        self.xaxismax.valueChanged.connect(lambda a: self.changeGraph('x-axis range max', a))

        self.xaxistitle = QLineEdit()
        self.xaxistitle.setText(graphSettings['x-axis title'])
        self.xaxistitle.setPlaceholderText('x-Axis title')
        self.xaxistitle.editingFinished.connect(lambda: self.changeGraph('x-axis title', self.xaxistitle.text()))

        self.xtitlefont = QComboBox()
        self.xtitlefont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        self.xtitlefont.setCurrentText(graphSettings['x-axis title font'])
        self.xtitlefont.currentIndexChanged.connect(lambda a: self.changeGraph('x-axis title font', self.xtitlefont.itemText(a)))

        self.xtitlesize = QSpinBox()
        self.xtitlesize.setValue(graphSettings['x-axis title size'])
        self.xtitlesize.valueChanged.connect(lambda a: self.changeGraph('x-axis title size', a))

        self.xtitlecolour = ColorButton('Colour')
        self.xtitlecolour.setColor(graphSettings['x-axis title colour'])
        self.xtitlecolour.colorChanged.connect(lambda a: self.changeGraph('x-axis title colour', a))

        self.xlabelsize = QSpinBox()
        self.xlabelsize.setValue(graphSettings['x-axis label size'])
        self.xlabelsize.valueChanged.connect(lambda a: self.changeGraph('x-axis label size', a))

        self.xlabelcolour = ColorButton('Colour')
        self.xlabelcolour.setColor(graphSettings['x-axis label colour'])
        self.xlabelcolour.colorChanged.connect(lambda a: self.changeGraph('x-axis label colour', a))

        self.xvisible = QCheckBox('x-axis visible')
        self.xvisible.setChecked(graphSettings['x-axis visible'])
        self.xvisible.stateChanged.connect(lambda a: self.changeGraph('x-axis visible', a))
        self.xvisible.stateChanged.connect(lambda a: self.autorange([self.xticksvisible], a))

        self.xticksvisible = QCheckBox('x-axis ticks visible')
        self.xticksvisible.setChecked(graphSettings['x-axis ticks visible'])
        self.xticksvisible.stateChanged.connect(lambda a: self.changeGraph('x-axis ticks visible', a))

        self.xgrid = QCheckBox('Gridlines x-axis')
        self.xgrid.stateChanged.connect(lambda a: self.changeGraph('x gridlines', a))

        self.ygrid = QCheckBox('Gridlines y-axis')
        self.ygrid.stateChanged.connect(lambda a: self.changeGraph('y gridlines', a))

        self.graphwidth = QSpinBox()
        self.graphwidth.setMaximum(2147483647)
        self.graphwidth.setValue(graphSettings['figure width'])
        self.graphwidth.valueChanged.connect(lambda a: self.changeGraph('figure width', a))
        self.graphwidth.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.graphwidth.setFont(QFont('Arial', 20))

        self.graphheight = QSpinBox()
        self.graphheight.setMaximum(2147483647)
        self.graphheight.setValue(graphSettings['figure height'])
        self.graphheight.valueChanged.connect(lambda a: self.changeGraph('figure height', a))
        self.graphheight.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.graphheight.setFont(QFont('Arial', 20))

        self.alllinevisible = QCheckBox("All lines visible")
        self.alllinevisible.setChecked(True)
        self.alllinevisible.stateChanged.connect(lambda a: self.groupChange('species', 'visibleline', a))

        self.alllinecolour = ColorButton('Colour')
        self.alllinecolour.setColor('black')
        self.alllinecolour.colorChanged.connect(lambda a: self.groupChange('species', 'linecolour', a))

        self.alllinestyle = QComboBox()
        self.alllinestyle.addItems(['solid', 'dotted', 'dashed', 'dashdot'])
        self.alllinestyle.setCurrentText('solid')
        self.alllinestyle.currentIndexChanged.connect(lambda a: self.groupChange('species', 'linestyle', self.allconnstyle.itemText(a)))

        self.allconncolour = ColorButton('Colour')
        self.allconncolour.setColor('black')
        self.allconncolour.colorChanged.connect(lambda a: self.groupChange('connection', 'linecolour', a))

        self.allconnstyle = QComboBox()
        self.allconnstyle.addItems(['solid', 'dotted', 'dashed', 'dashdot'])
        self.allconnstyle.setCurrentText('dashed')
        self.allconnstyle.currentIndexChanged.connect(lambda a: self.groupChange('connection', 'linestyle', self.allconnstyle.itemText(a)))

        self.allconnvisible = QCheckBox("All connecting lines visible")
        self.allconnvisible.setChecked(True)
        self.allconnvisible.stateChanged.connect(lambda a: self.groupChange('connection', 'visibleline', a))

        self.allnamefont = QComboBox()
        self.allnamefont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        self.allnamefont.setCurrentText('Arial')
        self.allnamefont.currentIndexChanged.connect(lambda a: self.groupChange('species', 'namefont', self.allnamefont.itemText(a)))

        self.allnamesize = QSpinBox()
        self.allnamesize.setValue(14)
        self.allnamesize.valueChanged.connect(lambda a: self.groupChange('species', 'namefontsize', a))

        self.allnamecolour = ColorButton('Colour')
        self.allnamecolour.setColor('black')
        self.allnamecolour.colorChanged.connect(lambda a: self.groupChange('species', 'namefontcolour', a))

        self.allnamedx = QDoubleSpinBox()
        self.allnamedx.setValue(0)
        self.allnamedx.setMaximum(9e99)
        self.allnamedx.setMinimum(-9e99)
        self.allnamedx.valueChanged.connect(lambda a: self.groupChange('species', 'namefontdx', a))

        self.allnamedy = QDoubleSpinBox()
        self.allnamedy.setValue(0.5)
        self.allnamedy.setMaximum(9e99)
        self.allnamedy.setMinimum(-9e99)
        self.allnamedy.valueChanged.connect(lambda a: self.groupChange('species', 'namefontdy', a))

        self.allnamevisible = QCheckBox("All labels visible")
        self.allnamevisible.setChecked(True)
        self.allnamevisible.stateChanged.connect(lambda a: self.groupChange('species', 'visiblename', a))

        self.allyfont = QComboBox()
        self.allyfont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        self.allyfont.setCurrentText('Arial')
        self.allyfont.setGeometry(0, 0, 10, self.allyfont.geometry().height())
        self.allyfont.currentIndexChanged.connect(lambda a: self.groupChange('species', 'yfont', self.allyfont.itemText(a)))

        self.allysize = QSpinBox()
        self.allysize.setValue(14)
        self.allysize.valueChanged.connect(lambda a: self.groupChange('species', 'yfontsize', a))

        self.allycolour = ColorButton('Colour')
        self.allycolour.setColor('black')
        self.allycolour.colorChanged.connect(lambda a: self.groupChange('species', 'yfontcolour', a))

        self.allydx = QDoubleSpinBox()
        self.allydx.setValue(0)
        self.allydx.setMaximum(9e99)
        self.allydx.setMinimum(-9e99)
        self.allydx.valueChanged.connect(lambda a: self.groupChange('species', 'yfontdx', a))

        self.allydy = QDoubleSpinBox()
        self.allydy.setValue(0.5)
        self.allydy.setMaximum(9e99)
        self.allydy.setMinimum(-9e99)
        self.allydy.valueChanged.connect(lambda a: self.groupChange('species', 'yfontdy', a))

        self.allyvisible = QCheckBox("All energies visible")
        self.allyvisible.setChecked(True)
        self.allyvisible.stateChanged.connect(lambda a: self.groupChange('species', 'visibleenergy', a))

        self.tabs = QTabWidget()

        self.graphwidthLabel = QLabel("Figure WIDTH")
        self.graphwidthLabel.setAlignment(Qt.AlignCenter)
        self.graphwidthLabel.setFont(QFont('Arial', 12))
        self.graphheightLabel = QLabel("Figure HEIGHT")
        self.graphheightLabel.setAlignment(Qt.AlignCenter)
        self.graphheightLabel.setFont(QFont('Arial', 12))

        self.glayout1 = QGridLayout()

        self.glayout1.addWidget(self.graphwidthLabel, 1, 4)
        self.glayout1.addWidget(self.graphheightLabel, 1, 5)

        self.glayout1.addWidget(self.save, 1, 1, 2, 1)
        self.glayout1.addWidget(self.exporter, 1, 2, 2, 1)
        self.glayout1.addWidget(self.importer, 1, 3, 2, 1)
        self.glayout1.addWidget(self.graphwidth, 2, 4)
        self.glayout1.addWidget(self.graphheight, 2, 5)

        self.glayout2 = QGridLayout()

        self.titleLabel = QLabel("Title:")
        self.gridlinesLabel = QLabel("Gridlines:")
        self.yyLabel = QLabel("y-Axis:")
        self.yrangeLabel = QLabel("y Range:")
        self.ytitleLabel = QLabel("y Title:")
        self.xxLabel = QLabel("x-Axis:")
        self.xrangeLabel = QLabel("x Range:")
        self.xtitleLabel = QLabel("x Title:")

        self.glayout2.addWidget(self.titleLabel, 3, 0)
        self.glayout2.addWidget(self.title, 3, 1)
        self.glayout2.addWidget(self.titlesize, 3, 2)
        self.glayout2.addWidget(self.titlecolour, 3, 3)
        self.glayout2.addWidget(self.titleFont, 3, 4)

        self.glayout2.addWidget(self.gridlinesLabel, 4, 0)
        self.glayout2.addWidget(self.ygrid, 4, 1)
        self.glayout2.addWidget(self.xgrid, 4, 2)

        self.glayout2.addWidget(self.yyLabel, 5, 0)
        self.glayout2.addWidget(self.yvisible, 5, 1)
        self.glayout2.addWidget(self.yticksvisible, 5, 2)
        self.glayout2.addWidget(self.ylabelsize, 5, 3)
        self.glayout2.addWidget(self.ylabelcolour, 5, 4)

        self.glayout2.addWidget(self.yrangeLabel, 6, 0)
        self.glayout2.addWidget(self.yaxisrangeauto, 6, 1)
        self.glayout2.addWidget(self.yaxismax, 6, 2)
        self.glayout2.addWidget(self.yaxismin, 6, 3)

        self.glayout2.addWidget(self.ytitleLabel, 7, 0)
        self.glayout2.addWidget(self.yaxistitle, 7, 1)
        self.glayout2.addWidget(self.ytitlesize, 7, 2)
        self.glayout2.addWidget(self.ytitlecolour, 7, 3)
        self.glayout2.addWidget(self.ytitlefont, 7, 4)

        self.glayout2.addWidget(self.xxLabel, 8, 0)
        self.glayout2.addWidget(self.xvisible, 8, 1)
        self.glayout2.addWidget(self.xticksvisible, 8, 2)
        self.glayout2.addWidget(self.xlabelsize, 8, 3)
        self.glayout2.addWidget(self.xlabelcolour, 8, 4)

        self.glayout2.addWidget(self.xrangeLabel, 9, 0)
        self.glayout2.addWidget(self.xaxisrangeauto, 9, 1)
        self.glayout2.addWidget(self.xaxismax, 9, 2)
        self.glayout2.addWidget(self.xaxismin, 9, 3)

        self.glayout2.addWidget(self.xtitleLabel, 10, 0)
        self.glayout2.addWidget(self.xaxistitle, 10, 1)
        self.glayout2.addWidget(self.xtitlesize, 10, 2)
        self.glayout2.addWidget(self.xtitlecolour, 10, 3)
        self.glayout2.addWidget(self.xtitlefont, 10, 4)

        self.glayout3 = QGridLayout()

        self.scaleLabel = QLabel("Scale")
        self.scaleLabel.setFont(QFont('Arial', 12))

        self.xposLabel = QLabel("x-Position")
        self.xposLabel.setFont(QFont('Arial', 12))

        self.yposLabel = QLabel("y-Position")
        self.yposLabel.setFont(QFont('Arial', 12))

        self.glayout3.addWidget(self.imggraphadd, 1, 1)
        self.glayout3.addWidget(self.scaleLabel, 1, 2)
        self.glayout3.addWidget(self.xposLabel, 1, 3)
        self.glayout3.addWidget(self.yposLabel, 1, 4)

        self.g1l = QWidget()
        self.g1l.setLayout(self.glayout1)
        self.g2l = QWidget()
        self.g2l.setLayout(self.glayout2)
        self.g3l = QScrollArea()
        self.g3l.setLayout(self.glayout3)

        self.tabs.addTab(self.g1l, "Save/Import/Export")
        self.tabs.addTab(self.g2l, "Edit graph")
        self.tabs.addTab(self.g3l, "Images")
        self.tabs.setStyleSheet('QTabBar {font-size: 12pt}')


        self.adjustAll = QGridLayout()

        self.allnameLabel = QLabel("Names")
        self.allyLabel = QLabel("y-Values")
        self.alllineLabel = QLabel("Species lines")
        self.allconnectionLabel = QLabel("Connection lines")
        self.wwidthLabel = QLabel("Length:")
        self.spacingLabel = QLabel("Spacing:")
        self.namedxLabel = QLabel("Δx")
        self.namedyLabel = QLabel("Δy")
        self.ydxLabel = QLabel("Δx")
        self.ydyLabel = QLabel("Δy")

        self.adjustAll.addWidget(self.allnameLabel, 0, 1, 1, 2)
        self.adjustAll.addWidget(self.allnamevisible, 1, 1, 1, 2)
        self.adjustAll.addWidget(self.allnamesize, 2, 1, 1, 2)
        self.adjustAll.addWidget(self.allnamecolour, 3, 1, 1, 2)
        self.adjustAll.addWidget(self.allnamedx, 4, 2)
        self.adjustAll.addWidget(self.namedxLabel, 4, 1)
        self.adjustAll.addWidget(self.allnamedy, 5, 2)
        self.adjustAll.addWidget(self.namedyLabel, 5, 1)
        self.adjustAll.addWidget(self.allnamefont, 6, 1, 1, 2)

        self.adjustAll.addWidget(self.allyLabel, 0, 3, 1, 2)
        self.adjustAll.addWidget(self.allyvisible, 1, 3, 1, 2)
        self.adjustAll.addWidget(self.allysize, 2, 3, 1, 2)
        self.adjustAll.addWidget(self.allycolour, 3, 3, 1, 2)
        self.adjustAll.addWidget(self.allydx, 4, 4)
        self.adjustAll.addWidget(self.ydxLabel, 4, 3)
        self.adjustAll.addWidget(self.allydy, 5, 4)
        self.adjustAll.addWidget(self.ydyLabel, 5, 3)
        self.adjustAll.addWidget(self.allyfont, 6, 3, 1, 2)

        self.adjustAll.addWidget(self.alllineLabel, 0, 5, 1, 2)
        self.adjustAll.addWidget(self.alllinevisible, 1, 5, 1, 2)
        self.adjustAll.addWidget(self.alllinecolour, 2, 5, 1, 2)
        self.adjustAll.addWidget(self.alllinestyle, 3, 5, 1, 2)
        self.adjustAll.addWidget(self.wwidthLabel, 4, 5)
        self.adjustAll.addWidget(self.wwidth, 4, 6)
        self.adjustAll.addWidget(self.spacingLabel, 5, 5)
        self.adjustAll.addWidget(self.spacing, 5, 6)

        self.adjustAll.addWidget(self.allconnectionLabel, 0, 7)
        self.adjustAll.addWidget(self.allconnvisible, 1, 7)
        self.adjustAll.addWidget(self.allconncolour, 2, 7)
        self.adjustAll.addWidget(self.allconnstyle, 3, 7)

        for i in range(self.adjustAll.count()):
            if self.adjustAll.itemAt(i):
                self.adjustAll.itemAt(i).widget().setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
                self.adjustAll.itemAt(i).widget().setFont(QFont('Arial', 10))

        self.metaAdjust = QWidget()
        self.metaAdjust.setLayout(self.adjustAll)

        #self.bottomright = QWidget()
        #self.bottomright.setLayout(self.glayout)
        #self.bottomright.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.scroll2 = QScrollArea()
        self.scroll2.setWidgetResizable(True)
        self.scroll2.setWidget(self.speciesField)
        #self.scroll2.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.buttonKeeper = QGridLayout()
        self.buttonKeeper.addWidget(self.button, 1, 1)
        #self.buttonKeeper.addWidget(self.createConnection, 1, 2)

        self.buttonWidget = QWidget()
        self.buttonWidget.setLayout(self.buttonKeeper)

        self.allIndividuals = QGridLayout()
        self.allIndividuals.addWidget(self.buttonWidget, 1, 1)
        self.allIndividuals.addWidget(self.scroll, 2, 1)

        self.indi = QWidget()
        self.indi.setLayout(self.allIndividuals)

        self.tabMaster = QTabWidget()
        self.tabMaster.addTab(self.scroll2, "Adjust selected species")
        self.tabMaster.addTab(self.metaAdjust, "Adjust all species")
        self.tabMaster.setCurrentWidget(self.metaAdjust)
        self.tabMaster.setStyleSheet('QTabBar {font-size: 18pt}')

        self.layout9 = QVBoxLayout()
        self.layout9.addWidget(self.canvas)

        self.widget9 = QWidget()
        self.widget9.setLayout(self.layout9)


        container = QGridLayout()
        container.addItem(QSpacerItem(100,10), 2, 0)
        container.addWidget(self.tabMaster, 1, 1)
        container.addWidget(self.indi, 2, 1)
        container.addWidget(self.widget9, 1, 2)
        container.addWidget(self.tabs, 2, 2)
        container.setColumnMinimumWidth(1, int(self.geometry().width()/2))
        container.setColumnMinimumWidth(2, int(self.geometry().width()/2))
        container.setRowMinimumHeight(1, int(self.geometry().height()*2/3))
        container.setRowMinimumHeight(2, int(self.geometry().height()*1/3))
        self.setLayout(container)

    def graphPrev(self):
        widw = window.widget9.geometry().width()
        widh = window.widget9.geometry().height()

        if widh > widh:
            canw = widw
            canh = canw * graphSettings['figure height'] / graphSettings['figure width']
            if canh > widh:
                canh = widh
                canw = canh * graphSettings['figure width'] / graphSettings['figure height']
        else:
            canh = widh
            canw = canh * graphSettings['figure width'] / graphSettings['figure height']
            if canw > widw:
                canw = widw
                canh = canw * graphSettings['figure height'] / graphSettings['figure width']

        window.canvas.setGeometry(int(window.canvas.geometry().x()), int(window.canvas.geometry().y()), int(canw), int(canh))

    def resizeEvent(self, event):
        self.graphPrev()
        QWidget.resizeEvent(self, event)

    def imageGraph(self, new = True):
        global graphSettings

        if new:
            asdf = QFileDialog()
            asdf.show()
            names = asdf.getOpenFileNames(self, 'Select Image', '', str("Images (*.png)"))[0]

            if names:
                for name in names:
                    number = 1
                    for key in graphSettings:
                        if 'imageGraph' in key:
                            number += 1
                    graphSettings[f'imageGraph{number}'] = {'name':name, 'scale':1, 'x':2, 'y':2, 'visible':2}
                    window.canvas.plot()
                    window.graphPrev()

        self.glayout3 = None
        self.glayout3 = QGridLayout()
        self.glayout3.addWidget(self.imggraphadd, 1, 1)
        self.glayout3.addWidget(self.scaleLabel, 1, 2)
        self.glayout3.addWidget(self.xposLabel, 1, 3)
        self.glayout3.addWidget(self.yposLabel, 1, 4)
        self.g3l = None
        self.g3l = QScrollArea()
        self.g3l.setLayout(self.glayout3)
        self.tabs.removeTab(2)
        self.tabs.addTab(self.g3l, 'Images')
        self.tabs.setCurrentWidget(self.g3l)
        self.tabs.setStyleSheet('QTabBar {font-size: 12pt}')

        images = dict()

        for key in graphSettings:
            if 'imageGraph' in key:
                images[key] = graphSettings[key]
        for index, key in enumerate(images):

            path = images[key]['name'].split('/')[-1]
            imgLabel = QLabel(path)
            imgLabel.setFont(QFont('Arial', 12))

            imgScale = QLineEdit()
            imgScale.setText(str(images[key]['scale']))
            imgScale.editingFinished.connect(lambda index = index, imgScale = imgScale: self.imgAlter(index + 1, 'scale', imgScale.text(), imgScale))
            imgScale.setFont(QFont('Arial', 12))

            imgX = QLineEdit()
            imgX.setText(str(images[key]['x']))
            imgX.editingFinished.connect(lambda index = index, imgX = imgX: self.imgAlter(index + 1, 'x', imgX.text(), imgX))
            imgX.setFont(QFont('Arial', 12))

            imgY = QLineEdit()
            imgY.setText(str(images[key]['y']))
            imgY.editingFinished.connect(lambda index = index, imgY = imgY: self.imgAlter(index + 1, 'y', imgY.text(), imgY))
            imgY.setFont(QFont('Arial', 12))

            imgVis = QCheckBox("Visible?")
            imgVis.setChecked(images[key]['visible'])
            imgVis.stateChanged.connect(lambda a, imgVis = imgVis, index = index: self.imgAlter(index + 1, 'visible', imgVis.checkState()))
            imgVis.setFont(QFont('Arial', 12))

            imgDel = QPushButton("Delete")
            imgDel.pressed.connect(lambda index = index: self.imgAlter(index + 1, 'delete', True))
            imgDel.setFont(QFont('Arial', 12))

            self.glayout3.addWidget(imgLabel, index + 2, 1)
            self.glayout3.addWidget(imgScale, index + 2, 2)
            self.glayout3.addWidget(imgX, index + 2, 3)
            self.glayout3.addWidget(imgY, index + 2, 4)
            self.glayout3.addWidget(imgVis, index + 2, 5)
            self.glayout3.addWidget(imgDel, index + 2, 6)

    def imgAlter(self, number, param, newValue, widget = None):
        global graphSettings

        if not newValue and param in ['scale', 'x', 'y']:
            if widget:
                widget.setText(str(graphSettings[f'imageGraph{number}'][param]))
            return

        if param in ['x', 'y'] and re.findall(r'[^+-.\d]', newValue.strip()):
            if widget:
                widget.setText(str(graphSettings[f'imageGraph{number}'][param]))
            return
        elif param == 'scale' and re.findall(r'[^+.\d]', newValue.strip()):
            if widget:
                widget.setText(str(graphSettings[f'imageGraph{number}'][param]))
            return

        if param in ['scale', 'x', 'y']:
            try:
                float(newValue)
            except ValueError:
                widget.setText(str(graphSettings[f'imageGraph{number}'][param]))
                return

        if param == 'delete':
            graphSettings.pop(f'imageGraph{number}', None)

            newlist = []
            for key in graphSettings:
                if 'imageGraph' in key:
                    newlist.append(key)
            for key in newlist:
                num = int(key.replace('imageGraph',''))
                if num > number:
                    current = graphSettings[key]
                    graphSettings.pop(key)
                    graphSettings[f'imageGraph{num-1}'] = current

            self.glayout3 = None
            self.imageGraph(new = False)
        else:
            graphSettings[f'imageGraph{number}'][param] = newValue

        window.canvas.plot()
        window.graphPrev()

    def groupChange(self, type, param, value):
        global df, defaults
        if type == 'species':
            if param not in ['visibleline', 'visiblename', 'visibleenergy']:
                if param in ['linestyle', 'linecolour']:
                    transformed = {'linestyle':'linestylespecies', 'linecolour':'linecolourspecies'}
                    defaults[transformed[param]] = value
                else:
                    defaults[param] = value
            if redrawn:
                old = self.name
            for species in self.buttonlist:
                self.name = re.split(r' \| ', species.text())[0]
                self.changeData(param, value)
            if redrawn:
                self.name = old
        elif type == 'connection':
            if param != 'visibleline':
                transformed = {'linestyle':'linestyleconnection', 'linecolour':'linecolourconnection'}
                defaults[transformed[param]] = value
            for id in df[df['type'] == 'connection'].index:
                self.changeConnection(id, param, value)

    def autorange(self, widgets, state):
        global graphSettings
        for widget in widgets:
            if widget in [self.yticksvisible, self.xticksvisible]:
                widget.setEnabled(state)
            else:
                widget.setEnabled(not state)

    def exportcsv(self):
        global df

        asdf = QFileDialog()
        asdf.show()
        name = asdf.getSaveFileName(self, 'Export File', '', str("Comma-separated values (*.csv)"))[0]

        if name:
            if '.' not in name:
                name += '.csv'
            df.to_csv(name, index_label = df.index.name)

    def importcsv(self):
        global df, window

        asdf = QFileDialog()
        asdf.show()
        name = asdf.getOpenFileName(self, 'Import File', '', str("Comma-separated values (*.csv)"))[0]

        if name:
            with open(name, 'r') as file:
                lines = file.readlines()
            if lines[0].startswith(',type,name,xvalue,yvalue,namefont,namefontsize,namefontcolour,namefontdx,namefontdy,yfont,yfontsize,yfontcolour,yfontdx,yfontdy,linecolour,linestyle,partner1name,partner2name,visibleline,visiblename,visibleenergy'):
                try:
                    df2 = df.copy()
                    df = pd.read_csv(name, index_col = 0)
                    window.close()
                    window = None
                    window = MainWindow()
                    window.show()
                    window.makeGrid()
                    window.canvas.plot()
                    window.graphPrev()
                except:
                    df = df2
                    window = None
                    window = MainWindow()
                    window.show()
                    window.makeGrid()
                    window.canvas.plot()
                    window.graphPrev()

    def file_save(self):
        asdf = QFileDialog()
        asdf.show()
        name = asdf.getSaveFileName(self, 'Save File', '', str("Images (*.png *.xpm *.jpg)"))[0]
        if name:
            geom = window.canvas.geometry()
            x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
            window.canvas.setGeometry(0, 0, graphSettings['figure width'], graphSettings['figure height'])
            window.canvas.print_figure(name)
            window.canvas.setGeometry(x, y, w, h)

    def changeGraph(self, key, value):
        global graphSettings
        graphSettings[key] = value
        if redrawn:
            self.redraw(f'{self.name} | {self.energy}')
        else:
            self.canvas.plot()
            self.graphPrev()

    def redraw(self, text):
        global df, redrawn
        redrawn = True
        for i in reversed(range(self.slayout.count())):
            if self.slayout.itemAt(i):
                self.slayout.itemAt(i).widget().setParent(None)

        self.name, self.energy = re.split(r' \| ', text)

        self.allToggle = QCheckBox('Species Visible')
        if df.loc[self.name, 'visibleline'] and df.loc[self.name, 'visiblename'] and df.loc[self.name, 'visibleenergy']:
            self.allToggle.setChecked(True)
        else:
            self.allToggle.setChecked(False)
        self.allToggle.stateChanged.connect(lambda a: self.changeData('allToggle', a))

        self.nameLabel = QLabel("LABEL")

        self.nameLine = QLineEdit()
        self.nameLine.setPlaceholderText('Species label')
        self.nameLine.setText(self.name)
        self.nameLine.editingFinished.connect(lambda: self.changeData('name', self.nameLine.text(), self.name))

        nameFont = QComboBox()
        nameFont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        nameFont.setCurrentText(df.loc[self.name, 'namefont'])
        nameFont.currentIndexChanged.connect(lambda a: self.changeData('namefont', nameFont.itemText(a)))

        nameFontSize = QSpinBox()
        nameFontSize.setValue(int(df.loc[self.name, 'namefontsize']))
        nameFontSize.valueChanged.connect(lambda a: self.changeData('namefontsize', a))

        nameFontColour = ColorButton("Colour")
        nameFontColour.setColor(df.loc[self.name, 'namefontcolour'])
        nameFontColour.colorChanged.connect(lambda a: self.changeData('namefontcolour', a))

        nameFontdx = QDoubleSpinBox()
        nameFontdx.setMinimum(-9e99)
        nameFontdx.setValue(df.loc[self.name, 'namefontdx'])
        nameFontdx.setSingleStep(0.25)
        nameFontdx.valueChanged.connect(lambda a: self.changeData('namefontdx', a))

        nameFontdy = QDoubleSpinBox()
        nameFontdy.setMinimum(-9e99)
        nameFontdy.setValue(df.loc[self.name, 'namefontdy'])
        nameFontdy.valueChanged.connect(lambda a: self.changeData('namefontdy', a))

        self.nameToggle = QCheckBox('Label visible')
        self.nameToggle.setChecked(df.loc[self.name, 'visiblename'])
        self.nameToggle.stateChanged.connect(lambda a: self.changeData('visiblename', a))

        self.xLabel = QLabel("x-Value")

        self.xValue = QLineEdit()
        self.xValue.setPlaceholderText('x-Value')
        self.xValue.setText(str(df.loc[self.name, 'xvalue']))
        self.xValue.setValidator(QRegExpValidator(QRegExp(r'[+-\d]*')))
        self.xValue.editingFinished.connect(lambda: self.changeData('xvalue', self.xValue.text()))

        self.yLabel = QLabel("y-Value")

        self.yValue = QLineEdit()
        self.yValue.setText(str(df.loc[self.name, 'yvalue']))
        self.yValue.setPlaceholderText('y-Value')
        self.yValue.setValidator(QRegExpValidator(QRegExp(r'[+-.\d]*')))
        self.yValue.editingFinished.connect(lambda: self.changeData('yvalue', self.yValue.text()))

        yValueFont = QComboBox()
        yValueFont.addItems(['Arial', 'Verdana', 'Tahoma', 'Trebuchet MS', 'Impact', 'Times New Roman', 'Georgia', 'DejaVu Sans', 'Lucida Console', 'Comic Sans MS'])
        yValueFont.setCurrentText(df.loc[self.name, 'yfont'])
        yValueFont.currentIndexChanged.connect(lambda a: self.changeData('yfont', yValueFont.itemText(a)))

        yValueFontSize = QSpinBox()
        yValueFontSize.setValue(int(df.loc[self.name, 'yfontsize']))
        yValueFontSize.valueChanged.connect(lambda a: self.changeData('yfontsize', a))

        yValueFontColour = ColorButton("Colour")
        yValueFontColour.setColor(df.loc[self.name, 'yfontcolour'])
        yValueFontColour.colorChanged.connect(lambda a: self.changeData('yfontcolour', a))

        yValueFontdx = QDoubleSpinBox()
        yValueFontdx.setMinimum(-9e99)
        yValueFontdx.setValue(df.loc[self.name, 'yfontdx'])
        yValueFontdx.setSingleStep(0.25)
        yValueFontdx.valueChanged.connect(lambda a: self.changeData('yfontdx', a))

        yValueFontdy = QDoubleSpinBox()
        yValueFontdy.setMinimum(-9e99)
        yValueFontdy.setValue(df.loc[self.name, 'yfontdy'])
        yValueFontdy.valueChanged.connect(lambda a: self.changeData('yfontdy', a))

        self.energyToggle = QCheckBox('y-value visible')
        self.energyToggle.setChecked(df.loc[self.name, 'visibleenergy'])
        self.energyToggle.stateChanged.connect(lambda a: self.changeData('visibleenergy', a))

        self.lineLabel = QLabel("Line")

        mainLineColour = ColorButton("Colour")
        mainLineColour.setColor(df.loc[self.name, 'linecolour'])
        mainLineColour.colorChanged.connect(lambda a: self.changeData('linecolour', a))

        mainLineStyle = QComboBox()
        mainLineStyle.addItems(['solid', 'dotted', 'dashed', 'dashdot'])
        mainLineStyle.setCurrentText(df.loc[self.name, 'linestyle'])
        mainLineStyle.currentIndexChanged.connect(lambda a: self.changeData('linestyle', mainLineStyle.itemText(a)))

        self.lineToggle = QCheckBox('Line visible')
        self.lineToggle.setChecked(df.loc[self.name, 'visibleline'])
        self.lineToggle.stateChanged.connect(lambda a: self.changeData('visibleline', a))

        metagridarea = QGroupBox("Connections:")

        gridarea = QGridLayout()

        field = QWidget()
        field.setLayout(gridarea)

        scrollarea = QScrollArea()
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(field)

        metascrollarea = QVBoxLayout()
        metascrollarea.addWidget(scrollarea)

        metagridarea.setLayout(metascrollarea)

        unsortedConnections = []
        for index, [idx, row] in enumerate(df[df['type'] == 'connection'].iterrows()):
            unsortedConnections.append([idx, row])

        sortedConnections = sorted(unsortedConnections, key=itemgetter(0))

        for index, [idx, row] in enumerate(sortedConnections):
            if self.name in re.split('⌬', idx):
                for x in re.split('⌬', idx):
                    if x != self.name:
                        partnerName = QLabel(x)
                        break

                lineColour = ColorButton('Colour')
                lineColour.setColor(row['linecolour'])
                lineColour.colorChanged.connect(lambda a, idx=idx: self.changeConnection(idx, 'linecolour', a))

                lineStyle = QComboBox()
                lineStyle.addItems(['solid', 'dotted', 'dashed', 'dashdot'])
                lineStyle.setCurrentText(row['linestyle'])
                lineStyle.currentIndexChanged.connect(lambda a, idx=idx: self.changeConnection(idx, 'linestyle', lineStyle.itemText(a)))

                delete = QPushButton("Delete")
                delete.clicked.connect(lambda a, idx=idx: [df.drop(idx, axis = 0, inplace = True), self.makeGrid(), self.redraw(f'{self.name} | {self.energy}')])

                visToggle = QCheckBox('Visible')
                visToggle.setChecked(row['visibleline'])
                visToggle.stateChanged.connect(lambda a, idx=idx: self.changeConnection(idx, 'visibleline', a))

                gridarea.addWidget(partnerName, index + 1, 1)
                gridarea.addWidget(lineColour, index + 1, 2)
                gridarea.addWidget(lineStyle, index + 1, 3)
                gridarea.addWidget(delete, index + 1, 4)
                gridarea.addWidget(visToggle, index + 1, 5)

                for i in range(gridarea.count()):
                    if gridarea.itemAt(i):
                        gridarea.itemAt(i).widget().setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
                        gridarea.itemAt(i).widget().setFont(QFont('Arial', 10))

        self.INDInamedxLabel = QLabel("Δx")
        self.INDInamedyLabel = QLabel("Δy")
        self.INDIydxLabel = QLabel("Δx")
        self.INDIydyLabel = QLabel("Δy")
        self.currSpecLabel = QLabel(self.name)

        self.slayout.addWidget(self.allToggle, 0, 2)
        self.slayout.addWidget(self.currSpecLabel, 0, 1)

        self.slayout.addWidget(self.nameLabel, 1, 1, 1, 2)
        #self.slayout.addWidget(self.nameLine, 2, 1)
        self.slayout.addWidget(self.nameToggle, 3, 1, 1, 2)
        self.slayout.addWidget(nameFontSize, 4, 1, 1, 2)
        self.slayout.addWidget(nameFontColour, 5, 1, 1, 2)
        self.slayout.addWidget(nameFontdx, 6, 2)
        self.slayout.addWidget(self.INDInamedxLabel, 6, 1)
        self.slayout.addWidget(nameFontdy, 7, 2)
        self.slayout.addWidget(self.INDInamedyLabel, 7, 1)
        self.slayout.addWidget(nameFont, 8, 1, 1, 2)

        #self.slayout.addWidget(self.xLabel, 1, 2)
        #self.slayout.addWidget(self.xValue, 2, 2)

        self.slayout.addWidget(self.yLabel, 1, 3, 1, 2)
        #self.slayout.addWidget(self.yValue, 2, 3)
        self.slayout.addWidget(self.energyToggle, 3, 3, 1, 2)
        self.slayout.addWidget(yValueFontSize, 4, 3, 1, 2)
        self.slayout.addWidget(yValueFontColour, 5, 3, 1, 2)
        self.slayout.addWidget(yValueFontdx, 6, 4)
        self.slayout.addWidget(self.INDIydxLabel, 6, 3)
        self.slayout.addWidget(yValueFontdy, 7, 4)
        self.slayout.addWidget(self.INDIydyLabel, 7, 3)
        self.slayout.addWidget(yValueFont, 8, 3, 1, 2)

        self.slayout.addWidget(self.lineLabel, 1, 5)
        self.slayout.addWidget(self.lineToggle, 3, 5)
        self.slayout.addWidget(mainLineColour, 4, 5)
        self.slayout.addWidget(mainLineStyle, 5, 5)

        self.slayout.addWidget(metagridarea, 9, 1, 1, 5)

        for i in range(self.slayout.count()):
            if self.slayout.itemAt(i):
                self.slayout.itemAt(i).widget().setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
                self.slayout.itemAt(i).widget().setFont(QFont('Arial', 10))

        self.canvas.plot()
        self.graphPrev()

    def makeGrid(self):
        global df
        for i in reversed(range(self.blayout.count())):
            self.blayout.itemAt(i).widget().setParent(None)
        species = []
        for idx, row in df[df['type'] == 'species'].iterrows():
            x = row['xvalue']
            y = row['yvalue']
            item = row['name']
            species.append([item, x, y])
        sortedSpecies = []
        xValues = list(sorted(set(x for [item, x, y] in species)))
        highest = -1
        for value in xValues:
            xlist = []
            for item in species:
                if item[1] == value:
                    xlist.append(item)
            if len(xlist) > highest:
                highest = len(xlist)
        ordinalX = dict()
        for idx, value in enumerate(xValues):
            ordinalX[value] = idx
        for idx, row in df[df['type'] == 'species'].iterrows():
            df.loc[idx,'xvalue'] = ordinalX[df.loc[idx,'xvalue']]
        for value in xValues:
            xlist = []
            for item in species:
                if item[1] == value:
                    xlist.append(item)
            for idx, [item, x, y] in enumerate(sorted(xlist, key=itemgetter(2))):
                sortedSpecies.append([item, ordinalX[x], highest - idx])

        self.buttonlist = list()

        for [item, x, y] in sortedSpecies:
            energy = df.loc[item, 'yvalue']
            btn = DragButton(f'{item} | {energy}')
            btn.setFont(QFont('Arial', 13))
            btn.setAccessibleName(item)
            btn.setCheckable(True)
            btn.setGeometry(200, 150, 100, 40)
            self.blayout.addWidget(btn, y, x)
            self.buttonlist.append(btn)

        if len(self.buttonlist) < 2:
            self.createConnection.setEnabled(False)
        else:
            self.createConnection.setEnabled(True)

        self.canvas.plot()
        self.graphPrev()

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        global df
        pos = e.pos()
        globalpos = window.mapToGlobal(pos).x()
        widget = e.source()
        w = self.blayout.itemAt(0).widget().size().width()
        globalzero = self.blayout.itemAt(0).widget().mapToGlobal(QPoint(0,0)).x()
        target = floor((globalpos - globalzero)/w)
        df.loc[widget.accessibleName(), 'xvalue'] = target
        self.makeGrid()
        e.accept()

    def showdialog(self):
        self.msg = AddSpeciesWindow()
        self.msg.setModal(True)
        self.msg.button.clicked.connect(self.makeGrid)
        self.msg.show()

    def changeData(self, param, newValue, priorName = None, makegrid = True):
        global df

        if param == 'xvalue' or param == 'yvalue':
            try:
                newValue = float(newValue)
            except ValueError:
                newValue = df.loc[self.name].copy()[param]
                if param == 'xvalue':
                    self.xValue.setText(str(newValue))
                    self.xValue.selectAll()
                elif param == 'yvalue':
                    self.yValue.setText(str(newValue))
                    self.yValue.selectAll()

        if param == 'allToggle':
            self.changeData('visibleline', newValue, makegrid = False)
            self.lineToggle.setChecked(newValue)
            self.changeData('visiblename', newValue, makegrid = False)
            self.nameToggle.setChecked(newValue)
            self.changeData('visibleenergy', newValue)
            self.energyToggle.setChecked(newValue)

        if param == 'name':
            if newValue in set(df.loc[:,'name']) and newValue != self.name:
                newValue = self.name
                self.nameLine.setText(newValue)
                self.nameLine.selectAll()

        old = df.loc[self.name].copy()
        old[param] = newValue

        df.drop([self.name], axis = 0, inplace = True)

        if param == 'name':
            old.name = newValue
            self.name = newValue

        df = pd.concat([df,pd.DataFrame(old).transpose()])

        if param == 'name':
            for idx, item in enumerate(df[df['type'] == 'connection'].index):
                if priorName in re.split('⌬', item):
                    if priorName == re.split('⌬', item)[0]:
                        otherName = re.split('⌬', item)[1]
                    else:
                        otherName = re.split('⌬', item)[0]
                    df.drop([item], axis = 0, inplace = True)
                    df = newRow('connection', partner1name = otherName, partner2name = newValue)
                    break

        if makegrid:
            self.makeGrid()

        if param in ['name','xvalue','yvalue']:
            self.redraw(f'{self.name} | {self.energy}')

    def changeConnection(self, id, param, newValue):
        global df

        old = df.loc[id].copy()
        old[param] = newValue

        df.drop([id], axis = 0, inplace = True)

        df = pd.concat([df,pd.DataFrame(old).transpose()])

        self.makeGrid()

    def connectionWindow(self):
        self.wind = AddConnectionWindow()
        self.wind.setModal(True)
        self.wind.show()
        self.wind.button.clicked.connect(self.makeGrid)
        if redrawn:
            self.wind.button.clicked.connect(lambda: self.redraw(f'{self.name} | {self.energy}'))

class AddSpeciesWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(self.windowFlags()
                    ^ Qt.WindowContextHelpButtonHint)

        self.setWindowIcon(QIcon('icon2.png'))

        layout = QVBoxLayout()
        label = QLabel("ALL SPECIES MUST HAVE UNIQUE NAMES!\nSEPARATE ENTRIES BY COMMA")
        label.setFont(QFont('Arial', 12))
        self.widget = QLineEdit("New names")
        self.widget.selectAll()
        self.widget.textChanged.connect(self.verify)
        self.widget.setFont(QFont('Arial', 12))
        self.widget2 = QLineEdit("New energies")
        self.widget2.textChanged.connect(self.verify)
        self.widget2.setFont(QFont('Arial', 12))
        self.button = QPushButton("ADD")
        self.button.clicked.connect(self.makeNew)
        self.button.setFont(QFont('Arial', 12))
        self.button2 = QPushButton("Cancel")
        self.button2.clicked.connect(self.close)
        self.button2.setFont(QFont('Arial', 12))
        self.setWindowTitle("Add new species")
        layout.addWidget(label)
        layout.addWidget(self.widget)
        layout.addWidget(self.widget2)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)
        self.setLayout(layout)
        self.verify()

    def makeNew(self):
        global df
        if [x for x in df[df['type'] == 'species'].iterrows()]:
            newX = max([df.loc[idx, 'xvalue'] for idx, row in df[df['type'] == 'species'].iterrows()])
        else:
            newX = 0
        names = re.split(',', self.widget.text())
        energies = re.split(',', self.widget2.text())
        if len(names) != len(energies):
            return
        for idx, name in enumerate(names):
            df = newRow('species', name.strip(), newX, float(energies[idx]))
        self.close()

    def verify(self):
        names = re.split(',', self.widget.text())
        energies = re.split(',', self.widget2.text())
        if len(names) != len(energies):
            self.button.setEnabled(False)
            return

        for name in names:
            if name.strip() in list(df.index):
                self.button.setEnabled(False)
                return

        for x in names + energies:
            if x.strip() == '':
                self.button.setEnabled(False)
                return
        for x in energies:
            if re.findall('[^+-.0-9]', x.strip()):
                self.button.setEnabled(False)
                return
        self.button.setEnabled(True)

class EditSpeciesWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icon2.png'))

        self.setWindowFlags(self.windowFlags()
                    ^ Qt.WindowContextHelpButtonHint)

        self.cur = "PLACEHOLDER"

        layout = QVBoxLayout()
        label = QLabel("ALL SPECIES MUST HAVE UNIQUE NAMES!")
        label.setFont(QFont('Arial', 12))
        self.widget = QLineEdit('name')
        self.widget.selectAll()
        self.widget.setFont(QFont('Arial', 12))
        self.widget.textChanged.connect(self.verify)
        self.widget2 = QLineEdit('energy')
        self.widget2.setFont(QFont('Arial', 12))
        self.widget2.textChanged.connect(self.verify)
        self.button = QPushButton("OK")
        self.button.setFont(QFont('Arial', 12))
        self.button2 = QPushButton("Cancel")
        self.button2.clicked.connect(self.close)
        self.button2.setFont(QFont('Arial', 12))
        self.setWindowTitle("Edit species")
        layout.addWidget(label)
        layout.addWidget(self.widget)
        layout.addWidget(self.widget2)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)
        self.setLayout(layout)
        self.verify()

    def verify(self):
        names = re.split(',', self.widget.text())
        energies = re.split(',', self.widget2.text())

        if len(names) != len(energies) or len(names) > 1 or len(energies) > 1:
            self.button.setEnabled(False)
            return

        for x in names + energies:
            if x.strip() == '':
                self.button.setEnabled(False)
                return

        for name in names:
            if name.strip() in list(df.index):
                if name.strip() != self.cur:
                    self.button.setEnabled(False)
                    return

        for x in energies:
            if re.findall('[^+-.0-9]', x.strip()):
                self.button.setEnabled(False)
                return
        self.button.setEnabled(True)

class AddConnectionWindow(QDialog):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowFlags(self.windowFlags()
                    ^ Qt.WindowContextHelpButtonHint)

        self.setGeometry(int(window.geometry().x() + window.geometry().width()/3),
                        int(window.geometry().y() + window.geometry().height()/3),
                        int(window.geometry().width()/5),
                        int(window.geometry().height()/5))
        self.setWindowIcon(QIcon('icon2.png'))

        self.label = QLabel("Add connection:")
        self.label.setFont(QFont('Arial', 12))

        self.widget = QComboBox()
        self.widget.addItems(list(df[df['type'] == 'species'].index))
        self.widget.setFont(QFont('Arial', 12))
        self.widget.activated.connect(lambda a: self.changeOptions(self.widget, self.widget2))
        self.widget2 = QComboBox()
        self.widget2.activated.connect(lambda a: self.changeOptions(self.widget2, self.widget))
        self.widget2.setFont(QFont('Arial', 12))
        self.changeOptions(self.widget, self.widget2)
        self.changeOptions(self.widget2, self.widget)

        self.button = QPushButton("ADD")
        self.button.clicked.connect(self.makeNew)
        self.button.setFont(QFont('Arial', 12))
        self.button2 = QPushButton("Cancel")
        self.button2.clicked.connect(self.close)
        self.button2.setFont(QFont('Arial', 12))
        self.setWindowTitle("Add new connection")
        layout.addWidget(self.label)
        layout.addWidget(self.widget)
        layout.addWidget(self.widget2)
        layout.addWidget(self.button)
        layout.addWidget(self.button2)
        self.setLayout(layout)

    def makeNew(self):
        global df
        df = newRow('connection', partner1name = self.widget.currentText(), partner2name = self.widget2.currentText())
        self.close()

    def changeOptions(self, widget1, widget2):
        selected = widget1.currentText()
        selected2 = widget2.currentText()
        toAdd = list(df[df['type'] == 'species'].index)
        for idx, item in enumerate(df[df['type'] == 'connection'].index):
            if selected in re.split('⌬', item):
                if selected == re.split('⌬', item)[1]:
                    toAdd.remove(re.split('⌬', item)[0])
                elif selected == re.split('⌬', item)[0]:
                    toAdd.remove(re.split('⌬', item)[1])
        toAdd.remove(selected)
        widget2.clear()
        if toAdd:
            widget2.addItems(toAdd)
        else:
            widget2.addItems(['All species connected'])
        widget2.setCurrentText(selected2)

if __name__ == '__main__':
    app = QApplication([])
    app.setStyleSheet(qdarktheme.load_stylesheet())
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    window = MainWindow()
    window.show()
    df = newRow('species','ALPHA', 0, -1.2)
    df = newRow('species','BETA', 1, 0.6)
    df = newRow('species','GAMMA', 2, 5.9)
    df = newRow('species','DELTA', 1, 3.6)
    df = newRow('connection', partner1name = 'ALPHA', partner2name = 'BETA')
    df = newRow('connection', partner1name = 'GAMMA', partner2name = 'DELTA')
    window.makeGrid()
    window.canvas.plot()
    window.graphPrev()
    sys.exit(app.exec())
