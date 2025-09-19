# REPORT_CART_FIX

## Overview
- Unified cart router based on `services.cart_store` with consistent qty/quantity synchronisation.
- Updated callbacks to `cart:add:<product_id>:<variant_id>` across handlers and UI renderers.
- Checkout view now produces sanitized summary and highlights currency conflicts.
- Recommendations buttons forward to cart handlers, avoiding duplicate store logic.

## Analytics Funnel
- `cart_opened`
- `cart_item_added`
- `cart_qty_changed`
- `cart_item_removed`
- `cart_cleared`
- `checkout_started`
- `checkout_links_generated`

## QA Notes
- Test command: `pytest tests/test_cart.py`
- Verified mixed-currency warning text rendered via `_compose_cart_view`.
- Debounce delays guard rapid callbacks; adjust `_DEBOUNCE_SECONDS` if UX requires.

## Follow-up
- Hook the new cart badge counter into the main UI flow.
- Capture live analytics post-deploy to validate funnel integrity.
