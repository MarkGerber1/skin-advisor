"""
Internationalization package for skincare chatbot.
Contains UI text constants to replace hardcoded strings.
"""

__version__ = "1.0.0"

# Ensure this package can be imported from anywhere
import os
import sys

# Add current directory to sys.path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to make ru module importable
try:
    import ru
except ImportError:
    # If ru.py exists but can't be imported, try absolute import
    ru_path = os.path.join(current_dir, 'ru.py')
    if os.path.exists(ru_path):
        # ru.py exists, try to execute it in current namespace
        with open(ru_path, 'r', encoding='utf-8') as f:
            ru_content = f.read()
        exec(ru_content, globals())

