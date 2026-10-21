# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_password.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QLineEdit, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_PasswordDialog(object):
    def setupUi(self, PasswordDialog):
        if not PasswordDialog.objectName():
            PasswordDialog.setObjectName(u"PasswordDialog")
        PasswordDialog.resize(420, 260)
        PasswordDialog.setMinimumSize(QSize(420, 0))
        PasswordDialog.setMaximumSize(QSize(420, 16777215))
        PasswordDialog.setModal(True)
        self.rootLayout = QVBoxLayout(PasswordDialog)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(20, 18, 20, 16)
        self.lblIntro = QLabel(PasswordDialog)
        self.lblIntro.setObjectName(u"lblIntro")
        self.lblIntro.setWordWrap(True)

        self.rootLayout.addWidget(self.lblIntro)

        self.lblIntroHint = QLabel(PasswordDialog)
        self.lblIntroHint.setObjectName(u"lblIntroHint")
        self.lblIntroHint.setProperty(u"role", u"hint")
        self.lblIntroHint.setWordWrap(True)

        self.rootLayout.addWidget(self.lblIntroHint)

        self.lblPass = QLabel(PasswordDialog)
        self.lblPass.setObjectName(u"lblPass")
        self.lblPass.setProperty(u"role", u"field")

        self.rootLayout.addWidget(self.lblPass)

        self.editPass = QLineEdit(PasswordDialog)
        self.editPass.setObjectName(u"editPass")
        self.editPass.setEchoMode(QLineEdit.Password)

        self.rootLayout.addWidget(self.editPass)

        self.lblConfirm = QLabel(PasswordDialog)
        self.lblConfirm.setObjectName(u"lblConfirm")
        self.lblConfirm.setProperty(u"role", u"field")

        self.rootLayout.addWidget(self.lblConfirm)

        self.editConfirm = QLineEdit(PasswordDialog)
        self.editConfirm.setObjectName(u"editConfirm")
        self.editConfirm.setEchoMode(QLineEdit.Password)

        self.rootLayout.addWidget(self.editConfirm)

        self.lblError = QLabel(PasswordDialog)
        self.lblError.setObjectName(u"lblError")
        self.lblError.setProperty(u"role", u"hintWarn")
        self.lblError.setWordWrap(True)

        self.rootLayout.addWidget(self.lblError)

        self.buttonBox = QDialogButtonBox(PasswordDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.rootLayout.addWidget(self.buttonBox)


        self.retranslateUi(PasswordDialog)

        QMetaObject.connectSlotsByName(PasswordDialog)
    # setupUi

    def retranslateUi(self, PasswordDialog):
        PasswordDialog.setWindowTitle(QCoreApplication.translate("PasswordDialog", u"Backup Maximus \u2014 Acesso restrito", None))
        self.lblIntro.setText(QCoreApplication.translate("PasswordDialog", u"Digite a senha para abrir as configura\u00e7\u00f5es:", None))
        self.lblIntroHint.setText(QCoreApplication.translate("PasswordDialog", u"A senha \u00e9 guardada apenas como hash com salt \u2014 n\u00e3o h\u00e1 como recuper\u00e1-la depois.", None))
        self.lblPass.setText(QCoreApplication.translate("PasswordDialog", u"Senha", None))
        self.lblConfirm.setText(QCoreApplication.translate("PasswordDialog", u"Confirmar senha", None))
        self.lblError.setText("")
    # retranslateUi

