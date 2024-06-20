# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hypnotoad_mainWindow.ui'
##
<<<<<<< HEAD
## Created by: Qt User Interface Compiler version 5.14.2
=======
## Created by: Qt User Interface Compiler version 5.15.2
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

<<<<<<< HEAD
from Qt.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from Qt.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
=======
from Qt.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from Qt.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QIcon,
    QKeySequence,
    QLinearGradient,
    QPalette,
    QPainter,
    QPixmap,
    QRadialGradient,
)
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
from Qt.QtWidgets import *


class Ui_Hypnotoad(object):
    def setupUi(self, Hypnotoad):
        if not Hypnotoad.objectName():
<<<<<<< HEAD
            Hypnotoad.setObjectName(u"Hypnotoad")
        Hypnotoad.resize(1215, 863)
        self.action_New = QAction(Hypnotoad)
        self.action_New.setObjectName(u"action_New")
        icon = QIcon()
        iconThemeName = u"document-new"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_New.setIcon(icon)
        self.action_Open = QAction(Hypnotoad)
        self.action_Open.setObjectName(u"action_Open")
        icon1 = QIcon()
        iconThemeName = u"document-open"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Open.setIcon(icon1)
        self.action_Save = QAction(Hypnotoad)
        self.action_Save.setObjectName(u"action_Save")
        icon2 = QIcon()
        iconThemeName = u"document-save"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Save.setIcon(icon2)
        self.action_Save_as = QAction(Hypnotoad)
        self.action_Save_as.setObjectName(u"action_Save_as")
        icon3 = QIcon()
        iconThemeName = u"document-save-as"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Save_as.setIcon(icon3)
        self.action_Quit = QAction(Hypnotoad)
        self.action_Quit.setObjectName(u"action_Quit")
        icon4 = QIcon()
        iconThemeName = u"application-exit"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Quit.setIcon(icon4)
        self.action_About = QAction(Hypnotoad)
        self.action_About.setObjectName(u"action_About")
        icon5 = QIcon()
        iconThemeName = u"help-about"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_About.setIcon(icon5)
        self.action_Run = QAction(Hypnotoad)
        self.action_Run.setObjectName(u"action_Run")
        icon6 = QIcon()
        iconThemeName = u"system-run"
        if QIcon.hasThemeIcon(iconThemeName):
            icon6 = QIcon.fromTheme(iconThemeName)
        else:
            icon6.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Run.setIcon(icon6)
        self.action_Write_grid = QAction(Hypnotoad)
        self.action_Write_grid.setObjectName(u"action_Write_grid")
        icon7 = QIcon()
        iconThemeName = u"document-print"
        if QIcon.hasThemeIcon(iconThemeName):
            icon7 = QIcon.fromTheme(iconThemeName)
        else:
            icon7.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Write_grid.setIcon(icon7)
        self.action_Revert = QAction(Hypnotoad)
        self.action_Revert.setObjectName(u"action_Revert")
        icon8 = QIcon()
        iconThemeName = u"document-revert"
        if QIcon.hasThemeIcon(iconThemeName):
            icon8 = QIcon.fromTheme(iconThemeName)
        else:
            icon8.addFile(u".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Revert.setIcon(icon8)
        self.action_Preferences = QAction(Hypnotoad)
        self.action_Preferences.setObjectName(u"action_Preferences")
        icon9 = QIcon(QIcon.fromTheme(u"document-properties"))
        self.action_Preferences.setIcon(icon9)
        self.action_Regrid = QAction(Hypnotoad)
        self.action_Regrid.setObjectName(u"action_Regrid")
        self.action_Regrid.setEnabled(False)
        self.action_Regrid.setIcon(icon6)
        self.centralwidget = QWidget(Hypnotoad)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.search_bar = QLineEdit(self.centralwidget)
        self.search_bar.setObjectName(u"search_bar")
=======
            Hypnotoad.setObjectName("Hypnotoad")
        Hypnotoad.resize(1215, 863)
        self.action_New = QAction(Hypnotoad)
        self.action_New.setObjectName("action_New")
        icon = QIcon()
        iconThemeName = "document-new"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_New.setIcon(icon)
        self.action_Open = QAction(Hypnotoad)
        self.action_Open.setObjectName("action_Open")
        icon1 = QIcon()
        iconThemeName = "document-open"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Open.setIcon(icon1)
        self.action_Save = QAction(Hypnotoad)
        self.action_Save.setObjectName("action_Save")
        icon2 = QIcon()
        iconThemeName = "document-save"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Save.setIcon(icon2)
        self.action_Save_as = QAction(Hypnotoad)
        self.action_Save_as.setObjectName("action_Save_as")
        icon3 = QIcon()
        iconThemeName = "document-save-as"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Save_as.setIcon(icon3)
        self.action_Quit = QAction(Hypnotoad)
        self.action_Quit.setObjectName("action_Quit")
        icon4 = QIcon()
        iconThemeName = "application-exit"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Quit.setIcon(icon4)
        self.action_About = QAction(Hypnotoad)
        self.action_About.setObjectName("action_About")
        icon5 = QIcon()
        iconThemeName = "help-about"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_About.setIcon(icon5)
        self.action_Run = QAction(Hypnotoad)
        self.action_Run.setObjectName("action_Run")
        icon6 = QIcon()
        iconThemeName = "system-run"
        if QIcon.hasThemeIcon(iconThemeName):
            icon6 = QIcon.fromTheme(iconThemeName)
        else:
            icon6.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Run.setIcon(icon6)
        self.action_Write_grid = QAction(Hypnotoad)
        self.action_Write_grid.setObjectName("action_Write_grid")
        icon7 = QIcon()
        iconThemeName = "document-print"
        if QIcon.hasThemeIcon(iconThemeName):
            icon7 = QIcon.fromTheme(iconThemeName)
        else:
            icon7.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Write_grid.setIcon(icon7)
        self.action_Revert = QAction(Hypnotoad)
        self.action_Revert.setObjectName("action_Revert")
        icon8 = QIcon()
        iconThemeName = "document-revert"
        if QIcon.hasThemeIcon(iconThemeName):
            icon8 = QIcon.fromTheme(iconThemeName)
        else:
            icon8.addFile(".", QSize(), QIcon.Normal, QIcon.Off)

        self.action_Revert.setIcon(icon8)
        self.action_Preferences = QAction(Hypnotoad)
        self.action_Preferences.setObjectName("action_Preferences")
        icon9 = QIcon(QIcon.fromTheme("document-properties"))
        self.action_Preferences.setIcon(icon9)
        self.action_Regrid = QAction(Hypnotoad)
        self.action_Regrid.setObjectName("action_Regrid")
        self.action_Regrid.setEnabled(False)
        self.action_Regrid.setIcon(icon6)
        self.action_Flux = QAction(Hypnotoad)
        self.action_Flux.setObjectName("action_Flux")
        self.action_Flux.setCheckable(True)
        self.action_Flux.setChecked(True)
        self.action_Wall = QAction(Hypnotoad)
        self.action_Wall.setObjectName("action_Wall")
        self.action_Wall.setCheckable(True)
        self.action_Wall.setChecked(True)
        self.action_Centers = QAction(Hypnotoad)
        self.action_Centers.setObjectName("action_Centers")
        self.action_Centers.setCheckable(True)
        self.action_Centers.setChecked(True)
        self.action_Corners = QAction(Hypnotoad)
        self.action_Corners.setObjectName("action_Corners")
        self.action_Corners.setCheckable(True)
        self.action_Corners.setChecked(True)
        self.action_Xlow = QAction(Hypnotoad)
        self.action_Xlow.setObjectName("action_Xlow")
        self.action_Xlow.setCheckable(True)
        self.action_Xlow.setChecked(True)
        self.action_Ylow = QAction(Hypnotoad)
        self.action_Ylow.setObjectName("action_Ylow")
        self.action_Ylow.setCheckable(True)
        self.action_Ylow.setChecked(True)
        self.action_Lines = QAction(Hypnotoad)
        self.action_Lines.setObjectName("action_Lines")
        self.action_Lines.setCheckable(True)
        self.action_Edges = QAction(Hypnotoad)
        self.action_Edges.setObjectName("action_Edges")
        self.action_Edges.setCheckable(True)
        self.action_Legend = QAction(Hypnotoad)
        self.action_Legend.setObjectName("action_Legend")
        self.action_Legend.setCheckable(True)
        self.action_Penalty = QAction(Hypnotoad)
        self.action_Penalty.setObjectName("action_Penalty")
        self.action_Penalty.setCheckable(True)
        self.action_Clear = QAction(Hypnotoad)
        self.action_Clear.setObjectName("action_Clear")
        self.centralwidget = QWidget(Hypnotoad)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.search_bar = QLineEdit(self.centralwidget)
        self.search_bar.setObjectName("search_bar")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.verticalLayout_2.addWidget(self.search_bar)

        self.options_form = QTableWidget(self.centralwidget)
<<<<<<< HEAD
        if (self.options_form.columnCount() < 2):
=======
        if self.options_form.columnCount() < 2:
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
            self.options_form.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.options_form.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.options_form.setHorizontalHeaderItem(1, __qtablewidgetitem1)
<<<<<<< HEAD
        self.options_form.setObjectName(u"options_form")
=======
        self.options_form.setObjectName("options_form")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.verticalLayout_2.addWidget(self.options_form)

        self.gridLayout_2 = QGridLayout()
<<<<<<< HEAD
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.options_file_browse_button = QPushButton(self.centralwidget)
        self.options_file_browse_button.setObjectName(u"options_file_browse_button")
=======
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.options_file_browse_button = QPushButton(self.centralwidget)
        self.options_file_browse_button.setObjectName("options_file_browse_button")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.options_file_browse_button, 0, 2, 1, 1)

        self.geqdsk_file_browse_button = QPushButton(self.centralwidget)
