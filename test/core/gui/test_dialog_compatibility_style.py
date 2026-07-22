from src.gui.style import APP_STYLE


def test_message_box_has_explicit_readable_background_and_text_colors() -> None:
    assert "QMessageBox {" in APP_STYLE
    assert "background: #f2f3ef;" in APP_STYLE
    assert "QMessageBox QLabel" in APP_STYLE
    assert "color: #171817;" in APP_STYLE


def test_compact_layout_has_smaller_navigation_and_titles() -> None:
    assert 'QPushButton#NavButton[compactLayout="true"]' in APP_STYLE
    assert 'QWidget#PageViewport[compactLayout="true"] QLabel#PageTitle' in APP_STYLE
