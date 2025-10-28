#!/usr/bin/env python3
"""
Test Runner for Mac OS Zero Trust Platform

Author: Adrian Johnson <adrian207@gmail.com>

Runs all tests and provides a summary report.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_tests():
    """Run all tests."""
    print_header("Mac OS Zero Trust Platform - Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Author: Adrian Johnson <adrian207@gmail.com>")
    
    test_files = [
        ("Configuration Tests", "tests/test_config.py"),
        ("Risk Engine Tests", "tests/test_risk_engine.py"),
        ("Compliance Tests", "tests/test_compliance.py"),
        ("API Tests", "tests/test_api.py"),
        ("Integration Tests", "tests/test_integration.py"),
    ]
    
    results = []
    
    for test_name, test_file in test_files:
        print_header(test_name)
        
        if not Path(test_file).exists():
            print(f"⚠ Test file not found: {test_file}")
            results.append((test_name, "SKIPPED"))
            continue
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            if result.returncode == 0:
                print(f"✓ {test_name} PASSED")
                results.append((test_name, "PASSED"))
            else:
                print(f"✗ {test_name} FAILED")
                if result.stderr:
                    print("Errors:")
                    print(result.stderr)
                results.append((test_name, "FAILED"))
        
        except Exception as e:
            print(f"✗ Error running {test_name}: {e}")
            results.append((test_name, "ERROR"))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, status in results if status == "PASSED")
    failed = sum(1 for _, status in results if status == "FAILED")
    skipped = sum(1 for _, status in results if status == "SKIPPED")
    errors = sum(1 for _, status in results if status == "ERROR")
    
    for test_name, status in results:
        symbol = {
            "PASSED": "✓",
            "FAILED": "✗",
            "SKIPPED": "⊘",
            "ERROR": "⚠"
        }.get(status, "?")
        
        print(f"  {symbol} {test_name:40} {status}")
    
    print()
    print(f"Total Tests: {len(results)}")
    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")
    print()
    
    if failed > 0 or errors > 0:
        print("❌ Some tests failed!")
        return 1
    elif passed == 0:
        print("⚠ No tests ran!")
        return 1
    else:
        print("✅ All tests passed!")
        return 0


def run_quick_validation():
    """Run quick validation checks without full test suite."""
    print_header("Quick Validation Checks")
    
    checks = []
    
    # Check Python version
    print("Checking Python version...")
    if sys.version_info >= (3, 10):
        print(f"  ✓ Python {sys.version_info.major}.{sys.version_info.minor}")
        checks.append(True)
    else:
        print(f"  ✗ Python {sys.version_info.major}.{sys.version_info.minor} (3.10+ required)")
        checks.append(False)
    
    # Check dependencies
    print("\nChecking dependencies...")
    required_packages = [
        "fastapi", "uvicorn", "sqlalchemy", "pydantic",
        "httpx", "prometheus_client", "structlog"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
            checks.append(True)
        except ImportError:
            print(f"  ✗ {package} (not installed)")
            checks.append(False)
    
    # Check config file
    print("\nChecking configuration...")
    config_file = Path("config/config.example.yaml")
    if config_file.exists():
        print(f"  ✓ Example config exists")
        checks.append(True)
    else:
        print(f"  ✗ Example config missing")
        checks.append(False)
    
    # Check module imports
    print("\nChecking module imports...")
    modules = [
        "core.config",
        "core.database",
        "telemetry.collector",
        "risk_engine.assessor",
        "hardening.compliance_checker",
        "workflows.orchestrator"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
            checks.append(True)
        except Exception as e:
            print(f"  ✗ {module} ({str(e)[:50]})")
            checks.append(False)
    
    print()
    passed = sum(checks)
    total = len(checks)
    print(f"Validation: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ Quick validation passed!")
        return 0
    else:
        print("⚠ Some validation checks failed")
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        return run_quick_validation()
    else:
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())

