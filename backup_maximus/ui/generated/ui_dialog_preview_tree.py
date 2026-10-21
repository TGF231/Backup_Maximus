# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_preview_tree.ui'
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
    QFrame, QHeaderView, QLabel, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_TreePreviewDialog(object):
    def setupUi(self, TreePreviewDialog):
        if not TreePreviewDialog.objectName():
            TreePreviewDialog.setObjectName(u"TreePreviewDialog")
        TreePreviewDialog.resize(620, 520)
        TreePreviewDialog.setModal(True)
        self.rootLayout = QVBoxLayout(TreePreviewDialog)
        self.rootLayout.setSpacing(10)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(18, 16, 18, 14)
        self.ruleBox = QFrame(TreePreviewDialog)
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

        self.tree = QTreeWidget(TreePreviewDialog)
        self.tree.setObjectName(u"tree")
        self.tree.setRootIsDecorated(True)

        self.rootLayout.addWidget(self.tree)

        self.lblSummary = QLabel(TreePreviewDialog)
        self.lblSummary.setObjectName(u"lblSummary")
        self.lblSummary.setProperty(u"role", u"hint")
        self.lblSummary.setWordWrap(True)

        self.rootLayout.addWidget(self.lblSummary)

        self.buttonBox = QDialogButtonBox(TreePreviewDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.rootLayout.addWidget(self.buttonBox)


        self.retranslateUi(TreePreviewDialog)

        QMetaObject.connectSlotsByName(TreePreviewDialog)
    # setupUi

    def retranslateUi(self, TreePreviewDialog):
        TreePreviewDialog.setWindowTitle(QCoreApplication.translate("TreePreviewDialog", u"Pr\u00e9via da \u00e1rvore", None))
        self.lblIntro.setText("")
        ___qtreewidgetitem = self.tree.headerItem()
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("TreePreviewDialog", u"Vem de", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("TreePreviewDialog", u"Caminho dentro do zip", None))
        self.lblSummary.setText("")
    # retranslateUi

