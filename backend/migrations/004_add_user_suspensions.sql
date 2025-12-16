-- User Suspensions Table Migration
-- 사용자 이용 정지 관리

CREATE TABLE IF NOT EXISTS user_suspensions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    
    -- 정지 타입 및 수준
    suspension_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    
    -- 사유
    reason VARCHAR(100) NOT NULL,
    description TEXT,
    notes TEXT,
    
    -- 기간
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    
    -- 상태
    status VARCHAR(20) DEFAULT 'active',
    
    -- 조치자
    suspended_by VARCHAR(100),
    lifted_by VARCHAR(100),
    
    -- 타임스탬프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lifted_at TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_user_suspensions_email ON user_suspensions(email);
CREATE INDEX idx_user_suspensions_user_id ON user_suspensions(user_id);
CREATE INDEX idx_user_suspensions_type ON user_suspensions(suspension_type);
CREATE INDEX idx_user_suspensions_status ON user_suspensions(status);
CREATE INDEX idx_user_suspensions_dates ON user_suspensions(start_date, end_date);

-- 복합 인덱스 (활성 정지 조회 최적화)
CREATE INDEX idx_user_suspensions_active ON user_suspensions(email, status, suspension_type)
WHERE status = 'active';

-- 업데이트 트리거
CREATE OR REPLACE FUNCTION update_user_suspension_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_suspension_updated_at
BEFORE UPDATE ON user_suspensions
FOR EACH ROW
EXECUTE FUNCTION update_user_suspension_updated_at();

-- 자동 만료 처리 함수
CREATE OR REPLACE FUNCTION expire_user_suspensions()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE user_suspensions
    SET status = 'expired'
    WHERE status = 'active'
      AND end_date IS NOT NULL
      AND end_date < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;