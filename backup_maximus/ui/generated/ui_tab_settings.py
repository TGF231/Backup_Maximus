# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tab_settings.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QSpinBox,
    QTimeEdit, QVBoxLayout, QWidget)

from backup_maximus.ui.pathedit import PathEdit

class Ui_TabSettings(object):
    def setupUi(self, TabSettings):
        if not TabSettings.objectName():
            TabSettings.setObjectName(u"TabSettings")
        TabSettings.resize(1000, 640)
        self.rootLayout = QVBoxLayout(TabSettings)
        self.rootLayout.setSpacing(8)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(16, 14, 16, 12)
        self.lblIdentSection = QLabel(TabSettings)
        self.lblIdentSection.setObjectName(u"lblIdentSection")
        self.lblIdentSection.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblIdentSection)

        self.gridIdent = QGridLayout()
        self.gridIdent.setObjectName(u"gridIdent")
        self.gridIdent.setHorizontalSpacing(8)
        self.gridIdent.setVerticalSpacing(7)
        self.gridIdent.setContentsMargins(0, -1, 0, -1)
        self.lblCompany = QLabel(TabSettings)
        self.lblCompany.setObjectName(u"lblCompany")
        self.lblCompany.setProperty(u"role", u"field")
        self.lblCompany.setMinimumSize(QSize(124, 0))
        self.lblCompany.setMaximumSize(QSize(124, 16777215))
        self.lblCompany.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridIdent.addWidget(self.lblCompany, 0, 0, 1, 1)

        self.editCompany = QLineEdit(TabSettings)
        self.editCompany.setObjectName(u"editCompany")

        self.gridIdent.addWidget(self.editCompany, 0, 1, 1, 3)

        self.lblEmail = QLabel(TabSettings)
        self.lblEmail.setObjectName(u"lblEmail")
        self.lblEmail.setProperty(u"role", u"field")
        self.lblEmail.setMinimumSize(QSize(124, 0))
        self.lblEmail.setMaximumSize(QSize(124, 16777215))
        self.lblEmail.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridIdent.addWidget(self.lblEmail, 1, 0, 1, 1)

        self.editEmail = QLineEdit(TabSettings)
        self.editEmail.setObjectName(u"editEmail")

        self.gridIdent.addWidget(self.editEmail, 1, 1, 1, 3)

        self.lblTimeout = QLabel(TabSettings)
        self.lblTimeout.setObjectName(u"lblTimeout")
        self.lblTimeout.setProperty(u"role", u"field")
        self.lblTimeout.setMinimumSize(QSize(124, 0))
        self.lblTimeout.setMaximumSize(QSize(124, 16777215))
        self.lblTimeout.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridIdent.addWidget(self.lblTimeout, 2, 0, 1, 1)

        self.spinTimeout = QSpinBox(TabSettings)
        self.spinTimeout.setObjectName(u"spinTimeout")
        self.spinTimeout.setMinimumSize(QSize(120, 0))
        self.spinTimeout.setMaximumSize(QSize(120, 16777215))
        self.spinTimeout.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinTimeout.setMinimum(1)
        self.spinTimeout.setMaximum(8760)

        self.gridIdent.addWidget(self.spinTimeout, 2, 1, 1, 1)

        self.lblAlertHint = QLabel(TabSettings)
        self.lblAlertHint.setObjectName(u"lblAlertHint")
        self.lblAlertHint.setProperty(u"role", u"hintWarn")
        self.lblAlertHint.setWordWrap(True)

        self.gridIdent.addWidget(self.lblAlertHint, 3, 1, 1, 3)

        self.lblReminder = QLabel(TabSettings)
        self.lblReminder.setObjectName(u"lblReminder")
        self.lblReminder.setProperty(u"role", u"field")
        self.lblReminder.setMinimumSize(QSize(124, 0))
        self.lblReminder.setMaximumSize(QSize(124, 16777215))
        self.lblReminder.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridIdent.addWidget(self.lblReminder, 5, 0, 1, 1)

        self.reminderLayout = QHBoxLayout()
        self.reminderLayout.setSpacing(10)
        self.reminderLayout.setObjectName(u"reminderLayout")
        self.timeReminder = QTimeEdit(TabSettings)
        self.timeReminder.setObjectName(u"timeReminder")
        self.timeReminder.setMinimumSize(QSize(96, 0))
        self.timeReminder.setMaximumSize(QSize(96, 16777215))
        self.timeReminder.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.reminderLayout.addWidget(self.timeReminder)

        self.chkReminder = QCheckBox(TabSettings)
        self.chkReminder.setObjectName(u"chkReminder")

        self.reminderLayout.addWidget(self.chkReminder)

        self.reminderSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.reminderLayout.addItem(self.reminderSpacer)


        self.gridIdent.addLayout(self.reminderLayout, 5, 1, 1, 3)

        self.lblReminderHint = QLabel(TabSettings)
        self.lblReminderHint.setObjectName(u"lblReminderHint")
        self.lblReminderHint.setProperty(u"role", u"hint")
        self.lblReminderHint.setWordWrap(True)

        self.gridIdent.addWidget(self.lblReminderHint, 6, 1, 1, 3)

        self.chkSendReport = QCheckBox(TabSettings)
        self.chkSendReport.setObjectName(u"chkSendReport")

        self.gridIdent.addWidget(self.chkSendReport, 4, 1, 1, 3)


        self.rootLayout.addLayout(self.gridIdent)

        self.dividerIdent = QFrame(TabSettings)
        self.dividerIdent.setObjectName(u"dividerIdent")
        self.dividerIdent.setProperty(u"role", u"divider")
        self.dividerIdent.setMinimumSize(QSize(0, 1))
        self.dividerIdent.setMaximumSize(QSize(16777215, 1))
        self.dividerIdent.setFrameShape(QFrame.HLine)

        self.rootLayout.addWidget(self.dividerIdent)

        self.lblSmtpSection = QLabel(TabSettings)
        self.lblSmtpSection.setObjectName(u"lblSmtpSection")
        self.lblSmtpSection.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblSmtpSection)

        self.gridSmtp = QGridLayout()
        self.gridSmtp.setObjectName(u"gridSmtp")
        self.gridSmtp.setHorizontalSpacing(8)
        self.gridSmtp.setVerticalSpacing(7)
        self.gridSmtp.setContentsMargins(0, -1, 0, -1)
        self.lblSmtpHost = QLabel(TabSettings)
        self.lblSmtpHost.setObjectName(u"lblSmtpHost")
        self.lblSmtpHost.setProperty(u"role", u"field")
        self.lblSmtpHost.setMinimumSize(QSize(124, 0))
        self.lblSmtpHost.setMaximumSize(QSize(124, 16777215))
        self.lblSmtpHost.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridSmtp.addWidget(self.lblSmtpHost, 0, 0, 1, 1)

        self.editSmtpHost = QLineEdit(TabSettings)
        self.editSmtpHost.setObjectName(u"editSmtpHost")
        self.editSmtpHost.setProperty(u"mono", u"true")

        self.gridSmtp.addWidget(self.editSmtpHost, 0, 1, 1, 2)

        self.spinSmtpPort = QSpinBox(TabSettings)
        self.spinSmtpPort.setObjectName(u"spinSmtpPort")
        self.spinSmtpPort.setMinimumSize(QSize(96, 0))
        self.spinSmtpPort.setMaximumSize(QSize(96, 16777215))
        self.spinSmtpPort.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinSmtpPort.setMinimum(1)
        self.spinSmtpPort.setMaximum(65535)

        self.gridSmtp.addWidget(self.spinSmtpPort, 0, 3, 1, 1)

        self.lblSmtpUser = QLabel(TabSettings)
        self.lblSmtpUser.setObjectName(u"lblSmtpUser")
        self.lblSmtpUser.setProperty(u"role", u"field")
        self.lblSmtpUser.setMinimumSize(QSize(124, 0))
        self.lblSmtpUser.setMaximumSize(QSize(124, 16777215))
        self.lblSmtpUser.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridSmtp.addWidget(self.lblSmtpUser, 1, 0, 1, 1)

        self.editSmtpUser = QLineEdit(TabSettings)
        self.editSmtpUser.setObjectName(u"editSmtpUser")

        self.gridSmtp.addWidget(self.editSmtpUser, 1, 1, 1, 2)

        self.editSmtpPass = QLineEdit(TabSettings)
        self.editSmtpPass.setObjectName(u"editSmtpPass")
        self.editSmtpPass.setEchoMode(QLineEdit.Password)

        self.gridSmtp.addWidget(self.editSmtpPass, 1, 3, 1, 1)

        self.lblSmtpFrom = QLabel(TabSettings)
        self.lblSmtpFrom.setObjectName(u"lblSmtpFrom")
        self.lblSmtpFrom.setProperty(u"role", u"field")
        self.lblSmtpFrom.setMinimumSize(QSize(124, 0))
        self.lblSmtpFrom.setMaximumSize(QSize(124, 16777215))
        self.lblSmtpFrom.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridSmtp.addWidget(self.lblSmtpFrom, 2, 0, 1, 1)

        self.editSmtpFrom = QLineEdit(TabSettings)
        self.editSmtpFrom.setObjectName(u"editSmtpFrom")

        self.gridSmtp.addWidget(self.editSmtpFrom, 2, 1, 1, 3)

        self.smtpActionsLayout = QHBoxLayout()
        self.smtpActionsLayout.setSpacing(10)
        self.smtpActionsLayout.setObjectName(u"smtpActionsLayout")
        self.chkSmtpSsl = QCheckBox(TabSettings)
        self.chkSmtpSsl.setObjectName(u"chkSmtpSsl")

        self.smtpActionsLayout.addWidget(self.chkSmtpSsl)

        self.btnTestMail = QPushButton(TabSettings)
        self.btnTestMail.setObjectName(u"btnTestMail")

        self.smtpActionsLayout.addWidget(self.btnTestMail)

        self.smtpActionsSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.smtpActionsLayout.addItem(self.smtpActionsSpacer)


        self.gridSmtp.addLayout(self.smtpActionsLayout, 3, 1, 1, 3)


        self.rootLayout.addLayout(self.gridSmtp)

        self.dividerSmtp = QFrame(TabSettings)
        self.dividerSmtp.setObjectName(u"dividerSmtp")
        self.dividerSmtp.setProperty(u"role", u"divider")
        self.dividerSmtp.setMinimumSize(QSize(0, 1))
        self.dividerSmtp.setMaximumSize(QSize(16777215, 1))
        self.dividerSmtp.setFrameShape(QFrame.HLine)

        self.rootLayout.addWidget(self.dividerSmtp)

        self.lblZipSection = QLabel(TabSettings)
        self.lblZipSection.setObjectName(u"lblZipSection")
        self.lblZipSection.setProperty(u"role", u"section")

        self.rootLayout.addWidget(self.lblZipSection)

        self.gridZip = QGridLayout()
        self.gridZip.setObjectName(u"gridZip")
        self.gridZip.setHorizontalSpacing(8)
        self.gridZip.setVerticalSpacing(7)
        self.gridZip.setContentsMargins(0, -1, 0, -1)
        self.lblSevenZip = QLabel(TabSettings)
        self.lblSevenZip.setObjectName(u"lblSevenZip")
        self.lblSevenZip.setProperty(u"role", u"field")
        self.lblSevenZip.setMinimumSize(QSize(124, 0))
        self.lblSevenZip.setMaximumSize(QSize(124, 16777215))
        self.lblSevenZip.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridZip.addWidget(self.lblSevenZip, 0, 0, 1, 1)

        self.editSevenZip = PathEdit(TabSettings)
        self.editSevenZip.setObjectName(u"editSevenZip")
        self.editSevenZip.setProperty(u"pathKind", u"file")
        self.editSevenZip.setProperty(u"mono", u"true")

        self.gridZip.addWidget(self.editSevenZip, 0, 1, 1, 3)

        self.btnBrowseSevenZip = QPushButton(TabSettings)
        self.btnBrowseSevenZip.setObjectName(u"btnBrowseSevenZip")
        self.btnBrowseSevenZip.setProperty(u"role", u"tiny")
        self.btnBrowseSevenZip.setMinimumSize(QSize(30, 0))
        self.btnBrowseSevenZip.setMaximumSize(QSize(30, 16777215))

        self.gridZip.addWidget(self.btnBrowseSevenZip, 0, 4, 1, 1)

        self.lblRclone = QLabel(TabSettings)
        self.lblRclone.setObjectName(u"lblRclone")
        self.lblRclone.setProperty(u"role", u"field")
        self.lblRclone.setMinimumSize(QSize(124, 0))
        self.lblRclone.setMaximumSize(QSize(124, 16777215))
        self.lblRclone.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridZip.addWidget(self.lblRclone, 1, 0, 1, 1)

        self.editRclone = PathEdit(TabSettings)
        self.editRclone.setObjectName(u"editRclone")
        self.editRclone.setProperty(u"pathKind", u"file")
        self.editRclone.setProperty(u"mono", u"true")

        self.gridZip.addWidget(self.editRclone, 1, 1, 1, 3)

        self.btnBrowseRclone = QPushButton(TabSettings)
        self.btnBrowseRclone.setObjectName(u"btnBrowseRclone")
        self.btnBrowseRclone.setProperty(u"role", u"tiny")
        self.btnBrowseRclone.setMinimumSize(QSize(30, 0))
        self.btnBrowseRclone.setMaximumSize(QSize(30, 16777215))

        self.gridZip.addWidget(self.btnBrowseRclone, 1, 4, 1, 1)

        self.lblSevenZipHint = QLabel(TabSettings)
        self.lblSevenZipHint.setObjectName(u"lblSevenZipHint")
        self.lblSevenZipHint.setProperty(u"role", u"hint")
        self.lblSevenZipHint.setWordWrap(True)

        self.gridZip.addWidget(self.lblSevenZipHint, 2, 1, 1, 3)

        self.maintenanceLayout = QHBoxLayout()
        self.maintenanceLayout.setSpacing(8)
        self.maintenanceLayout.setObjectName(u"maintenanceLayout")
        self.btnChangePassword = QPushButton(TabSettings)
        self.btnChangePassword.setObjectName(u"btnChangePassword")

        self.maintenanceLayout.addWidget(self.btnChangePassword)

        self.btnShortcut = QPushButton(TabSettings)
        self.btnShortcut.setObjectName(u"btnShortcut")

        self.maintenanceLayout.addWidget(self.btnShortcut)

        self.maintenanceSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.maintenanceLayout.addItem(self.maintenanceSpacer)


        self.gridZip.addLayout(self.maintenanceLayout, 3, 1, 1, 3)


        self.rootLayout.addLayout(self.gridZip)

        self.bottomSpacer = QSpacerItem(0, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.rootLayout.addItem(self.bottomSpacer)


        self.retranslateUi(TabSettings)

        QMetaObject.connectSlotsByName(TabSettings)
    # setupUi

    def retranslateUi(self, TabSettings):
        self.lblIdentSection.setText(QCoreApplication.translate("TabSettings", u"IDENTIFICA\u00c7\u00c3O E ALERTAS", None))
        self.lblCompany.setText(QCoreApplication.translate("TabSettings", u"Nome da empresa", None))
        self.lblEmail.setText(QCoreApplication.translate("TabSettings", u"E-mail de notifica\u00e7\u00f5es", None))
        self.editEmail.setPlaceholderText(QCoreApplication.translate("TabSettings", u"ti@suaempresa.com.br", None))
        self.lblTimeout.setText(QCoreApplication.translate("TabSettings", u"Alertar se sem backup h\u00e1", None))
        self.spinTimeout.setSuffix(QCoreApplication.translate("TabSettings", u" horas", None))
        self.lblAlertHint.setText("")
        self.lblReminder.setText(QCoreApplication.translate("TabSettings", u"Lembrar backup \u00e0s", None))
        self.timeReminder.setDisplayFormat(QCoreApplication.translate("TabSettings", u"HH:mm", None))
        self.chkReminder.setText(QCoreApplication.translate("TabSettings", u"Mostrar lembrete di\u00e1rio", None))
        self.lblReminderHint.setText("")
        self.chkSendReport.setText(QCoreApplication.translate("TabSettings", u"Enviar relat\u00f3rio por e-mail a cada backup", None))
        self.lblSmtpSection.setText(QCoreApplication.translate("TabSettings", u"SERVIDOR SMTP (RELAT\u00d3RIOS E ALERTAS)", None))
        self.lblSmtpHost.setText(QCoreApplication.translate("TabSettings", u"Servidor / porta", None))
        self.editSmtpHost.setPlaceholderText(QCoreApplication.translate("TabSettings", u"smtp.suaempresa.com.br", None))
        self.lblSmtpUser.setText(QCoreApplication.translate("TabSettings", u"Usu\u00e1rio / senha", None))
        self.lblSmtpFrom.setText(QCoreApplication.translate("TabSettings", u"Remetente (De)", None))
        self.editSmtpFrom.setPlaceholderText(QCoreApplication.translate("TabSettings", u"vazio = mesmo do usu\u00e1rio", None))
        self.chkSmtpSsl.setText(QCoreApplication.translate("TabSettings", u"Usar SSL/TLS", None))
        self.btnTestMail.setText(QCoreApplication.translate("TabSettings", u"Testar e-mail", None))
        self.lblZipSection.setText(QCoreApplication.translate("TabSettings", u"COMPACTA\u00c7\u00c3O E MANUTEN\u00c7\u00c3O", None))
        self.lblSevenZip.setText(QCoreApplication.translate("TabSettings", u"Caminho do 7z.exe", None))
        self.editSevenZip.setPlaceholderText(QCoreApplication.translate("TabSettings", u"vazio = autodetecta; sem 7-Zip usa o compactador nativo do Python", None))
        self.btnBrowseSevenZip.setText(QCoreApplication.translate("TabSettings", u"\u2026", None))
        self.lblRclone.setText(QCoreApplication.translate("TabSettings", u"Caminho do rclone.exe", None))
        self.editRclone.setPlaceholderText(QCoreApplication.translate("TabSettings", u"vazio = empacotado com o app, ou do sistema", None))
        self.btnBrowseRclone.setText(QCoreApplication.translate("TabSettings", u"\u2026", None))
        self.lblSevenZipHint.setText("")
        self.btnChangePassword.setText(QCoreApplication.translate("TabSettings", u"Alterar senha da interface", None))
        self.btnShortcut.setText(QCoreApplication.translate("TabSettings", u"Criar atalho na \u00e1rea de trabalho", None))
        pass
    # retranslateUi

