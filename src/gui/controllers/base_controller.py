from PySide6.QtCore import QObject, Signal

from src.core.security.sensitive_data_redactor import SensitiveDataRedactor


class BaseController(QObject):
    status_changed = Signal(str)
    log_created = Signal(str)
    error_created = Signal(str, str)

    def _emit_error(self, title: str, error: Exception | str) -> None:
        raw_message = str(error) if isinstance(error, str) else f"{type(error).__name__}: {error}"
        message = SensitiveDataRedactor.redact_text(raw_message)
        self.log_created.emit(message)
        self.error_created.emit(title, message)
