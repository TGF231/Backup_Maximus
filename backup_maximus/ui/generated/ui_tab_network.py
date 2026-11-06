# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tab_network.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_TabNetwork(object):
    def setupUi(self, TabNetwork):
        if not TabNetwork.objectName():
            TabNetwork.setObjectName(u"TabNetwork")
        TabNetwork.resize(1000, 640)
        self.rootLayout = QVBoxLayout(TabNetwork)
        self.rootLayout.setSpacing(8)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(16, 14, 16, 12)
        self.lblNetSection = QLabel(TabNetwork)
        self.lblNetSection.setObjectName(u"lblNetSection")
        self.lblNetSection.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblNetSection)

        self.ruleBox = QFrame(TabNetwork)
        self.ruleBox.setObjectName(u"ruleBox")
        self.ruleBox.setProperty(u"role", u"rule")
        self.ruleLayout = QVBoxLayout(self.ruleBox)
        self.ruleLayout.setObjectName(u"ruleLayout")
        self.ruleLayout.setContentsMargins(14, 10, 14, 10)
        self.lblRuleText = QLabel(self.ruleBox)
        self.lblRuleText.setObjectName(u"lblRuleText")
        self.lblRuleText.setWordWrap(True)

        self.ruleLayout.addWidget(self.lblRuleText)


        self.rootLayout.addWidget(self.ruleBox)

        self.bodyLayout = QHBoxLayout()
        self.bodyLayout.setSpacing(16)
        self.bodyLayout.setObjectName(u"bodyLayout")
        self.listCreds = QListWidget(TabNetwork)
        self.listCreds.setObjectName(u"listCreds")

        self.bodyLayout.addWidget(self.listCreds)

        self.credPanel = QWidget(TabNetwork)
        self.credPanel.setObjectName(u"credPanel")
        self.credPanel.setMinimumSize(QSize(380, 0))
        self.credPanel.setMaximumSize(QSize(380, 16777215))
        self.credLayout = QVBoxLayout(self.credPanel)
        self.credLayout.setSpacing(7)
        self.credLayout.setObjectName(u"credLayout")
        self.credLayout.setContentsMargins(0, 0, 0, 0)
        self.gridCred = QGridLayout()
        self.gridCred.setObjectName(u"gridCred")
        self.gridCred.setHorizontalSpacing(8)
        self.gridCred.setVerticalSpacing(7)
        self.gridCred.setContentsMargins(0, -1, 0, -1)
        self.lblUnc = QLabel(self.credPanel)
        self.lblUnc.setObjectName(u"lblUnc")
        self.lblUnc.setProperty(u"role", u"field")
        self.lblUnc.setMinimumSize(QSize(124, 0))
        self.lblUnc.setMaximumSize(QSize(124, 16777215))
        self.lblUnc.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridCred.addWidget(self.lblUnc, 0, 0, 1, 1)

        self.editUnc = QLineEdit(self.credPanel)
        self.editUnc.setObjectName(u"editUnc")
        self.editUnc.setProperty(u"mono", u"true")

        self.gridCred.addWidget(self.editUnc, 0, 1, 1, 1)

        self.lblNetUser = QLabel(self.credPanel)
        self.lblNetUser.setObjectName(u"lblNetUser")
        self.lblNetUser.setProperty(u"role", u"field")
        self.lblNetUser.setMinimumSize(QSize(124, 0))
        self.lblNetUser.setMaximumSize(QSize(124, 16777215))
        self.lblNetUser.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridCred.addWidget(self.lblNetUser, 1, 0, 1, 1)

        self.editNetUser = QLineEdit(self.credPanel)
        self.editNetUser.setObjectName(u"editNetUser")

        self.gridCred.addWidget(self.editNetUser, 1, 1, 1, 1)

        self.lblNetPass = QLabel(self.credPanel)
        self.lblNetPass.setObjectName(u"lblNetPass")
        self.lblNetPass.setProperty(u"role", u"field")
        self.lblNetPass.setMinimumSize(QSize(124, 0))
        self.lblNetPass.setMaximumSize(QSize(124, 16777215))
        self.lblNetPass.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridCred.addWidget(self.lblNetPass, 2, 0, 1, 1)

        self.editNetPass = QLineEdit(self.credPanel)
        self.editNetPass.setObjectName(u"editNetPass")
        self.editNetPass.setEchoMode(QLineEdit.Password)

        self.gridCred.addWidget(self.editNetPass, 2, 1, 1, 1)

        self.credActionsLayout = QHBoxLayout()
        self.credActionsLayout.setSpacing(8)
        self.credActionsLayout.setObjectName(u"credActionsLayout")
        self.btnCredAdd = QPushButton(self.credPanel)
        self.btnCredAdd.setObjectName(u"btnCredAdd")
        self.btnCredAdd.setProperty(u"role", u"accent")

        self.credActionsLayout.addWidget(self.btnCredAdd)

        self.btnCredDel = QPushButton(self.credPanel)
        self.btnCredDel.setObjectName(u"btnCredDel")

        self.credActionsLayout.addWidget(self.btnCredDel)


        self.gridCred.addLayout(self.credActionsLayout, 3, 1, 1, 1)

        self.lblCredHint = QLabel(self.credPanel)
        self.lblCredHint.setObjectName(u"lblCredHint")
        self.lblCredHint.setProperty(u"role", u"hint")
        self.lblCredHint.setWordWrap(True)

        self.gridCred.addWidget(self.lblCredHint, 4, 1, 1, 1)


        self.credLayout.addLayout(self.gridCred)

        self.credSpacer = QSpacerItem(0, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.credLayout.addItem(self.credSpacer)


        self.bodyLayout.addWidget(self.credPanel)


        self.rootLayout.addLayout(self.bodyLayout)


        self.retranslateUi(TabNetwork)

        QMetaObject.connectSlotsByName(TabNetwork)
    # setupUi

    def retranslateUi(self, TabNetwork):
        self.lblNetSection.setText(QCoreApplication.translate("TabNetwork", u"CREDENCIAIS PARA COMPARTILHAMENTOS DE REDE (UNC)", None))
        self.lblRuleText.setText(QCoreApplication.translate("TabNetwork", u"A credencial pertence ao compartilhamento, n\u00e3o ao item. V\u00e1rios itens que gravam no mesmo servidor usam uma entrada s\u00f3 \u2014 quando a senha do servi\u00e7o muda, voc\u00ea a troca aqui e acabou.", None))
        self.lblUnc.setText(QCoreApplication.translate("TabNetwork", u"Compartilhamento", None))
        self.editUnc.setPlaceholderText(QCoreApplication.translate("TabNetwork", u"\\\\servidor\\backups", None))
        self.lblNetUser.setText(QCoreApplication.translate("TabNetwork", u"Usu\u00e1rio", None))
        self.editNetUser.setPlaceholderText(QCoreApplication.translate("TabNetwork", u"DOMINIO\\usuario", None))
        self.lblNetPass.setText(QCoreApplication.translate("TabNetwork", u"Senha", None))
        self.btnCredAdd.setText(QCoreApplication.translate("TabNetwork", u"Adicionar", None))
        self.btnCredDel.setText(QCoreApplication.translate("TabNetwork", u"Remover selecionada", None))
        self.lblCredHint.setText(QCoreApplication.translate("TabNetwork", u"Usada automaticamente quando a origem de um item ou o destino de um conjunto estiver nesse compartilhamento. A conex\u00e3o \u00e9 desfeita ao final do backup.", None))
        pass
    # retranslateUi

