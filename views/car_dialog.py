"""Диалог добавления и изменения автомобиля."""
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout,
)


class CarDialog(QDialog):
    def __init__(self, parent=None, car=None, manufacturers=()):
        super().__init__(parent)
        self.setWindowTitle("Добавить автомобиль" if car is None else "Редактировать автомобиль")
        self.car_id = car["car_id"] if car is not None else None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_field = QLineEdit(car["model_name"] if car else "")
        self.manufacturer_combo = QComboBox()
        for manufacturer in manufacturers:
            self.manufacturer_combo.addItem(
                manufacturer["manufacturer_name"], manufacturer["manufacturer_id"]
            )
        if car is not None:
            index = self.manufacturer_combo.findData(car["manufacturer_id"])
            if index >= 0:
                self.manufacturer_combo.setCurrentIndex(index)
        self.price_field = QLineEdit(str(car["price"]) if car else "")
        self.year_field = QLineEdit(str(car["year_of_manufacture"]) if car else "")
        self.body_field = QLineEdit(car["body_type"] if car else "")
        self.color_field = QLineEdit((car["color"] or "") if car else "")

        form.addRow("Модель:", self.name_field)
        form.addRow("Производитель:", self.manufacturer_combo)
        form.addRow("Цена:", self.price_field)
        form.addRow("Год выпуска:", self.year_field)
        form.addRow("Тип кузова:", self.body_field)
        form.addRow("Цвет:", self.color_field)
        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def show_errors(self, errors: list[str]):
        self.error_label.setText("\n".join(errors))

    def get_values(self) -> dict:
        return {
            "model_name": self.name_field.text(),
            "price": self.price_field.text(),
            "year": self.year_field.text(),
            "body_type": self.body_field.text(),
            "manufacturer_id": self.manufacturer_combo.currentData(),
            "color": self.color_field.text().strip() or None,
        }