<<<<<<< HEAD
        self.geqdsk_file_browse_button.setObjectName(u"geqdsk_file_browse_button")
=======
        self.geqdsk_file_browse_button.setObjectName("geqdsk_file_browse_button")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.geqdsk_file_browse_button, 0, 6, 1, 1)

        self.options_file_line_edit = QLineEdit(self.centralwidget)
<<<<<<< HEAD
        self.options_file_line_edit.setObjectName(u"options_file_line_edit")
=======
        self.options_file_line_edit.setObjectName("options_file_line_edit")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.options_file_line_edit, 0, 1, 1, 1)

        self.run_button = QPushButton(self.centralwidget)
<<<<<<< HEAD
        self.run_button.setObjectName(u"run_button")
=======
        self.run_button.setObjectName("run_button")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.run_button, 0, 7, 1, 1)

        self.write_grid_button = QPushButton(self.centralwidget)
<<<<<<< HEAD
        self.write_grid_button.setObjectName(u"write_grid_button")
=======
        self.write_grid_button.setObjectName("write_grid_button")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.write_grid_button, 0, 9, 1, 1)

        self.geqdsk_file_line_edit = QLineEdit(self.centralwidget)
<<<<<<< HEAD
        self.geqdsk_file_line_edit.setObjectName(u"geqdsk_file_line_edit")
