from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pycqlog.localization import LocalizationService


class DirectoriesDialog(QDialog):
    def __init__(
        self,
        localization: LocalizationService,
        data_dir: str,
        log_dir: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._localization = localization
        self._build_ui(data_dir, log_dir)
        self._apply_initial_size()

    def _build_ui(self, data_dir: str, log_dir: str) -> None:
        self.setWindowTitle(self._localization.t("directories.title"))
        root = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.data_dir_input = QLineEdit(data_dir)
        self.data_dir_button = QPushButton(self._localization.t("settings.choose_directory"))
        self.data_dir_button.clicked.connect(self._choose_data_dir)
        data_dir_row = QHBoxLayout()
        data_dir_row.setContentsMargins(0, 0, 0, 0)
        data_dir_row.addWidget(self.data_dir_input, 1)
        data_dir_row.addWidget(self.data_dir_button)

        self.log_dir_input = QLineEdit(log_dir)
        self.log_dir_button = QPushButton(self._localization.t("settings.choose_directory"))
        self.log_dir_button.clicked.connect(self._choose_log_dir)
        log_dir_row = QHBoxLayout()
        log_dir_row.setContentsMargins(0, 0, 0, 0)
        log_dir_row.addWidget(self.log_dir_input, 1)
        log_dir_row.addWidget(self.log_dir_button)

        form_layout.addRow(QLabel(self._localization.t("settings.data_dir")), data_dir_row)
        form_layout.addRow(QLabel(self._localization.t("settings.log_dir")), log_dir_row)
        root.addLayout(form_layout)

        self.notice_label = QLabel(self._localization.t("directories.help"))
        self.notice_label.setWordWrap(True)
        root.addWidget(self.notice_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(
            self._localization.t("button.save_settings")
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
            self._localization.t("button.cancel")
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        root.addWidget(self.button_box)

    def _apply_initial_size(self) -> None:
        parent = self.parentWidget()
        preferred_width = self.sizeHint().width()
        preferred_height = max(self.sizeHint().height(), 220)
        if parent is None:
            self.resize(max(520, preferred_width), preferred_height)
            return
        target_width = max(520, int(parent.width() * 0.5))
        self.resize(target_width, preferred_height)

    def data_dir(self) -> str:
        value = self.data_dir_input.text().strip()
        return str(Path(value).expanduser()) if value else ""

    def log_dir(self) -> str:
        value = self.log_dir_input.text().strip()
        return str(Path(value).expanduser()) if value else ""

    def accept(self) -> None:
        for selected_dir, title_key, body_key in (
            (self.data_dir(), "settings.invalid_data_dir_title", "settings.invalid_data_dir_body"),
            (self.log_dir(), "settings.invalid_log_dir_title", "settings.invalid_log_dir_body"),
        ):
            if not selected_dir:
                continue
            try:
                Path(selected_dir).mkdir(parents=True, exist_ok=True)
            except OSError:
                QMessageBox.warning(
                    self,
                    self._localization.t(title_key),
                    self._localization.t(body_key),
                )
                return
        super().accept()

    def _choose_data_dir(self) -> None:
        start_dir = self.data_dir() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self,
            self._localization.t("settings.directory_dialog_title"),
            start_dir,
        )
        if chosen:
            self.data_dir_input.setText(chosen)

    def _choose_log_dir(self) -> None:
        start_dir = self.log_dir() or self.data_dir() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self,
            self._localization.t("settings.log_dir_dialog_title"),
            start_dir,
        )
        if chosen:
            self.log_dir_input.setText(chosen)
