-- Beta Tester Table (외래키 제약조건 제거 버전)
CREATE TABLE IF NOT EXISTS beta_testers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER,  -- 외래키 제거
    
    benefit_type VARCHAR(50) NOT NULL DEFAULT 'free_trial',
    benefit_value VARCHAR(255),
    
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    
    invited_by VARCHAR(255),
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_beta_testers_email ON beta_testers(email);
CREATE INDEX IF NOT EXISTS idx_beta_testers_status ON beta_testers(status);
CREATE INDEX IF NOT EXISTS idx_beta_testers_user_id ON beta_testers(user_id);

-- 업데이트 트리거
CREATE OR REPLACE FUNCTION update_beta_testers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS beta_testers_updated_at ON beta_testers;
CREATE TRIGGER beta_testers_updated_at
BEFORE UPDATE ON beta_testers
FOR EACH ROW
EXECUTE FUNCTION update_beta_testers_updated_at();
