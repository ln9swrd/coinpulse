-- Beta Tester Table Migration
-- 베타 테스터 관리 테이블 생성

CREATE TABLE IF NOT EXISTS beta_testers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    
    benefit_type VARCHAR(50) NOT NULL DEFAULT 'free_trial',
    benefit_value INTEGER DEFAULT 30,
    
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_beta_testers_email ON beta_testers(email);
CREATE INDEX idx_beta_testers_status ON beta_testers(status);
CREATE INDEX idx_beta_testers_user_id ON beta_testers(user_id);

-- 업데이트 트리거 (updated_at 자동 갱신)
CREATE OR REPLACE FUNCTION update_beta_tester_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER beta_tester_updated_at
BEFORE UPDATE ON beta_testers
FOR EACH ROW
EXECUTE FUNCTION update_beta_tester_updated_at();

-- 샘플 베타 테스터 (옵션)
-- INSERT INTO beta_testers (email, name, benefit_type, benefit_value, status)
-- VALUES ('beta@example.com', 'Test User', 'free_trial', 90, 'active');