#!/usr/bin/env python3
"""
Build and upload script for PyPI.
PyPI用ビルド・アップロードスクリプト

Usage:
    python scripts/build_and_upload.py [--test]
    
    --test: Upload to TestPyPI instead of PyPI
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    print(f"✅ Success: {description}")
    if result.stdout.strip():
        print(f"Output: {result.stdout.strip()}")
    return result

def clean_build_artifacts():
    """Clean previous build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    # Remove build directories
    for path in ['build', 'dist', '*.egg-info']:
        if os.path.exists(path):
            if os.path.isdir(path):
                run_command(f"rmdir /s /q {path}", f"Remove {path} directory")
            else:
                run_command(f"del {path}", f"Remove {path}")

def run_tests():
    """Run tests before building"""
    print("🧪 Running tests...")
    
    # Check if pytest is available
    result = subprocess.run("python -m pytest --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("⚠️  pytest not available, skipping tests")
        return
    
    # Run tests
    run_command("python -m pytest tests/ -v", "Run test suite")

def build_package():
    """Build the package"""
    print("📦 Building package...")
    
    # Build source distribution and wheel
    run_command("python setup.py sdist bdist_wheel", "Build distribution packages")
    
    # Verify the build
    print("📋 Build artifacts:")
    for file in Path("dist").glob("*"):
        print(f"  {file.name} ({file.stat().st_size} bytes)")

def upload_package(test_pypi=False):
    """Upload package to PyPI or TestPyPI"""
    target = "TestPyPI" if test_pypi else "PyPI"
    print(f"🚀 Uploading to {target}...")
    
    # Check if twine is available
    result = subprocess.run("python -m twine --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ twine not available. Install with: pip install twine")
        sys.exit(1)
    
    # Upload command
    if test_pypi:
        upload_cmd = "python -m twine upload --repository testpypi dist/*"
    else:
        upload_cmd = "python -m twine upload dist/*"
    
    print(f"Running: {upload_cmd}")
    print("Note: You will be prompted for your PyPI credentials")
    
    # Run upload command interactively
    result = subprocess.run(upload_cmd, shell=True)
    
    if result.returncode == 0:
        print(f"✅ Successfully uploaded to {target}")
        if test_pypi:
            print("🔗 Test installation: pip install -i https://test.pypi.org/simple/ murata-sensor-receiver")
        else:
            print("🔗 Installation: pip install murata-sensor-receiver")
    else:
        print(f"❌ Failed to upload to {target}")
        sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build and upload murata-sensor-receiver package")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build artifacts")
    
    args = parser.parse_args()
    
    print("🏗️  Murata Sensor Receiver - Build & Upload Script")
    print("=" * 50)
    
    # Clean build artifacts
    clean_build_artifacts()
    
    if args.clean_only:
        print("✅ Cleaning completed")
        return
    
    # Run tests
    if not args.skip_tests:
        run_tests()
    
    # Build package
    build_package()
    
    # Upload package
    target = "TestPyPI" if args.test else "PyPI"
    
    response = input(f"\n📤 Upload to {target}? (y/N): ")
    if response.lower() in ['y', 'yes']:
        upload_package(args.test)
    else:
        print("⏸️  Upload skipped")
        print("📦 Package built successfully. Manual upload commands:")
        if args.test:
            print("  python -m twine upload --repository testpypi dist/*")
        else:
            print("  python -m twine upload dist/*")

if __name__ == "__main__":
    main()
