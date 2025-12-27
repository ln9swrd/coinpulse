# -*- coding: utf-8 -*-
"""
Auto-Trading Preset Configurations
자동매매 프리셋 설정

사용자가 쉽게 선택할 수 있는 3가지 프리셋 제공:
- Conservative (보수적): 높은 신뢰도, 낮은 위험
- Balanced (균형): 중간 신뢰도와 위험 (기본값)
- Aggressive (공격적): 낮은 신뢰도, 높은 위험
"""

# 프리셋 정의
AUTO_TRADING_PRESETS = {
    'conservative': {
        'name': '보수적 (Conservative)',
        'description': '높은 신뢰도의 신호만 선택, 안정적인 수익 추구',
        'icon': '🛡️',
        'settings': {
            # 신호 필터링
            'min_confidence': 80,  # 80% 이상의 신호만 매수

            # 수익 목표 (보수적 - 작은 이익 확보)
            'take_profit_percent': 8.0,  # +8% 익절
            'stop_loss_percent': -3.0,   # -3% 손절

            # 동적 목표가 설정
            'use_dynamic_target': True,
            'target_calculation_mode': 'dynamic',
            'min_target_percent': 5.0,
            'max_target_percent': 12.0,

            # 설명
            'risk_level': 'low',
            'expected_win_rate': '60-70%',
            'avg_profit': '+5~8%'
        }
    },

    'balanced': {
        'name': '균형 (Balanced)',
        'description': '적절한 신뢰도와 수익률의 균형, 가장 추천하는 설정',
        'icon': '⚖️',
        'settings': {
            # 신호 필터링
            'min_confidence': 65,  # 65% 이상의 신호 매수

            # 수익 목표 (균형)
            'take_profit_percent': 10.0,  # +10% 익절
            'stop_loss_percent': -5.0,    # -5% 손절

            # 동적 목표가 설정
            'use_dynamic_target': True,
            'target_calculation_mode': 'dynamic',
            'min_target_percent': 5.0,
            'max_target_percent': 18.0,

            # 설명
            'risk_level': 'medium',
            'expected_win_rate': '50-60%',
            'avg_profit': '+8~12%'
        }
    },

    'aggressive': {
        'name': '공격적 (Aggressive)',
        'description': '낮은 신뢰도 신호도 포함, 높은 수익률 추구 (높은 위험)',
        'icon': '🚀',
        'settings': {
            # 신호 필터링
            'min_confidence': 50,  # 50% 이상의 신호도 매수

            # 수익 목표 (공격적 - 큰 이익 추구)
            'take_profit_percent': 15.0,  # +15% 익절
            'stop_loss_percent': -7.0,    # -7% 손절

            # 동적 목표가 설정
            'use_dynamic_target': True,
            'target_calculation_mode': 'dynamic',
            'min_target_percent': 8.0,
            'max_target_percent': 25.0,

            # 설명
            'risk_level': 'high',
            'expected_win_rate': '40-50%',
            'avg_profit': '+12~20%'
        }
    }
}


def get_preset(preset_name: str) -> dict:
    """
    Get preset configuration by name

    Args:
        preset_name: Preset name ('conservative', 'balanced', 'aggressive')

    Returns:
        Preset configuration dict
    """
    preset_name = preset_name.lower()
    if preset_name not in AUTO_TRADING_PRESETS:
        # Default to balanced if invalid preset
        return AUTO_TRADING_PRESETS['balanced']

    return AUTO_TRADING_PRESETS[preset_name]


def get_preset_settings(preset_name: str) -> dict:
    """
    Get only the settings part of a preset

    Args:
        preset_name: Preset name ('conservative', 'balanced', 'aggressive')

    Returns:
        Settings dict ready to apply to SurgeAutoTradingSettings
    """
    preset = get_preset(preset_name)
    return preset['settings']


def get_all_presets() -> dict:
    """
    Get all available presets

    Returns:
        Dictionary of all presets
    """
    return AUTO_TRADING_PRESETS


def apply_preset_to_settings(settings_obj, preset_name: str):
    """
    Apply preset configuration to a SurgeAutoTradingSettings object

    Args:
        settings_obj: SurgeAutoTradingSettings instance
        preset_name: Preset name to apply
    """
    preset_settings = get_preset_settings(preset_name)

    # Apply settings
    settings_obj.min_confidence = preset_settings['min_confidence']
    settings_obj.take_profit_percent = preset_settings['take_profit_percent']
    settings_obj.stop_loss_percent = preset_settings['stop_loss_percent']
    settings_obj.use_dynamic_target = preset_settings['use_dynamic_target']
    settings_obj.target_calculation_mode = preset_settings['target_calculation_mode']
    settings_obj.min_target_percent = preset_settings['min_target_percent']
    settings_obj.max_target_percent = preset_settings['max_target_percent']

    return settings_obj


# 프리셋 비교 정보
PRESET_COMPARISON = {
    'headers': ['프리셋', '최소 신뢰도', '익절 목표', '손절 기준', '위험도', '예상 승률', '평균 수익'],
    'rows': [
        {
            'preset': 'conservative',
            'name': '🛡️ 보수적',
            'min_confidence': '80%',
            'take_profit': '+8%',
            'stop_loss': '-3%',
            'risk': '낮음',
            'win_rate': '60-70%',
            'avg_profit': '+5~8%'
        },
        {
            'preset': 'balanced',
            'name': '⚖️ 균형 (추천)',
            'min_confidence': '65%',
            'take_profit': '+10%',
            'stop_loss': '-5%',
            'risk': '중간',
            'win_rate': '50-60%',
            'avg_profit': '+8~12%'
        },
        {
            'preset': 'aggressive',
            'name': '🚀 공격적',
            'min_confidence': '50%',
            'take_profit': '+15%',
            'stop_loss': '-7%',
            'risk': '높음',
            'win_rate': '40-50%',
            'avg_profit': '+12~20%'
        }
    ]
}


if __name__ == "__main__":
    """테스트 및 프리셋 정보 출력"""
    print("\n" + "="*60)
    print("Auto-Trading Presets")
    print("="*60 + "\n")

    for preset_key, preset_data in AUTO_TRADING_PRESETS.items():
        print(f"{preset_data['icon']} {preset_data['name']}")
        print(f"   설명: {preset_data['description']}")
        print(f"   신뢰도: {preset_data['settings']['min_confidence']}%")
        print(f"   익절: {preset_data['settings']['take_profit_percent']:+.1f}%")
        print(f"   손절: {preset_data['settings']['stop_loss_percent']:+.1f}%")
        print(f"   위험도: {preset_data['settings']['risk_level']}")
        print(f"   예상 승률: {preset_data['settings']['expected_win_rate']}")
        print(f"   평균 수익: {preset_data['settings']['avg_profit']}")
        print()

    print("="*60)
    print("프리셋 비교표")
    print("="*60 + "\n")

    for row in PRESET_COMPARISON['rows']:
        print(f"{row['name']:15} | {row['min_confidence']:6} | {row['take_profit']:6} | "
              f"{row['stop_loss']:6} | {row['risk']:6} | {row['win_rate']:8} | {row['avg_profit']}")
