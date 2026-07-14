from PySide6.QtWidgets import QFrame


class Separator(QFrame):
    def __init__(self, color: str = "#151713", thickness: int = 3) -> None:
        super().__init__()
        self.setFixedHeight(thickness)
        self.setStyleSheet(f"QFrame {{ background-color: {color}; border: none; }}")
