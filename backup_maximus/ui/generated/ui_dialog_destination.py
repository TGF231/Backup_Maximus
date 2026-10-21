# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_destination.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_DestinationDialog(object):
    def setupUi(self, DestinationDialog):
        if not DestinationDialog.objectName():
            DestinationDialog.setObjectName(u"DestinationDialog")
        DestinationDialog.resize(660, 520)
        DestinationDialog.setModal(True)
        self.rootLayout = QVBoxLayout(DestinationDialog)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(18, 16, 18, 14)
        self.lblSummary = QLabel(DestinationDialog)
        self.lblSummary.setObjectName(u"lblSummary")
        self.lblSummary.setProperty(u"role", u"bigStatus")
        self.lblSummary.setWordWrap(True)

        self.rootLayout.addWidget(self.lblSummary)

        self.lblDetail = QLabel(DestinationDialog)
        self.lblDetail.setObjectName(u"lblDetail")
        self.lblDetail.setProperty(u"role", u"hint")
        self.lblDetail.setWordWrap(True)

        self.rootLayout.addWidget(self.lblDetail)

        self.listing = QTreeWidget(DestinationDialog)
        self.listing.setObjectName(u"listing")
        self.listing.setRootIsDecorated(False)

        self.rootLayout.addWidget(self.listing)

        self.lblPolicy = QLabel(DestinationDialog)
        self.lblPolicy.setObjectName(u"lblPolicy")
        self.lblPolicy.setProperty(u"role", u"hint")
        self.lblPolicy.setWordWrap(True)

        self.rootLayout.addWidget(self.lblPolicy)

        self.actionsLayout = QHBoxLayout()
        self.actionsLayout.setSpacing(8)
        self.actionsLayout.setObjectName(u"actionsLayout")
        self.btnPrune = QPushButton(DestinationDialog)
        self.btnPrune.setObjectName(u"btnPrune")
        self.btnPrune.setProperty(u"role", u"accent")

        self.actionsLayout.addWidget(self.btnPrune)

        self.actionsSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionsLayout.addItem(self.actionsSpacer)

        self.btnClose = QPushButton(DestinationDialog)
        self.btnClose.setObjectName(u"btnClose")

        self.actionsLayout.addWidget(self.btnClose)


        self.rootLayout.addLayout(self.actionsLayout)


        self.retranslateUi(DestinationDialog)

        QMetaObject.connectSlotsByName(DestinationDialog)
    # setupUi

    def retranslateUi(self, DestinationDialog):
        DestinationDialog.setWindowTitle(QCoreApplication.translate("DestinationDialog", u"Destino", None))
        self.lblSummary.setText("")
        self.lblDetail.setText("")
        ___qtreewidgetitem = self.listing.headerItem()
        ___qtreewidgetitem.setText(3, QCoreApplication.translate("DestinationDialog", u"Situa\u00e7\u00e3o", None))
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("DestinationDialog", u"Data", None))
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("DestinationDialog", u"Tamanho", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("DestinationDialog", u"Arquivo", None))
        self.lblPolicy.setText("")
        self.btnPrune.setText(QCoreApplication.translate("DestinationDialog", u"Limpar backups antigos", None))
        self.btnClose.setText(QCoreApplication.translate("DestinationDialog", u"Fechar", None))
    # retranslateUi

