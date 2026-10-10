import pytest

from exceptions import ValidationError
from services.car_service import CarService


class FakeRepo:
    def __init__(self):
        self.calls = []

    def add_car(self, **kwargs):
        self.calls.append(("add", kwargs))
        return 100

    def update_car(self, car_id, **kwargs):
        self.calls.append(("update", car_id, kwargs))
        return True


def service():
    repo = FakeRepo()
    return CarService(repo), repo


def valid():
    return {
        "model_name": "Camry",
        "price": 32000,
        "year": 2023,
        "body_type": "Седан",
        "manufacturer_id": 1,
        "color": "Белый",
    }


def error_text(exc_info):
    """Текст ошибки независимо от того, строка в ValidationError или список."""
    return str(exc_info.value) + repr(exc_info.value.args)


def test_add_valid_car():
    s, repo = service()
    assert s.add_car(**valid()) == 100
    assert repo.calls[0][0] == "add"
    assert repo.calls[0][1]["model_name"] == "Camry"


def test_reject_empty_name():
    s, repo = service()
    data = valid()
    data["model_name"] = " "
    with pytest.raises(ValidationError) as exc:
        s.add_car(**data)
    assert "Название" in error_text(exc)
    assert repo.calls == []


def test_reject_non_positive_price():
    s, _ = service()
    data = valid()
    data["price"] = 0
    with pytest.raises(ValidationError) as exc:
        s.add_car(**data)
    assert "Цена" in error_text(exc)


def test_reject_invalid_year():
    s, _ = service()
    data = valid()
    data["year"] = 1800
    with pytest.raises(ValidationError) as exc:
        s.add_car(**data)
    assert "Год выпуска" in error_text(exc)


def test_reject_missing_manufacturer():
    s, _ = service()
    data = valid()
    data["manufacturer_id"] = None
    with pytest.raises(ValidationError) as exc:
        s.add_car(**data)
    assert "производител" in error_text(exc)


def test_update_valid_car():
    s, repo = service()
    assert s.update_car(1, **valid()) is True
    assert repo.calls[0][:2] == ("update", 1)
