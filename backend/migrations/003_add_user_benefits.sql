-- User Benefits Table Migration
-- 범용 사용자 혜택 관리 테이블

CREATE TABLE IF NOT EXISTS user_benefits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    
    -- 혜택 분류
    category VARCHAR(50) NOT NULL,
    code VARCHAR(100) UNIQUE,
    
    -- 혜택 타입 및 값
    benefit_type VARCHAR(50) NOT NULL,
    benefit_value INTEGER DEFAULT 0,
    applicable_to VARCHAR(100) DEFAULT 'all',
    
    -- 기간
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    
    -- 사용 제한
    usage_limit INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    
    -- 우선순위 및 상태
    priority INTEGER DEFAULT 100,
    status VARCHAR(20) DEFAULT 'active',
    stackable BOOLEAN DEFAULT FALSE,
    
    -- 설명
    title VARCHAR(200),
    description TEXT,
    notes TEXT,
    issued_by VARCHAR(100),
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX idx_user_benefits_email ON user_benefits(email);
CREATE INDEX idx_user_benefits_user_id ON user_benefits(user_id);
CREATE INDEX idx_user_benefits_category ON user_benefits(category);
CREATE INDEX idx_user_benefits_code ON user_benefits(code);
CREATE INDEX idx_user_benefits_status ON user_benefits(status);
CREATE INDEX idx_user_benefits_dates ON user_benefits(start_date, end_date);

-- 복합 인덱스 (자주 사용되는 쿼리 최적화)
CREATE INDEX idx_user_benefits_active ON user_benefits(email, status, category)
WHERE status = 'active';

-- 업데이트 트리거
CREATE OR REPLACE FUNCTION update_user_benefit_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_benefit_updated_at
BEFORE UPDATE ON user_benefits
FOR EACH ROW
EXECUTE FUNCTION update_user_benefit_updated_at();

-- 자동 만료 처리 함수
CREATE OR REPLACE FUNCTION expire_user_benefits()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE user_benefits
    SET status = 'expired'
    WHERE status = 'active'
      AND end_date IS NOT NULL
      AND end_date < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- 샘플 데이터 (옵션)
-- 베타 테스터 혜택
INSERT INTO user_benefits (email, category, code, benefit_type, benefit_value, 
                          applicable_to, title, description, stackable, priority)
VALUES 
    ('beta@example.com', 'beta_tester', 'BETA2024', 'free_trial', 90, 'all',
     'Beta Tester - 90 Days Free', 'Early adopter benefit', false, 10);

-- 프로모션 쿠폰
INSERT INTO user_benefits (email, category, code, benefit_type, benefit_value,
                          applicable_to, title, description, stackable, usage_limit, priority)
VALUES
    ('promo@example.com', 'promotion', 'LAUNCH50', 'discount', 50, 'all',
     'Launch Promotion - 50% OFF', 'Limited time offer', true, 1, 20);

-- VIP 멤버십
INSERT INTO user_benefits (email, category, benefit_type, benefit_value,
                          applicable_to, title, description, end_date, priority)
VALUES
    ('vip@example.com', 'vip', 'upgrade', 0, 'pro',
     'VIP Membership - Pro Features', 'Exclusive VIP access',
     CURRENT_TIMESTAMP + INTERVAL '1 year', 5);