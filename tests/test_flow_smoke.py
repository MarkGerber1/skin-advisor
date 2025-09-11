"""Дымовые тесты для flow'ов palette и skincare"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.asyncio
async def test_palette_flow_smoke():
    """Дымовой тест полного flow palette: от старта до рендера"""
    try:
        # Импортируем необходимые модули
        from bot.handlers.detailed_palette import q8_lip_color

        # Mock объекты
        mock_cb = Mock()
        mock_cb.from_user = Mock()
        mock_cb.from_user.id = 12345
        mock_cb.data = "lip:c"
        mock_cb.message = AsyncMock()

        mock_state = AsyncMock()
        mock_state.get_data.return_value = {
            "hair": "a",
            "eyes": "a",
            "undertone": "b",
            "contrast": "a",
            "sun": "c",
            "face_shape": "a",
            "makeup_style": "a",
            "lips": "a",
        }
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        # Mock внешние зависимости
        with (
            patch("bot.handlers.detailed_palette.determine_skin_type") as mock_determine,
            patch("bot.handlers.detailed_palette.UserProfile") as mock_user_profile,
            patch("bot.handlers.detailed_palette.SelectorV2") as mock_selector,
            patch("bot.handlers.detailed_palette.AnswerExpanderV2") as mock_expander,
            patch("bot.handlers.detailed_palette.save_last_json") as mock_save_json,
            patch("bot.handlers.detailed_palette.save_text_pdf") as mock_save_pdf,
            patch("bot.ui.render.render_makeup_report") as mock_render,
        ):

            # Настройка моков
            mock_determine.return_value = {
                "season": "spring",
                "undertone": "cool",
                "profile": {"season": "spring"},
            }

            mock_user_profile.return_value = Mock()
            mock_user_profile.return_value.model_dump.return_value = {"season": "spring"}

            mock_selector.return_value.select.return_value = {
                "skincare": {},
                "makeup": {"base": []},
                "compatibility_warnings": [],
                "routine_suggestions": [],
            }

            mock_expander.return_value = Mock()
            mock_expander.return_value.generate_tldr_report.return_value = "TLDR report"
            mock_expander.return_value.generate_full_report.return_value = "Full report"

            mock_render.return_value = ("Test report", Mock())

            # Запускаем тест
            await q8_lip_color(mock_cb, mock_state)

            # Проверяем, что рендер был вызван
            mock_render.assert_called_once()
            print("✅ Palette flow smoke test passed")

    except Exception as e:
        pytest.fail(f"Palette flow smoke test failed: {e}")


@pytest.mark.asyncio
async def test_skincare_flow_smoke():
    """Дымовой тест полного flow skincare: от старта до рендера"""
    try:
        # Импортируем необходимые модули
        from bot.handlers.detailed_skincare import q8_desired_effect

        # Mock объекты
        mock_cb = Mock()
        mock_cb.from_user = Mock()
        mock_cb.from_user.id = 12345
        mock_cb.data = "effect:c"
        mock_cb.message = AsyncMock()

        mock_state = AsyncMock()
        mock_state.get_data.return_value = {
            "skin_type": "combination",
            "concerns": ["pigmentation", "redness"],
            "sensitivity": "sensitive",
            "age": 25,
            "effect": "a",
        }
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        # Mock внешние зависимости
        with (
            patch("bot.handlers.detailed_skincare.determine_skin_type") as mock_determine,
            patch("bot.handlers.detailed_skincare.UserProfile") as mock_user_profile,
            patch("bot.handlers.detailed_skincare.SelectorV2") as mock_selector,
            patch("bot.handlers.detailed_skincare.AnswerExpanderV2") as mock_expander,
            patch("bot.handlers.detailed_skincare.save_last_json") as mock_save_json,
            patch("bot.handlers.detailed_skincare.save_text_pdf") as mock_save_pdf,
            patch("bot.handlers.detailed_skincare.get_user_profile_store") as mock_profile_store,
            patch("bot.ui.render.render_skincare_report") as mock_render,
        ):

            # Настройка моков
            mock_determine.return_value = {
                "type": "combination",
                "concerns": ["pigmentation", "redness"],
                "sensitivity": "sensitive",
            }

            mock_user_profile.return_value = Mock()
            mock_user_profile.return_value.model_dump.return_value = {
                "skin_type": "combination",
                "concerns": ["pigmentation", "redness"],
            }

            mock_selector.return_value.select.return_value = {
                "skincare": {"cleanser": [], "toner": []},
                "makeup": {},
                "compatibility_warnings": [],
                "routine_suggestions": [],
            }

            mock_expander.return_value = Mock()
            mock_expander.return_value.generate_tldr_report.return_value = "TLDR report"
            mock_expander.return_value.generate_full_report.return_value = "Full report"

            mock_profile_store.return_value = Mock()
            mock_profile_store.return_value.save_profile.return_value = True

            mock_render.return_value = ("Test skincare report", Mock())

            # Запускаем тест
            await q8_desired_effect(mock_cb, mock_state)

            # Проверяем, что рендер был вызван
            mock_render.assert_called_once()
            print("✅ Skincare flow smoke test passed")

    except Exception as e:
        pytest.fail(f"Skincare flow smoke test failed: {e}")


@pytest.mark.asyncio
async def test_render_fallback_smoke():
    """Тест fallback рендера при ошибке"""
    try:
        # Импортируем модули
        from bot.handlers.detailed_palette import q8_lip_color

        # Mock объекты
        mock_cb = Mock()
        mock_cb.from_user = Mock()
        mock_cb.from_user.id = 12345
        mock_cb.data = "lip:c"
        mock_cb.message = AsyncMock()

        mock_state = AsyncMock()
        mock_state.get_data.return_value = {
            "hair": "a",
            "eyes": "a",
            "undertone": "b",
            "contrast": "a",
            "sun": "c",
            "face_shape": "a",
            "makeup_style": "a",
            "lips": "a",
        }
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        # Mock с ошибкой рендера
        with (
            patch("bot.handlers.detailed_palette.determine_skin_type") as mock_determine,
            patch("bot.handlers.detailed_palette.UserProfile") as mock_user_profile,
            patch("bot.handlers.detailed_palette.SelectorV2") as mock_selector,
            patch("bot.handlers.detailed_palette.AnswerExpanderV2") as mock_expander,
            patch("bot.handlers.detailed_palette.save_last_json") as mock_save_json,
            patch("bot.handlers.detailed_palette.save_text_pdf") as mock_save_pdf,
            patch("bot.ui.render.render_makeup_report", side_effect=Exception("Render failed")),
        ):

            # Настройка моков
            mock_determine.return_value = {"season": "spring", "undertone": "cool"}
            mock_user_profile.return_value = Mock()
            mock_selector.return_value.select.return_value = {"makeup": {}}
            mock_expander.return_value = Mock()
            mock_expander.return_value.generate_tldr_report.return_value = "Report"

            # Запускаем тест - должен сработать fallback
            await q8_lip_color(mock_cb, mock_state)

            # Проверяем, что сообщение было отправлено (fallback сработал)
            mock_cb.message.edit_text.assert_called()
            print("✅ Render fallback smoke test passed")

    except Exception as e:
        pytest.fail(f"Render fallback smoke test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
