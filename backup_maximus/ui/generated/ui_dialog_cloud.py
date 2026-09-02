# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_cloud.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QComboBox, QDialog,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

class Ui_CloudDialog(object):
    def setupUi(self, CloudDialog):
        if not CloudDialog.objectName():
            CloudDialog.setObjectName(u"CloudDialog")
        CloudDialog.resize(640, 480)
        CloudDialog.setModal(True)
        self.rootLayout = QVBoxLayout(CloudDialog)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(18, 16, 18, 14)
        self.ruleBox = QFrame(CloudDialog)
        self.ruleBox.setObjectName(u"ruleBox")
        self.ruleBox.setProperty(u"role", u"rule")
        self.ruleLayout = QVBoxLayout(self.ruleBox)
        self.ruleLayout.setObjectName(u"ruleLayout")
        self.ruleLayout.setContentsMargins(14, 10, 14, 10)
        self.lblIntro = QLabel(self.ruleBox)
        self.lblIntro.setObjectName(u"lblIntro")
        self.lblIntro.setWordWrap(True)

        self.ruleLayout.addWidget(self.lblIntro)


        self.rootLayout.addWidget(self.ruleBox)

        self.gridCloud = QGridLayout()
        self.gridCloud.setObjectName(u"gridCloud")
        self.gridCloud.setHorizontalSpacing(8)
        self.gridCloud.setVerticalSpacing(7)
        self.lblRemote = QLabel(CloudDialog)
        self.lblRemote.setObjectName(u"lblRemote")
        self.lblRemote.setProperty(u"role", u"field")
        self.lblRemote.setMinimumSize(QSize(124, 0))
        self.lblRemote.setMaximumSize(QSize(124, 16777215))
        self.lblRemote.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridCloud.addWidget(self.lblRemote, 0, 0, 1, 1)

        self.comboRemote = QComboBox(CloudDialog)
        self.comboRemote.setObjectName(u"comboRemote")

        self.gridCloud.addWidget(self.comboRemote, 0, 1, 1, 1)

        self.remoteActionsLayout = QHBoxLayout()
        self.remoteActionsLayout.setSpacing(6)
        self.remoteActionsLayout.setObjectName(u"remoteActionsLayout")
        self.btnConfigure = QPushButton(CloudDialog)
        self.btnConfigure.setObjectName(u"btnConfigure")

        self.remoteActionsLayout.addWidget(self.btnConfigure)

        self.btnRemove = QPushButton(CloudDialog)
        self.btnRemove.setObjectName(u"btnRemove")

        self.remoteActionsLayout.addWidget(self.btnRemove)


        self.gridCloud.addLayout(self.remoteActionsLayout, 0, 2, 1, 1)

        self.lblPath = QLabel(CloudDialog)
        self.lblPath.setObjectName(u"lblPath")
        self.lblPath.setProperty(u"role", u"field")
        self.lblPath.setMinimumSize(QSize(124, 0))
        self.lblPath.setMaximumSize(QSize(124, 16777215))
        self.lblPath.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridCloud.addWidget(self.lblPath, 1, 0, 1, 1)

        self.editPath = QLineEdit(CloudDialog)
        self.editPath.setObjectName(u"editPath")
        self.editPath.setProperty(u"mono", u"true")

        self.gridCloud.addWidget(self.editPath, 1, 1, 1, 1)

        self.btnTest = QPushButton(CloudDialog)
        self.btnTest.setObjectName(u"btnTest")

        self.gridCloud.addWidget(self.btnTest, 1, 2, 1, 1)

        self.lblKeep = QLabel(CloudDialog)
        self.lblKeep.setObjectName(u"lblKeep")
        self.lblKeep.setProperty(u"role", u"field")
        self.lblKeep.setMinimumSize(QSize(124, 0))
        self.lblKeep.setMaximumSize(QSize(124, 16777215))
        self.lblKeep.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridCloud.addWidget(self.lblKeep, 2, 0, 1, 1)

        self.keepLayout = QHBoxLayout()
        self.keepLayout.setSpacing(10)
        self.keepLayout.setObjectName(u"keepLayout")
        self.spinKeep = QSpinBox(CloudDialog)
        self.spinKeep.setObjectName(u"spinKeep")
        self.spinKeep.setMinimumSize(QSize(96, 0))
        self.spinKeep.setMaximumSize(QSize(96, 16777215))
        self.spinKeep.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinKeep.setMaximum(999)

        self.keepLayout.addWidget(self.spinKeep)

        self.lblKeepNote = QLabel(CloudDialog)
        self.lblKeepNote.setObjectName(u"lblKeepNote")
        self.lblKeepNote.setProperty(u"role", u"hint")

        self.keepLayout.addWidget(self.lblKeepNote)

        self.keepSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.keepLayout.addItem(self.keepSpacer)


        self.gridCloud.addLayout(self.keepLayout, 2, 1, 1, 2)

        self.lblStatus = QLabel(CloudDialog)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setProperty(u"role", u"hint")
        self.lblStatus.setWordWrap(True)

        self.gridCloud.addWidget(self.lblStatus, 3, 1, 1, 2)


        self.rootLayout.addLayout(self.gridCloud)

        self.lblFilesHeader = QLabel(CloudDialog)
        self.lblFilesHeader.setObjectName(u"lblFilesHeader")
        self.lblFilesHeader.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblFilesHeader)

        self.listing = QTreeWidget(CloudDialog)
        self.listing.setObjectName(u"listing")
        self.listing.setRootIsDecorated(False)

        self.rootLayout.addWidget(self.listing)

        self.actionsLayout = QHBoxLayout()
        self.actionsLayout.setSpacing(8)
        self.actionsLayout.setObjectName(u"actionsLayout")
        self.lblTerabox = QLabel(CloudDialog)
        self.lblTerabox.setObjectName(u"lblTerabox")
        self.lblTerabox.setProperty(u"role", u"hint")
        self.lblTerabox.setWordWrap(True)

        self.actionsLayout.addWidget(self.lblTerabox)

        self.actionsSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionsLayout.addItem(self.actionsSpacer)

        self.btnOk = QPushButton(CloudDialog)
        self.btnOk.setObjectName(u"btnOk")
        self.btnOk.setProperty(u"role", u"accent")

        self.actionsLayout.addWidget(self.btnOk)

        self.btnCancel = QPushButton(CloudDialog)
        self.btnCancel.setObjectName(u"btnCancel")

        self.actionsLayout.addWidget(self.btnCancel)


        self.rootLayout.addLayout(self.actionsLayout)


        self.retranslateUi(CloudDialog)

        QMetaObject.connectSlotsByName(CloudDialog)
    # setupUi

    def retranslateUi(self, CloudDialog):
        CloudDialog.setWindowTitle(QCoreApplication.translate("CloudDialog", u"Envio \u00e0 nuvem", None))
        self.lblIntro.setText(QCoreApplication.translate("CloudDialog", u"O zip \u00e9 enviado pela API do servi\u00e7o e o backup s\u00f3 \u00e9 dado como conclu\u00eddo depois que o arquivo chega. Diferente de gravar numa pasta sincronizada, onde o envio acontece depois e ningu\u00e9m confere.", None))
        self.lblRemote.setText(QCoreApplication.translate("CloudDialog", u"Servi\u00e7o", None))
        self.btnConfigure.setText(QCoreApplication.translate("CloudDialog", u"Adicionar\u2026", None))