=======
        self.geqdsk_file_line_edit.setObjectName("geqdsk_file_line_edit")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.geqdsk_file_line_edit, 0, 4, 1, 1)

        self.geqdsk_file_label = QLabel(self.centralwidget)
<<<<<<< HEAD
        self.geqdsk_file_label.setObjectName(u"geqdsk_file_label")
=======
        self.geqdsk_file_label.setObjectName("geqdsk_file_label")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.geqdsk_file_label, 0, 3, 1, 1)

        self.options_file_label = QLabel(self.centralwidget)
<<<<<<< HEAD
        self.options_file_label.setObjectName(u"options_file_label")
=======
        self.options_file_label.setObjectName("options_file_label")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.gridLayout_2.addWidget(self.options_file_label, 0, 0, 1, 1)

        self.regrid_button = QPushButton(self.centralwidget)
<<<<<<< HEAD
        self.regrid_button.setObjectName(u"regrid_button")
=======
        self.regrid_button.setObjectName("regrid_button")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
        self.regrid_button.setEnabled(False)

        self.gridLayout_2.addWidget(self.regrid_button, 1, 7, 1, 1)

        self.nonorthogonal_box = QCheckBox(self.centralwidget)
<<<<<<< HEAD
        self.nonorthogonal_box.setObjectName(u"nonorthogonal_box")
