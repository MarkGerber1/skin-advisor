#!/usr/bin/env python3
"""
🔍 SECURITY AUDIT - Check for sensitive information in files
Usage: python check_sensitive_files.py
"""

import os
import re
from pathlib import Path

# Patterns for sensitive data
SENSITIVE_PATTERNS = {
    "Telegram Bot Token": r"\d{9,10}:[A-Za-z0-9_-]{35}",
    "GitHub Token": r"ghp_[A-Za-z0-9]{36}",
    "Generic API Key": r"[A-Za-z0-9]{32,}",
    "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "Password": r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    "Secret": r'secret["\']?\s*[:=]\s*["\']([^"\']+)["\']',
    "Key": r'key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
}

# Files to exclude from checking
EXCLUDE_FILES = {
    ".git/",
    "node_modules/",
    "__pycache__/",
    ".pytest_cache/",
    "BeautyCare-Site/",
    "*.pyc",
    "*.log",
    "*.pdf",
}


def should_exclude_file(file_path):
    """Check if file should be excluded from scanning"""
    for exclude in EXCLUDE_FILES:
        if exclude in str(file_path) or str(file_path).endswith(exclude.replace("*", "")):
            return True
    return False


def scan_file_for_sensitive_data(file_path):
    """Scan a single file for sensitive data"""
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Limit to first 3 matches
                    findings.append(
                        {
                            "file": str(file_path),
                            "type": pattern_name,
                            "value": match[:20] + "..." if len(match) > 20 else match,
                        }
                    )

    except Exception:
        pass  # Skip files that can't be read

    return findings


def main():
    """Main security audit function"""
    print("🔍 SECURITY AUDIT - Scanning for sensitive data...")
    print("=" * 60)

    all_findings = []
    total_files_scanned = 0

    # Scan all files in project
    for root, dirs, files in os.walk("."):
        for file in files:
            file_path = Path(root) / file

            # Skip excluded files
            if should_exclude_file(file_path):
                continue

            total_files_scanned += 1
            findings = scan_file_for_sensitive_data(file_path)

            if findings:
                all_findings.extend(findings)

    # Report results
    print("\n📊 RESULTS:")
    print(f"Files scanned: {total_files_scanned}")
    print(f"Sensitive items found: {len(all_findings)}")

    if all_findings:
        print("\n🚨 SENSITIVE DATA FOUND:")
        print("-" * 40)

        for finding in all_findings:
            print(f"❌ {finding['type']}")
            print(f"   File: {finding['file']}")
            print(f"   Value: {finding['value']}")
            print()

        print("🚨 IMMEDIATE ACTION REQUIRED!")
        print("1. Remove these files from Git history")
        print("2. Change all compromised tokens/keys")
        print("3. Update .gitignore to prevent future commits")

    else:
        print("\n✅ No sensitive data found in scanned files!")
        print("🎉 Your repository appears to be secure.")

    print("\n" + "=" * 60)
    print("🔒 Security audit completed")


if __name__ == "__main__":
    main()
