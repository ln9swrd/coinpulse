-- Plan Configuration Table Migration
-- 동적 요금제 관리 시스템

CREATE TABLE IF NOT EXISTS plan_configs (
    id SERIAL PRIMARY KEY,
    plan_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- 기본 정보
    plan_name VARCHAR(100) NOT NULL,
    plan_name_ko VARCHAR(100),
    description TEXT,
    display_order INTEGER DEFAULT 0,
    
    -- 가격 정보
    monthly_price INTEGER DEFAULT 0,
    annual_price INTEGER DEFAULT 0,
    setup_fee INTEGER DEFAULT 0,
    annual_discount_rate INTEGER DEFAULT 0,
    trial_days INTEGER DEFAULT 0,
    
    -- 기능 제한 - 모니터링
    max_coins INTEGER DEFAULT 1,
    max_watchlists INTEGER DEFAULT 1,
    
    -- 기능 제한 - 자동매매
    auto_trading_enabled BOOLEAN DEFAULT FALSE,
    max_auto_strategies INTEGER DEFAULT 0,
    max_concurrent_trades INTEGER DEFAULT 0,
    
    -- 기능 제한 - 분석
    advanced_indicators BOOLEAN DEFAULT FALSE,
    custom_indicators BOOLEAN DEFAULT FALSE,
    backtesting_enabled BOOLEAN DEFAULT FALSE,
    
    -- 기능 제한 - 데이터
    history_days INTEGER DEFAULT 7,
    data_export BOOLEAN DEFAULT FALSE,
    api_access BOOLEAN DEFAULT FALSE,
    
    -- 기능 제한 - 지원
    support_level VARCHAR(50) DEFAULT 'community',
    response_time_hours INTEGER DEFAULT 72,
    
    -- 기능 제한 - 기타
    white_labeling BOOLEAN DEFAULT FALSE,
    sla_guarantee BOOLEAN DEFAULT FALSE,
    custom_development BOOLEAN DEFAULT FALSE,
    
    -- 표시 설정
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    badge_text VARCHAR(50),
    cta_text VARCHAR(100),
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_plan_configs_code ON plan_configs(plan_code);
CREATE INDEX idx_plan_configs_active ON plan_configs(is_active, is_visible, display_order);

-- 업데이트 트리거
CREATE OR REPLACE FUNCTION update_plan_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER plan_config_updated_at
BEFORE UPDATE ON plan_configs
FOR EACH ROW
EXECUTE FUNCTION update_plan_config_updated_at();

-- 초기 데이터 삽입
INSERT INTO plan_configs (
    plan_code, plan_name, plan_name_ko, description, display_order,
    monthly_price, annual_price, annual_discount_rate, trial_days,
    max_coins, max_watchlists,
    auto_trading_enabled, max_auto_strategies, max_concurrent_trades,
    advanced_indicators, custom_indicators, backtesting_enabled,
    history_days, data_export, api_access,
    support_level, response_time_hours,
    white_labeling, sla_guarantee, custom_development,
    is_active, is_featured, is_visible, badge_text, cta_text
) VALUES
-- 무료 플랜
('free', 'Free', '무료', '개인 투자자를 위한 기본 기능', 1,
 0, 0, 0, 0,
 1, 1,
 FALSE, 0, 0,
 FALSE, FALSE, FALSE,
 7, FALSE, FALSE,
 'community', 72,
 FALSE, FALSE, FALSE,
 TRUE, FALSE, TRUE, NULL, '시작하기'),

-- 프리미엄 플랜
('premium', 'Premium', '프리미엄', '전문 트레이더를 위한 완전한 자동매매', 2,
 29900, 299000, 17, 14,
 10, 5,
 TRUE, 3, 5,
 TRUE, FALSE, FALSE,
 0, TRUE, FALSE,
 'email', 24,
 FALSE, FALSE, FALSE,
 TRUE, TRUE, TRUE, '가장 인기', '무료 체험 시작'),

-- 프로 플랜 (추가)
('pro', 'Pro', '프로', '고급 분석과 백테스팅이 필요한 전문가', 3,
 79900, 799000, 17, 14,
 20, 10,
 TRUE, 10, 20,
 TRUE, TRUE, TRUE,
 0, TRUE, TRUE,
 'priority', 12,
 FALSE, FALSE, FALSE,
 TRUE, FALSE, TRUE, NULL, '지금 시작하기'),

-- 엔터프라이즈 플랜
('enterprise', 'Enterprise', '엔터프라이즈', '기관 투자자를 위한 맞춤형 솔루션', 4,
 0, 0, 0, 30,
 0, 0,
 TRUE, 0, 0,
 TRUE, TRUE, TRUE,
 0, TRUE, TRUE,
 'dedicated', 1,
 TRUE, TRUE, TRUE,
 TRUE, FALSE, TRUE, NULL, '영업팀 문의')
ON CONFLICT (plan_code) DO NOTHING;