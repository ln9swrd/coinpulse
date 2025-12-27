# -*- coding: utf-8 -*-
"""
Codebase Verification Script
코드베이스 검증 스크립트

검증 항목:
1. Python 문법 오류
2. Import 오류
3. DB 스키마와 모델 불일치
4. 클래스 참조 오류
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import ast
import glob
from pathlib import Path
from sqlalchemy import inspect, text
from backend.database.connection import get_db_session
import importlib.util

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_python_syntax():
    """Check Python syntax errors"""
    print_section("1. Python 문법 오류 체크")

    errors = []
    python_files = []

    # Find all Python files
    for pattern in ['backend/**/*.py', 'scripts/**/*.py']:
        python_files.extend(glob.glob(pattern, recursive=True))

    print(f"Found {len(python_files)} Python files")

    for filepath in python_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append({
                'file': filepath,
                'line': e.lineno,
                'error': str(e)
            })

    if errors:
        print(f"\n❌ Found {len(errors)} syntax errors:")
        for err in errors:
            print(f"   {err['file']}:{err['line']} - {err['error']}")
    else:
        print("✅ No syntax errors found")

    return len(errors) == 0

def check_imports():
    """Check import errors"""
    print_section("2. Import 오류 체크")

    errors = []

    # Key imports to check
    critical_imports = [
        ('backend.database.models', 'User'),
        ('backend.models.surge_alert_models', 'SurgeAlert'),
        ('backend.models.surge_alert_models', 'SurgeAutoTradingSettings'),
        ('backend.models.subscription_models', 'Subscription'),
        ('backend.models.surge_system_settings', 'SurgeSystemSettings'),
        ('backend.services.surge_auto_trading_worker', 'SurgeAutoTradingWorker'),
        ('backend.services.surge_alert_scheduler', 'SurgeAlertScheduler'),
    ]

    print(f"Checking {len(critical_imports)} critical imports...")

    for module_name, class_name in critical_imports:
        try:
            module = __import__(module_name, fromlist=[class_name])
            if not hasattr(module, class_name):
                errors.append(f"{module_name}.{class_name} not found")
        except Exception as e:
            errors.append(f"{module_name}.{class_name} - {str(e)}")

    if errors:
        print(f"\n❌ Found {len(errors)} import errors:")
        for err in errors:
            print(f"   {err}")
    else:
        print("✅ All critical imports are valid")

    return len(errors) == 0

def check_schema_model_consistency():
    """Check DB schema vs SQLAlchemy models"""
    print_section("3. DB 스키마와 모델 불일치 체크")

    inconsistencies = []

    with get_db_session() as session:
        # Check surge_alerts table
        print("\nChecking surge_alerts table...")

        # Get actual table columns
        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'surge_alerts'
            ORDER BY ordinal_position
        """))

        db_columns = {row[0]: {'type': row[1], 'nullable': row[2] == 'YES'}
                      for row in result}

        print(f"   DB has {len(db_columns)} columns")

        # Check model
        from backend.models.surge_alert_models import SurgeAlert
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(SurgeAlert)
        model_columns = {col.name: col for col in mapper.columns}

        print(f"   Model has {len(model_columns)} columns")

        # Check for missing columns in model
        missing_in_model = set(db_columns.keys()) - set(model_columns.keys())
        if missing_in_model:
            for col in missing_in_model:
                inconsistencies.append(f"surge_alerts.{col} exists in DB but not in model")

        # Check for missing columns in DB
        missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
        if missing_in_db:
            for col in missing_in_db:
                inconsistencies.append(f"surge_alerts.{col} exists in model but not in DB")

        # Check user_subscriptions table
        print("\nChecking user_subscriptions table...")

        result = session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_subscriptions'
            ORDER BY ordinal_position
        """))

        db_columns = {row[0]: {'type': row[1], 'nullable': row[2] == 'YES'}
                      for row in result}

        print(f"   DB has {len(db_columns)} columns")

        from backend.models.subscription_models import Subscription
        mapper = sa_inspect(Subscription)
        model_columns = {col.name: col for col in mapper.columns}

        print(f"   Model has {len(model_columns)} columns")

        # Check for missing columns
        missing_in_model = set(db_columns.keys()) - set(model_columns.keys())
        if missing_in_model:
            for col in missing_in_model:
                inconsistencies.append(f"user_subscriptions.{col} exists in DB but not in model")

        missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
        if missing_in_db:
            for col in missing_in_db:
                inconsistencies.append(f"user_subscriptions.{col} exists in model but not in DB")

    if inconsistencies:
        print(f"\n❌ Found {len(inconsistencies)} inconsistencies:")
        for inc in inconsistencies:
            print(f"   {inc}")
    else:
        print("✅ DB schema and models are consistent")

    return len(inconsistencies) == 0

def check_class_references():
    """Check for incorrect class references"""
    print_section("4. 클래스 참조 오류 체크")

    errors = []

    # Known incorrect references to check
    checks = [
        {
            'pattern': 'UserSubscription',
            'files': ['backend/services/**/*.py', 'backend/routes/**/*.py'],
            'correct': 'Subscription',
            'message': 'UserSubscription should be Subscription'
        },
        {
            'pattern': 'SurgeAlertSettings',
            'files': ['backend/services/**/*.py'],
            'correct': 'SurgeAutoTradingSettings',
            'message': 'SurgeAlertSettings should be SurgeAutoTradingSettings'
        }
    ]

    for check in checks:
        pattern = check['pattern']
        for file_pattern in check['files']:
            files = glob.glob(file_pattern, recursive=True)
            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern in content and check['correct'] not in content:
                            # Check if it's in import or usage
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if pattern in line:
                                    errors.append({
                                        'file': filepath,
                                        'line': i,
                                        'message': check['message'],
                                        'code': line.strip()
                                    })
                except Exception as e:
                    pass

    if errors:
        print(f"\n❌ Found {len(errors)} class reference errors:")
        for err in errors:
            print(f"   {err['file']}:{err['line']}")
            print(f"      {err['message']}")
            print(f"      Code: {err['code'][:80]}")
    else:
        print("✅ No class reference errors found")

    return len(errors) == 0

def check_required_fields():
    """Check for missing required fields in DB operations"""
    print_section("5. 필수 필드 누락 체크")

    warnings = []

    with get_db_session() as session:
        # Check surge_alerts for signal_type (NOT NULL)
        result = session.execute(text("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'surge_alerts'
            AND is_nullable = 'NO'
            AND column_default IS NULL
        """))

        required_fields = [row[0] for row in result]

        print(f"surge_alerts has {len(required_fields)} required fields (NOT NULL, no default):")
        for field in required_fields:
            print(f"   - {field}")

        # Check if signal_type is in model
        from backend.models.surge_alert_models import SurgeAlert
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(SurgeAlert)
        model_columns = {col.name for col in mapper.columns}

        for field in required_fields:
            if field not in model_columns:
                warnings.append(f"Required field '{field}' missing in SurgeAlert model")

    if warnings:
        print(f"\n⚠️ Found {len(warnings)} warnings:")
        for warn in warnings:
            print(f"   {warn}")
    else:
        print("✅ All required fields are properly defined")

    return len(warnings) == 0

def main():
    """Run all verification checks"""
    print("\n" + "🔍"*35)
    print("Codebase Verification - 코드베이스 검증")
    print("🔍"*35)

    results = {
        'Syntax': check_python_syntax(),
        'Imports': check_imports(),
        'Schema': check_schema_model_consistency(),
        'Classes': check_class_references(),
        'Required Fields': check_required_fields()
    }

    print_section("검증 결과 요약")

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check:20s}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("✅ 모든 검증 통과! All checks passed!")
    else:
        print("❌ 일부 검증 실패! Some checks failed!")
    print("="*70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