#if QT_CONFIG(tooltip)
        self.btnConfigure.setToolTip(QCoreApplication.translate("CloudDialog", u"Cadastra um servi\u00e7o novo, com login pelo navegador.", None))
#endif // QT_CONFIG(tooltip)
        self.btnRemove.setText(QCoreApplication.translate("CloudDialog", u"Remover", None))
#if QT_CONFIG(tooltip)
        self.btnRemove.setToolTip(QCoreApplication.translate("CloudDialog", u"Apaga o servi\u00e7o escolhido do rclone.", None))
#endif // QT_CONFIG(tooltip)
        self.lblPath.setText(QCoreApplication.translate("CloudDialog", u"Pasta na nuvem", None))
        self.editPath.setPlaceholderText(QCoreApplication.translate("CloudDialog", u"ex.: Backups/Loja1   (vazio = raiz)", None))
        self.btnTest.setText(QCoreApplication.translate("CloudDialog", u"Testar conex\u00e3o", None))
        self.lblKeep.setText(QCoreApplication.translate("CloudDialog", u"Manter na nuvem", None))
        self.lblKeepNote.setText(QCoreApplication.translate("CloudDialog", u"0 = manter todos \u00b7 a nuvem costuma ter mais espa\u00e7o que o pen drive", None))
        self.lblStatus.setText("")
        self.lblFilesHeader.setText(QCoreApplication.translate("CloudDialog", u"J\u00c1 NA NUVEM", None))
        ___qtreewidgetitem = self.listing.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("CloudDialog", u"Enviado em", None))
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("CloudDialog", u"Tamanho", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("CloudDialog", u"Arquivo", None))
        self.lblTerabox.setText(QCoreApplication.translate("CloudDialog", u"Terabox n\u00e3o tem API p\u00fablica: para ele, aponte o destino do conjunto para a pasta do cliente de sincroniza\u00e7\u00e3o.", None))
        self.btnOk.setText(QCoreApplication.translate("CloudDialog", u"Aplicar", None))
        self.btnCancel.setText(QCoreApplication.translate("CloudDialog", u"Cancelar", None))
    # retranslateUi