=======
        self.nonorthogonal_box.setObjectName("nonorthogonal_box")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
        self.nonorthogonal_box.setEnabled(True)

        self.gridLayout_2.addWidget(self.nonorthogonal_box, 1, 6, 1, 1)

<<<<<<< HEAD

        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
=======
        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2

        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.gridLayout = QGridLayout()
<<<<<<< HEAD
        self.gridLayout.setObjectName(u"gridLayout")

        self.verticalLayout_2.addLayout(self.gridLayout)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.plottingArea = QWidget(self.centralwidget)
        self.plottingArea.setObjectName(u"plottingArea")

        self.horizontalLayout.addWidget(self.plottingArea)


=======
        self.gridLayout.setObjectName("gridLayout")

        self.verticalLayout_2.addLayout(self.gridLayout)

        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.plottingArea = QWidget(self.centralwidget)
        self.plottingArea.setObjectName("plottingArea")

        self.horizontalLayout.addWidget(self.plottingArea)

>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        Hypnotoad.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(Hypnotoad)
<<<<<<< HEAD
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1215, 22))
        self.menu_File = QMenu(self.menubar)
        self.menu_File.setObjectName(u"menu_File")
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setObjectName(u"menu_Help")
        self.menu_Mesh = QMenu(self.menubar)
        self.menu_Mesh.setObjectName(u"menu_Mesh")
        Hypnotoad.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(Hypnotoad)
        self.statusbar.setObjectName(u"statusbar")
        Hypnotoad.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(Hypnotoad)
        self.toolBar.setObjectName(u"toolBar")
        Hypnotoad.addToolBar(Qt.TopToolBarArea, self.toolBar)
        self.toolBar_2 = QToolBar(Hypnotoad)
        self.toolBar_2.setObjectName(u"toolBar_2")
        Hypnotoad.addToolBar(Qt.TopToolBarArea, self.toolBar_2)
        self.toolBar_3 = QToolBar(Hypnotoad)
        self.toolBar_3.setObjectName(u"toolBar_3")
=======
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1215, 22))
        self.menu_File = QMenu(self.menubar)
        self.menu_File.setObjectName("menu_File")
        self.menu_Help = QMenu(self.menubar)
        self.menu_Help.setObjectName("menu_Help")
        self.menu_Mesh = QMenu(self.menubar)
        self.menu_Mesh.setObjectName("menu_Mesh")
        self.menu_View = QMenu(self.menubar)
        self.menu_View.setObjectName("menu_View")
        Hypnotoad.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(Hypnotoad)
        self.statusbar.setObjectName("statusbar")
        Hypnotoad.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(Hypnotoad)
        self.toolBar.setObjectName("toolBar")
        Hypnotoad.addToolBar(Qt.TopToolBarArea, self.toolBar)
        self.toolBar_2 = QToolBar(Hypnotoad)
        self.toolBar_2.setObjectName("toolBar_2")
        Hypnotoad.addToolBar(Qt.TopToolBarArea, self.toolBar_2)
        self.toolBar_3 = QToolBar(Hypnotoad)
        self.toolBar_3.setObjectName("toolBar_3")
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
        Hypnotoad.addToolBar(Qt.TopToolBarArea, self.toolBar_3)

        self.menubar.addAction(self.menu_File.menuAction())
        self.menubar.addAction(self.menu_Mesh.menuAction())
