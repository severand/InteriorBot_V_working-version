#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Аргос Транлейт - Загрузка языковых моделей

Этот скрипт загружает модели перевода русский -> английский
Для работы нужен интернет (скачивает ~600MB)

Использование:
    python download_models.py
"""

import sys
import time
from argostranslate import package

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_step(num, text):
    print(f"\n{num}️⃣  {text}")

def print_success(text):
    print(f"   ✅ {text}")

def print_error(text):
    print(f"   ❌ {text}")

def print_info(text):
    print(f"   ℹ️  {text}")

if __name__ == "__main__":
    print_header("🌐 ARGOS TRANSLATE - LANGUAGE MODELS INSTALLER")
    
    try:
        print_step(1, "Updating package index...")
        print_info("Checking available models (may take 30 seconds)...")
        
        package.update_package_index()
        available_packages = package.get_available_packages()
        
        print_success(f"Found {len(available_packages)} available packages")
        
        # Ищем Russian -> English модель
        print_step(2, "Looking for Russian → English model...")
        
        ru_to_en = None
        en_to_ru = None
        
        for pkg in available_packages:
            if pkg.from_code == "ru" and pkg.to_code == "en":
                ru_to_en = pkg
                print_info(f"Found: {pkg.from_code} → {pkg.to_code} (v{pkg.version})")
            elif pkg.from_code == "en" and pkg.to_code == "ru":
                en_to_ru = pkg
                print_info(f"Found: {pkg.from_code} → {pkg.to_code} (v{pkg.version})")
        
        if not ru_to_en:
            print_error("Russian → English model not found!")
            sys.exit(1)
        
        # Загружаем Russian -> English
        print_step(3, "Installing Russian → English model...")
        print_info("This may take 5-10 minutes (downloading ~300MB)...")
        
        start_time = time.time()
        package.install_from_pkg(ru_to_en)
        elapsed = time.time() - start_time
        
        print_success(f"Russian → English installed (took {elapsed:.1f}s)")
        
        # Загружаем English -> Russian (опционально)
        if en_to_ru:
            print_step(4, "Installing English → Russian model...")
            print_info("This may take 5-10 minutes (downloading ~300MB)...")
            
            start_time = time.time()
            package.install_from_pkg(en_to_ru)
            elapsed = time.time() - start_time
            
            print_success(f"English → Russian installed (took {elapsed:.1f}s)")
        
        # Проверяем что установилось
        print_step(5, "Verifying installed models...")
        
        installed = package.get_installed_languages()
        
        if not installed:
            print_error("No models installed!")
            sys.exit(1)
        
        print_success(f"Found {len(installed)} installed language(s):")
        for lang in installed:
            print(f"\n   From language: {lang.code}")
            if lang.translations_to:
                for target in lang.translations_to:
                    print(f"      → {target.code}")
            else:
                print(f"      (no translation models available)")
        
        # Проверяем именно русский-английский
        print_step(6, "Testing translation...")
        
        try:
            from argostranslate import translate
            
            test_text = "Привет мир"
            result = translate.translate_text(test_text, "ru", "en")
            
            if result:
                print_success(f"Translation test successful!")
                print(f"   Input:  {test_text}")
                print(f"   Output: {result}")
            else:
                print_error("Translation returned empty result")
        except Exception as e:
            print_error(f"Translation test failed: {e}")
        
        # Финально
        print_header("✅ INSTALLATION COMPLETE")
        print("\n📝 Next steps:")
        print("   1. Set USE_PROMPT_TRANSLATION=True in .env")
        print("   2. Restart your bot: python bot/main.py")
        print("   3. Check logs for 'Translation successful' messages")
        print("\n🚀 Ready to use!\n")
        
    except KeyboardInterrupt:
        print_error("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_header("❌ INSTALLATION FAILED")
        print_error(f"Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check internet connection: python -c \"import urllib.request; urllib.request.urlopen('https://google.com')\"")
        print("   2. Try reinstalling: pip install --upgrade argostranslate")
        print("   3. Check disk space (need ~600MB)")
        print("   4. Try again: python download_models.py\n")
        sys.exit(1)
