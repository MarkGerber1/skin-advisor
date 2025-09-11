#!/usr/bin/env python3
"""
Check if all required files exist and have content
"""
import os

print("=== CHECKING REQUIRED FILES ===")

required_files = [
    "bot/handlers/skincare_picker.py",
    "engine/source_resolver.py",
    "engine/analytics.py",
    "services/cart_service.py",
    "i18n/ru.py",
    "COMMITS_TO_MAKE.md",
    "push_changes.bat",
    "test_imports.py",
]

for file_path in required_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {file_path} - {size} bytes")
    else:
        print(f"❌ {file_path} - MISSING")

print("\n=== CHECK COMPLETE ===")

# Check if we have uncommitted changes by looking at file modification times
print("\n=== CHECKING FOR CHANGES ===")
import time


def get_file_age_days(filepath):
    if os.path.exists(filepath):
        return (time.time() - os.path.getmtime(filepath)) / (24 * 3600)
    return -1


recent_files = []
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith((".py", ".md", ".bat")):
            filepath = os.path.join(root, file)
            age_days = get_file_age_days(filepath)
            if age_days >= 0 and age_days < 1:  # Modified within last 24 hours
                recent_files.append((filepath, age_days))

print(f"Files modified in last 24 hours: {len(recent_files)}")
for filepath, age in recent_files[:10]:  # Show first 10
    print(".2f")

if len(recent_files) > 10:
    print(f"... and {len(recent_files) - 10} more")
