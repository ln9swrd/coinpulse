#!/usr/bin/env python3
"""
CoinPulse Pre-Deployment Verification Script
Checks if all necessary files and configurations are ready for DigitalOcean deployment
"""

import os
import sys
import json
import yaml
from pathlib import Path

class DeploymentVerifier:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []

    def check_file_exists(self, filepath, required=True):
        """Check if a file exists"""
        if os.path.exists(filepath):
            print(f"[OK] Found: {filepath}")
            self.checks_passed += 1
            return True
        else:
            if required:
                print(f"[FAIL] Missing: {filepath}")
                self.errors.append(f"Required file missing: {filepath}")
                self.checks_failed += 1
            else:
                print(f"[WARN] Optional: {filepath} (not found)")
                self.warnings.append(f"Optional file missing: {filepath}")
            return False

    def check_requirements_txt(self):
        """Verify requirements.txt has production dependencies"""
        print("\n📦 Checking requirements.txt...")

        if not self.check_file_exists('requirements.txt'):
            return False

        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        required_packages = ['gunicorn', 'eventlet', 'flask', 'flask-socketio', 'psycopg2-binary']
        missing_packages = []

        for package in required_packages:
            if package.lower() in content.lower():
                print(f"  ✅ {package} found")
            else:
                print(f"  ❌ {package} missing")
                missing_packages.append(package)

        if missing_packages:
            self.errors.append(f"Missing packages in requirements.txt: {', '.join(missing_packages)}")
            self.checks_failed += 1
            return False
        else:
            self.checks_passed += 1
            return True

    def check_app_yaml(self):
        """Verify DigitalOcean app.yaml configuration"""
        print("\n🔧 Checking .do/app.yaml...")

        if not self.check_file_exists('.do/app.yaml'):
            return False

        try:
            with open('.do/app.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Check if GitHub repo is still placeholder
            services = config.get('services', [])
            if services:
                github_repo = services[0].get('github', {}).get('repo', '')
                if 'yourusername' in github_repo or 'placeholder' in github_repo.lower():
                    print("  ⚠️  GitHub repo is still placeholder")
                    self.warnings.append("Update .do/app.yaml line 12 with your GitHub repo name")
                else:
                    print(f"  ✅ GitHub repo: {github_repo}")

            # Check environment variables
            envs = services[0].get('envs', []) if services else []
            required_env_keys = ['SECRET_KEY', 'APP_URL', 'DATABASE_URL', 'SMTP_PASSWORD']

            env_keys = [env['key'] for env in envs]
            for key in required_env_keys:
                if key in env_keys:
                    print(f"  ✅ Environment variable defined: {key}")
                else:
                    print(f"  ⚠️  Environment variable missing: {key}")
                    self.warnings.append(f"Add {key} to environment variables in DigitalOcean")

            self.checks_passed += 1
            return True

        except yaml.YAMLError as e:
            print(f"  ❌ Invalid YAML: {e}")
            self.errors.append(f"app.yaml syntax error: {e}")
            self.checks_failed += 1
            return False

    def check_procfile(self):
        """Verify Procfile exists"""
        print("\n🚀 Checking Procfile...")

        if not self.check_file_exists('Procfile'):
            return False

        with open('Procfile', 'r', encoding='utf-8') as f:
            content = f.read()

        if 'gunicorn' in content and 'eventlet' in content:
            print("  ✅ Procfile has correct gunicorn command")
            self.checks_passed += 1
            return True
        else:
            print("  ❌ Procfile missing gunicorn with eventlet")
            self.errors.append("Procfile should contain: gunicorn --worker-class eventlet")
            self.checks_failed += 1
            return False

    def check_runtime_txt(self):
        """Verify runtime.txt exists"""
        print("\n🐍 Checking runtime.txt...")

        if not self.check_file_exists('runtime.txt'):
            return False

        with open('runtime.txt', 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if content.startswith('python-3.'):
            print(f"  ✅ Python version: {content}")
            self.checks_passed += 1
            return True
        else:
            print(f"  ⚠️  Python version format: {content}")
            self.warnings.append("runtime.txt should be in format: python-3.11.9")
            return True

    def check_env_example(self):
        """Verify .env.example exists"""
        print("\n🔐 Checking .env.example...")
        return self.check_file_exists('.env.example', required=False)

    def check_gitignore(self):
        """Verify .gitignore exists and contains important entries"""
        print("\n🙈 Checking .gitignore...")

        if not self.check_file_exists('.gitignore', required=False):
            self.warnings.append("Create .gitignore to avoid committing secrets")
            return False

        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()

        important_entries = ['.env', '__pycache__', '*.pyc', 'venv', 'node_modules']
        missing_entries = []

        for entry in important_entries:
            if entry in content:
                print(f"  ✅ {entry} ignored")
            else:
                print(f"  ⚠️  {entry} not in .gitignore")
                missing_entries.append(entry)

        if missing_entries:
            self.warnings.append(f"Add to .gitignore: {', '.join(missing_entries)}")

        return True

    def check_app_py(self):
        """Verify app.py exists and has basic structure"""
        print("\n📄 Checking app.py...")

        if not self.check_file_exists('app.py'):
            return False

        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()

        checks = {
            'Flask app': 'Flask(__name__)',
            'SocketIO': 'SocketIO',
            'Database': 'DATABASE_URL',
            'Health endpoint': '/health'
        }

        all_good = True
        for check_name, check_str in checks.items():
            if check_str in content:
                print(f"  ✅ {check_name} found")
            else:
                print(f"  ⚠️  {check_name} not found (may be in blueprints)")
                all_good = False

        if all_good:
            self.checks_passed += 1

        return True

    def check_init_scripts(self):
        """Check for database initialization scripts"""
        print("\n💾 Checking database initialization scripts...")

        init_files = ['init_auth_db.py', 'init_order_sync.py']
        found_any = False

        for init_file in init_files:
            if self.check_file_exists(init_file, required=False):
                found_any = True

        if not found_any:
            self.warnings.append("No database initialization scripts found")

        return found_any

    def check_backend_structure(self):
        """Check backend folder structure"""
        print("\n📁 Checking backend structure...")

        backend_dirs = ['backend', 'backend/common', 'backend/services', 'backend/routes']
        for directory in backend_dirs:
            if os.path.isdir(directory):
                print(f"  ✅ {directory}/ exists")
            else:
                print(f"  ⚠️  {directory}/ not found")

        return True

    def generate_summary(self):
        """Generate summary report"""
        print("\n" + "="*60)
        print("📊 VERIFICATION SUMMARY")
        print("="*60)

        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            pass_rate = (self.checks_passed / total_checks) * 100
            print(f"✅ Passed: {self.checks_passed}/{total_checks} ({pass_rate:.1f}%)")

        if self.checks_failed > 0:
            print(f"❌ Failed: {self.checks_failed}")

        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}")

        print()

        if self.errors:
            print("🚨 CRITICAL ERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()

        print("="*60)

        if self.checks_failed > 0:
            print("❌ DEPLOYMENT NOT READY")
            print("Fix the errors above before deploying to DigitalOcean")
            return False
        elif self.warnings:
            print("⚠️  DEPLOYMENT READY WITH WARNINGS")
            print("Review warnings above, but you can proceed with deployment")
            return True
        else:
            print("✅ DEPLOYMENT READY!")
            print("All checks passed. You can deploy to DigitalOcean.")
            return True

    def run_all_checks(self):
        """Run all verification checks"""
        print("🔍 CoinPulse Pre-Deployment Verification")
        print("="*60)

        # Core deployment files
        self.check_app_yaml()
        self.check_procfile()
        self.check_runtime_txt()
        self.check_requirements_txt()

        # Application files
        self.check_app_py()
        self.check_backend_structure()
        self.check_init_scripts()

        # Configuration files
        self.check_env_example()
        self.check_gitignore()

        # Generate summary
        is_ready = self.generate_summary()

        return is_ready

def main():
    verifier = DeploymentVerifier()
    is_ready = verifier.run_all_checks()

    if is_ready:
        print("\n📋 Next Steps:")
        print("1. Run: python generate_secrets.py")
        print("2. Update .do/app.yaml with your GitHub repo name")
        print("3. Commit all files to GitHub")
        print("4. Follow DEPLOYMENT_CHECKLIST.md")
        sys.exit(0)
    else:
        print("\n🔧 Fix the errors above before deploying")
        sys.exit(1)

if __name__ == "__main__":
    main()
