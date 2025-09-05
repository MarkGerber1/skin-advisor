#!/usr/bin/env python3
"""Test A/B testing system"""

import sys
import os

# Test A/B framework
try:
    from engine.ab_testing import get_ab_testing_framework, setup_default_ab_tests

    print("🧪 Testing A/B Framework...")

    # Setup tests
    setup_default_ab_tests()
    framework = get_ab_testing_framework()

    # Test user assignment
    test_user = 12345
    test_name = framework.get_test_name_variant(test_user)
    category_order = framework.get_category_order_variant(test_user)

    print(f"✅ Test name for user {test_user}: {test_name}")
    print(f"✅ Category order: {category_order}")

    # Test logging
    framework.log_button_click(test_user, "test_name_experiment", 7)
    framework.log_add_to_cart(test_user, "test_name_experiment", 2)

    print("✅ A/B logging test passed")
    print("📊 Check data/ab_tests/conversion_metrics.csv for results")

except Exception as e:
    print(f"❌ A/B test failed: {e}")
    sys.exit(1)

print("🎉 A/B testing system ready!")