<<<<<<< HEAD
=======
        self.menubar.addAction(self.menu_View.menuAction())
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
        self.menubar.addAction(self.menu_Help.menuAction())
        self.menu_File.addAction(self.action_New)
        self.menu_File.addAction(self.action_Open)
        self.menu_File.addAction(self.action_Save)
        self.menu_File.addAction(self.action_Save_as)
        self.menu_File.addAction(self.action_Revert)
        self.menu_File.addSeparator()
        self.menu_File.addAction(self.action_Preferences)
        self.menu_File.addAction(self.action_Quit)
        self.menu_Help.addAction(self.action_About)
        self.menu_Mesh.addAction(self.action_Run)
        self.menu_Mesh.addAction(self.action_Regrid)
        self.menu_Mesh.addAction(self.action_Write_grid)
<<<<<<< HEAD
=======
        self.menu_View.addAction(self.action_Flux)
        self.menu_View.addAction(self.action_Wall)
        self.menu_View.addAction(self.action_Centers)
        self.menu_View.addAction(self.action_Corners)
        self.menu_View.addAction(self.action_Xlow)
        self.menu_View.addAction(self.action_Ylow)
        self.menu_View.addAction(self.action_Lines)
        self.menu_View.addAction(self.action_Edges)
        self.menu_View.addAction(self.action_Legend)
        self.menu_View.addAction(self.action_Penalty)
        self.menu_View.addAction(self.action_Clear)
>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
        self.toolBar.addAction(self.action_New)
        self.toolBar.addAction(self.action_Open)
        self.toolBar.addAction(self.action_Save)
        self.toolBar.addAction(self.action_Save_as)
        self.toolBar.addAction(self.action_Run)
        self.toolBar.addAction(self.action_Write_grid)

        self.retranslateUi(Hypnotoad)

        QMetaObject.connectSlotsByName(Hypnotoad)
<<<<<<< HEAD
    # setupUi

    def retranslateUi(self, Hypnotoad):
        Hypnotoad.setWindowTitle(QCoreApplication.translate("Hypnotoad", u"MainWindow", None))
        self.action_New.setText(QCoreApplication.translate("Hypnotoad", u"&New", None))
#if QT_CONFIG(shortcut)
        self.action_New.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
        self.action_Open.setText(QCoreApplication.translate("Hypnotoad", u"&Open", None))
#if QT_CONFIG(shortcut)
        self.action_Open.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.action_Save.setText(QCoreApplication.translate("Hypnotoad", u"&Save", None))
