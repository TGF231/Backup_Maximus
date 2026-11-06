# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_profile.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_ProfileDialog(object):
    def setupUi(self, ProfileDialog):
        if not ProfileDialog.objectName():
            ProfileDialog.setObjectName(u"ProfileDialog")
        ProfileDialog.resize(660, 540)
        ProfileDialog.setMinimumSize(QSize(620, 500))
        self.rootLayout = QVBoxLayout(ProfileDialog)
        self.rootLayout.setSpacing(12)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(22, 20, 22, 18)
        self.lblOrigemTitle = QLabel(ProfileDialog)
        self.lblOrigemTitle.setObjectName(u"lblOrigemTitle")
        self.lblOrigemTitle.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblOrigemTitle)

        self.origemLayout = QHBoxLayout()
        self.origemLayout.setSpacing(8)
        self.origemLayout.setObjectName(u"origemLayout")
        self.comboOrigem = QComboBox(ProfileDialog)
        self.comboOrigem.setObjectName(u"comboOrigem")

        self.origemLayout.addWidget(self.comboOrigem)

        self.btnBrowse = QPushButton(ProfileDialog)
        self.btnBrowse.setObjectName(u"btnBrowse")

        self.origemLayout.addWidget(self.btnBrowse)


        self.rootLayout.addLayout(self.origemLayout)

        self.lblConteudoTitle = QLabel(ProfileDialog)
        self.lblConteudoTitle.setObjectName(u"lblConteudoTitle")
        self.lblConteudoTitle.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblConteudoTitle)

        self.listing = QTreeWidget(ProfileDialog)
        self.listing.setObjectName(u"listing")
        self.listing.setRootIsDecorated(False)
        self.listing.setAlternatingRowColors(True)
        self.listing.setUniformRowHeights(True)

        self.rootLayout.addWidget(self.listing)

        self.lblComoTitle = QLabel(ProfileDialog)
        self.lblComoTitle.setObjectName(u"lblComoTitle")
        self.lblComoTitle.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblComoTitle)

        self.comoLayout = QGridLayout()
        self.comoLayout.setObjectName(u"comoLayout")
        self.comoLayout.setHorizontalSpacing(10)
        self.comoLayout.setVerticalSpacing(6)
        self.lblModo = QLabel(ProfileDialog)
        self.lblModo.setObjectName(u"lblModo")
        self.lblModo.setProperty(u"role", u"field")
        self.lblModo.setMinimumSize(QSize(124, 0))
        self.lblModo.setMaximumSize(QSize(124, 16777215))
        self.lblModo.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.comoLayout.addWidget(self.lblModo, 0, 0, 1, 1)

        self.comboModo = QComboBox(ProfileDialog)
        self.comboModo.setObjectName(u"comboModo")

        self.comoLayout.addWidget(self.comboModo, 0, 1, 1, 1)

        self.chkGerais = QCheckBox(ProfileDialog)
        self.chkGerais.setObjectName(u"chkGerais")

        self.comoLayout.addWidget(self.chkGerais, 1, 1, 1, 1)


        self.rootLayout.addLayout(self.comoLayout)

        self.lblStatus = QLabel(ProfileDialog)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setProperty(u"role", u"hint")
        self.lblStatus.setWordWrap(True)

        self.rootLayout.addWidget(self.lblStatus)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(8)
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.buttonSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.buttonSpacer)

        self.btnImport = QPushButton(ProfileDialog)
        self.btnImport.setObjectName(u"btnImport")
        self.btnImport.setProperty(u"role", u"accent")

        self.buttonLayout.addWidget(self.btnImport)

        self.btnCancel = QPushButton(ProfileDialog)
        self.btnCancel.setObjectName(u"btnCancel")

        self.buttonLayout.addWidget(self.btnCancel)


        self.rootLayout.addLayout(self.buttonLayout)


        self.retranslateUi(ProfileDialog)

        QMetaObject.connectSlotsByName(ProfileDialog)
    # setupUi

    def retranslateUi(self, ProfileDialog):
        ProfileDialog.setWindowTitle(QCoreApplication.translate("ProfileDialog", u"Importar configura\u00e7\u00f5es", None))
        self.lblOrigemTitle.setText(QCoreApplication.translate("ProfileDialog", u"DE ONDE VEM", None))
#if QT_CONFIG(tooltip)
        self.comboOrigem.setToolTip(QCoreApplication.translate("ProfileDialog", u"Um modelo que acompanha o programa, ou um arquivo exportado de outra m\u00e1quina", None))
#endif // QT_CONFIG(tooltip)
        self.btnBrowse.setText(QCoreApplication.translate("ProfileDialog", u"Escolher arquivo\u2026", None))
        self.lblConteudoTitle.setText(QCoreApplication.translate("ProfileDialog", u"O QUE H\u00c1 DENTRO", None))
        ___qtreewidgetitem = self.listing.headerItem()
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("ProfileDialog", u"Destino", None))
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("ProfileDialog", u"Itens", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("ProfileDialog", u"Conjunto", None))
        self.lblComoTitle.setText(QCoreApplication.translate("ProfileDialog", u"COMO APLICAR", None))
        self.lblModo.setText(QCoreApplication.translate("ProfileDialog", u"Conjuntos", None))
        self.chkGerais.setText(QCoreApplication.translate("ProfileDialog", u"Trazer tamb\u00e9m empresa, e-mail e servidor de envio", None))
        self.lblStatus.setText("")
        self.btnImport.setText(QCoreApplication.translate("ProfileDialog", u"Importar", None))
        self.btnCancel.setText(QCoreApplication.translate("ProfileDialog", u"Cancelar", None))
    # retranslateUi

