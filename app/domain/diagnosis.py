from collections import defaultdict


def diagnose_skin(answers: dict) -> dict:
    """
    Анализирует ответы анкеты и выносит детерминированный диагноз.
    Возвращает словарь с типом кожи, состояниями и обоснованием.
    """
    type_scores = defaultdict(int)
    state_scores = defaultdict(int)
    reasoning = []

    # Q1: Стянутость после умывания (сухость/обезвоженность)
    if answers.get("Q1") == "Q1_A1":
        type_scores["сухая"] += 2
        state_scores["обезвоженность"] += 2
        reasoning.append(
            "Ощущение стянутости после умывания указывает на недостаток влаги или липидов."
        )

    # Q2: Поведение кожи в течение дня
    if answers.get("Q2") == "Q2_A1":  # Блеск через 2-3 часа
        type_scores["жирная"] += 3
        reasoning.append(
            "Быстрое появление жирного блеска — классический признак жирной кожи."
        )
    elif answers.get("Q2") == "Q2_A2":  # Блеск к вечеру
        type_scores["нормальная"] += 1
        type_scores["комбинированная"] += 1
    elif answers.get("Q2") == "Q2_A3":  # Стянутость к обеду
        type_scores["сухая"] += 2
        state_scores["обезвоженность"] += 2
        reasoning.append(
            "Появление стянутости в течение дня говорит о нехватке увлажнения."
        )
    elif answers.get("Q2") == "Q2_A4":  # Т-зона блестит, периферия стянута
        type_scores["комбинированная"] += 3
        reasoning.append(
            "Разное поведение кожи на Т-зоне и щеках характерно для комбинированного типа."
        )

    # Q3: Расширенные поры
    if answers.get("Q3") == "Q3_A3":
        type_scores["жирная"] += 1
        state_scores["расширенные поры"] += 2
    elif answers.get("Q3") == "Q3_A4":
        type_scores["жирная"] += 2
        state_scores["расширенные поры"] += 3
        reasoning.append(
            "Выраженные поры часто связаны с повышенной активностью сальных желез."
        )

    # Q4: Шелушения
    if answers.get("Q4") == "Q4_A1":
        state_scores["обезвоженность"] += 2
        state_scores["чувствительность"] += 1
        reasoning.append(
            "Шелушения являются признаком нарушения защитного барьера и обезвоженности."
        )

    # Q5: Несовершенства (мультивыбор)
    if "Q5_A1" in answers.get("Q5", []):  # Черные точки
        state_scores["расширенные поры"] += 2
        type_scores["жирная"] += 1
        type_scores["комбинированная"] += 1
    if "Q5_A2" in answers.get("Q5", []):  # Воспаления
        state_scores["акне"] += 2
        reasoning.append(
            "Периодические воспаления требуют внимания к очищению и использованию противовоспалительных активов."
        )

    # Q6: Пигментация
    if answers.get("Q6") == "Q6_A2" or answers.get("Q6") == "Q6_A3":
        state_scores["пигментация"] += 3
        reasoning.append(
            "Наличие пигментации указывает на необходимость использования SPF и осветляющих компонентов."
        )

    # Q7: Постакне/акне
    if answers.get("Q7") == "Q7_A2" or answers.get("Q7") == "Q7_A3":
        state_scores["постакне"] += 3
        if answers.get("Q7") == "Q7_A3":
            state_scores["акне"] += 2
        reasoning.append(
            "Следы от акне (постакне) требуют активов, направленных на обновление кожи."
        )

    # Q8: Морщины
    if answers.get("Q8") == "Q8_A2" or answers.get("Q8") == "Q8_A3":
        state_scores["морщины"] += 3
        reasoning.append(
            "Наличие морщин — показание к использованию антивозрастных компонентов (пептиды, ретиноиды)."
        )

    # Q9: Область вокруг глаз (мультивыбор)
    if "Q9_A1" in answers.get("Q9", []):
        state_scores["отеки"] += 2
    if "Q9_A2" in answers.get("Q9", []):
        state_scores["темные круги"] += 2
    if "Q9_A3" in answers.get("Q9", []):
        state_scores["морщины вокруг глаз"] += 2

    # Q11: Тон и рельеф
    if answers.get("Q11") == "Q11_A2":  # Тусклая
        state_scores["тусклость"] += 2
        reasoning.append(
            "Тусклый цвет лица говорит о необходимости улучшения микроциркуляции и эксфолиации."
        )
    if answers.get("Q11") == "Q11_A3":  # Покраснения
        state_scores["чувствительность"] += 2
        state_scores["купероз"] += 1
        reasoning.append(
            "Покраснения и сосудистые звездочки требуют деликатного ухода и укрепления сосудов."
        )
    if answers.get("Q11") == "Q11_A4":  # Раздражения
        state_scores["чувствительность"] += 3
        reasoning.append(
            "Частые раздражения — признак чувствительной кожи и поврежденного барьера."
        )

    # Q12: Купероз
    if answers.get("Q12") == "Q12_A1" or answers.get("Q12") == "Q12_A2":
        state_scores["купероз"] += 3
        state_scores["чувствительность"] += 2

    # Определение типа кожи
    if type_scores["комбинированная"] >= max(type_scores.values(), default=0):
        skin_type = "комбинированная"
    elif (
        abs(type_scores["жирная"] - type_scores["сухая"]) <= 1
        and type_scores["жирная"] > 1
        and type_scores["сухая"] > 1
    ):
        skin_type = "комбинированная"
    else:
        # Убираем "комби" из сравнения, чтобы найти доминирующий тип
        if "комбинированная" in type_scores:
            del type_scores["комбинированная"]
        if not type_scores or max(type_scores.values(), default=0) == 0:
            skin_type = "нормальная"
        else:
            skin_type = max(type_scores, key=type_scores.get)

    # Определение подтона
    undertone_map = {"Q13_A1": "тёплый", "Q13_A2": "холодный", "Q13_A3": "нейтральный"}
    undertone = undertone_map.get(answers.get("Q13"), "не определен")

    # Определение колорита
    color_palette = undertone
    if undertone == "холодный" and answers.get("Q14") in [
        "Q14_A2",
        "Q14_A4",
    ]:  # Синие/серые глаза
        color_palette = "холодная гамма"
    elif undertone == "тёплый" and answers.get("Q14") in [
        "Q14_A1",
        "Q14_A5",
    ]:  # Карие/ореховые
        color_palette = "тёплая гамма"

    # Формирование итогового списка состояний
    final_states = [state for state, score in state_scores.items() if score > 0]
    if not final_states:
        final_states.append("сбалансированная")

    return {
        "skin_type": skin_type,
        "states": final_states,
        "undertone": undertone,
        "color_palette": color_palette,
        "reasoning": reasoning,
        "uses_retinoids": answers.get("Q10") == "Q10_A1",
    }

