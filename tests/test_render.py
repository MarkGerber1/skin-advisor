from app.ui.messages import render_item_text

def test_render_with_price():
	item = {"brand": "Brand", "name": "Name", "_stock": {"price": 2990.0}}
	txt = render_item_text(item)
	assert "Brand Name" in txt and "≈" in txt and "2 990" in txt

def test_render_without_price():
	item = {"brand": "Brand", "name": "Name", "_stock": {}}
	txt = render_item_text(item)
	assert "Цена на странице магазина" in txt

