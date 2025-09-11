"""
Модуль для сохранения и загрузки профилей пользователей
"""

import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

from engine.models import UserProfile


class UserProfileStore:
    """Хранилище профилей пользователей"""

    def __init__(self, storage_path: str = "data/user_profiles"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _get_profile_path(self, user_id: int) -> str:
        """Получить путь к файлу профиля пользователя"""
        return os.path.join(self.storage_path, f"user_{user_id}.json")

    def save_profile(
        self, user_id: int, profile_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Сохранить профиль пользователя"""
        try:
            # Нормализуем данные профиля
            normalized_data = {
                "user_id": user_id,
                "skin_type": profile_data.get("skin_type", "normal"),
                "concerns": profile_data.get("concerns", []),
                "sensitivity": profile_data.get("sensitivity", "normal"),
                "season": profile_data.get("season", "spring"),
                "undertone": profile_data.get("undertone", "neutral"),
                "contrast": profile_data.get("contrast", "medium"),
                "saved_at": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            profile_path = self._get_profile_path(user_id)
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(normalized_data, f, ensure_ascii=False, indent=2)

            print(f"✅ Profile saved for user {user_id}")
            return True

        except Exception as e:
            print(f"❌ Error saving profile for user {user_id}: {e}")
            return False

    def load_profile(self, user_id: int) -> Optional[UserProfile]:
        """Загрузить профиль пользователя"""
        try:
            profile_path = self._get_profile_path(user_id)

            if not os.path.exists(profile_path):
                print(f"⚠️ Profile not found for user {user_id}")
                return None

            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            # Создаем профиль из сохраненных данных
            profile = UserProfile(
                user_id=profile_data["user_id"],
                skin_type=profile_data["skin_type"],
                concerns=profile_data["concerns"],
                season=profile_data.get("season", "spring"),
                undertone=profile_data.get("undertone", "neutral"),
                contrast=profile_data.get("contrast", "medium"),
            )

            print(f"✅ Profile loaded for user {user_id}: skin_type={profile.skin_type}")
            return profile

        except Exception as e:
            print(f"❌ Error loading profile for user {user_id}: {e}")
            return None

    def delete_profile(self, user_id: int) -> bool:
        """Удалить профиль пользователя"""
        try:
            profile_path = self._get_profile_path(user_id)

            if os.path.exists(profile_path):
                os.remove(profile_path)
                print(f"🗑️ Profile deleted for user {user_id}")
                return True

            return False

        except Exception as e:
            print(f"❌ Error deleting profile for user {user_id}: {e}")
            return False


# Глобальный экземпляр хранилища профилей
_profile_store = None


def get_user_profile_store() -> UserProfileStore:
    """Получить глобальный экземпляр хранилища профилей"""
    global _profile_store
    if _profile_store is None:
        _profile_store = UserProfileStore()
    return _profile_store
