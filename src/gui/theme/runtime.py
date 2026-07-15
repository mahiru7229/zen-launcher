from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from src.core.theme.theme_manager import ThemeManager, theme_manager


def set_theme_icon(button: QPushButton, key: str, size: int = 24) -> QPushButton:
    button.setProperty("themeIcon", str(key))
    button.setProperty("themeIconSize", int(size))
    path = theme_manager.resolve_asset(str(key))
    if path is not None:
        button.setIcon(QIcon(str(path)))
        button.setIconSize(QSize(int(size), int(size)))
    return button


def set_theme_pixmap(label: QLabel, key: str, width: int, height: int, fallback_text: str = "") -> QLabel:
    label.setProperty("themePixmap", str(key))
    label.setProperty("themePixmapWidth", int(width))
    label.setProperty("themePixmapHeight", int(height))
    label.setProperty("themeFallbackText", str(fallback_text))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    path = theme_manager.resolve_asset(str(key))
    if path is not None:
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(int(width), int(height), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            label.setText(str(fallback_text))
    else:
        label.setText(str(fallback_text))
    return label


def set_theme_static_text(widget: QLabel | QPushButton, role: str, fallback_text: str | None = None) -> QLabel | QPushButton:
    text = str(widget.text() if fallback_text is None else fallback_text)
    widget.setProperty("themeStaticTextRole", str(role))
    widget.setProperty("themeStaticTextFallback", text)
    widget.setProperty("themeStaticTextHidden", False)
    if widget.property("mcw_i18n_source_text") is None:
        widget.setProperty("mcw_i18n_source_text", text)
    return widget


class ThemeRuntime:
    STYLE_ASSETS = {
        "background.window": ("QWidget#Root", 0),
        "background.center": ("QWidget#CenterArea", 0),
        "background.sidebar": ("QFrame#Sidebar", 0),
        "background.right_panel": ("QFrame#RightPanel", 0),
        "background.launch_control": ("QFrame#LaunchControl", 0),
        "background.page.home": ('QWidget#PageViewport[themePage="home"]', 0),
        "background.page.accounts": ('QWidget#PageViewport[themePage="accounts"]', 0),
        "background.page.instances": ('QWidget#PageViewport[themePage="instances"]', 0),
        "background.page.instance_settings": ('QWidget#PageViewport[themePage="instance_settings"]', 0),
        "background.page.launcher_settings": ('QWidget#PageViewport[themePage="launcher_settings"]', 0),
        "background.page.logs": ('QWidget#PageViewport[themePage="logs"]', 0),
        "background.page.about": ('QWidget#PageViewport[themePage="about"]', 0),
        "background.dialog.mod_manager": ("QDialog#ModManagerDialog", 0),
        "background.dialog.modrinth": ("QDialog#ModrinthDialog", 0),
        "background.dialog.update": ("QDialog#UpdateDialog", 0),
        "background.dialog.message": ("QMessageBox", 0),
        "surface.microsoft_card": ('QFrame#Card[themeRole="microsoft"]', 14),
        "surface.java_card": ('QFrame#Card[themeRole="java"]', 14),
        "surface.lifecycle_card": ('QFrame#Card[themeRole="lifecycle"]', 14),
        "surface.security_card": ('QFrame#Card[themeRole="security"]', 14),
        "surface.card": ("QFrame#Card", 14),
        "surface.hero_card": ("QFrame#HeroCard", 18),
        "surface.inset": ("QFrame#InsetPanel", 12),
        "surface.table": ("QTableWidget", 10),
        "surface.table_header": ("QHeaderView::section", 8),
        "surface.log": ("QTextEdit#LogOutput", 10),
        "surface.details": ("QPlainTextEdit#DetailsOutput", 10),
        "surface.group_box": ("QGroupBox", 10),
        "surface.tab_pane": ("QTabWidget::pane", 10),
        "surface.tab": ("QTabBar::tab", 8),
        "surface.tab_hover": ("QTabBar::tab:hover", 8),
        "surface.tab_selected": ("QTabBar::tab:selected", 8),
        "surface.table_selected": ("QTableWidget::item:selected", 6),
        "surface.tooltip": ("QToolTip", 8),
        "button.default": ("QPushButton", 10),
        "button.hover": ("QPushButton:hover", 10),
        "button.pressed": ("QPushButton:pressed", 10),
        "button.disabled": ("QPushButton:disabled", 10),
        "button.primary": ("QPushButton#PrimaryButton", 14),
        "button.primary_hover": ("QPushButton#PrimaryButton:hover", 14),
        "button.primary_pressed": ("QPushButton#PrimaryButton:pressed", 14),
        "button.launch": ('QPushButton#PrimaryButton[themeRole="launch"]', 18),
        "button.launch_hover": ('QPushButton#PrimaryButton[themeRole="launch"]:hover', 18),
        "button.launch_pressed": ('QPushButton#PrimaryButton[themeRole="launch"]:pressed', 18),
        "button.launch_disabled": ('QPushButton#PrimaryButton[themeRole="launch"]:disabled', 18),
        "button.danger": ("QPushButton#DangerButton", 10),
        "button.danger_hover": ("QPushButton#DangerButton:hover", 10),
        "button.nav": ("QPushButton#NavButton", 10),
        "button.nav_hover": ("QPushButton#NavButton:hover", 10),
        "button.nav_selected": ("QPushButton#NavButton:checked", 10),
        "input.default": ("QLineEdit, QComboBox, QSpinBox", 9),
        "input.focus": ("QLineEdit:focus, QComboBox:focus, QSpinBox:focus", 9),
        "input.text_area": ("QTextEdit#ArgumentEditor", 9),
        "input.text_area_focus": ("QTextEdit#ArgumentEditor:focus", 9),
        "combo.popup": ("QComboBox QAbstractItemView", 9),
        "progress.track": ("QProgressBar", 8),
        "progress.chunk": ("QProgressBar::chunk", 7),
        "scrollbar.track": ("QScrollBar:vertical", 0),
        "scrollbar.handle": ("QScrollBar::handle:vertical", 6),
        "scrollbar.horizontal_track": ("QScrollBar:horizontal", 0),
        "scrollbar.horizontal_handle": ("QScrollBar::handle:horizontal", 6),
        "badge.status": ("QLabel#StatusBadge, QLabel#StageBadge[state=success]", 8),
        "badge.warning": ("QLabel#WarningBadge, QLabel#StageBadge[state=busy], QLabel#StageBadge[state=warning]", 8),
        "badge.locked": ("QLabel#LockedBadge", 8),
        "badge.error": ("QLabel#StageBadge[state=error]", 8),
    }

    IMAGE_ASSETS = {
        "checkbox.unchecked": "QCheckBox::indicator:unchecked",
        "checkbox.checked": "QCheckBox::indicator:checked",
        "checkbox.disabled": "QCheckBox::indicator:disabled",
        "combo.arrow": "QComboBox::down-arrow",
    }

    def __init__(self, manager: ThemeManager | None = None) -> None:
        self.manager = manager or theme_manager
        self._base_stylesheet = ""
        self._show_static_text = True

    def apply(self, root: QWidget, base_stylesheet: str, theme_id: str, show_static_text: bool = True) -> str:
        self._base_stylesheet = str(base_stylesheet)
        self._show_static_text = bool(show_static_text)
        self.manager.reload()
        self.manager.select(theme_id)
        stylesheet = self.build_stylesheet(self._base_stylesheet)
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(stylesheet)
        else:
            root.setStyleSheet(stylesheet)
        self.apply_assets(root)
        return self.manager.current.theme_id

    def reapply_assets(self, root: QWidget) -> None:
        self.apply_assets(root)

    def build_stylesheet(self, base_stylesheet: str = "") -> str:
        rules: list[str] = [str(base_stylesheet).rstrip()]
        for key, (selector, slice_size) in self.STYLE_ASSETS.items():
            path = self.manager.resolve_asset(key)
            if path is None:
                continue
            url = self._qss_url(path)
            if slice_size:
                rules.append(f'{selector} {{ border-image: url("{url}") {slice_size} {slice_size} {slice_size} {slice_size} stretch stretch; background: transparent; }}')
            else:
                rules.append(f'{selector} {{ border-image: url("{url}") 0 0 0 0 stretch stretch; background: transparent; }}')
        for key, selector in self.IMAGE_ASSETS.items():
            path = self.manager.resolve_asset(key)
            if path is not None:
                rules.append(f'{selector} {{ image: url("{self._qss_url(path)}"); }}')
        return "\n\n".join(rule for rule in rules if rule)

    def apply_assets(self, root: QWidget) -> None:
        widgets = [root, *root.findChildren(QWidget)]
        for widget in widgets:
            if isinstance(widget, QPushButton):
                self._apply_button_icon(widget)
                self._apply_static_text(widget)
            elif isinstance(widget, QLabel):
                self._apply_label_pixmap(widget)
                self._apply_static_text(widget)
        icon_path = self.manager.resolve_asset("icon.app")
        window = root.window()
        if icon_path is not None:
            window.setWindowIcon(QIcon(str(icon_path)))

    def _apply_button_icon(self, button: QPushButton) -> None:
        key = str(button.property("themeIcon") or "").strip()
        if not key:
            return
        path = self.manager.resolve_asset(key)
        if path is None:
            button.setIcon(QIcon())
            return
        size = max(1, int(button.property("themeIconSize") or 24))
        button.setIcon(QIcon(str(path)))
        button.setIconSize(QSize(size, size))

    def _apply_static_text(self, widget: QLabel | QPushButton) -> None:
        role = str(widget.property("themeStaticTextRole") or "").strip()
        if not role:
            return
        fallback_text = str(widget.property("themeStaticTextFallback") or "")
        should_hide = not self._show_static_text and self.manager.resolve_text_asset(role) is not None
        widget.setProperty("themeStaticTextHidden", should_hide)
        widget.setText("" if should_hide else fallback_text)

    def _apply_label_pixmap(self, label: QLabel) -> None:
        key = str(label.property("themePixmap") or "").strip()
        if not key:
            return
        fallback_text = str(label.property("themeFallbackText") or "")
        path = self.manager.resolve_asset(key)
        if path is None:
            label.setPixmap(QPixmap())
            label.setText(fallback_text)
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            label.setPixmap(QPixmap())
            label.setText(fallback_text)
            return
        width = max(1, int(label.property("themePixmapWidth") or pixmap.width()))
        height = max(1, int(label.property("themePixmapHeight") or pixmap.height()))
        label.setText("")
        label.setPixmap(pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    @staticmethod
    def _qss_url(path: Path) -> str:
        return path.resolve().as_posix().replace('"', '\\"')