#if QT_CONFIG(tooltip)
        self.action_Save.setToolTip(QCoreApplication.translate("Hypnotoad", u"Save", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.action_Save.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.action_Save_as.setText(QCoreApplication.translate("Hypnotoad", u"Save as", None))
#if QT_CONFIG(shortcut)
        self.action_Save_as.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+Shift+S", None))
#endif // QT_CONFIG(shortcut)
        self.action_Quit.setText(QCoreApplication.translate("Hypnotoad", u"&Quit", None))
#if QT_CONFIG(shortcut)
        self.action_Quit.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.action_About.setText(QCoreApplication.translate("Hypnotoad", u"&About", None))
        self.action_Run.setText(QCoreApplication.translate("Hypnotoad", u"&Run", None))
#if QT_CONFIG(shortcut)
        self.action_Run.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
        self.action_Write_grid.setText(QCoreApplication.translate("Hypnotoad", u"&Write grid", None))
#if QT_CONFIG(shortcut)
        self.action_Write_grid.setShortcut(QCoreApplication.translate("Hypnotoad", u"Ctrl+W", None))
#endif // QT_CONFIG(shortcut)
        self.action_Revert.setText(QCoreApplication.translate("Hypnotoad", u"&Revert", None))
        self.action_Preferences.setText(QCoreApplication.translate("Hypnotoad", u"&Preferences...", None))
        self.action_Regrid.setText(QCoreApplication.translate("Hypnotoad", u"Re&grid", None))
        self.action_Regrid.setToolTip(QCoreApplication.translate("Hypnotoad", u"Regrid non-orthogonal mesh", None))
        ___qtablewidgetitem = self.options_form.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Hypnotoad", u"Name", None));
        ___qtablewidgetitem1 = self.options_form.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Hypnotoad", u"Value", None));
        self.options_file_browse_button.setText(QCoreApplication.translate("Hypnotoad", u"Browse", None))
        self.geqdsk_file_browse_button.setText(QCoreApplication.translate("Hypnotoad", u"Browse", None))
        self.run_button.setText(QCoreApplication.translate("Hypnotoad", u"Run", None))
        self.write_grid_button.setText(QCoreApplication.translate("Hypnotoad", u"Write Grid", None))
        self.geqdsk_file_label.setText(QCoreApplication.translate("Hypnotoad", u"geqdsk file", None))
        self.options_file_label.setText(QCoreApplication.translate("Hypnotoad", u"Options file", None))
        self.regrid_button.setToolTip(QCoreApplication.translate("Hypnotoad", u"Recalculate spacing of non-orthogonal grids (check 'Non-Orthogonal' box to activate)", None))
        self.regrid_button.setText(QCoreApplication.translate("Hypnotoad", u"Regrid", None))
        self.nonorthogonal_box.setToolTip(QCoreApplication.translate("Hypnotoad", u"Check to generate non-orthogonal grids", None))
        self.nonorthogonal_box.setText(QCoreApplication.translate("Hypnotoad", u"Non-Orthogonal", None))
        self.menu_File.setTitle(QCoreApplication.translate("Hypnotoad", u"&File", None))
        self.menu_Help.setTitle(QCoreApplication.translate("Hypnotoad", u"&Help", None))
        self.menu_Mesh.setTitle(QCoreApplication.translate("Hypnotoad", u"&Mesh", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("Hypnotoad", u"toolBar", None))
        self.toolBar_2.setWindowTitle(QCoreApplication.translate("Hypnotoad", u"toolBar_2", None))
        self.toolBar_3.setWindowTitle(QCoreApplication.translate("Hypnotoad", u"toolBar_3", None))
=======

    # setupUi

    def retranslateUi(self, Hypnotoad):
        Hypnotoad.setWindowTitle(
            QCoreApplication.translate("Hypnotoad", "MainWindow", None)
        )
        self.action_New.setText(QCoreApplication.translate("Hypnotoad", "&New", None))
        # if QT_CONFIG(shortcut)
        self.action_New.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+N", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_Open.setText(QCoreApplication.translate("Hypnotoad", "&Open", None))
        # if QT_CONFIG(shortcut)
        self.action_Open.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+O", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_Save.setText(QCoreApplication.translate("Hypnotoad", "&Save", None))
        # if QT_CONFIG(tooltip)
        self.action_Save.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Save", None)
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(shortcut)
        self.action_Save.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+S", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_Save_as.setText(
            QCoreApplication.translate("Hypnotoad", "Save as", None)
        )
        # if QT_CONFIG(shortcut)
        self.action_Save_as.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+Shift+S", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_Quit.setText(QCoreApplication.translate("Hypnotoad", "&Quit", None))
        # if QT_CONFIG(shortcut)
        self.action_Quit.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+Q", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_About.setText(
            QCoreApplication.translate("Hypnotoad", "&About", None)
        )
        self.action_Run.setText(QCoreApplication.translate("Hypnotoad", "&Run", None))
        # if QT_CONFIG(shortcut)
        self.action_Run.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+R", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_Write_grid.setText(
            QCoreApplication.translate("Hypnotoad", "&Write grid", None)
        )
        # if QT_CONFIG(shortcut)
        self.action_Write_grid.setShortcut(
            QCoreApplication.translate("Hypnotoad", "Ctrl+W", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.action_Revert.setText(
            QCoreApplication.translate("Hypnotoad", "&Revert", None)
        )
        self.action_Preferences.setText(
            QCoreApplication.translate("Hypnotoad", "&Preferences...", None)
        )
        self.action_Regrid.setText(
            QCoreApplication.translate("Hypnotoad", "Re&grid", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Regrid.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Regrid non-orthogonal mesh", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Flux.setText(
            QCoreApplication.translate("Hypnotoad", "Poloidal flux", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Flux.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot poloidal flux?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Wall.setText(QCoreApplication.translate("Hypnotoad", "Wall", None))
        # if QT_CONFIG(tooltip)
        self.action_Wall.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot wall?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Centers.setText(
            QCoreApplication.translate("Hypnotoad", "Cell centers", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Centers.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot cell centers?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Corners.setText(
            QCoreApplication.translate("Hypnotoad", "Cell corners", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Corners.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot cell corners?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Xlow.setText(
            QCoreApplication.translate("Hypnotoad", "Cell Xlow", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Xlow.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot cell Xlow locations?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Ylow.setText(
            QCoreApplication.translate("Hypnotoad", "Cell Ylow", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Ylow.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot cell Ylow locations?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Lines.setText(
            QCoreApplication.translate("Hypnotoad", "Grid lines", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Lines.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot grid lines?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Edges.setText(
            QCoreApplication.translate("Hypnotoad", "Cell edges", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Edges.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot cell edges?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Legend.setText(
            QCoreApplication.translate("Hypnotoad", "Legend", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Legend.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot legend?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Penalty.setText(
            QCoreApplication.translate("Hypnotoad", "Penalty mask", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Penalty.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Plot penalty mask?", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_Clear.setText(
            QCoreApplication.translate("Hypnotoad", "Clear plot", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_Clear.setToolTip(
            QCoreApplication.translate("Hypnotoad", "Clear grid plot", None)
        )
        # endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem = self.options_form.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(
            QCoreApplication.translate("Hypnotoad", "Name", None)
        )
        ___qtablewidgetitem1 = self.options_form.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(
            QCoreApplication.translate("Hypnotoad", "Value", None)
        )
        self.options_file_browse_button.setText(
            QCoreApplication.translate("Hypnotoad", "Browse", None)
        )
        self.geqdsk_file_browse_button.setText(
            QCoreApplication.translate("Hypnotoad", "Browse", None)
        )
        self.run_button.setText(QCoreApplication.translate("Hypnotoad", "Run", None))
        self.write_grid_button.setText(
            QCoreApplication.translate("Hypnotoad", "Write Grid", None)
        )
        self.geqdsk_file_label.setText(
            QCoreApplication.translate("Hypnotoad", "geqdsk file", None)
        )
        self.options_file_label.setText(
            QCoreApplication.translate("Hypnotoad", "Options file", None)
        )
        # if QT_CONFIG(tooltip)
        self.regrid_button.setToolTip(
            QCoreApplication.translate(
                "Hypnotoad",
                "Recalculate spacing of non-orthogonal grids (check 'Non-Orthogonal' box to activate)",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.regrid_button.setText(
            QCoreApplication.translate("Hypnotoad", "Regrid", None)
        )
        # if QT_CONFIG(tooltip)
        self.nonorthogonal_box.setToolTip(
            QCoreApplication.translate(
                "Hypnotoad", "Check to generate non-orthogonal grids", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.nonorthogonal_box.setText(
            QCoreApplication.translate("Hypnotoad", "Non-Orthogonal", None)
        )
        self.menu_File.setTitle(QCoreApplication.translate("Hypnotoad", "&File", None))
        self.menu_Help.setTitle(QCoreApplication.translate("Hypnotoad", "&Help", None))
        self.menu_Mesh.setTitle(QCoreApplication.translate("Hypnotoad", "&Mesh", None))
        self.menu_View.setTitle(QCoreApplication.translate("Hypnotoad", "&View", None))
        self.toolBar.setWindowTitle(
            QCoreApplication.translate("Hypnotoad", "toolBar", None)
        )
        self.toolBar_2.setWindowTitle(
            QCoreApplication.translate("Hypnotoad", "toolBar_2", None)
        )
        self.toolBar_3.setWindowTitle(
            QCoreApplication.translate("Hypnotoad", "toolBar_3", None)
        )

>>>>>>> d8e6be6086b9c27aa1e1011713e10d829e5dc6d2
    # retranslateUi
