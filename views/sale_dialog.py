"""Диалог оформления продажи автомобилей."""
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

class SaleDialog(QDialog):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.setWindowTitle("Новая продажа")
        self.resize(650, 480)
        self.controller = controller
        self.items: list[dict] = []

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.dealership_combo = QComboBox()
        for dealership in self.controller.get_dealerships():
            self.dealership_combo.addItem(
                f"{dealership['city']}, {dealership['address']}", dealership["dealership_id"]
            )
        self.dealership_combo.currentIndexChanged.connect(self._on_dealership_changed)

        self.employee_combo = QComboBox()
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Без клиента", None)
        for customer in self.controller.get_customers():
            self.customer_combo.addItem(
                f"{customer['last_name']} {customer['first_name']}",
                customer["customer_id"],
            )
        form.addRow("Автосалон:", self.dealership_combo)
        form.addRow("Сотрудник:", self.employee_combo)
        form.addRow("Клиент:", self.customer_combo)
        layout.addLayout(form)

        add_row = QHBoxLayout()
        self.car_search = QLineEdit()
        self.car_search.setPlaceholderText("Модель или производитель...")
        self.car_combo = QComboBox()
        self.qty_field = QLineEdit()
        self.qty_field.setPlaceholderText("Кол-во")
        self.qty_field.setFixedWidth(75)
        self.add_item_button = QPushButton("Добавить")
        self.car_search.textChanged.connect(self._on_car_search_changed)
        self.add_item_button.clicked.connect(self._on_add_item_clicked)
        add_row.addWidget(self.car_search)
        add_row.addWidget(self.car_combo)
        add_row.addWidget(self.qty_field)
        add_row.addWidget(self.add_item_button)
        layout.addLayout(add_row)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["Автомобиль", "Кол-во", "Цена"])
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.items_table)

        self.total_label = QLabel("Итого: 0.00")
        layout.addWidget(self.total_label)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Оформить продажу")
        buttons.accepted.connect(self._on_confirm)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_cars()
        self._on_dealership_changed()

    def _on_dealership_changed(self, *_):
        dealership_id = self.dealership_combo.currentData()
        self.employee_combo.clear()
        if dealership_id is None:
            return
        for employee in self.controller.get_employees(dealership_id):
            self.employee_combo.addItem(
                f"{employee['last_name']} {employee['first_name']}",
                employee["employee_id"],
            )

    def _load_cars(self):
        self._set_car_options(self.controller.search_cars(""))

    def _set_car_options(self, cars):
        self.car_combo.clear()
        for car in cars:
            self.car_combo.addItem(
                f"{car['manufacturer_name']} {car['model_name']} ({float(car['price']):.2f} р.)",
                (car["car_id"], car["model_name"], float(car["price"])),
            )

    def _on_car_search_changed(self, text: str):
        self._set_car_options(self.controller.search_cars(text))

    def _on_add_item_clicked(self):
        data = self.car_combo.currentData()
        if data is None:
            self.error_label.setText("Выберите автомобиль")
            return
        car_id, model_name, price = data
        try:
            quantity = int(self.qty_field.text())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            self.error_label.setText("Количество должно быть положительным целым числом")
            return

        existing = next((item for item in self.items if item["car_id"] == car_id), None)
        if existing:
            existing["quantity"] += quantity
        else:
            self.items.append({
                "car_id": car_id,
                "model_name": model_name,
                "quantity": quantity,
                "price": price,
            })
        self.error_label.clear()
        self._refresh_items_table()
        self.qty_field.clear()

    def _refresh_items_table(self):
        self.items_table.setRowCount(len(self.items))
        total = 0
        for row, item in enumerate(self.items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item["model_name"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            total += item["quantity"] * item["price"]
        self.total_label.setText(f"Итого: {total:.2f}")

    def _on_confirm(self):
        _, errors = self.controller.create_sale(
            self.dealership_combo.currentData(),
            self.employee_combo.currentData(),
            self.customer_combo.currentData(),
            self.items,
        )
        if errors:
            self.error_label.setText("\n".join(errors))
            return
        self.accept()
