-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    avatar VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remark TEXT
);

-- 创建用户名索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 创建邮箱索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 创建API日志表
CREATE TABLE IF NOT EXISTS api_logs (
    id SERIAL PRIMARY KEY,
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    query_params TEXT,
    request_body TEXT,
    status_code INTEGER,
    response_body TEXT,
    duration FLOAT,
    user_id INTEGER,
    username VARCHAR(50),
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建路径索引
CREATE INDEX IF NOT EXISTS idx_api_logs_path ON api_logs(path);

-- 创建用户ID索引
CREATE INDEX IF NOT EXISTS idx_api_logs_user_id ON api_logs(user_id);

-- 创建时间索引
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_logs(created_at);

-- 插入默认管理员用户（密码：admin123）
-- 注意：这个密码哈希是 bcrypt 加密的 "admin123"
INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqVr/qvQqK',
    '系统管理员',
    TRUE,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- 查看创建的表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

