#!/usr/bin/env python3
# ========================================
# ФАЙЛ: test_kie_api.py
# НАЗНАЧЕНИЕ: Тесты для KIE.AI NANO BANANA API
# ВЕРСИЯ: 2.0 (2025-12-23) - ONLY NANO BANANA
# ========================================

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class TestNanoBananaApi:
    """
    Тесты для Nano Banana API через Kie.ai.
    """

    def __init__(self):
        """Initialize test suite."""
        self.api_key = os.getenv('KIE_API_KEY')
        self.passed = 0
        self.failed = 0

    def print_header(self, title: str) -> None:
        """Print test header."""
        print("\n" + "="*70)
        print(f"🦧 {title}")
        print("="*70)

    def print_success(self, msg: str) -> None:
        """Print success message."""
        print(f"✅ {msg}")
        self.passed += 1

    def print_error(self, msg: str) -> None:
        """Print error message."""
        print(f"❌ {msg}")
        self.failed += 1

    def print_info(self, msg: str) -> None:
        """Print info message."""
        print(f"ℹ️  {msg}")

    # ===== TEST 1: Check API Key =====
    def test_api_key(self) -> bool:
        """Check if API key is configured."""
        self.print_header("Test 1: API Key Configuration")

        if not self.api_key:
            self.print_error(
                "KIE_API_KEY not configured in .env\n"
                "   Get it from: https://kie.ai/account"
            )
            return False

        self.print_success(f"API key found: {self.api_key[:20]}...")
        return True

    # ===== TEST 2: Import modules =====
    def test_imports(self) -> bool:
        """Test if all required modules can be imported."""
        self.print_header("Test 2: Module Imports")

        try:
            from services.kie_api import (
                generate_interior_with_nano_banana,
                clear_space_with_kie,
                check_kie_api_health,
            )
            self.print_success("All Nano Banana modules imported successfully")
            return True

        except ImportError as e:
            self.print_error(f"Import error: {e}")
            return False

        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            return False

    # ===== TEST 3: Config validation =====
    def test_config(self) -> bool:
        """Test configuration module."""
        self.print_header("Test 3: Config Validation")

        try:
            from config_kie import config_kie

            self.print_info(f"USE_KIE_API: {config_kie.USE_KIE_API}")
            self.print_info(f"Base URL: {config_kie.KIE_API_BASE_URL}")
            self.print_info(f"Format: {config_kie.KIE_NANO_BANANA_FORMAT}")
            self.print_info(f"Size: {config_kie.KIE_NANO_BANANA_SIZE}")

            if not config_kie.validate():
                self.print_error("Configuration validation failed")
                return False

            self.print_success("Configuration is valid")
            return True

        except Exception as e:
            self.print_error(f"Config error: {e}")
            return False

    # ===== TEST 4: Check API connectivity =====
    async def test_api_connectivity(self) -> bool:
        """Test API connectivity."""
        self.print_header("Test 4: API Connectivity (Async)")

        try:
            from config_kie import config_kie

            if not config_kie.USE_KIE_API:
                self.print_info(
                    "USE_KIE_API=False, skipping API connectivity test.\n"
                    "   Set USE_KIE_API=True in .env to test."
                )
                return True

            from services.kie_api import check_kie_api_health
            
            self.print_info("Connecting to Kie.ai API...")
            is_healthy = await check_kie_api_health()
            
            if not is_healthy:
                self.print_error("API health check failed")
                return False

            self.print_success("Connected to Kie.ai API (health check passed)")
            return True

        except Exception as e:
            self.print_error(f"API connectivity error: {e}")
            return False

    # ===== TEST 5: Check credits =====
    async def test_credits(self) -> bool:
        """Test credit balance check."""
        self.print_header("Test 5: Check Credits (Async)")

        try:
            from config_kie import config_kie

            if not config_kie.USE_KIE_API:
                self.print_info("USE_KIE_API=False, skipping credits test.")
                return True

            from services.kie_api import KieApiClient
            
            client = KieApiClient()
            credits = await client.check_credits()

            if credits is None:
                self.print_error("Could not retrieve credits")
                return False

            if credits <= 0:
                self.print_error(f"Insufficient credits: {credits}")
                return False

            self.print_success(f"Credits available: {credits}")
            return True

        except Exception as e:
            self.print_error(f"Credits check error: {e}")
            return False

    # ===== TEST 6: Test Nano Banana function =====
    def test_nano_banana_function(self) -> bool:
        """Test that Nano Banana function exists and is callable."""
        self.print_header("Test 6: Nano Banana Integration Function")

        try:
            from services.kie_api import generate_interior_with_nano_banana

            if not callable(generate_interior_with_nano_banana):
                self.print_error("generate_interior_with_nano_banana is not callable")
                return False
            
            self.print_success("generate_interior_with_nano_banana is callable")
            return True

        except Exception as e:
            self.print_error(f"Function check error: {e}")
            return False

    # ===== TEST 7: Test telegram file URL function =====
    async def test_telegram_file_url(self) -> bool:
        """Test telegram file URL retrieval."""
        self.print_header("Test 7: Telegram File URL (Async)")

        try:
            from services.kie_api import get_telegram_file_url

            bot_token = os.getenv('BOT_TOKEN')
            if not bot_token:
                self.print_info("BOT_TOKEN not set, skipping telegram file test.")
                return True

            test_file_id = os.getenv('TEST_FILE_ID')
            if not test_file_id:
                self.print_info(
                    "TEST_FILE_ID not set.\n"
                    "   To test: set TEST_FILE_ID=your_photo_file_id in .env"
                )
                return True

            self.print_info(f"Testing with file_id: {test_file_id[:20]}...")
            url = await get_telegram_file_url(test_file_id, bot_token)

            if not url:
                self.print_error("Failed to get file URL")
                return False

            self.print_success(f"Got URL: {url[:50]}...")
            return True

        except Exception as e:
            self.print_error(f"Telegram file URL error: {e}")
            return False

    # ===== SUMMARY =====
    def print_summary(self) -> None:
        """Print test summary."""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "="*70)
        print(f"📊 TEST SUMMARY")
        print("="*70)
        print(f"Total: {total}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Success Rate: {percentage:.1f}%")
        print("="*70)

        if self.failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Please review the output above.")

    async def run_all_tests(self) -> None:
        """Run all tests."""
        print("\n" + "#"*70)
        print("# NANO BANANA API INTEGRATION TEST SUITE")
        print("# Version 2.0 (2025-12-23) - ONLY NANO BANANA")
        print("#"*70)

        # Sync tests
        self.test_api_key()
        self.test_imports()
        self.test_config()
        self.test_nano_banana_function()

        # Async tests
        await self.test_api_connectivity()
        await self.test_credits()
        await self.test_telegram_file_url()

        # Summary
        self.print_summary()


async def main():
    """Main entry point."""
    tester = TestNanoBananaApi()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

    print("\n" + "#"*70)
    print("# NEXT STEPS")
    print("#"*70)
    print("""
1. If all tests passed:
   ✓ Отправьте данные в handlers/creation.py
   ✓ Установите USE_KIE_API=True в .env
   ✓ Перезагрузите бот: sudo systemctl restart interior-bot

2. If some tests failed:
   ✓ Проверьте .env конфигурацию
   ✓ Проверьте, что KIE_API_KEY корректен
   ✓ Обеспечите достаточно кредитов: https://kie.ai/account

3. Для дебаггинга:
   $ export KIE_VERBOSE=True
   $ python test_kie_api.py
""")
    print("#"*70)
