# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_cloud_setup.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QStackedWidget, QVBoxLayout, QWidget)

class Ui_CloudSetupDialog(object):
    def setupUi(self, CloudSetupDialog):
        if not CloudSetupDialog.objectName():
            CloudSetupDialog.setObjectName(u"CloudSetupDialog")
        CloudSetupDialog.resize(660, 560)
        CloudSetupDialog.setModal(True)
        self.rootLayout = QVBoxLayout(CloudSetupDialog)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(18, 16, 18, 14)
        self.gridTop = QGridLayout()
        self.gridTop.setObjectName(u"gridTop")
        self.gridTop.setHorizontalSpacing(8)
        self.gridTop.setVerticalSpacing(7)
        self.lblProvider = QLabel(CloudSetupDialog)
        self.lblProvider.setObjectName(u"lblProvider")
        self.lblProvider.setProperty(u"role", u"field")
        self.lblProvider.setMinimumSize(QSize(124, 0))
        self.lblProvider.setMaximumSize(QSize(124, 16777215))
        self.lblProvider.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridTop.addWidget(self.lblProvider, 0, 0, 1, 1)

        self.comboProvider = QComboBox(CloudSetupDialog)
        self.comboProvider.setObjectName(u"comboProvider")

        self.gridTop.addWidget(self.comboProvider, 0, 1, 1, 1)

        self.lblName = QLabel(CloudSetupDialog)
        self.lblName.setObjectName(u"lblName")
        self.lblName.setProperty(u"role", u"field")
        self.lblName.setMinimumSize(QSize(124, 0))
        self.lblName.setMaximumSize(QSize(124, 16777215))
        self.lblName.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridTop.addWidget(self.lblName, 1, 0, 1, 1)

        self.editName = QLineEdit(CloudSetupDialog)
        self.editName.setObjectName(u"editName")
        self.editName.setProperty(u"mono", u"true")

        self.gridTop.addWidget(self.editName, 1, 1, 1, 1)

        self.lblNameHint = QLabel(CloudSetupDialog)
        self.lblNameHint.setObjectName(u"lblNameHint")
        self.lblNameHint.setProperty(u"role", u"hint")
        self.lblNameHint.setWordWrap(True)

        self.gridTop.addWidget(self.lblNameHint, 2, 1, 1, 1)


        self.rootLayout.addLayout(self.gridTop)

        self.dividerTop = QFrame(CloudSetupDialog)
        self.dividerTop.setObjectName(u"dividerTop")
        self.dividerTop.setProperty(u"role", u"divider")
        self.dividerTop.setMinimumSize(QSize(0, 1))
        self.dividerTop.setMaximumSize(QSize(16777215, 1))
        self.dividerTop.setFrameShape(QFrame.HLine)

        self.rootLayout.addWidget(self.dividerTop)

        self.lblStepHeader = QLabel(CloudSetupDialog)
        self.lblStepHeader.setObjectName(u"lblStepHeader")
        self.lblStepHeader.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblStepHeader)

        self.stack = QStackedWidget(CloudSetupDialog)
        self.stack.setObjectName(u"stack")
        self.pageOauth = QWidget()
        self.pageOauth.setObjectName(u"pageOauth")
        self.oauthLayout = QVBoxLayout(self.pageOauth)
        self.oauthLayout.setSpacing(10)
        self.oauthLayout.setObjectName(u"oauthLayout")
        self.oauthLayout.setContentsMargins(0, 0, 0, 0)
        self.oauthRule = QFrame(self.pageOauth)
        self.oauthRule.setObjectName(u"oauthRule")
        self.oauthRule.setProperty(u"role", u"rule")
        self.oauthRuleLayout = QVBoxLayout(self.oauthRule)
        self.oauthRuleLayout.setObjectName(u"oauthRuleLayout")
        self.oauthRuleLayout.setContentsMargins(14, 10, 14, 10)
        self.lblOauthIntro = QLabel(self.oauthRule)
        self.lblOauthIntro.setObjectName(u"lblOauthIntro")
        self.lblOauthIntro.setWordWrap(True)

        self.oauthRuleLayout.addWidget(self.lblOauthIntro)


        self.oauthLayout.addWidget(self.oauthRule)

        self.btnAuthorize = QPushButton(self.pageOauth)
        self.btnAuthorize.setObjectName(u"btnAuthorize")
        self.btnAuthorize.setProperty(u"role", u"accent")

        self.oauthLayout.addWidget(self.btnAuthorize)

        self.lblOauthStatus = QLabel(self.pageOauth)
        self.lblOauthStatus.setObjectName(u"lblOauthStatus")
        self.lblOauthStatus.setProperty(u"role", u"hint")
        self.lblOauthStatus.setWordWrap(True)

        self.oauthLayout.addWidget(self.lblOauthStatus)

        self.oauthLinkLayout = QHBoxLayout()
        self.oauthLinkLayout.setSpacing(8)
        self.oauthLinkLayout.setObjectName(u"oauthLinkLayout")
        self.btnOpenAgain = QPushButton(self.pageOauth)
        self.btnOpenAgain.setObjectName(u"btnOpenAgain")

        self.oauthLinkLayout.addWidget(self.btnOpenAgain)

        self.btnCopyLink = QPushButton(self.pageOauth)
        self.btnCopyLink.setObjectName(u"btnCopyLink")

        self.oauthLinkLayout.addWidget(self.btnCopyLink)

        self.btnCancelAuth = QPushButton(self.pageOauth)
        self.btnCancelAuth.setObjectName(u"btnCancelAuth")

        self.oauthLinkLayout.addWidget(self.btnCancelAuth)

        self.oauthLinkSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.oauthLinkLayout.addItem(self.oauthLinkSpacer)


        self.oauthLayout.addLayout(self.oauthLinkLayout)

        self.lblKeyWarn = QLabel(self.pageOauth)
        self.lblKeyWarn.setObjectName(u"lblKeyWarn")
        self.lblKeyWarn.setProperty(u"role", u"hintWarn")
        self.lblKeyWarn.setWordWrap(True)

        self.oauthLayout.addWidget(self.lblKeyWarn)

        self.chkOwnKey = QCheckBox(self.pageOauth)
        self.chkOwnKey.setObjectName(u"chkOwnKey")

        self.oauthLayout.addWidget(self.chkOwnKey)

        self.keyBox = QWidget(self.pageOauth)
        self.keyBox.setObjectName(u"keyBox")
        self.keyLayout = QGridLayout(self.keyBox)
        self.keyLayout.setObjectName(u"keyLayout")
        self.keyLayout.setHorizontalSpacing(10)
        self.keyLayout.setVerticalSpacing(6)
        self.keyLayout.setContentsMargins(0, 0, 0, 0)
        self.lblKeyId = QLabel(self.keyBox)
        self.lblKeyId.setObjectName(u"lblKeyId")
        self.lblKeyId.setProperty(u"role", u"field")
        self.lblKeyId.setMinimumSize(QSize(124, 0))
        self.lblKeyId.setMaximumSize(QSize(124, 16777215))
        self.lblKeyId.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.keyLayout.addWidget(self.lblKeyId, 0, 0, 1, 1)

        self.editClientId = QLineEdit(self.keyBox)
        self.editClientId.setObjectName(u"editClientId")

        self.keyLayout.addWidget(self.editClientId, 0, 1, 1, 1)

        self.lblKeySecret = QLabel(self.keyBox)
        self.lblKeySecret.setObjectName(u"lblKeySecret")
        self.lblKeySecret.setProperty(u"role", u"field")
        self.lblKeySecret.setMinimumSize(QSize(124, 0))
        self.lblKeySecret.setMaximumSize(QSize(124, 16777215))
        self.lblKeySecret.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.keyLayout.addWidget(self.lblKeySecret, 1, 0, 1, 1)

        self.editClientSecret = QLineEdit(self.keyBox)
        self.editClientSecret.setObjectName(u"editClientSecret")
        self.editClientSecret.setEchoMode(QLineEdit.EchoMode.Password)

        self.keyLayout.addWidget(self.editClientSecret, 1, 1, 1, 1)

        self.lblKeyHint = QLabel(self.keyBox)
        self.lblKeyHint.setObjectName(u"lblKeyHint")
        self.lblKeyHint.setProperty(u"role", u"hint")
        self.lblKeyHint.setWordWrap(True)

        self.keyLayout.addWidget(self.lblKeyHint, 2, 1, 1, 1)


        self.oauthLayout.addWidget(self.keyBox)

        self.oauthSpacer = QSpacerItem(0, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.oauthLayout.addItem(self.oauthSpacer)

        self.stack.addWidget(self.pageOauth)
        self.pageFields = QWidget()
        self.pageFields.setObjectName(u"pageFields")
        self.fieldsLayout = QVBoxLayout(self.pageFields)
        self.fieldsLayout.setSpacing(8)
        self.fieldsLayout.setObjectName(u"fieldsLayout")
        self.fieldsLayout.setContentsMargins(0, 0, 0, 0)
        self.fieldsScroll = QScrollArea(self.pageFields)
        self.fieldsScroll.setObjectName(u"fieldsScroll")
        self.fieldsScroll.setFrameShape(QFrame.NoFrame)
        self.fieldsScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.fieldsScroll.setWidgetResizable(True)
        self.fieldsContents = QWidget()
        self.fieldsContents.setObjectName(u"fieldsContents")
        self.fieldsContents.setGeometry(QRect(0, 0, 600, 240))
        self.gridFields = QGridLayout(self.fieldsContents)
        self.gridFields.setObjectName(u"gridFields")
        self.gridFields.setHorizontalSpacing(8)
        self.gridFields.setVerticalSpacing(7)
        self.gridFields.setContentsMargins(0, -1, 0, -1)
        self.fieldsScroll.setWidget(self.fieldsContents)

        self.fieldsLayout.addWidget(self.fieldsScroll)

        self.stack.addWidget(self.pageFields)

        self.rootLayout.addWidget(self.stack)

        self.lblResult = QLabel(CloudSetupDialog)
        self.lblResult.setObjectName(u"lblResult")
        self.lblResult.setProperty(u"role", u"hint")
        self.lblResult.setWordWrap(True)

        self.rootLayout.addWidget(self.lblResult)

        self.actionsLayout = QHBoxLayout()
        self.actionsLayout.setSpacing(8)
        self.actionsLayout.setObjectName(u"actionsLayout")
        self.actionsSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionsLayout.addItem(self.actionsSpacer)

        self.btnSave = QPushButton(CloudSetupDialog)
        self.btnSave.setObjectName(u"btnSave")
        self.btnSave.setProperty(u"role", u"accent")

        self.actionsLayout.addWidget(self.btnSave)

        self.btnClose = QPushButton(CloudSetupDialog)
        self.btnClose.setObjectName(u"btnClose")

        self.actionsLayout.addWidget(self.btnClose)


        self.rootLayout.addLayout(self.actionsLayout)


        self.retranslateUi(CloudSetupDialog)

        self.stack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(CloudSetupDialog)
    # setupUi

    def retranslateUi(self, CloudSetupDialog):
        CloudSetupDialog.setWindowTitle(QCoreApplication.translate("CloudSetupDialog", u"Adicionar servi\u00e7o de nuvem", None))
        self.lblProvider.setText(QCoreApplication.translate("CloudSetupDialog", u"Servi\u00e7o", None))
        self.lblName.setText(QCoreApplication.translate("CloudSetupDialog", u"Nome interno", None))
        self.editName.setPlaceholderText(QCoreApplication.translate("CloudSetupDialog", u"ex.: drive_loja1", None))
        self.lblNameHint.setText(QCoreApplication.translate("CloudSetupDialog", u"Como este servi\u00e7o aparece na lista dos conjuntos. Letras, n\u00fameros, ponto, h\u00edfen e sublinhado.", None))
        self.lblStepHeader.setText(QCoreApplication.translate("CloudSetupDialog", u"ACESSO", None))
        self.lblOauthIntro.setText(QCoreApplication.translate("CloudSetupDialog", u"O login acontece no site do pr\u00f3prio servi\u00e7o, no seu navegador \u2014 a senha nunca passa por aqui. Ao autorizar, o servi\u00e7o devolve uma credencial que fica guardada nesta m\u00e1quina.", None))
        self.btnAuthorize.setText(QCoreApplication.translate("CloudSetupDialog", u"Entrar e autorizar no navegador", None))
        self.lblOauthStatus.setText("")
        self.btnOpenAgain.setText(QCoreApplication.translate("CloudSetupDialog", u"Abrir o link de novo", None))
        self.btnCopyLink.setText(QCoreApplication.translate("CloudSetupDialog", u"Copiar link", None))
        self.btnCancelAuth.setText(QCoreApplication.translate("CloudSetupDialog", u"Cancelar", None))
        self.lblKeyWarn.setText("")
        self.chkOwnKey.setText(QCoreApplication.translate("CloudSetupDialog", u"Usar uma chave de API pr\u00f3pria neste computador", None))
        self.lblKeyId.setText(QCoreApplication.translate("CloudSetupDialog", u"ID do cliente", None))
        self.editClientId.setPlaceholderText(QCoreApplication.translate("CloudSetupDialog", u"algo.apps.googleusercontent.com", None))
        self.lblKeySecret.setText(QCoreApplication.translate("CloudSetupDialog", u"Segredo do cliente", None))
        self.lblKeyHint.setText(QCoreApplication.translate("CloudSetupDialog", u"S\u00f3 para quem criou a pr\u00f3pria chave no console do servi\u00e7o. Em branco, o programa usa a chave dele mesmo.", None))
        self.lblResult.setText("")
        self.btnSave.setText(QCoreApplication.translate("CloudSetupDialog", u"Cadastrar", None))
        self.btnClose.setText(QCoreApplication.translate("CloudSetupDialog", u"Cancelar", None))
    # retranslateUi

