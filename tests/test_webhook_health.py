import asyncio
import os
import pytest
from aiohttp import web
from aiogram import Bot, Dispatcher
from app.webhook import create_app


@pytest.mark.asyncio
async def test_healthz(aiohttp_client):
	bot = Bot(token="TEST:TOKEN")
	dp = Dispatcher()
	app = create_app(bot, dp, secret="secret")
	client = await aiohttp_client(app)
	resp = await client.get("/healthz")
	text = await resp.text()
	assert resp.status == 200
	assert text == "ok"
