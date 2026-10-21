# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'window_progress.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_ProgressWindow(object):
    def setupUi(self, ProgressWindow):
        if not ProgressWindow.objectName():
            ProgressWindow.setObjectName(u"ProgressWindow")
        ProgressWindow.resize(540, 150)
        ProgressWindow.setMinimumSize(QSize(540, 0))
        ProgressWindow.setMaximumSize(QSize(540, 16777215))
        self.rootLayout = QVBoxLayout(ProgressWindow)
        self.rootLayout.setSpacing(12)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(20, 18, 20, 16)
        self.lblStatus = QLabel(ProgressWindow)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setProperty(u"role", u"bigStatus")
        self.lblStatus.setMinimumSize(QSize(0, 38))
        self.lblStatus.setWordWrap(True)
        self.lblStatus.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.rootLayout.addWidget(self.lblStatus)

        self.bar = QProgressBar(ProgressWindow)
        self.bar.setObjectName(u"bar")
        self.bar.setValue(0)
        self.bar.setTextVisible(False)

        self.rootLayout.addWidget(self.bar)

        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setSpacing(10)
        self.bottomLayout.setObjectName(u"bottomLayout")
        self.lblTime = QLabel(ProgressWindow)
        self.lblTime.setObjectName(u"lblTime")
        self.lblTime.setProperty(u"role", u"mono")

        self.bottomLayout.addWidget(self.lblTime)

        self.bottomSpacer = QSpacerItem(1, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottomLayout.addItem(self.bottomSpacer)

        self.btnCancel = QPushButton(ProgressWindow)
        self.btnCancel.setObjectName(u"btnCancel")

        self.bottomLayout.addWidget(self.btnCancel)

        self.btnClose = QPushButton(ProgressWindow)
        self.btnClose.setObjectName(u"btnClose")
        self.btnClose.setProperty(u"role", u"accent")

        self.bottomLayout.addWidget(self.btnClose)


        self.rootLayout.addLayout(self.bottomLayout)


        self.retranslateUi(ProgressWindow)

        QMetaObject.connectSlotsByName(ProgressWindow)
    # setupUi

    def retranslateUi(self, ProgressWindow):
        ProgressWindow.setWindowTitle(QCoreApplication.translate("ProgressWindow", u"Backup Maximus \u2014 Executando backup\u2026", None))
        self.lblStatus.setText(QCoreApplication.translate("ProgressWindow", u"Iniciando backup\u2026", None))
        self.lblTime.setText(QCoreApplication.translate("ProgressWindow", u"Tempo: 0 s", None))
        self.btnCancel.setText(QCoreApplication.translate("ProgressWindow", u"Cancelar", None))
        self.btnClose.setText(QCoreApplication.translate("ProgressWindow", u"Fechar", None))
    # retranslateUi

