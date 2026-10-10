import pytest
from exceptions import ValidationError
from services.sale_service import SaleService


class FakeRepo:
    def __init__(self, error=None):
        self.error = error

    def create_sale(self, *args):
        if self.error:
            raise self.error
        return 77


ITEMS = [{"car_id": 1, "quantity": 1, "price": 100}]


def error_text(exc_info):
    return str(exc_info.value) + repr(exc_info.value.args)


def test_sale_requires_dealership():
    with pytest.raises(ValidationError) as exc:
        SaleService(FakeRepo()).create_sale(None, 1, None, ITEMS)
    assert "автосалон" in error_text(exc)


def test_sale_requires_employee():
    with pytest.raises(ValidationError) as exc:
        SaleService(FakeRepo()).create_sale(1, None, None, ITEMS)
    assert "сотрудника" in error_text(exc)


def test_sale_requires_items():
    with pytest.raises(ValidationError) as exc:
        SaleService(FakeRepo()).create_sale(1, 1, None, [])
    assert "хотя бы один" in error_text(exc)


def test_sale_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        SaleService(FakeRepo()).create_sale(
            1, 1, None, [{"car_id": 1, "quantity": 0, "price": 100}])


def test_sale_propagates_repository_error():
    # сервис не глотает ошибки слоя данных (например, нехватку остатка)
    with pytest.raises(RuntimeError):
        SaleService(FakeRepo(RuntimeError("Недостаточно автомобилей"))).create_sale(
            1, 1, None, ITEMS)


def test_sale_success():
    assert SaleService(FakeRepo()).create_sale(1, 1, None, ITEMS) == 77
