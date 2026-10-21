# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1040, 800)
        MainWindow.setMinimumSize(QSize(980, 735))
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralLayout = QVBoxLayout(self.centralWidget)
        self.centralLayout.setSpacing(0)
        self.centralLayout.setObjectName(u"centralLayout")
        self.centralLayout.setContentsMargins(10, 10, 10, 0)
        self.tabs = QTabWidget(self.centralWidget)
        self.tabs.setObjectName(u"tabs")
        self.pageBackups = QWidget()
        self.pageBackups.setObjectName(u"pageBackups")
        self.pageBackupsLayout = QVBoxLayout(self.pageBackups)
        self.pageBackupsLayout.setObjectName(u"pageBackupsLayout")
        self.pageBackupsLayout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.pageBackups, "")
        self.pageSettings = QWidget()
        self.pageSettings.setObjectName(u"pageSettings")
        self.pageSettingsLayout = QVBoxLayout(self.pageSettings)
        self.pageSettingsLayout.setObjectName(u"pageSettingsLayout")
        self.pageSettingsLayout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.pageSettings, "")
        self.pageNetwork = QWidget()
        self.pageNetwork.setObjectName(u"pageNetwork")
        self.pageNetworkLayout = QVBoxLayout(self.pageNetwork)
        self.pageNetworkLayout.setObjectName(u"pageNetworkLayout")
        self.pageNetworkLayout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.pageNetwork, "")

        self.centralLayout.addWidget(self.tabs)

        self.footerBar = QFrame(self.centralWidget)
        self.footerBar.setObjectName(u"footerBar")
        self.footerBar.setMinimumSize(QSize(0, 50))
        self.footerBar.setMaximumSize(QSize(16777215, 50))
        self.footerBar.setProperty(u"role", u"footerBar")
        self.footerLayout = QHBoxLayout(self.footerBar)
        self.footerLayout.setSpacing(10)
        self.footerLayout.setObjectName(u"footerLayout")
        self.footerLayout.setContentsMargins(16, 8, 16, 8)
        self.lblFooter = QLabel(self.footerBar)
        self.lblFooter.setObjectName(u"lblFooter")
        self.lblFooter.setProperty(u"role", u"footer")

        self.footerLayout.addWidget(self.lblFooter)

        self.footerSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.footerSpacer)

        self.btnAbout = QPushButton(self.footerBar)
        self.btnAbout.setObjectName(u"btnAbout")

        self.footerLayout.addWidget(self.btnAbout)

        self.btnTheme = QPushButton(self.footerBar)
        self.btnTheme.setObjectName(u"btnTheme")

        self.footerLayout.addWidget(self.btnTheme)

        self.btnSave = QPushButton(self.footerBar)
        self.btnSave.setObjectName(u"btnSave")
        self.btnSave.setProperty(u"role", u"accent")

        self.footerLayout.addWidget(self.btnSave)

        self.btnClose = QPushButton(self.footerBar)
        self.btnClose.setObjectName(u"btnClose")

        self.footerLayout.addWidget(self.btnClose)


        self.centralLayout.addWidget(self.footerBar)

        MainWindow.setCentralWidget(self.centralWidget)

        self.retranslateUi(MainWindow)

        self.tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Backup Maximus \u2014 Configura\u00e7\u00f5es", None))
        self.tabs.setTabText(self.tabs.indexOf(self.pageBackups), QCoreApplication.translate("MainWindow", u"Backups", None))
        self.tabs.setTabText(self.tabs.indexOf(self.pageSettings), QCoreApplication.translate("MainWindow", u"Configura\u00e7\u00f5es", None))
        self.tabs.setTabText(self.tabs.indexOf(self.pageNetwork), QCoreApplication.translate("MainWindow", u"Rede", None))
        self.lblFooter.setText("")
#if QT_CONFIG(tooltip)
        self.btnAbout.setToolTip(QCoreApplication.translate("MainWindow", u"Vers\u00e3o, licen\u00e7as e avisos de terceiros", None))
#endif // QT_CONFIG(tooltip)
        self.btnAbout.setText(QCoreApplication.translate("MainWindow", u"Sobre", None))
#if QT_CONFIG(tooltip)
        self.btnTheme.setToolTip(QCoreApplication.translate("MainWindow", u"Alterna entre tema claro e escuro", None))
#endif // QT_CONFIG(tooltip)
        self.btnTheme.setText(QCoreApplication.translate("MainWindow", u"Tema escuro", None))
        self.btnSave.setText(QCoreApplication.translate("MainWindow", u"Salvar tudo", None))
        self.btnClose.setText(QCoreApplication.translate("MainWindow", u"Fechar", None))
    # retranslateUi

