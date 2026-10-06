"""Главное окно приложения «Автосалон» (слой представления PyQt6).

Окно не создаёт контроллеры сами: они передаются в конструктор (внедрение зависимостей),
сборка выполняется в composition.py.
"""
import csv
import logging

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from exceptions import ApplicationError
from views.car_dialog import CarDialog
from views.sale_dialog import SaleDialog

CAR_ID_ROLE = 1000
logger = logging.getLogger("autosalon.view")


class MainWindow(QMainWindow):
    def __init__(self, car_controller, sale_controller, stock_controller,
                 report_controller, backup_controller):
        super().__init__()
        self.setWindowTitle("Автосалон")
        self.resize(900, 580)

        self.car_controller = car_controller
        self.sale_controller = sale_controller
        self.stock_controller = stock_controller
        self.report_controller = report_controller
        self.backup_controller = backup_controller

        self._build_database_menu()

        tabs = QTabWidget()
        tabs.addTab(self._build_cars_tab(), "Автомобили")
        tabs.addTab(self._build_sales_tab(), "Продажи")
        tabs.addTab(self._build_stock_tab(), "Остатки")
        tabs.addTab(self._build_reports_tab(), "Отчёты")
        self.setCentralWidget(tabs)

        self._reload_all()

    def _reload_all(self):
        self._load_cars()
        self._load_sales()
        self._load_stock()
        self._run_report()

    # ------------------------------------------------------------ меню «База данных»
    def _build_database_menu(self):
        menu = self.menuBar().addMenu("База данных")
        backup_action = menu.addAction("Создать резервную копию...")
        backup_action.triggered.connect(self._create_database_backup)
        restore_action = menu.addAction("Восстановить из копии...")
        restore_action.triggered.connect(self._restore_database_backup)

    def _create_database_backup(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Создать резервную копию", "AutoSalon_backup.db", "SQLite DB (*.db)"
        )
        if not path:
            return
        backup_path, error = self.backup_controller.create_backup(path)
        if error:
            QMessageBox.critical(self, "Ошибка резервного копирования", error)
            return
        QMessageBox.information(
            self, "Резервная копия", f"Копия базы данных сохранена:\n{backup_path}"
        )

    def _restore_database_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать резервную копию", "", "SQLite DB (*.db)"
        )
        if not path:
            return
        answer = QMessageBox.warning(
            self,
            "Подтверждение восстановления",
            "Текущие данные будут заменены данными выбранной копии. Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        success, error = self.backup_controller.restore_backup(path)
        if not success:
            QMessageBox.critical(self, "Ошибка восстановления", error)
            return
        self._reload_all()
        QMessageBox.information(self, "Восстановление", "База данных восстановлена.")

    # ------------------------------------------------------------ вкладка «Автомобили»
    def _build_cars_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        search_row = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Поиск по модели или производителю...")
        self.search_field.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.search_field)
        layout.addLayout(search_row)

        self.cars_table = QTableWidget()
        self.cars_table.setColumnCount(5)
        self.cars_table.setHorizontalHeaderLabels(
            ["Модель", "Производитель", "Цена", "Тип кузова", "Год"]
        )
        self.cars_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cars_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cars_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cars_table.doubleClicked.connect(self._on_car_double_clicked)
        layout.addWidget(self.cars_table)

        buttons_row = QHBoxLayout()
        self.add_button = QPushButton("Добавить")
        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.add_button.clicked.connect(self._on_add_clicked)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        buttons_row.addWidget(self.add_button)
        buttons_row.addWidget(self.edit_button)
        buttons_row.addWidget(self.delete_button)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)

        widget.setLayout(layout)
        return widget

    def _load_cars(self, cars=None):
        if cars is None:
            cars = self._safe(self.car_controller.get_all_cars, default=[])
        self.cars_table.setRowCount(len(cars))
        for row, car in enumerate(cars):
            self.cars_table.setItem(row, 0, QTableWidgetItem(car["model_name"]))
            self.cars_table.setItem(row, 1, QTableWidgetItem(car["manufacturer_name"]))
            self.cars_table.setItem(row, 2, QTableWidgetItem(f"{car['price']:,.2f}".replace(",", " ")))
            self.cars_table.setItem(row, 3, QTableWidgetItem(car["body_type"]))
            self.cars_table.setItem(row, 4, QTableWidgetItem(str(car["year_of_manufacture"])))
            self.cars_table.item(row, 0).setData(CAR_ID_ROLE, car["car_id"])

    def _selected_car_id(self):
        rows = self.cars_table.selectionModel().selectedRows()
        if not rows:
            return None
        return self.cars_table.item(rows[0].row(), 0).data(CAR_ID_ROLE)

    def _on_search_changed(self, text: str):
        found = self._safe(lambda: self.car_controller.search_cars(text), default=[])
        self._load_cars(found)

    def _on_add_clicked(self):
        dialog = CarDialog(self, manufacturers=self.car_controller.get_manufacturers())
        while dialog.exec():
            _, errors = self.car_controller.add_car(**dialog.get_values())
            if errors:
                dialog.show_errors(errors)
                continue
            self._load_cars()
            break

    def _on_edit_clicked(self):
        car_id = self._selected_car_id()
        if car_id is None:
            QMessageBox.warning(self, "Изменение", "Сначала выберите автомобиль в таблице.")
            return
        self._open_edit_dialog(car_id)

    def _on_car_double_clicked(self, index):
        car_id = self.cars_table.item(index.row(), 0).data(CAR_ID_ROLE)
        self._open_edit_dialog(car_id)

    def _open_edit_dialog(self, car_id: int):
        car = self.car_controller.get_car_by_id(car_id)
        if car is None:
            QMessageBox.warning(self, "Изменение", "Автомобиль не найден.")
            self._load_cars()
            return
        dialog = CarDialog(self, car=car, manufacturers=self.car_controller.get_manufacturers())
        while dialog.exec():
            success, errors = self.car_controller.update_car(car_id, **dialog.get_values())
            if errors:
                dialog.show_errors(errors)
                continue
            if success:
                self._load_cars()
            break

    def _on_delete_clicked(self):
        car_id = self._selected_car_id()
        if car_id is None:
            QMessageBox.warning(self, "Удаление", "Сначала выберите автомобиль в таблице.")
            return

        row = self.cars_table.selectionModel().selectedRows()[0].row()
        model_name = self.cars_table.item(row, 0).text()

        confirm = QMessageBox.question(self, "Подтверждение", f"Удалить автомобиль «{model_name}»?")
        if confirm != QMessageBox.StandardButton.Yes:
            return

        success, message = self.car_controller.delete_car(car_id)
        if success:
            self._load_cars()
        else:
            QMessageBox.critical(self, "Ошибка", message)

    # ------------------------------------------------------------ вкладка «Продажи»
    def _build_sales_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(5)
        self.sales_table.setHorizontalHeaderLabels(["№", "Дата", "Город", "Сотрудник", "Сумма"])
        self.sales_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.sales_table)

        buttons_row = QHBoxLayout()
        self.new_sale_button = QPushButton("Новая продажа")
        self.new_sale_button.clicked.connect(self._on_new_sale_clicked)
        buttons_row.addWidget(self.new_sale_button)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)
        return widget

    def _load_sales(self):
        sales = self._safe(self.sale_controller.get_sale_history, default=[])
        self.sales_table.setRowCount(len(sales))
        for row, sale in enumerate(sales):
            self.sales_table.setItem(row, 0, QTableWidgetItem(str(sale["sale_id"])))
            self.sales_table.setItem(row, 1, QTableWidgetItem(str(sale["sale_date"])))
            self.sales_table.setItem(row, 2, QTableWidgetItem(sale["city"]))
            self.sales_table.setItem(row, 3, QTableWidgetItem(sale["employee_last_name"]))
            self.sales_table.setItem(row, 4, QTableWidgetItem(f"{sale['total_amount']:.2f}"))

    def _on_new_sale_clicked(self):
        dialog = SaleDialog(self, controller=self.sale_controller)
        if dialog.exec():
            self._load_sales()
            self._load_stock()
            self._load_cars()

    # ------------------------------------------------------------ вкладка «Остатки»
    def _build_stock_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Автосалон:"))
        self.stock_dealership_combo = QComboBox()
        for dealership in self.stock_controller.get_dealerships():
            self.stock_dealership_combo.addItem(
                f"{dealership['city']}, {dealership['address']}", dealership["dealership_id"]
            )
        self.stock_dealership_combo.currentIndexChanged.connect(self._load_stock)
        top_row.addWidget(self.stock_dealership_combo)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(2)
        self.stock_table.setHorizontalHeaderLabels(["Автомобиль", "Остаток"])
        self.stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.stock_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.stock_table)
        return widget

    def _load_stock(self, *_):
        dealership_id = self.stock_dealership_combo.currentData()
        stock = self._safe(lambda: self.stock_controller.get_stock(dealership_id), default=[])
        self.stock_table.setRowCount(len(stock))
        for row, item in enumerate(stock):
            self.stock_table.setItem(row, 0, QTableWidgetItem(item["model_name"]))
            self.stock_table.setItem(row, 1, QTableWidgetItem(str(item["car_count"])))

    # ------------------------------------------------------------ вкладка «Отчёты»
    def _build_reports_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        filters = QHBoxLayout()

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("Продажи за период", "sales")
        self.report_type_combo.addItem("Автомобили по производителям", "manufacturers")
        self.report_type_combo.addItem("Остатки автосалона", "stock")
        self.report_type_combo.currentIndexChanged.connect(self._on_report_type_changed)
        filters.addWidget(self.report_type_combo)

        self.report_from_date = QDateEdit()
        self.report_from_date.setCalendarPopup(True)
        self.report_from_date.setDate(QDate(2000, 1, 1))
        self.report_to_date = QDateEdit()
        self.report_to_date.setCalendarPopup(True)
        self.report_to_date.setDate(QDate.currentDate())
        filters.addWidget(QLabel("С:"))
        filters.addWidget(self.report_from_date)
        filters.addWidget(QLabel("По:"))
        filters.addWidget(self.report_to_date)

        self.report_dealership_combo = QComboBox()
        for dealership in self.report_controller.get_dealerships():
            self.report_dealership_combo.addItem(
                f"{dealership['city']}, {dealership['address']}", dealership["dealership_id"]
            )
        filters.addWidget(self.report_dealership_combo)

        self.run_report_button = QPushButton("Сформировать")
        self.run_report_button.clicked.connect(self._run_report)
        filters.addWidget(self.run_report_button)
        self.export_report_button = QPushButton("Экспорт CSV")
        self.export_report_button.clicked.connect(self._export_report)
        filters.addWidget(self.export_report_button)
        filters.addStretch()
        layout.addLayout(filters)

        self.report_table = QTableWidget()
        self.report_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.report_table)
        self._on_report_type_changed()
        return widget

    def _on_report_type_changed(self, *_):
        report_type = self.report_type_combo.currentData()
        show_dates = report_type == "sales"
        for date_widget in (self.report_from_date, self.report_to_date):
            date_widget.setVisible(show_dates)
        self.report_dealership_combo.setVisible(report_type == "stock")
        if hasattr(self, "report_table"):
            self._run_report()

    def _run_report(self, *_):
        report_type = self.report_type_combo.currentData()
        try:
            if report_type == "sales":
                headers = ["Дата", "Количество продаж", "Продано автомобилей", "Выручка"]
                rows = self.report_controller.sales_by_period(
                    self.report_from_date.date().toString("yyyy-MM-dd"),
                    self.report_to_date.date().toString("yyyy-MM-dd"),
                )
            elif report_type == "manufacturers":
                headers = ["Производитель", "Автомобилей", "Средняя цена"]
                rows = self.report_controller.cars_by_manufacturer()
            else:
                headers = ["Автомобиль", "Тип кузова", "Остаток", "Стоимость остатка"]
                rows = self.report_controller.stock_by_dealership(
                    self.report_dealership_combo.currentData()
                )
        except ApplicationError as error:
            QMessageBox.warning(self, "Параметры отчёта", str(error))
            return

        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(len(rows))
        for row_index, report_row in enumerate(rows):
            for column_index, value in enumerate(report_row):
                text = "" if value is None else str(value)
                self.report_table.setItem(row_index, column_index, QTableWidgetItem(text))

    def _export_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт отчёта", "report.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow([
                    self.report_table.horizontalHeaderItem(column).text()
                    for column in range(self.report_table.columnCount())
                ])
                for row in range(self.report_table.rowCount()):
                    writer.writerow([
                        self.report_table.item(row, column).text()
                        if self.report_table.item(row, column) else ""
                        for column in range(self.report_table.columnCount())
                    ])
        except OSError as error:
            logger.error("Ошибка экспорта CSV: %s", error)
            QMessageBox.critical(self, "Ошибка экспорта", str(error))
            return
        logger.info("Отчёт выгружен в CSV: %s", path)

    # ------------------------------------------------------------ вспомогательное
    def _safe(self, action, default):
        """Выполняет чтение данных; ошибки слоя данных показывает пользователю."""
        try:
            return action()
        except ApplicationError as error:
            logger.error("Ошибка чтения данных: %s", error)
            QMessageBox.critical(self, "Ошибка данных", str(error))
            return default
