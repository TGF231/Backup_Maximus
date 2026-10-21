# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_about.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_DialogAbout(object):
    def setupUi(self, DialogAbout):
        if not DialogAbout.objectName():
            DialogAbout.setObjectName(u"DialogAbout")
        DialogAbout.resize(560, 520)
        DialogAbout.setMinimumSize(QSize(520, 460))
        self.rootLayout = QVBoxLayout(DialogAbout)
        self.rootLayout.setSpacing(12)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(22, 20, 22, 18)
        self.lblTitle = QLabel(DialogAbout)
        self.lblTitle.setObjectName(u"lblTitle")
        self.lblTitle.setProperty(u"role", u"title")

        self.rootLayout.addWidget(self.lblTitle)

        self.lblVersion = QLabel(DialogAbout)
        self.lblVersion.setObjectName(u"lblVersion")
        self.lblVersion.setProperty(u"role", u"hint")

        self.rootLayout.addWidget(self.lblVersion)

        self.tabs = QTabWidget(DialogAbout)
        self.tabs.setObjectName(u"tabs")
        self.tabApp = QWidget()
        self.tabApp.setObjectName(u"tabApp")
        self.appLayout = QVBoxLayout(self.tabApp)
        self.appLayout.setObjectName(u"appLayout")
        self.textApp = QTextBrowser(self.tabApp)
        self.textApp.setObjectName(u"textApp")
        self.textApp.setOpenExternalLinks(True)

        self.appLayout.addWidget(self.textApp)

        self.tabs.addTab(self.tabApp, "")
        self.tabThird = QWidget()
        self.tabThird.setObjectName(u"tabThird")
        self.thirdLayout = QVBoxLayout(self.tabThird)
        self.thirdLayout.setObjectName(u"thirdLayout")
        self.textThird = QTextBrowser(self.tabThird)
        self.textThird.setObjectName(u"textThird")
        self.textThird.setOpenExternalLinks(True)

        self.thirdLayout.addWidget(self.textThird)

        self.tabs.addTab(self.tabThird, "")
        self.tabSystem = QWidget()
        self.tabSystem.setObjectName(u"tabSystem")
        self.systemLayout = QVBoxLayout(self.tabSystem)
        self.systemLayout.setObjectName(u"systemLayout")
        self.textSystem = QTextBrowser(self.tabSystem)
        self.textSystem.setObjectName(u"textSystem")

        self.systemLayout.addWidget(self.textSystem)

        self.tabs.addTab(self.tabSystem, "")

        self.rootLayout.addWidget(self.tabs)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.btnLicenses = QPushButton(DialogAbout)
        self.btnLicenses.setObjectName(u"btnLicenses")

        self.buttonLayout.addWidget(self.btnLicenses)

        self.btnCopy = QPushButton(DialogAbout)
        self.btnCopy.setObjectName(u"btnCopy")

        self.buttonLayout.addWidget(self.btnCopy)

        self.buttonSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.buttonSpacer)

        self.btnClose = QPushButton(DialogAbout)
        self.btnClose.setObjectName(u"btnClose")
        self.btnClose.setProperty(u"role", u"accent")

        self.buttonLayout.addWidget(self.btnClose)


        self.rootLayout.addLayout(self.buttonLayout)


        self.retranslateUi(DialogAbout)

        self.tabs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DialogAbout)
    # setupUi

    def retranslateUi(self, DialogAbout):
        DialogAbout.setWindowTitle(QCoreApplication.translate("DialogAbout", u"Sobre o Backup Maximus", None))
        self.lblTitle.setText(QCoreApplication.translate("DialogAbout", u"Backup Maximus", None))
        self.lblVersion.setText("")
        self.tabs.setTabText(self.tabs.indexOf(self.tabApp), QCoreApplication.translate("DialogAbout", u"Aplicativo", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tabThird), QCoreApplication.translate("DialogAbout", u"Componentes de terceiros", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tabSystem), QCoreApplication.translate("DialogAbout", u"Diagn\u00f3stico", None))
#if QT_CONFIG(tooltip)
        self.btnLicenses.setToolTip(QCoreApplication.translate("DialogAbout", u"Abre a pasta com os textos completos das licen\u00e7as", None))
#endif // QT_CONFIG(tooltip)
        self.btnLicenses.setText(QCoreApplication.translate("DialogAbout", u"Ver licen\u00e7as", None))
#if QT_CONFIG(tooltip)
        self.btnCopy.setToolTip(QCoreApplication.translate("DialogAbout", u"Copia o diagn\u00f3stico para enviar ao suporte", None))
#endif // QT_CONFIG(tooltip)
        self.btnCopy.setText(QCoreApplication.translate("DialogAbout", u"Copiar diagn\u00f3stico", None))
        self.btnClose.setText(QCoreApplication.translate("DialogAbout", u"Fechar", None))
    # retranslateUi

