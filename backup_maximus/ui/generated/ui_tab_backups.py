# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tab_backups.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

from backup_maximus.ui.drivecombo import DriveCombo
from backup_maximus.ui.pathedit import PathEdit

class Ui_TabBackups(object):
    def setupUi(self, TabBackups):
        if not TabBackups.objectName():
            TabBackups.setObjectName(u"TabBackups")
        TabBackups.resize(1000, 800)
        self.rootLayout = QHBoxLayout(TabBackups)
        self.rootLayout.setSpacing(18)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(16, 10, 16, 8)
        self.leftLayout = QVBoxLayout()
        self.leftLayout.setSpacing(6)
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.lblSetsHeader = QLabel(TabBackups)
        self.lblSetsHeader.setObjectName(u"lblSetsHeader")
        self.lblSetsHeader.setProperty(u"role", u"section")

        self.leftLayout.addWidget(self.lblSetsHeader)

        self.listSets = QListWidget(TabBackups)
        self.listSets.setObjectName(u"listSets")
        self.listSets.setMinimumSize(QSize(0, 122))
        self.listSets.setMaximumSize(QSize(16777215, 122))

        self.leftLayout.addWidget(self.listSets)

        self.setButtonsLayout = QHBoxLayout()
        self.setButtonsLayout.setSpacing(5)
        self.setButtonsLayout.setObjectName(u"setButtonsLayout")
        self.btnSetNew = QPushButton(TabBackups)
        self.btnSetNew.setObjectName(u"btnSetNew")

        self.setButtonsLayout.addWidget(self.btnSetNew)

        self.btnSetDup = QPushButton(TabBackups)
        self.btnSetDup.setObjectName(u"btnSetDup")

        self.setButtonsLayout.addWidget(self.btnSetDup)

        self.btnSetDel = QPushButton(TabBackups)
        self.btnSetDel.setObjectName(u"btnSetDel")

        self.setButtonsLayout.addWidget(self.btnSetDel)


        self.leftLayout.addLayout(self.setButtonsLayout)

        self.spacerLeftGap = QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.leftLayout.addItem(self.spacerLeftGap)

        self.lblItemsHeader = QLabel(TabBackups)
        self.lblItemsHeader.setObjectName(u"lblItemsHeader")
        self.lblItemsHeader.setProperty(u"role", u"section")

        self.leftLayout.addWidget(self.lblItemsHeader)

        self.listItems = QListWidget(TabBackups)
        self.listItems.setObjectName(u"listItems")

        self.leftLayout.addWidget(self.listItems)

        self.itemButtonsLayout = QHBoxLayout()
        self.itemButtonsLayout.setSpacing(5)
        self.itemButtonsLayout.setObjectName(u"itemButtonsLayout")
        self.btnItemNew = QPushButton(TabBackups)
        self.btnItemNew.setObjectName(u"btnItemNew")

        self.itemButtonsLayout.addWidget(self.btnItemNew)

        self.btnItemDup = QPushButton(TabBackups)
        self.btnItemDup.setObjectName(u"btnItemDup")

        self.itemButtonsLayout.addWidget(self.btnItemDup)

        self.btnItemDel = QPushButton(TabBackups)
        self.btnItemDel.setObjectName(u"btnItemDel")

        self.itemButtonsLayout.addWidget(self.btnItemDel)

        self.btnItemUp = QPushButton(TabBackups)
        self.btnItemUp.setObjectName(u"btnItemUp")
        self.btnItemUp.setMaximumSize(QSize(44, 16777215))
        self.btnItemUp.setProperty(u"role", u"tiny")

        self.itemButtonsLayout.addWidget(self.btnItemUp)

        self.btnItemDown = QPushButton(TabBackups)
        self.btnItemDown.setObjectName(u"btnItemDown")
        self.btnItemDown.setMaximumSize(QSize(44, 16777215))
        self.btnItemDown.setProperty(u"role", u"tiny")

        self.itemButtonsLayout.addWidget(self.btnItemDown)


        self.leftLayout.addLayout(self.itemButtonsLayout)

        self.spacerLeftGap2 = QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.leftLayout.addItem(self.spacerLeftGap2)

        self.btnRun = QPushButton(TabBackups)
        self.btnRun.setObjectName(u"btnRun")
        self.btnRun.setProperty(u"role", u"accent")

        self.leftLayout.addWidget(self.btnRun)

        self.inspectLayout = QHBoxLayout()
        self.inspectLayout.setSpacing(5)
        self.inspectLayout.setObjectName(u"inspectLayout")
        self.btnPreview = QPushButton(TabBackups)
        self.btnPreview.setObjectName(u"btnPreview")

        self.inspectLayout.addWidget(self.btnPreview)

        self.btnDestInfo = QPushButton(TabBackups)
        self.btnDestInfo.setObjectName(u"btnDestInfo")

        self.inspectLayout.addWidget(self.btnDestInfo)


        self.leftLayout.addLayout(self.inspectLayout)

        self.detectLayout = QHBoxLayout()
        self.detectLayout.setSpacing(5)
        self.detectLayout.setObjectName(u"detectLayout")
        self.btnCloud = QPushButton(TabBackups)
        self.btnCloud.setObjectName(u"btnCloud")

        self.detectLayout.addWidget(self.btnCloud)

        self.btnDetectAliases = QPushButton(TabBackups)
        self.btnDetectAliases.setObjectName(u"btnDetectAliases")

        self.detectLayout.addWidget(self.btnDetectAliases)


        self.leftLayout.addLayout(self.detectLayout)


        self.rootLayout.addLayout(self.leftLayout)

        self.scrollRight = QScrollArea(TabBackups)
        self.scrollRight.setObjectName(u"scrollRight")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollRight.sizePolicy().hasHeightForWidth())
        self.scrollRight.setSizePolicy(sizePolicy)
        self.scrollRight.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollRight.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollRight.setWidgetResizable(True)
        self.rightContents = QWidget()
        self.rightContents.setObjectName(u"rightContents")
        self.rightContents.setGeometry(QRect(0, 0, 640, 774))
        self.rightLayout = QVBoxLayout(self.rightContents)
        self.rightLayout.setSpacing(6)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.lblSetSection = QLabel(self.rightContents)
        self.lblSetSection.setObjectName(u"lblSetSection")
        self.lblSetSection.setProperty(u"role", u"section")

        self.rightLayout.addWidget(self.lblSetSection)

        self.gridSet = QGridLayout()
        self.gridSet.setObjectName(u"gridSet")
        self.gridSet.setHorizontalSpacing(8)
        self.gridSet.setVerticalSpacing(5)
        self.gridSet.setContentsMargins(0, -1, 0, -1)
        self.lblSetName = QLabel(self.rightContents)
        self.lblSetName.setObjectName(u"lblSetName")
        self.lblSetName.setMinimumSize(QSize(124, 0))
        self.lblSetName.setMaximumSize(QSize(124, 16777215))
        self.lblSetName.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblSetName.setProperty(u"role", u"field")

        self.gridSet.addWidget(self.lblSetName, 0, 0, 1, 1)

        self.editSetName = QLineEdit(self.rightContents)
        self.editSetName.setObjectName(u"editSetName")

        self.gridSet.addWidget(self.editSetName, 0, 1, 1, 3)

        self.lblSetDest = QLabel(self.rightContents)
        self.lblSetDest.setObjectName(u"lblSetDest")
        self.lblSetDest.setMinimumSize(QSize(124, 0))
        self.lblSetDest.setMaximumSize(QSize(124, 16777215))
        self.lblSetDest.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblSetDest.setProperty(u"role", u"field")

        self.gridSet.addWidget(self.lblSetDest, 1, 0, 1, 1)

        self.editSetDest = PathEdit(self.rightContents)
        self.editSetDest.setObjectName(u"editSetDest")
        self.editSetDest.setProperty(u"pathKind", u"dest")
        self.editSetDest.setProperty(u"mono", u"true")

        self.gridSet.addWidget(self.editSetDest, 1, 1, 1, 3)

        self.btnBrowseDest = QPushButton(self.rightContents)
        self.btnBrowseDest.setObjectName(u"btnBrowseDest")
        self.btnBrowseDest.setMinimumSize(QSize(30, 0))
        self.btnBrowseDest.setMaximumSize(QSize(30, 16777215))
        self.btnBrowseDest.setProperty(u"role", u"tiny")

        self.gridSet.addWidget(self.btnBrowseDest, 1, 4, 1, 1)

        self.lblSetMode = QLabel(self.rightContents)
        self.lblSetMode.setObjectName(u"lblSetMode")
        self.lblSetMode.setMinimumSize(QSize(124, 0))
        self.lblSetMode.setMaximumSize(QSize(124, 16777215))
        self.lblSetMode.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblSetMode.setProperty(u"role", u"field")

        self.gridSet.addWidget(self.lblSetMode, 2, 0, 1, 1)

        self.comboSetMode = QComboBox(self.rightContents)
        self.comboSetMode.setObjectName(u"comboSetMode")

        self.gridSet.addWidget(self.comboSetMode, 2, 1, 1, 1)

        self.lblKeepLast = QLabel(self.rightContents)
        self.lblKeepLast.setObjectName(u"lblKeepLast")
        self.lblKeepLast.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblKeepLast.setProperty(u"role", u"field")

        self.gridSet.addWidget(self.lblKeepLast, 2, 2, 1, 1)

        self.spinKeepLast = QSpinBox(self.rightContents)
        self.spinKeepLast.setObjectName(u"spinKeepLast")
        self.spinKeepLast.setMinimumSize(QSize(96, 0))
        self.spinKeepLast.setMaximumSize(QSize(96, 16777215))
        self.spinKeepLast.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinKeepLast.setMaximum(999)

        self.gridSet.addWidget(self.spinKeepLast, 2, 3, 1, 1)

        self.lblSetStaging = QLabel(self.rightContents)
        self.lblSetStaging.setObjectName(u"lblSetStaging")
        self.lblSetStaging.setMinimumSize(QSize(124, 0))
        self.lblSetStaging.setMaximumSize(QSize(124, 16777215))
        self.lblSetStaging.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblSetStaging.setProperty(u"role", u"field")

        self.gridSet.addWidget(self.lblSetStaging, 3, 0, 1, 1)

        self.editSetStaging = PathEdit(self.rightContents)
        self.editSetStaging.setObjectName(u"editSetStaging")
        self.editSetStaging.setProperty(u"pathKind", u"dest")
        self.editSetStaging.setProperty(u"mono", u"true")

        self.gridSet.addWidget(self.editSetStaging, 3, 1, 1, 3)

        self.btnBrowseStaging = QPushButton(self.rightContents)
        self.btnBrowseStaging.setObjectName(u"btnBrowseStaging")
        self.btnBrowseStaging.setMinimumSize(QSize(30, 0))
        self.btnBrowseStaging.setMaximumSize(QSize(30, 16777215))
        self.btnBrowseStaging.setProperty(u"role", u"tiny")

        self.gridSet.addWidget(self.btnBrowseStaging, 3, 4, 1, 1)

        self.lblSetWait = QLabel(self.rightContents)
        self.lblSetWait.setObjectName(u"lblSetWait")
        self.lblSetWait.setMinimumSize(QSize(124, 0))
        self.lblSetWait.setMaximumSize(QSize(124, 16777215))
        self.lblSetWait.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblSetWait.setProperty(u"role", u"field")

        self.gridSet.addWidget(self.lblSetWait, 4, 0, 1, 1)

        self.comboSetWait = DriveCombo(self.rightContents)
        self.comboSetWait.setObjectName(u"comboSetWait")

        self.gridSet.addWidget(self.comboSetWait, 4, 1, 1, 2)

        self.spinWaitSecs = QSpinBox(self.rightContents)
        self.spinWaitSecs.setObjectName(u"spinWaitSecs")
        self.spinWaitSecs.setMinimumSize(QSize(96, 0))
        self.spinWaitSecs.setMaximumSize(QSize(96, 16777215))
        self.spinWaitSecs.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinWaitSecs.setMaximum(86400)

        self.gridSet.addWidget(self.spinWaitSecs, 4, 3, 1, 1)

        self.lblSetHint = QLabel(self.rightContents)
        self.lblSetHint.setObjectName(u"lblSetHint")
        self.lblSetHint.setWordWrap(True)
        self.lblSetHint.setProperty(u"role", u"hint")

        self.gridSet.addWidget(self.lblSetHint, 5, 1, 1, 3)

        self.lblSetDestHint = QLabel(self.rightContents)
        self.lblSetDestHint.setObjectName(u"lblSetDestHint")
        self.lblSetDestHint.setWordWrap(True)
        self.lblSetDestHint.setProperty(u"role", u"hint")

        self.gridSet.addWidget(self.lblSetDestHint, 6, 1, 1, 3)

        self.setChecksLayout = QHBoxLayout()
        self.setChecksLayout.setSpacing(16)
        self.setChecksLayout.setObjectName(u"setChecksLayout")
        self.chkKeepStaging = QCheckBox(self.rightContents)
        self.chkKeepStaging.setObjectName(u"chkKeepStaging")

        self.setChecksLayout.addWidget(self.chkKeepStaging)

        self.chkSetEnabled = QCheckBox(self.rightContents)
        self.chkSetEnabled.setObjectName(u"chkSetEnabled")

        self.setChecksLayout.addWidget(self.chkSetEnabled)

        self.setChecksSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.setChecksLayout.addItem(self.setChecksSpacer)


        self.gridSet.addLayout(self.setChecksLayout, 7, 1, 1, 3)


        self.rightLayout.addLayout(self.gridSet)

        self.dividerSets = QFrame(self.rightContents)
        self.dividerSets.setObjectName(u"dividerSets")
        self.dividerSets.setMinimumSize(QSize(0, 1))
        self.dividerSets.setMaximumSize(QSize(16777215, 1))
        self.dividerSets.setFrameShape(QFrame.Shape.HLine)
        self.dividerSets.setProperty(u"role", u"divider")

        self.rightLayout.addWidget(self.dividerSets)

        self.lblItemSection = QLabel(self.rightContents)
        self.lblItemSection.setObjectName(u"lblItemSection")
        self.lblItemSection.setProperty(u"role", u"section")

        self.rightLayout.addWidget(self.lblItemSection)

        self.gridItem = QGridLayout()
        self.gridItem.setObjectName(u"gridItem")
        self.gridItem.setHorizontalSpacing(8)
        self.gridItem.setVerticalSpacing(5)
        self.gridItem.setContentsMargins(0, -1, 0, -1)
        self.lblItemName = QLabel(self.rightContents)
        self.lblItemName.setObjectName(u"lblItemName")
        self.lblItemName.setMinimumSize(QSize(124, 0))
        self.lblItemName.setMaximumSize(QSize(124, 16777215))
        self.lblItemName.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemName.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemName, 0, 0, 1, 1)

        self.editItemName = QLineEdit(self.rightContents)
        self.editItemName.setObjectName(u"editItemName")

        self.gridItem.addWidget(self.editItemName, 0, 1, 1, 3)

        self.lblItemType = QLabel(self.rightContents)
        self.lblItemType.setObjectName(u"lblItemType")
        self.lblItemType.setMinimumSize(QSize(124, 0))
        self.lblItemType.setMaximumSize(QSize(124, 16777215))
        self.lblItemType.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemType.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemType, 1, 0, 1, 1)

        self.comboItemType = QComboBox(self.rightContents)
        self.comboItemType.setObjectName(u"comboItemType")

        self.gridItem.addWidget(self.comboItemType, 1, 1, 1, 1)

        self.chkMirror = QCheckBox(self.rightContents)
        self.chkMirror.setObjectName(u"chkMirror")

        self.gridItem.addWidget(self.chkMirror, 1, 2, 1, 2)

        self.lblItemSource = QLabel(self.rightContents)
        self.lblItemSource.setObjectName(u"lblItemSource")
        self.lblItemSource.setMinimumSize(QSize(124, 0))
        self.lblItemSource.setMaximumSize(QSize(124, 16777215))
        self.lblItemSource.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemSource.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemSource, 2, 0, 1, 1)

        self.editItemSource = PathEdit(self.rightContents)
        self.editItemSource.setObjectName(u"editItemSource")
        self.editItemSource.setProperty(u"pathKind", u"any")
        self.editItemSource.setProperty(u"mono", u"true")

        self.gridItem.addWidget(self.editItemSource, 2, 1, 1, 3)

        self.btnBrowseSource = QPushButton(self.rightContents)
        self.btnBrowseSource.setObjectName(u"btnBrowseSource")
        self.btnBrowseSource.setMinimumSize(QSize(30, 0))
        self.btnBrowseSource.setMaximumSize(QSize(30, 16777215))
        self.btnBrowseSource.setProperty(u"role", u"tiny")

        self.gridItem.addWidget(self.btnBrowseSource, 2, 4, 1, 1)

        self.lblItemSubfolder = QLabel(self.rightContents)
        self.lblItemSubfolder.setObjectName(u"lblItemSubfolder")
        self.lblItemSubfolder.setMinimumSize(QSize(124, 0))
        self.lblItemSubfolder.setMaximumSize(QSize(124, 16777215))
        self.lblItemSubfolder.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemSubfolder.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemSubfolder, 3, 0, 1, 1)

        self.editItemSubfolder = QLineEdit(self.rightContents)
        self.editItemSubfolder.setObjectName(u"editItemSubfolder")
        self.editItemSubfolder.setProperty(u"mono", u"true")

        self.gridItem.addWidget(self.editItemSubfolder, 3, 1, 1, 3)

        self.lblItemOutput = QLabel(self.rightContents)
        self.lblItemOutput.setObjectName(u"lblItemOutput")
        self.lblItemOutput.setMinimumSize(QSize(124, 0))
        self.lblItemOutput.setMaximumSize(QSize(124, 16777215))
        self.lblItemOutput.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemOutput.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemOutput, 4, 0, 1, 1)

        self.editItemOutput = QLineEdit(self.rightContents)
        self.editItemOutput.setObjectName(u"editItemOutput")
        self.editItemOutput.setProperty(u"mono", u"true")

        self.gridItem.addWidget(self.editItemOutput, 4, 1, 1, 3)

        self.lblItemHost = QLabel(self.rightContents)
        self.lblItemHost.setObjectName(u"lblItemHost")
        self.lblItemHost.setMinimumSize(QSize(124, 0))
        self.lblItemHost.setMaximumSize(QSize(124, 16777215))
        self.lblItemHost.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemHost.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemHost, 5, 0, 1, 1)

        self.editItemHost = QLineEdit(self.rightContents)
        self.editItemHost.setObjectName(u"editItemHost")
        self.editItemHost.setProperty(u"mono", u"true")

        self.gridItem.addWidget(self.editItemHost, 5, 1, 1, 2)

        self.editItemPort = QLineEdit(self.rightContents)
        self.editItemPort.setObjectName(u"editItemPort")
        self.editItemPort.setMinimumSize(QSize(96, 0))
        self.editItemPort.setMaximumSize(QSize(96, 16777215))
        self.editItemPort.setProperty(u"mono", u"true")

        self.gridItem.addWidget(self.editItemPort, 5, 3, 1, 1)

        self.lblItemUser = QLabel(self.rightContents)
        self.lblItemUser.setObjectName(u"lblItemUser")
        self.lblItemUser.setMinimumSize(QSize(124, 0))
        self.lblItemUser.setMaximumSize(QSize(124, 16777215))
        self.lblItemUser.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemUser.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemUser, 6, 0, 1, 1)

        self.editItemUser = QLineEdit(self.rightContents)
        self.editItemUser.setObjectName(u"editItemUser")

        self.gridItem.addWidget(self.editItemUser, 6, 1, 1, 1)

        self.editItemPass = QLineEdit(self.rightContents)
        self.editItemPass.setObjectName(u"editItemPass")
        self.editItemPass.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridItem.addWidget(self.editItemPass, 6, 2, 1, 2)

        self.lblItemTool = QLabel(self.rightContents)
        self.lblItemTool.setObjectName(u"lblItemTool")
        self.lblItemTool.setMinimumSize(QSize(124, 0))
        self.lblItemTool.setMaximumSize(QSize(124, 16777215))
        self.lblItemTool.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.lblItemTool.setProperty(u"role", u"field")

        self.gridItem.addWidget(self.lblItemTool, 7, 0, 1, 1)

        self.editItemTool = PathEdit(self.rightContents)
        self.editItemTool.setObjectName(u"editItemTool")
        self.editItemTool.setProperty(u"pathKind", u"file")
        self.editItemTool.setProperty(u"mono", u"true")

        self.gridItem.addWidget(self.editItemTool, 7, 1, 1, 3)

        self.btnBrowseTool = QPushButton(self.rightContents)
        self.btnBrowseTool.setObjectName(u"btnBrowseTool")
        self.btnBrowseTool.setMinimumSize(QSize(30, 0))
        self.btnBrowseTool.setMaximumSize(QSize(30, 16777215))
        self.btnBrowseTool.setProperty(u"role", u"tiny")

        self.gridItem.addWidget(self.btnBrowseTool, 7, 4, 1, 1)

        self.itemActionsLayout = QHBoxLayout()
        self.itemActionsLayout.setSpacing(8)
        self.itemActionsLayout.setObjectName(u"itemActionsLayout")
        self.chkItemEnabled = QCheckBox(self.rightContents)
        self.chkItemEnabled.setObjectName(u"chkItemEnabled")

        self.itemActionsLayout.addWidget(self.chkItemEnabled)

        self.btnTest = QPushButton(self.rightContents)
        self.btnTest.setObjectName(u"btnTest")

        self.itemActionsLayout.addWidget(self.btnTest)


        self.gridItem.addLayout(self.itemActionsLayout, 8, 1, 1, 3)

        self.lblItemHint = QLabel(self.rightContents)
        self.lblItemHint.setObjectName(u"lblItemHint")
        self.lblItemHint.setWordWrap(True)
        self.lblItemHint.setProperty(u"role", u"hint")

        self.gridItem.addWidget(self.lblItemHint, 9, 1, 1, 3)

        self.lblItemSourceHint = QLabel(self.rightContents)
        self.lblItemSourceHint.setObjectName(u"lblItemSourceHint")
        self.lblItemSourceHint.setWordWrap(True)
        self.lblItemSourceHint.setProperty(u"role", u"hint")

        self.gridItem.addWidget(self.lblItemSourceHint, 10, 1, 1, 3)


        self.rightLayout.addLayout(self.gridItem)

        self.rightBottomSpacer = QSpacerItem(0, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.rightLayout.addItem(self.rightBottomSpacer)

        self.scrollRight.setWidget(self.rightContents)

        self.rootLayout.addWidget(self.scrollRight)


        self.retranslateUi(TabBackups)

        QMetaObject.connectSlotsByName(TabBackups)
    # setupUi

    def retranslateUi(self, TabBackups):
        self.lblSetsHeader.setText(QCoreApplication.translate("TabBackups", u"CONJUNTOS \u2014 CADA UM GERA 1 ZIP", None))
        self.btnSetNew.setText(QCoreApplication.translate("TabBackups", u"+ Conjunto", None))
        self.btnSetDup.setText(QCoreApplication.translate("TabBackups", u"Duplicar", None))
        self.btnSetDel.setText(QCoreApplication.translate("TabBackups", u"Excluir", None))
        self.lblItemsHeader.setText(QCoreApplication.translate("TabBackups", u"ITENS \u2014 CADA UM VAI PARA SUA SUBPASTA", None))
        self.btnItemNew.setText(QCoreApplication.translate("TabBackups", u"+ Item", None))
        self.btnItemDup.setText(QCoreApplication.translate("TabBackups", u"Duplicar", None))
        self.btnItemDel.setText(QCoreApplication.translate("TabBackups", u"Excluir", None))
        self.btnItemUp.setText(QCoreApplication.translate("TabBackups", u"\u2191", None))
        self.btnItemDown.setText(QCoreApplication.translate("TabBackups", u"\u2193", None))
        self.btnRun.setText(QCoreApplication.translate("TabBackups", u"\u25b6  Executar backup agora", None))
        self.btnPreview.setText(QCoreApplication.translate("TabBackups", u"Pr\u00e9via da \u00e1rvore", None))
        self.btnDestInfo.setText(QCoreApplication.translate("TabBackups", u"Espa\u00e7o e limpeza", None))
        self.btnCloud.setText(QCoreApplication.translate("TabBackups", u"Nuvem\u2026", None))
#if QT_CONFIG(tooltip)
        self.btnCloud.setToolTip(QCoreApplication.translate("TabBackups", u"Gravar o zip numa pasta sincronizada (OneDrive, Google Drive, Dropbox, MEGA)", None))
#endif // QT_CONFIG(tooltip)
        self.btnDetectAliases.setText(QCoreApplication.translate("TabBackups", u"Detectar bancos do Firebird", None))
#if QT_CONFIG(tooltip)
        self.btnDetectAliases.setToolTip(QCoreApplication.translate("TabBackups", u"L\u00ea os bancos registrados no aliases.conf / databases.conf e cria um item para cada.", None))
#endif // QT_CONFIG(tooltip)
        self.lblSetSection.setText(QCoreApplication.translate("TabBackups", u"DADOS DO CONJUNTO", None))
        self.lblSetName.setText(QCoreApplication.translate("TabBackups", u"Nome (do zip)", None))
        self.lblSetDest.setText(QCoreApplication.translate("TabBackups", u"Destino do zip", None))
        self.btnBrowseDest.setText(QCoreApplication.translate("TabBackups", u"\u2026", None))
        self.lblSetMode.setText(QCoreApplication.translate("TabBackups", u"Modo", None))
        self.lblKeepLast.setText(QCoreApplication.translate("TabBackups", u"Manter \u00faltimos", None))
#if QT_CONFIG(tooltip)
        self.spinKeepLast.setToolTip(QCoreApplication.translate("TabBackups", u"0 = manter todos os arquivos. S\u00f3 se aplica ao modo Completo.", None))
#endif // QT_CONFIG(tooltip)
        self.lblSetStaging.setText(QCoreApplication.translate("TabBackups", u"Pasta de montagem", None))
        self.editSetStaging.setPlaceholderText(QCoreApplication.translate("TabBackups", u"vazio = <pasta do app>\\staging\\<nome do conjunto>", None))
        self.btnBrowseStaging.setText(QCoreApplication.translate("TabBackups", u"\u2026", None))
        self.lblSetWait.setText(QCoreApplication.translate("TabBackups", u"Aguardar unidade", None))
#if QT_CONFIG(tooltip)
        self.comboSetWait.setToolTip(QCoreApplication.translate("TabBackups", u"Unidades do computador, relidas cada vez que a lista \u00e9 aberta. Caminhos de rede aparecem aqui depois de cadastrados na aba Rede.", None))
#endif // QT_CONFIG(tooltip)
        self.spinWaitSecs.setSuffix(QCoreApplication.translate("TabBackups", u" seg", None))
        self.lblSetHint.setText("")
        self.lblSetDestHint.setText("")
        self.chkKeepStaging.setText(QCoreApplication.translate("TabBackups", u"Manter a pasta de montagem (mais r\u00e1pido)", None))
#if QT_CONFIG(tooltip)
        self.chkKeepStaging.setToolTip(QCoreApplication.translate("TabBackups", u"Reaproveita a \u00e1rvore entre execu\u00e7\u00f5es: s\u00f3 o que mudou \u00e9 recopiado.", None))
#endif // QT_CONFIG(tooltip)
        self.chkSetEnabled.setText(QCoreApplication.translate("TabBackups", u"Conjunto habilitado", None))
        self.lblItemSection.setText(QCoreApplication.translate("TabBackups", u"DADOS DO ITEM SELECIONADO", None))
        self.lblItemName.setText(QCoreApplication.translate("TabBackups", u"Nome", None))
        self.lblItemType.setText(QCoreApplication.translate("TabBackups", u"Tipo", None))
#if QT_CONFIG(tooltip)
        self.chkMirror.setToolTip(QCoreApplication.translate("TabBackups", u"Remove do backup os arquivos que foram apagados na origem.", None))
#endif // QT_CONFIG(tooltip)
        self.chkMirror.setText(QCoreApplication.translate("TabBackups", u"Espelhar (/MIR)", None))
        self.lblItemSource.setText(QCoreApplication.translate("TabBackups", u"Origem", None))
        self.btnBrowseSource.setText(QCoreApplication.translate("TabBackups", u"\u2026", None))
        self.lblItemSubfolder.setText(QCoreApplication.translate("TabBackups", u"Subpasta no zip", None))
        self.editItemSubfolder.setPlaceholderText(QCoreApplication.translate("TabBackups", u"vazio = raiz do zip", None))
        self.lblItemOutput.setText(QCoreApplication.translate("TabBackups", u"Arquivo gerado", None))
        self.lblItemHost.setText(QCoreApplication.translate("TabBackups", u"Servidor / porta", None))
        self.lblItemUser.setText(QCoreApplication.translate("TabBackups", u"Usu\u00e1rio / senha", None))
        self.lblItemTool.setText(QCoreApplication.translate("TabBackups", u"Ferramenta", None))
        self.btnBrowseTool.setText(QCoreApplication.translate("TabBackups", u"\u2026", None))
        self.chkItemEnabled.setText(QCoreApplication.translate("TabBackups", u"Item habilitado", None))
        self.btnTest.setText(QCoreApplication.translate("TabBackups", u"Testar conex\u00e3o", None))
        self.lblItemHint.setText("")
        self.lblItemSourceHint.setText("")
        pass
    # retranslateUi

