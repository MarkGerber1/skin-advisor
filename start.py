#!/usr/bin/env python
"""Railway entry point - starts the bot."""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from bot.main import main
import asyncio

if __name__ == "__main__":
    print("Starting bot via start.py...")
    asyncio.run(main())


