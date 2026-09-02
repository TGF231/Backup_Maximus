# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_aliases.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

class Ui_AliasDialog(object):
    def setupUi(self, AliasDialog):
        if not AliasDialog.objectName():
            AliasDialog.setObjectName(u"AliasDialog")
        AliasDialog.resize(720, 520)
        AliasDialog.setModal(True)
        self.rootLayout = QVBoxLayout(AliasDialog)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(18, 16, 18, 14)
        self.ruleBox = QFrame(AliasDialog)
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

        self.tree = QTreeWidget(AliasDialog)
        self.tree.setObjectName(u"tree")
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(False)

        self.rootLayout.addWidget(self.tree)

        self.selectLayout = QHBoxLayout()
        self.selectLayout.setSpacing(0)
        self.selectLayout.setObjectName(u"selectLayout")
        self.btnAll = QPushButton(AliasDialog)
        self.btnAll.setObjectName(u"btnAll")

        self.selectLayout.addWidget(self.btnAll)

        self.btnNone = QPushButton(AliasDialog)
        self.btnNone.setObjectName(u"btnNone")

        self.selectLayout.addWidget(self.btnNone)

        self.selectSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.selectLayout.addItem(self.selectSpacer)

        self.lblCount = QLabel(AliasDialog)
        self.lblCount.setObjectName(u"lblCount")
        self.lblCount.setProperty(u"role", u"hint")

        self.selectLayout.addWidget(self.lblCount)


        self.rootLayout.addLayout(self.selectLayout)

        self.optionsLayout = QHBoxLayout()
        self.optionsLayout.setSpacing(0)
        self.optionsLayout.setObjectName(u"optionsLayout")
        self.chkSubfolder = QCheckBox(AliasDialog)
        self.chkSubfolder.setObjectName(u"chkSubfolder")
        self.chkSubfolder.setChecked(True)

        self.optionsLayout.addWidget(self.chkSubfolder)

        self.optionsSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.optionsLayout.addItem(self.optionsSpacer)


        self.rootLayout.addLayout(self.optionsLayout)

        self.lblHint = QLabel(AliasDialog)
        self.lblHint.setObjectName(u"lblHint")
        self.lblHint.setProperty(u"role", u"hint")
        self.lblHint.setWordWrap(True)

        self.rootLayout.addWidget(self.lblHint)

        self.actionsLayout = QHBoxLayout()
        self.actionsLayout.setSpacing(0)
        self.actionsLayout.setObjectName(u"actionsLayout")
        self.btnRescan = QPushButton(AliasDialog)
        self.btnRescan.setObjectName(u"btnRescan")

        self.actionsLayout.addWidget(self.btnRescan)

        self.actionsSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionsLayout.addItem(self.actionsSpacer)

        self.btnAdd = QPushButton(AliasDialog)
        self.btnAdd.setObjectName(u"btnAdd")
        self.btnAdd.setProperty(u"role", u"accent")

        self.actionsLayout.addWidget(self.btnAdd)

        self.btnCancel = QPushButton(AliasDialog)
        self.btnCancel.setObjectName(u"btnCancel")

        self.actionsLayout.addWidget(self.btnCancel)


        self.rootLayout.addLayout(self.actionsLayout)


        self.retranslateUi(AliasDialog)

        QMetaObject.connectSlotsByName(AliasDialog)
    # setupUi

    def retranslateUi(self, AliasDialog):
        AliasDialog.setWindowTitle(QCoreApplication.translate("AliasDialog", u"Bancos registrados no Firebird", None))
        self.lblIntro.setText("")
        ___qtreewidgetitem = self.tree.headerItem()
        ___qtreewidgetitem.setText(3, QCoreApplication.translate("AliasDialog", u"Arquivo", None))
        ___qtreewidgetitem.setText(2, QCoreApplication.translate("AliasDialog", u"Tamanho", None))
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("AliasDialog", u"Servidor", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("AliasDialog", u"Alias", None))
        self.btnAll.setText(QCoreApplication.translate("AliasDialog", u"Marcar todos", None))
        self.btnNone.setText(QCoreApplication.translate("AliasDialog", u"Desmarcar todos", None))
        self.lblCount.setText("")
        self.chkSubfolder.setText(QCoreApplication.translate("AliasDialog", u"Criar uma subpasta por banco dentro do zip", None))
        self.lblHint.setText(QCoreApplication.translate("AliasDialog", u"Cada banco marcado vira um item do tipo Firebird, com o alias como origem e o gbak da instala\u00e7\u00e3o correspondente. A senha do SYSDBA precisa ser preenchida depois, em cada item.", None))
        self.btnRescan.setText(QCoreApplication.translate("AliasDialog", u"Procurar de novo", None))
        self.btnAdd.setText(QCoreApplication.translate("AliasDialog", u"Adicionar selecionados", None))
        self.btnCancel.setText(QCoreApplication.translate("AliasDialog", u"Cancelar", None))
    # retranslateUi

