from atmosfera.entity.city import City
from atmosfera.entity.user import User
from atmosfera.entity.weather import WeatherCondition

JF = City("Juiz de Fora", -21.76, -43.35, "America/Sao_Paulo", "Minas Gerais", "Brasil")


def test_city_key_and_display():
    assert JF.key == "-21.7600,-43.3500"
    assert JF.display == "Juiz de Fora, Minas Gerais — Brasil"
    assert City.from_dict(JF.to_dict()) == JF


def test_user_favorites_rules():
    user = User("a@b.co", "Ana", "hash")
    assert user.add_city(JF) is True
    assert user.add_city(JF) is False          # sem duplicidade
    assert user.has_city(JF.key)
    assert user.remove_city(JF.key) is True
    assert user.remove_city(JF.key) is False


def test_weather_condition_texts():
    assert WeatherCondition.describe(0) == "Céu limpo"
    assert WeatherCondition.describe(95) == "Tempestade"
    assert WeatherCondition.describe(1234) == "Desconhecido"
