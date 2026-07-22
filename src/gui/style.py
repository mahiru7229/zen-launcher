APP_STYLE = """
QWidget {
    color: #f3f0e8;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}

QMainWindow, QWidget#Root {
    background: #171817;
}

QDialog {
    background: #252823;
    color: #f5f1e8;
}

QMessageBox {
    background: #f2f3ef;
    color: #171817;
}

QMessageBox QLabel {
    background: transparent;
    color: #171817;
    font-family: "Segoe UI";
}

QMessageBox QPushButton {
    min-width: 88px;
    background: #dfe3da;
    color: #171817;
    border-color: #747a6e;
}

QMessageBox QPushButton:hover {
    background: #cbd7bf;
    color: #10120e;
}

QFrame#Sidebar {
    background: #20221f;
    border-right: 3px solid #11120f;
}

QWidget#CenterArea {
    background: #2b2d29;
}

QStackedWidget#ContentStack, QScrollArea, QWidget#PageViewport {
    background: #2b2d29;
    border: none;
}

QFrame#RightPanel {
    background: #252723;
    border-left: 3px solid #11120f;
}

QFrame#LaunchControl {
    background: #1e201d;
    border-top: 3px solid #11120f;
}

QFrame#Card {
    background: #343730;
    border: 2px solid #161713;
    border-bottom-color: #0d0e0c;
    border-right-color: #0d0e0c;
}

QFrame#HeroCard {
    background: #30342d;
    border: 3px solid #151713;
}

QFrame#InsetPanel {
    background: #262923;
    border: 2px solid #151713;
}

QLabel#BrandLabel {
    color: #a8db72;
    font-size: 25px;
    font-weight: 900;
    letter-spacing: 1px;
}

QLabel#VersionLabel, QLabel#MutedLabel {
    color: #aaa99f;
}

QLabel#PageTitle {
    color: #f5f1e8;
    font-size: 27px;
    font-weight: 800;
}

QLabel#PageSubtitle {
    color: #b9b7ad;
    font-size: 11pt;
}

QLabel#CardTitle {
    color: #d9e6c8;
    font-size: 14px;
    font-weight: 800;
}

QLabel#CardSubtitle {
    color: #a6a69d;
}

QLabel#ValueLabel {
    color: #ffffff;
    font-size: 12pt;
    font-weight: 700;
}

QLabel#TinyLabel {
    color: #9c9b92;
    font-size: 9pt;
}

QLabel#StatusBadge {
    background: #344329;
    color: #bde98a;
    border: 2px solid #12140f;
    padding: 6px 10px;
    font-weight: 800;
}

QLabel#WarningBadge {
    background: #4a3824;
    color: #f0c37d;
    border: 2px solid #15120e;
    padding: 6px 10px;
    font-weight: 800;
}

QPushButton {
    background: #454940;
    color: #f4f1e9;
    border: 2px solid #171814;
    border-bottom-color: #0c0d0b;
    border-right-color: #0c0d0b;
    padding: 8px 12px;
    font-weight: 700;
}

QPushButton:hover {
    background: #565c4e;
    color: #c9f49a;
}

QPushButton:pressed {
    background: #30332d;
    border-top-color: #0c0d0b;
    border-left-color: #0c0d0b;
    border-bottom-color: #171814;
    border-right-color: #171814;
}

QPushButton:disabled {
    background: #30322e;
    color: #74756f;
    border-color: #1d1e1b;
}

QPushButton#PrimaryButton {
    background: #63984a;
    color: #0e120b;
    border: 3px solid #11150e;
    font-size: 13pt;
    font-weight: 900;
}

QPushButton#PrimaryButton:hover {
    background: #7db45e;
    color: #0c1009;
}

QPushButton#DangerButton {
    background: #6e3937;
    color: #ffe2dc;
}

QPushButton#DangerButton:hover {
    background: #884743;
}

QPushButton#NavButton {
    background: transparent;
    color: #c5c4ba;
    border: 2px solid transparent;
    padding: 10px 12px;
    text-align: left;
    font-size: 11.5pt;
}

QPushButton#NavButton:hover {
    background: #2e312b;
    color: #d9ffc0;
    border-color: #161713;
}

QPushButton#NavButton:checked {
    background: #3d4c32;
    color: #c8f29d;
    border-color: #11130f;
}

QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background: #20221f;
    color: #f5f1e8;
    border: 2px solid #11120f;
    padding: 7px 9px;
    selection-background-color: #688f4d;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border-color: #83b75f;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: #252823;
    color: #f5f1e8;
    border: 2px solid #11120f;
    selection-background-color: #4f6d3c;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background: #20221f;
    border: 2px solid #10110f;
}

QCheckBox::indicator:checked {
    background: #7eaf59;
    border: 3px solid #10110f;
}

QLabel#MemoryValueLabel {
    color: #c9f49a;
    font-weight: 800;
}

QSlider::groove:horizontal {
    height: 10px;
    background: #171915;
    border: 2px solid #0d0e0c;
}

QSlider::sub-page:horizontal {
    background: #6f9f52;
    border: 2px solid #0d0e0c;
}

QSlider::add-page:horizontal {
    background: #292c27;
    border: 2px solid #0d0e0c;
}

QSlider::handle:horizontal {
    width: 20px;
    margin: -7px 0;
    background: #b7e784;
    border: 3px solid #11130f;
}

QSlider::handle:horizontal:hover {
    background: #d0f4a8;
}

QSlider::tick-mark:horizontal {
    background: #8b8d84;
}

QProgressBar {
    background: #11120f;
    color: #f5f1e8;
    border: 2px solid #090a08;
    min-height: 18px;
    text-align: center;
    font-weight: 700;
}

QProgressBar::chunk {
    background: #77a957;
}

QTextEdit#LogOutput {
    background: #141613;
    color: #c9d8ba;
    font-family: Consolas;
    font-size: 10pt;
}

QScrollBar:vertical {
    background: #1b1d1a;
    width: 14px;
    border-left: 2px solid #10110f;
}

QScrollBar::handle:vertical {
    background: #51564c;
    min-height: 28px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QTableWidget, QPlainTextEdit {
    background: #20221f;
    color: #f5f1e8;
    border: 2px solid #11120f;
    gridline-color: #11120f;
    selection-background-color: #4f6d3c;
    selection-color: #ffffff;
}

QHeaderView::section {
    background: #343730;
    color: #d9e6c8;
    border: 1px solid #11120f;
    padding: 7px;
    font-weight: 800;
}

QTableWidget::item {
    padding: 5px;
}

QToolTip {
    background: #252823;
    color: #f5f1e8;
    border: 2px solid #11120f;
    padding: 5px;
}

QFrame#Sidebar[compactLayout="true"] QLabel#BrandLabel {
    font-size: 20px;
}

QPushButton#NavButton[compactLayout="true"] {
    padding: 6px 8px;
    font-size: 10.5pt;
}

QWidget#PageViewport[compactLayout="true"] QLabel#PageTitle,
QFrame#RightPanel[compactLayout="true"] QLabel#PageTitle {
    font-size: 22px;
}

QWidget#PageViewport[compactLayout="true"] QLabel#PageSubtitle {
    font-size: 10pt;
}

QFrame#RightPanel[compactLayout="true"] QLabel#ValueLabel {
    font-size: 10.5pt;
}

QFrame#RightPanel[compactLayout="true"] QLabel#CardTitle {
    font-size: 12px;
}

QFrame#RightPanel[compactLayout="true"] QPushButton {
    padding: 6px 8px;
}

QFrame#LaunchControl[compactLayout="true"] QLabel#ValueLabel {
    font-size: 10.5pt;
}
"""
