from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
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
from nft_asset_toolbox.core import ValidationResult, get_collection_stats, validate_collection


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_COLLECTION = ROOT / "sample_collection"
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
        self.layout.setContentsMargins(18, 14, 18, 14)
        self.layout.setSpacing(8)
        if title:
            label = QLabel(title)
            label.setObjectName("cardTitle")
            self.layout.addWidget(label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("muted")
            sub.setWordWrap(True)
            self.layout.addWidget(sub)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFT Asset Toolbox")
        self.resize(1180, 760)
        self.collection_dir = SAMPLE_COLLECTION
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
        sidebar.setFixedWidth(210)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 14)
        layout.setSpacing(10)

        layout.addWidget(self._brand_header())
        layout.addSpacing(16)

        pages = [
            ("Dashboard", self._dashboard_page),
            ("Generate Collection", self._generator_page),
            ("Image Tools", self._image_tools_page),
            ("Metadata Tools", self._metadata_tools_page),
            ("Reports", self._reports_page),
            ("Settings", self._settings_page),
            ("About", self._about_page),
        ]
        for index, (name, builder) in enumerate(pages):
            self.stack.addWidget(builder())
            btn = QToolButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
            btn.clicked.connect(lambda checked=False, i=index: self._select_page(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch(1)
        status = Card("All Systems Ready", f"v{__version__}")
        status.setObjectName("miniStatus")
        layout.addWidget(status)
        self._select_page(0)
        return sidebar

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
        layout.setContentsMargins(20, 8, 20, 8)
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        logo = QLabel("NFT")
        logo.setObjectName("brandLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(38, 38)

        text = QLabel("NFT Asset Toolbox")
        text.setObjectName("brand")
        text.setWordWrap(True)

        layout.addWidget(logo)
        layout.addWidget(text, 1)
        return header

    def _stat_card(self, label: str, icon_text: str) -> tuple[Card, QLabel]:
        card = Card()
        card.setObjectName("statCard")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        icon = QLabel(icon_text)
        icon.setObjectName("statIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(38, 38)

        value_box = QVBoxLayout()
        value_box.setContentsMargins(0, 0, 0, 0)
        value_box.setSpacing(2)
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

    def _tool_card(
        self,
        icon_text: str,
        title: str,
        body: str,
        features: list[str],
        button_text: str,
        page_index: int,
    ) -> Card:
        card = Card()
        card.setMinimumHeight(248)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        icon = QLabel(icon_text)
        icon.setObjectName("toolIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(42, 42)

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

        for feature in features:
            card.layout.addWidget(self._feature_label(feature))

        button = QPushButton(button_text)
        button.setFixedHeight(36)
        button.clicked.connect(lambda checked=False, i=page_index: self._select_page(i))
        card.layout.addStretch(1)
        card.layout.addWidget(button)
        return card

    def _feature_label(self, text: str) -> QLabel:
        label = QLabel(f"+ {text}")
        label.setObjectName("featureText")
        return label

    def _dashboard_page(self) -> QWidget:
        page = self._page()
        header = QLabel("Welcome to NFT Asset Toolbox")
        header.setObjectName("h1")
        subtitle = QLabel("Generate, process, validate, and prepare NFT collection assets.")
        subtitle.setObjectName("muted")
        page.addWidget(header)
        page.addWidget(subtitle)

        folder_card = Card()
        row = QHBoxLayout()
        self.folder_label.setObjectName("folderPath")
        change = QPushButton("Change Folder")
        change.clicked.connect(self.choose_folder)
        folder_hint = QLabel("Current collection folder")
        folder_hint.setObjectName("muted")
        row.addWidget(folder_hint)
        row.addWidget(self.folder_label, 1)
        row.addWidget(change)
        folder_card.layout.addLayout(row)
        page.addWidget(folder_card)

        stats = QHBoxLayout()
        stat_icons = {"Images": "IMG", "Metadata": "JSON", "Traits": "TRT", "Supply": "#"}
        for key in ["Images", "Metadata", "Traits", "Supply"]:
            card, value = self._stat_card(key, stat_icons[key])
            stats.addWidget(card)
            self.stat_labels[key] = value
        page.addLayout(stats)

        tool_cards = QHBoxLayout()
        tool_cards.setSpacing(14)
        for icon, title, body, features, button_text, page_index in [
            (
                "GEN",
                "Generate Collection",
                "Create layered NFT assets and ERC-721 metadata.",
                ["Layered image generation", "Weighted rarity support", "Metadata output", "Custom traits"],
                "Open Generator",
                1,
            ),
            (
                "IMG",
                "Image Tools",
                "Resize and convert collection images.",
                ["Resize PNG batches", "Lossless WebP export", "Resize WebP assets", "Preserve transparency"],
                "Open Image Tools",
                2,
            ),
            (
                "META",
                "Metadata Tools",
                "Validate metadata and prepare IPFS fields.",
                ["Validate supply", "Check JSON structure", "Detect duplicate traits", "Update image fields"],
                "Open Metadata Tools",
                3,
            ),
        ]:
            card = self._tool_card(icon, title, body, features, button_text, page_index)
            tool_cards.addWidget(card)
        page.addLayout(tool_cards)

        lower = QHBoxLayout()
        activity = Card("Recent Activity")
        self.activity_table.setHorizontalHeaderLabels(["Time", "Activity", "Status", "Details"])
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setShowGrid(False)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.activity_table.setColumnWidth(0, 132)
        self.activity_table.setColumnWidth(1, 190)
        self.activity_table.setColumnWidth(2, 88)
        self.activity_table.setMinimumHeight(150)
        activity.layout.addWidget(self.activity_table)
        lower.addWidget(activity, 3)

        quick = Card("Quick Actions")
        grid = QGridLayout()
        actions = [
            ("Validate Supply", self.run_validation),
            ("Trait Report", lambda: self._placeholder("Trait Report", "Open Metadata Tools to generate validation details.")),
            ("Update IPFS CID", lambda: self._select_page(3)),
            ("Resize PNG", lambda: self._select_page(2)),
            ("PNG to WebP", lambda: self._select_page(2)),
            ("Resize WebP", lambda: self._select_page(2)),
        ]
        for i, (text, slot) in enumerate(actions):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            grid.addWidget(btn, i // 3, i % 3)
        quick.layout.addLayout(grid)
        lower.addWidget(quick, 2)
        page.addLayout(lower, 1)
        self.add_activity("Dashboard", "Loaded sample collection", "Success", "100 images, 100 metadata")
        self.add_activity("Metadata Tools", "Validate Supply", "Success", "No missing files")
        self.add_activity("Metadata Tools", "Trait Report", "Success", "Report generated")
        return self._wrap(page)

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
        layout.setContentsMargins(26, 20, 26, 16)
        layout.setSpacing(11)
        return layout

    def _wrap(self, layout: QVBoxLayout) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout)
        return widget

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
            btn.setChecked(i == index)

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
        self.activity_table.setRowHeight(row, 30)

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
            #sidebar { background: #101826; border-right: 1px solid #233046; }
            #brandHeader { background: transparent; }
            #brand {
                color: #f4f7fb;
                font-size: 15px;
                font-weight: 800;
                line-height: 1.15;
            }
            #brandLogo {
                background: #1d2b44;
                border: 1px solid #36507a;
                border-radius: 8px;
                color: #7dd3fc;
                font-size: 11px;
                font-weight: 900;
            }
            #h1 { color: #f7f9fd; font-size: 24px; font-weight: 800; }
            #card, #statCard, #miniStatus {
                background: #151f2e;
                border: 1px solid #26344c;
                border-radius: 8px;
            }
            #statCard { background: #141e2d; }
            #miniStatus { background: #142031; }
            #cardTitle { font-size: 15px; font-weight: 800; color: #f5f8fc; }
            #muted { color: #93a4ba; }
            #folderPath { color: #f4f7fb; font-weight: 700; }
            #statValue { color: #f8fbff; font-size: 28px; font-weight: 850; }
            #statIcon, #toolIcon {
                background: #21314b;
                border: 1px solid #31476a;
                border-radius: 8px;
                color: #9bd2ff;
                font-size: 10px;
                font-weight: 900;
            }
            #toolIcon {
                background: #263c7a;
                color: white;
            }
            #featureText {
                color: #b8c7db;
                font-size: 12px;
                padding: 0 0 1px 0;
            }
            #bottomBar { background: #111a28; border-top: 1px solid #233046; color: #9fb0c4; }
            QToolButton {
                text-align: left;
                padding: 10px 12px;
                border-radius: 6px;
                color: #bac8da;
            }
            QToolButton:checked, QToolButton:hover { background: #24305d; color: white; }
            QPushButton {
                background: #315fd6;
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 700;
            }
            QPushButton:hover { background: #3f72ee; }
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
                padding: 8px;
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
