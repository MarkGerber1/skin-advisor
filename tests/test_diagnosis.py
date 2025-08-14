from app.domain.diagnosis import diagnose_skin


def test_diagnose_dry_skin():
    """Тест для определения сухой, чувствительной кожи с пигментацией."""
    answers = {
        "Q1": "Q1_A1",  # Стянутость -> сухость
        "Q2": "Q2_A3",  # Стянутость днем -> сухость, обезвоженность
        "Q3": "Q3_A1",  # Поры незаметны
        "Q4": "Q4_A1",  # Шелушения -> обезвоженность, чувствительность
        "Q6": "Q6_A2",  # Пигментация
        "Q11": "Q11_A4",  # Раздражения -> чувствительность
        "Q13": "Q13_A2",  # Холодный подтон
    }
    result = diagnose_skin(answers)
    assert result["skin_type"] in ["сухая", "комбинированная", "нормальная"]
    assert "обезвоженность" in result["states"]
    assert "чувствительность" in result["states"]
    assert "пигментация" in result["states"]


def test_diagnose_oily_skin_acne():
    """Тест для определения жирной кожи с акне и расширенными порами."""
    answers = {
        "Q1": "Q1_A2",  # Нет стянутости
        "Q2": "Q2_A1",  # Блеск через 2-3 часа -> жирная
        "Q3": "Q3_A4",  # Сильно выражены поры -> жирная, расширенные поры
        "Q5": ["Q5_A1", "Q5_A2"],  # Черные точки и воспаления -> поры, акне
        "Q7": "Q7_A3",  # Постакне/акне по всей поверхности
        "Q13": "Q13_A3",  # Нейтральный подтон
    }
    result = diagnose_skin(answers)
    assert result["skin_type"] in ["жирная", "комбинированная"]
    assert "расширенные поры" in result["states"]
    assert "акне" in result["states"]
    assert "постакне" in result["states"]

