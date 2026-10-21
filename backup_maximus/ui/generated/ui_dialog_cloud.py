# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_cloud.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
    QWidget)

class Ui_CloudDialog(object):
    def setupUi(self, CloudDialog):
        if not CloudDialog.objectName():
            CloudDialog.setObjectName(u"CloudDialog")
        CloudDialog.resize(640, 470)
        CloudDialog.setMinimumSize(QSize(600, 430))
        self.rootLayout = QVBoxLayout(CloudDialog)
        self.rootLayout.setSpacing(12)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(22, 20, 22, 18)
        self.lblHeader = QLabel(CloudDialog)
        self.lblHeader.setObjectName(u"lblHeader")
        self.lblHeader.setProperty(u"role", u"title")

        self.rootLayout.addWidget(self.lblHeader)

        self.soonRule = QFrame(CloudDialog)
        self.soonRule.setObjectName(u"soonRule")
        self.soonRule.setProperty(u"role", u"rule")
        self.soonLayout = QVBoxLayout(self.soonRule)
        self.soonLayout.setSpacing(4)
        self.soonLayout.setObjectName(u"soonLayout")
        self.soonLayout.setContentsMargins(14, 10, 14, 10)
        self.lblSoonTitle = QLabel(self.soonRule)
        self.lblSoonTitle.setObjectName(u"lblSoonTitle")
        self.lblSoonTitle.setProperty(u"role", u"hintWarn")

        self.soonLayout.addWidget(self.lblSoonTitle)

        self.lblSoon = QLabel(self.soonRule)
        self.lblSoon.setObjectName(u"lblSoon")
        self.lblSoon.setWordWrap(True)

        self.soonLayout.addWidget(self.lblSoon)


        self.rootLayout.addWidget(self.soonRule)

        self.lblFoldersTitle = QLabel(CloudDialog)
        self.lblFoldersTitle.setObjectName(u"lblFoldersTitle")
        self.lblFoldersTitle.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblFoldersTitle)

        self.listing = QTreeWidget(CloudDialog)
        self.listing.setObjectName(u"listing")
        self.listing.setRootIsDecorated(False)
        self.listing.setAlternatingRowColors(True)
        self.listing.setUniformRowHeights(True)

        self.rootLayout.addWidget(self.listing)

        self.lblStatus = QLabel(CloudDialog)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setProperty(u"role", u"hint")
        self.lblStatus.setWordWrap(True)

        self.rootLayout.addWidget(self.lblStatus)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.btnUse = QPushButton(CloudDialog)
        self.btnUse.setObjectName(u"btnUse")
        self.btnUse.setProperty(u"role", u"accent")

        self.buttonLayout.addWidget(self.btnUse)

        self.btnRefresh = QPushButton(CloudDialog)
        self.btnRefresh.setObjectName(u"btnRefresh")

        self.buttonLayout.addWidget(self.btnRefresh)

        self.buttonSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.buttonSpacer)

        self.btnClose = QPushButton(CloudDialog)
        self.btnClose.setObjectName(u"btnClose")

        self.buttonLayout.addWidget(self.btnClose)


        self.rootLayout.addLayout(self.buttonLayout)


        self.retranslateUi(CloudDialog)

        QMetaObject.connectSlotsByName(CloudDialog)
    # setupUi

    def retranslateUi(self, CloudDialog):
        CloudDialog.setWindowTitle(QCoreApplication.translate("CloudDialog", u"Nuvem", None))
        self.lblHeader.setText(QCoreApplication.translate("CloudDialog", u"Backup na nuvem", None))
        self.lblSoonTitle.setText(QCoreApplication.translate("CloudDialog", u"EM BREVE \u2014 envio direto pela API do servi\u00e7o", None))
        self.lblSoon.setText("")
        self.lblFoldersTitle.setText(QCoreApplication.translate("CloudDialog", u"PASTAS SINCRONIZADAS NESTE COMPUTADOR", None))
        ___qtreewidgetitem = self.listing.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("CloudDialog", u"Livre", None))
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("CloudDialog", u"Pasta", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("CloudDialog", u"Servi\u00e7o", None))
        self.lblStatus.setText("")
#if QT_CONFIG(tooltip)
        self.btnUse.setToolTip(QCoreApplication.translate("CloudDialog", u"Grava o zip deste conjunto na pasta escolhida; o cliente de sincroniza\u00e7\u00e3o envia", None))
#endif // QT_CONFIG(tooltip)
        self.btnUse.setText(QCoreApplication.translate("CloudDialog", u"Usar como destino deste conjunto", None))
        self.btnRefresh.setText(QCoreApplication.translate("CloudDialog", u"Procurar de novo", None))
        self.btnClose.setText(QCoreApplication.translate("CloudDialog", u"Fechar", None))
    # retranslateUi

