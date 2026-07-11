from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from nft_asset_toolbox import __version__
from nft_asset_toolbox.core import (
    ValidationResult,
    get_collection_stats,
    metadata_dir_for,
    validate_collection,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_COLLECTION = ROOT / "sample_collection"
SAMPLE_OUTPUT = SAMPLE_COLLECTION / "output"
DEFAULT_COLLECTION = SAMPLE_OUTPUT if SAMPLE_OUTPUT.exists() else SAMPLE_COLLECTION
REPORTS_DIR = ROOT / "reports"


class ValidationWorker(QThread):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, collection_dir: Path):
        super().__init__()
        self.collection_dir = collection_dir

    def run(self) -> None:
        try:
            self.finished.emit(validate_collection(self.collection_dir, REPORTS_DIR))
        except Exception as exc:  # pragma: no cover - defensive UI boundary
            self.failed.emit(str(exc))


class Card(QFrame):
    def __init__(self, title: str = "", subtitle: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 8, 14, 8)
        self.layout.setSpacing(5)
        if title:
            label = QLabel(title)
            label.setObjectName("cardTitle")
            self.layout.addWidget(label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("muted")
            sub.setWordWrap(True)
            self.layout.addWidget(sub)


ICON_ACCENTS = {
    "images": ("#3b82f6", "#1a2b4a"),
    "generate": ("#3b82f6", "#1a2b4a"),
    "metadata": ("#8b5cf6", "#291f4d"),
    "metadata_tools": ("#8b5cf6", "#291f4d"),
    "traits": ("#22c55e", "#123322"),
    "image_tools": ("#22c55e", "#123322"),
    "supply": ("#eab308", "#332a12"),
    "folder": ("#eab308", "#332a12"),
}
DEFAULT_ACCENT = ("#9bd2ff", "#21314b")


class IconBadge(QWidget):
    def __init__(self, icon_name: str, size: int = 36):
        super().__init__()
        self.icon_name = icon_name
        self.setObjectName("iconBadge")
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        stroke, fill = ICON_ACCENTS.get(self.icon_name, DEFAULT_ACCENT)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setPen(QPen(QColor(stroke).lighter(140), 1))
        painter.setBrush(QBrush(QColor(fill)))
        painter.drawRoundedRect(rect, 7, 7)

        pen = QPen(QColor(stroke), 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        w = self.width()
        h = self.height()
        name = self.icon_name

        if name == "folder":
            painter.drawRoundedRect(QRectF(w * 0.22, h * 0.32, w * 0.56, h * 0.4), 3, 3)
            painter.drawLine(QPointF(w * 0.22, h * 0.36), QPointF(w * 0.4, h * 0.36))
            painter.drawLine(QPointF(w * 0.4, h * 0.36), QPointF(w * 0.46, h * 0.28))
            painter.drawLine(QPointF(w * 0.46, h * 0.28), QPointF(w * 0.62, h * 0.28))
        elif name == "images":
            painter.drawRoundedRect(QRectF(w * 0.25, h * 0.28, w * 0.5, h * 0.42), 3, 3)
            painter.drawEllipse(QPointF(w * 0.62, h * 0.39), 2.1, 2.1)
            painter.drawPolyline([QPointF(w * 0.30, h * 0.65), QPointF(w * 0.43, h * 0.52), QPointF(w * 0.53, h * 0.61), QPointF(w * 0.69, h * 0.45)])
        elif name == "metadata":
            painter.drawRoundedRect(QRectF(w * 0.31, h * 0.22, w * 0.38, h * 0.56), 3, 3)
            painter.drawLine(QPointF(w * 0.40, h * 0.40), QPointF(w * 0.60, h * 0.40))
            painter.drawLine(QPointF(w * 0.40, h * 0.52), QPointF(w * 0.60, h * 0.52))
            painter.drawLine(QPointF(w * 0.40, h * 0.64), QPointF(w * 0.54, h * 0.64))
        elif name == "traits":
            painter.drawRoundedRect(QRectF(w * 0.30, h * 0.28, w * 0.42, h * 0.34), 4, 4)
            painter.drawLine(QPointF(w * 0.31, h * 0.45), QPointF(w * 0.47, h * 0.73))
            painter.drawEllipse(QPointF(w * 0.39, h * 0.39), 1.8, 1.8)
        elif name == "supply":
            painter.drawRoundedRect(QRectF(w * 0.29, h * 0.25, w * 0.42, h * 0.14), 2, 2)
            painter.drawRoundedRect(QRectF(w * 0.25, h * 0.43, w * 0.50, h * 0.14), 2, 2)
            painter.drawRoundedRect(QRectF(w * 0.29, h * 0.61, w * 0.42, h * 0.14), 2, 2)
        elif name == "generate":
            painter.drawRoundedRect(QRectF(w * 0.25, h * 0.47, w * 0.34, h * 0.18), 2, 2)
            painter.drawRoundedRect(QRectF(w * 0.33, h * 0.36, w * 0.34, h * 0.18), 2, 2)
            painter.drawLine(QPointF(w * 0.67, h * 0.31), QPointF(w * 0.75, h * 0.23))
            painter.drawLine(QPointF(w * 0.70, h * 0.23), QPointF(w * 0.75, h * 0.23))
            painter.drawLine(QPointF(w * 0.75, h * 0.23), QPointF(w * 0.75, h * 0.28))
            painter.drawLine(QPointF(w * 0.66, h * 0.68), QPointF(w * 0.72, h * 0.74))
        elif name == "image_tools":
            painter.drawRoundedRect(QRectF(w * 0.26, h * 0.25, w * 0.48, h * 0.42), 3, 3)
            painter.drawLine(QPointF(w * 0.36, h * 0.73), QPointF(w * 0.64, h * 0.73))
            painter.drawLine(QPointF(w * 0.39, h * 0.45), QPointF(w * 0.49, h * 0.55))
            painter.drawLine(QPointF(w * 0.49, h * 0.55), QPointF(w * 0.61, h * 0.42))
        elif name == "metadata_tools":
            painter.drawRoundedRect(QRectF(w * 0.30, h * 0.22, w * 0.36, h * 0.56), 3, 3)
            painter.drawLine(QPointF(w * 0.39, h * 0.42), QPointF(w * 0.47, h * 0.50))
            painter.drawLine(QPointF(w * 0.47, h * 0.50), QPointF(w * 0.61, h * 0.36))
            painter.drawLine(QPointF(w * 0.39, h * 0.64), QPointF(w * 0.57, h * 0.64))


class BrandLogo(QWidget):
    def __init__(self, size: int = 42):
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 2

        outer = [
            QPointF(cx + r * math.cos(math.radians(60 * i - 90)), cy + r * math.sin(math.radians(60 * i - 90)))
            for i in range(6)
        ]
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0, QColor("#3b82f6"))
        gradient.setColorAt(1, QColor("#8b5cf6"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawPolygon(outer)

        inner_r = r * 0.58
        inner = [
            QPointF(cx + inner_r * math.cos(math.radians(60 * i - 90)), cy + inner_r * math.sin(math.radians(60 * i - 90)))
            for i in range(6)
        ]
        painter.setBrush(QBrush(QColor("#0a1422")))
        painter.drawPolygon(inner)

        painter.setPen(QPen(QColor("#dce8ff")))
        font = QFont("Inter", max(9, int(r * 0.62)), QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, "N")


class StatusCheckIcon(QWidget):
    def __init__(self, size: int = 20):
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#22c55e")))
        painter.drawEllipse(QRectF(1, 1, w - 2, h - 2))
        pen = QPen(QColor("#0a1422"), 1.8)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPolyline(
            [
                QPointF(w * 0.28, h * 0.52),
                QPointF(w * 0.44, h * 0.68),
                QPointF(w * 0.74, h * 0.32),
            ]
        )


class HeroVisual(QWidget):
    def __init__(self, icon_name: str, start_color: str, end_color: str, width: int = 108, height: int = 88):
        super().__init__()
        self.icon_name = icon_name
        self.start_color = start_color
        self.end_color = end_color
        self.setFixedSize(width, height)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0, QColor(self.start_color))
        gradient.setColorAt(1, QColor(self.end_color))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(QRectF(0, 0, w, h), 14, 14)

        pen = QPen(QColor(255, 255, 255, 235), 2.4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if self.icon_name == "generate":
            painter.drawLine(QPointF(w * 0.32, h * 0.74), QPointF(w * 0.68, h * 0.26))
            painter.drawLine(QPointF(w * 0.56, h * 0.18), QPointF(w * 0.76, h * 0.18))
            painter.drawLine(QPointF(w * 0.76, h * 0.18), QPointF(w * 0.76, h * 0.38))
            painter.drawLine(QPointF(w * 0.56, h * 0.18), QPointF(w * 0.76, h * 0.38))
            self._sparkle(painter, w * 0.24, h * 0.34, 5)
            self._sparkle(painter, w * 0.7, h * 0.66, 4)
        elif self.icon_name == "image_tools":
            painter.drawRoundedRect(QRectF(w * 0.22, h * 0.2, w * 0.56, h * 0.54), 4, 4)
            painter.drawEllipse(QPointF(w * 0.62, h * 0.36), 3.4, 3.4)
            painter.drawPolyline(
                [
                    QPointF(w * 0.28, h * 0.64),
                    QPointF(w * 0.42, h * 0.48),
                    QPointF(w * 0.54, h * 0.58),
                    QPointF(w * 0.72, h * 0.4),
                ]
            )
        painter.end()

    def _sparkle(self, painter: QPainter, cx: float, cy: float, r: float) -> None:
        painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        painter.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFT Asset Toolbox")
        self.resize(1280, 800)
        self.collection_dir = DEFAULT_COLLECTION
        self.worker: ValidationWorker | None = None

        self.stack = QStackedWidget()
        self.nav_buttons: list[QToolButton] = []
        self.activity_table = QTableWidget(0, 4)
        self.results_panel = QTextEdit()
        self.meta_results = QTextEdit()
        self.folder_label = QLabel()
        self.status_ready = QLabel("Ready")
        self.stat_labels: dict[str, QLabel] = {}

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_main_area(), 1)
        self.setCentralWidget(root)
        self._apply_theme()
        self.refresh_stats()

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(244)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 16)
        layout.setSpacing(4)

        layout.addWidget(self._brand_header())
        layout.addSpacing(22)

        pages = [
            ("Dashboard", "dashboard", self._dashboard_page),
            ("Generate Collection", "generate", self._generator_page),
            ("Image Tools", "image_tools", self._image_tools_page),
            ("Metadata Tools", "metadata_tools", self._metadata_tools_page),
            ("Reports", "reports", self._reports_page),
            ("Settings", "settings", self._settings_page),
            ("About", "about", self._about_page),
        ]
        section_labels = {1: "TOOLS", 5: "SETTINGS"}
        self.nav_icon_names: list[str] = []
        for index, (name, icon_name, builder) in enumerate(pages):
            if index in section_labels:
                layout.addSpacing(14)
                layout.addWidget(self._section_label(section_labels[index]))
                layout.addSpacing(2)
            self.stack.addWidget(builder())
            btn = QToolButton()
            btn.setText(f"  {name}")
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.setIconSize(QSize(18, 18))
            btn.setIcon(self._nav_icon(icon_name, False))
            btn.setFixedHeight(38)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=index: self._select_page(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
            self.nav_icon_names.append(icon_name)

        layout.addStretch(1)
        layout.addWidget(self._status_card())
        self._select_page(0)
        return sidebar

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("navSection")
        return label

    def _status_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("miniStatus")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(StatusCheckIcon(20))
        title = QLabel("All Systems Ready")
        title.setObjectName("statusTitle")
        top.addWidget(title, 1)
        layout.addLayout(top)

        body = QLabel("Your toolbox is ready to go!")
        body.setObjectName("muted")
        body.setWordWrap(True)
        layout.addWidget(body)

        version = QLabel(f"v{__version__}")
        version.setObjectName("statusVersion")
        layout.addWidget(version)
        return card

    def _nav_icon(self, name: str, active: bool) -> QIcon:
        color = "#f4f7fb" if active else "#8291a8"
        size = 18
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(color), 1.5)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        w = h = float(size)

        if name == "dashboard":
            painter.drawPolyline(
                [QPointF(w * 0.16, h * 0.5), QPointF(w * 0.5, h * 0.16), QPointF(w * 0.84, h * 0.5)]
            )
            painter.drawLine(QPointF(w * 0.26, h * 0.46), QPointF(w * 0.26, h * 0.82))
            painter.drawLine(QPointF(w * 0.74, h * 0.46), QPointF(w * 0.74, h * 0.82))
            painter.drawLine(QPointF(w * 0.26, h * 0.82), QPointF(w * 0.74, h * 0.82))
        elif name == "generate":
            painter.drawLine(QPointF(w * 0.28, h * 0.78), QPointF(w * 0.72, h * 0.28))
            painter.drawLine(QPointF(w * 0.6, h * 0.18), QPointF(w * 0.8, h * 0.18))
            painter.drawLine(QPointF(w * 0.8, h * 0.18), QPointF(w * 0.8, h * 0.38))
            painter.drawLine(QPointF(w * 0.6, h * 0.18), QPointF(w * 0.8, h * 0.38))
        elif name == "image_tools":
            painter.drawRoundedRect(QRectF(w * 0.18, h * 0.24, w * 0.64, h * 0.52), 2.4, 2.4)
            painter.drawEllipse(QPointF(w * 0.38, h * 0.42), 1.5, 1.5)
            painter.drawPolyline(
                [
                    QPointF(w * 0.22, h * 0.68),
                    QPointF(w * 0.42, h * 0.52),
                    QPointF(w * 0.56, h * 0.62),
                    QPointF(w * 0.78, h * 0.4),
                ]
            )
        elif name == "metadata_tools":
            painter.drawRoundedRect(QRectF(w * 0.28, h * 0.16, w * 0.44, h * 0.68), 2.4, 2.4)
            painter.drawLine(QPointF(w * 0.38, h * 0.36), QPointF(w * 0.62, h * 0.36))
            painter.drawLine(QPointF(w * 0.38, h * 0.5), QPointF(w * 0.62, h * 0.5))
            painter.drawLine(QPointF(w * 0.38, h * 0.64), QPointF(w * 0.54, h * 0.64))
        elif name == "reports":
            painter.drawLine(QPointF(w * 0.2, h * 0.82), QPointF(w * 0.2, h * 0.32))
            painter.drawLine(QPointF(w * 0.2, h * 0.82), QPointF(w * 0.84, h * 0.82))
            painter.drawRect(QRectF(w * 0.32, h * 0.58, w * 0.12, h * 0.24))
            painter.drawRect(QRectF(w * 0.5, h * 0.46, w * 0.12, h * 0.36))
            painter.drawRect(QRectF(w * 0.68, h * 0.32, w * 0.12, h * 0.5))
        elif name == "settings":
            painter.drawEllipse(QPointF(w * 0.5, h * 0.5), w * 0.16, w * 0.16)
            for i in range(8):
                angle = math.pi / 4 * i
                x1 = w * 0.5 + math.cos(angle) * w * 0.28
                y1 = h * 0.5 + math.sin(angle) * w * 0.28
                x2 = w * 0.5 + math.cos(angle) * w * 0.4
                y2 = h * 0.5 + math.sin(angle) * w * 0.4
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        elif name == "about":
            painter.drawEllipse(QPointF(w * 0.5, h * 0.5), w * 0.32, w * 0.32)
            painter.drawLine(QPointF(w * 0.5, h * 0.44), QPointF(w * 0.5, h * 0.68))
            dot_pen = QPen(QColor(color), 2.2)
            dot_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(dot_pen)
            painter.drawPoint(QPointF(w * 0.5, h * 0.32))
        painter.end()
        return QIcon(pixmap)

    def _build_main_area(self) -> QWidget:
        shell = QWidget()
        shell.setObjectName("mainShell")
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack, 1)
        layout.addWidget(self._status_bar())
        return shell

    def _status_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("bottomBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.addWidget(QLabel("Python " + sys.version.split()[0]))
        layout.addSpacing(18)
        layout.addWidget(QLabel("Pillow required for image scripts"))
        layout.addStretch(1)
        layout.addWidget(QLabel("Working Directory:"))
        layout.addWidget(QLabel(str(self.collection_dir.relative_to(ROOT))))
        layout.addStretch(1)
        layout.addWidget(self.status_ready)
        return bar

    def _brand_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("brandHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(12)

        logo = BrandLogo(42)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(0)
        line1 = QLabel("ASSET")
        line1.setObjectName("brandLine1")
        line2 = QLabel("TOOLBOX")
        line2.setObjectName("brandLine2")
        text_box.addWidget(line1)
        text_box.addWidget(line2)

        layout.addWidget(logo)
        layout.addLayout(text_box, 1)
        return header

    def _stat_card(self, label: str, icon_name: str) -> tuple[Card, QLabel]:
        card = Card()
        card.setObjectName("statCard")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        icon = IconBadge(icon_name, 30)

        value_box = QVBoxLayout()
        value_box.setContentsMargins(0, 0, 0, 0)
        value_box.setSpacing(0)
        value = QLabel("0")
        value.setObjectName("statValue")
        label_widget = QLabel(label)
        label_widget.setObjectName("muted")
        value_box.addWidget(value)
        value_box.addWidget(label_widget)

        row.addWidget(icon)
        row.addLayout(value_box, 1)
        card.layout.addLayout(row)
        return card, value

    TOOL_CARD_HEIGHT = 282

    def _tool_card(
        self,
        icon_name: str,
        title: str,
        body: str,
        features: list[str],
        button_text: str,
        page_index: int,
        preview: QWidget | None = None,
    ) -> Card:
        card = Card()
        card.setFixedHeight(self.TOOL_CARD_HEIGHT)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.layout.setSpacing(6)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        icon = IconBadge(icon_name, 30)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setWordWrap(True)
        header.addWidget(icon)
        header.addWidget(title_label, 1)
        card.layout.addLayout(header)

        desc = QLabel(body)
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        card.layout.addWidget(desc)

        if preview is not None:
            card.layout.addWidget(preview)

        card.layout.addWidget(self._feature_list(features))
        card.layout.addStretch(1)

        button = QPushButton(button_text)
        button.setFixedHeight(32)
        button.clicked.connect(lambda checked=False, i=page_index: self._select_page(i))
        card.layout.addWidget(button)
        return card

    def _feature_list(self, features: list[str]) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        for feature in features:
            layout.addWidget(self._feature_label(feature))
        return box

    def _feature_label(self, text: str) -> QLabel:
        label = QLabel(f"+ {text}")
        label.setObjectName("featureText")
        return label

    def _dashboard_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._dashboard_header())

        folder_card = Card()
        row = QHBoxLayout()
        row.setSpacing(10)
        folder_icon = IconBadge("folder", 28)
        text_box = QVBoxLayout()
        text_box.setSpacing(0)
        folder_hint = QLabel("Current Collection Folder")
        folder_hint.setObjectName("muted")
        self.folder_label.setObjectName("folderPath")
        self.folder_label.setWordWrap(True)
        text_box.addWidget(folder_hint)
        text_box.addWidget(self.folder_label)
        change = QPushButton("Change Folder")
        change.clicked.connect(self.choose_folder)
        row.addWidget(folder_icon)
        row.addLayout(text_box, 1)
        row.addWidget(change)
        folder_card.layout.addLayout(row)
        page.addWidget(folder_card)

        stats = QHBoxLayout()
        stat_icons = {"Images": "images", "Metadata": "metadata", "Traits": "traits", "Supply": "supply"}
        for key in ["Images", "Metadata", "Traits", "Supply"]:
            card, value = self._stat_card(key, stat_icons[key])
            stats.addWidget(card)
            self.stat_labels[key] = value
        page.addLayout(stats)

        tool_cards = QHBoxLayout()
        tool_cards.setSpacing(14)
        tool_specs = [
            (
                "generate",
                "Generate Collection",
                "Create unique NFT images using layered assets and rarity rules.",
                ["Layered image generation", "Weighted rarity support", "Metadata output", "Custom trait configuration"],
                "Open Generator",
                1,
                self._generate_preview(),
            ),
            (
                "image_tools",
                "Image Tools",
                "Batch process collection images for optimal quality and size.",
                ["Resize PNG images", "Convert PNG to WebP", "Resize WebP images", "Preserve transparency"],
                "Open Image Tools",
                2,
                self._image_tools_preview(),
            ),
            (
                "metadata_tools",
                "Metadata Tools",
                "Validate, analyze, and update your NFT metadata files.",
                [
                    "Validate supply & files",
                    "Validate JSON structure",
                    "Trait uniqueness check",
                    "Generate trait reports",
                    "Update IPFS CID in metadata",
                ],
                "Open Metadata Tools",
                3,
                self._metadata_preview(),
            ),
        ]
        for icon, title, body, features, button_text, page_index, preview in tool_specs:
            card = self._tool_card(icon, title, body, features, button_text, page_index, preview=preview)
            tool_cards.addWidget(card)
        page.addLayout(tool_cards)

        lower = QHBoxLayout()
        lower.setSpacing(14)
        activity = Card("Recent Activity")
        activity.setFixedHeight(196)
        self.activity_table.setHorizontalHeaderLabels(["Time", "Activity", "Status", "Details"])
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setShowGrid(False)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.activity_table.setColumnWidth(0, 132)
        self.activity_table.setColumnWidth(1, 190)
        self.activity_table.setColumnWidth(2, 88)
        activity.layout.addWidget(self.activity_table)
        lower.addWidget(activity, 3)

        quick = Card("Quick Actions")
        quick.setFixedHeight(196)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(14)
        actions = [
            ("Validate Supply", "metadata_tools", self.run_validation),
            (
                "Trait Report",
                "reports",
                lambda: self._placeholder("Trait Report", "Open Metadata Tools to generate validation details."),
            ),
            ("Update IPFS CID", "metadata_tools", lambda: self._select_page(3)),
            ("Resize PNG", "image_tools", lambda: self._select_page(2)),
            ("PNG to WebP", "image_tools", lambda: self._select_page(2)),
            ("Resize WebP", "image_tools", lambda: self._select_page(2)),
        ]
        for i, (text, icon_name, slot) in enumerate(actions):
            btn = QPushButton(text)
            btn.setObjectName("quickActionBtn")
            btn.setIcon(self._nav_icon(icon_name, True))
            btn.setIconSize(QSize(15, 15))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(slot)
            grid.addWidget(btn, i // 3, i % 3)
        quick.layout.addLayout(grid)
        quick.layout.addStretch(1)
        lower.addWidget(quick, 2)
        page.addLayout(lower)
        page.addStretch(1)
        self.add_activity("Dashboard", "Loaded sample collection", "Success", "100 images, 100 metadata")
        self.add_activity("Generator", "Generated 100 sample NFTs", "Success", "sample_collection/output")
        self.add_activity("Metadata Tools", "Validated supply", "Success", "No missing files")
        self.add_activity("Metadata Tools", "Generated trait report", "Success", "trait_frequency.csv")
        return self._scroll_wrap(page)

    def _dashboard_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("dashboardHeader")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(1)
        title = QLabel("Welcome to NFT Asset Toolbox")
        title.setObjectName("dashboardTitle")
        subtitle = QLabel("Generate, process, validate, and prepare NFT collection assets.")
        subtitle.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _generate_preview(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(HeroVisual("generate", "#7c3aed", "#4c1d95"))
        layout.addStretch(1)
        return row

    def _image_tools_preview(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(HeroVisual("image_tools", "#3b82f6", "#1e40af"))
        layout.addStretch(1)
        return row

    def _metadata_preview(self) -> QWidget:
        self.metadata_snippet = QLabel()
        self.metadata_snippet.setObjectName("metaSnippet")
        font = QFont("Monospace")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(8)
        self.metadata_snippet.setFont(font)
        self._refresh_metadata_preview()
        return self.metadata_snippet

    def _refresh_metadata_preview(self) -> None:
        self.metadata_snippet.setText(self._load_metadata_snippet(self.collection_dir))

    def _load_metadata_snippet(self, collection_dir: Path, limit_attrs: int = 2) -> str:
        try:
            meta_dir = metadata_dir_for(Path(collection_dir))

            def sort_key(path: Path):
                try:
                    return (0, int(path.stem))
                except ValueError:
                    return (1, path.stem)

            candidates = sorted(meta_dir.glob("*.json"), key=sort_key)
            data = json.loads(candidates[0].read_text(encoding="utf-8")) if candidates else {}
        except Exception:
            data = {}

        attrs = data.get("attributes", []) if isinstance(data, dict) else []
        lines = ["{", f'  "name": "{data.get("name", "Sample NFT")}",', '  "attributes": [']
        for attr in attrs[:limit_attrs]:
            if not isinstance(attr, dict):
                continue
            lines.append(f'    {{"trait_type": "{attr.get("trait_type", "")}", "value": "{attr.get("value", "")}"}},')
        remaining = len(attrs) - limit_attrs
        if remaining > 0:
            lines.append(f"    ... (+{remaining} more)")
        lines.append("  ]")
        lines.append("}")
        return "\n".join(lines)

    def _generator_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._title("Generate Collection", "Configure layered image and metadata generation."))
        card = Card("Generator Settings")
        form = QFormLayout()
        form.addRow("Collection name", QLineEdit("Sample Collection"))
        form.addRow("Layers folder", self._path_row("Select layers folder"))
        form.addRow("Output folder", self._path_row("Select output folder"))
        supply = QSpinBox()
        supply.setRange(1, 10000)
        supply.setValue(100)
        form.addRow("Supply count", supply)
        form.addRow("", QCheckBox("Generate images"))
        form.addRow("", QCheckBox("Generate metadata"))
        card.layout.addLayout(form)
        run = QPushButton("Prepare Generator")
        run.clicked.connect(lambda: self._placeholder("Generate Collection", "The page is ready; script wiring is intentionally conservative in this milestone."))
        card.layout.addWidget(run)
        page.addWidget(card)
        return self._wrap(page)

    def _image_tools_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._title("Image Tools", "Batch process collection image assets."))
        card = Card("Image Operation")
        form = QFormLayout()
        operation = QComboBox()
        operation.addItems(["Resize PNG", "Convert PNG to lossless WebP", "Resize WebP"])
        form.addRow("Operation", operation)
        form.addRow("Input folder", self._path_row("Select input folder"))
        form.addRow("Output folder", self._path_row("Select output folder"))
        size = QSpinBox()
        size.setRange(16, 4096)
        size.setValue(512)
        form.addRow("Target size", size)
        form.addRow("", QCheckBox("Preserve transparency"))
        card.layout.addLayout(form)
        run = QPushButton("Run Image Tool")
        run.clicked.connect(lambda: self._placeholder("Image Tools", "The controls are in place; existing scripts remain available from the command line."))
        card.layout.addWidget(run)
        page.addWidget(card)
        return self._wrap(page)

    def _metadata_tools_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._title("Metadata Tools", "Validate and prepare collection metadata."))
        card = Card("Validation")
        form = QFormLayout()
        form.addRow("Metadata folder", QLabel(str(self.collection_dir / "metadata")))
        form.addRow("IPFS CID", QLineEdit("bafy..."))
        card.layout.addLayout(form)
        buttons = QHBoxLayout()
        validate = QPushButton("Validate Supply")
        validate.clicked.connect(self.run_validation)
        buttons.addWidget(validate)
        buttons.addWidget(QPushButton("Generate Trait Report"))
        buttons.addWidget(QPushButton("Update IPFS CID"))
        card.layout.addLayout(buttons)
        self.meta_results.setReadOnly(True)
        self.meta_results.setPlaceholderText("Validation results will appear here.")
        card.layout.addWidget(self.meta_results, 1)
        page.addWidget(card)
        return self._wrap(page)

    def _reports_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._title("Reports", "Generated validation and trait reports."))
        card = Card("Report Files")
        self.results_panel.setReadOnly(True)
        self.results_panel.setText(self._report_listing())
        card.layout.addWidget(self.results_panel)
        open_folder = QPushButton("Open Reports Folder")
        open_folder.clicked.connect(self.open_reports_folder)
        card.layout.addWidget(open_folder)
        page.addWidget(card)
        return self._wrap(page)

    def _settings_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._title("Settings", "Local desktop preferences."))
        page.addWidget(Card("Safe Defaults", "Operations write to new output folders and validation reports are stored in ./reports."))
        return self._wrap(page)

    def _about_page(self) -> QWidget:
        page = self._page()
        page.addWidget(self._title("About", "NFT Asset Toolbox"))
        page.addWidget(Card("Desktop Portfolio App", "A professional Python desktop UI wrapped around the existing asset, image, and metadata scripts."))
        return self._wrap(page)

    def _page(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 12, 24, 14)
        layout.setSpacing(7)
        return layout

    def _wrap(self, layout: QVBoxLayout) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def _scroll_wrap(self, layout: QVBoxLayout) -> QScrollArea:
        content = QWidget()
        content.setObjectName("dashboardContent")
        content.setLayout(layout)

        scroll = QScrollArea()
        scroll.setObjectName("dashboardScroll")
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        return scroll

    def _title(self, title: str, subtitle: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        h = QLabel(title)
        h.setObjectName("h1")
        s = QLabel(subtitle)
        s.setObjectName("muted")
        layout.addWidget(h)
        layout.addWidget(s)
        return box

    def _path_row(self, button_text: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        field = QLineEdit()
        browse = QPushButton(button_text)
        browse.clicked.connect(lambda: self._browse_into(field))
        layout.addWidget(field, 1)
        layout.addWidget(browse)
        return row

    def _browse_into(self, field: QLineEdit) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", str(ROOT))
        if folder:
            field.setText(folder)

    def _select_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            active = i == index
            btn.setChecked(active)
            btn.setIcon(self._nav_icon(self.nav_icon_names[i], active))

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Collection Folder", str(self.collection_dir))
        if folder:
            self.collection_dir = Path(folder)
            self.refresh_stats()
            self.add_activity("Dashboard", "Changed collection folder", "Success", str(self.collection_dir))

    def refresh_stats(self) -> None:
        stats = get_collection_stats(self.collection_dir)
        self.folder_label.setText(str(self.collection_dir.relative_to(ROOT) if self.collection_dir.is_relative_to(ROOT) else self.collection_dir))
        self.stat_labels["Images"].setText(str(stats.images))
        self.stat_labels["Metadata"].setText(str(stats.metadata))
        self.stat_labels["Traits"].setText(str(stats.traits))
        self.stat_labels["Supply"].setText(str(stats.supply))
        self._refresh_metadata_preview()

    def run_validation(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        self.status_ready.setText("Validating...")
        self.meta_results.setText("Running metadata validation...")
        self.worker = ValidationWorker(self.collection_dir)
        self.worker.finished.connect(self.validation_finished)
        self.worker.failed.connect(self.validation_failed)
        self.worker.start()

    def validation_finished(self, result: ValidationResult) -> None:
        self.refresh_stats()
        status = "Success" if result.ok else "Warning"
        details = f"{result.images_found} images, {result.metadata_found} metadata files, {result.trait_count} traits"
        self.add_activity("Metadata Tools", "Validate Supply", status, details)
        report = [
            f"Images found: {result.images_found}",
            f"Metadata files found: {result.metadata_found}",
            f"JSON valid: {'Yes' if result.json_valid else 'No'}",
            f"Missing files: {len(result.missing_images) + len(result.missing_metadata)}",
            f"Duplicate trait combinations: {len(result.duplicate_trait_combinations)}",
            f"Trait count: {result.trait_count}",
            f"Report path: {result.report_path}",
        ]
        self.meta_results.setText("\n".join(report))
        self.results_panel.setText(self._report_listing())
        self.status_ready.setText("Ready")

    def validation_failed(self, message: str) -> None:
        self.add_activity("Metadata Tools", "Validate Supply", "Failed", message)
        self.meta_results.setText(message)
        self.status_ready.setText("Ready")

    def add_activity(self, tool: str, action: str, status: str, details: str) -> None:
        row = self.activity_table.rowCount()
        self.activity_table.insertRow(row)
        values = [datetime.now().strftime("%Y-%m-%d %H:%M"), action, status, details]
        for col, value in enumerate(values):
            self.activity_table.setItem(row, col, QTableWidgetItem(value))
        self.activity_table.setRowHeight(row, 26)

    def _placeholder(self, title: str, body: str) -> None:
        self.add_activity(title, "Opened placeholder", "Info", body)
        QMessageBox.information(self, title, body)

    def _report_listing(self) -> str:
        REPORTS_DIR.mkdir(exist_ok=True)
        files = sorted(REPORTS_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return "No reports generated yet."
        return "\n".join(str(path.relative_to(ROOT)) for path in files)

    def open_reports_folder(self) -> None:
        REPORTS_DIR.mkdir(exist_ok=True)
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", str(REPORTS_DIR)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(REPORTS_DIR)])
            else:
                subprocess.Popen(["explorer", str(REPORTS_DIR)])
        except OSError as exc:
            QMessageBox.warning(self, "Open Reports Folder", str(exc))

    def _apply_theme(self) -> None:
        QApplication.instance().setFont(QFont("Inter", 10))
        self.setStyleSheet(
            """
            QMainWindow { background: #0f1722; }
            QWidget { background: transparent; color: #dbe6f4; }
            QLabel { background: transparent; }
            #mainShell { background: #0f1722; }
            #dashboardScroll, #dashboardScroll > QWidget, #dashboardContent { background: #0f1722; }
            #sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a1422, stop:1 #07101b);
                border-right: 1px solid #253044;
            }
            #brandHeader { background: transparent; }
            #brandLine1, #brandLine2 {
                color: #f4f7fb;
                font-size: 15px;
                font-weight: 800;
            }
            #brandLine2 { color: #9aa8ba; }
            #navSection {
                color: #64748b;
                font-size: 10px;
                font-weight: 800;
                padding: 2px 10px;
            }
            #h1 { color: #f7f9fd; font-size: 23px; font-weight: 800; }
            #dashboardHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a2447, stop:0.55 #1e1f3d, stop:1 #172436);
                border: 1px solid #2c3b60;
                border-radius: 12px;
            }
            #dashboardTitle { color: #f7f9fd; font-size: 19px; font-weight: 800; }
            #card, #statCard, #miniStatus {
                background: #141b2a;
                border: 1px solid #253044;
                border-radius: 8px;
            }
            #statCard { background: #141e2d; }
            #miniStatus { background: #111827; border: 1px solid #253044; border-radius: 10px; }
            #statusTitle { color: #f4f7fb; font-size: 13px; font-weight: 800; }
            #statusVersion { color: #64748b; font-size: 11px; font-weight: 700; margin-top: 2px; }
            #cardTitle { font-size: 14px; font-weight: 800; color: #f5f8fc; }
            #muted { color: #93a4ba; }
            #folderPath { color: #f4f7fb; font-weight: 700; font-size: 14px; }
            #statValue { color: #f8fbff; font-size: 26px; font-weight: 850; }
            #featureText {
                color: #b8c7db;
                font-size: 11px;
                padding: 0;
            }
            #metaSnippet {
                background: #0e1520;
                border: 1px solid #253044;
                border-radius: 6px;
                color: #9bd2ff;
                padding: 5px 8px;
            }
            #bottomBar { background: #111a28; border-top: 1px solid #233046; color: #9fb0c4; }
            #sidebar QToolButton {
                text-align: left;
                padding: 8px 10px;
                border-radius: 8px;
                color: #9aa8ba;
                font-weight: 600;
                background: transparent;
                border: none;
            }
            #sidebar QToolButton:hover { background: #141b2a; color: #dbe6f4; }
            #sidebar QToolButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #8b5cf6);
                color: #ffffff;
            }
            QPushButton {
                background: #315fd6;
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 5px 12px;
                font-weight: 700;
            }
            QPushButton:hover { background: #3f72ee; }
            QPushButton#quickActionBtn {
                background: #171f30;
                border: 1px solid #29385a;
                color: #dbe6f4;
                text-align: left;
                padding: 6px 10px;
                font-weight: 600;
            }
            QPushButton#quickActionBtn:hover {
                background: #1c2740;
                border: 1px solid #3b82f6;
            }
            QLineEdit, QSpinBox, QComboBox, QTextEdit, QTableWidget {
                background: #101826;
                border: 1px solid #2a3952;
                border-radius: 6px;
                color: #e5edf8;
                padding: 7px;
            }
            QHeaderView::section {
                background: #172235;
                color: #9fb0c4;
                border: 0;
                padding: 6px;
            }
            QTableWidget {
                gridline-color: #26344c;
                selection-background-color: #24305d;
                alternate-background-color: #121b29;
            }
            """
        )


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    if os.environ.get("NFT_TOOLBOX_SMOKE"):
        QTimer.singleShot(800, app.quit)
    return app.exec()
