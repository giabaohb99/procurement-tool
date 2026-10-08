-- ai-CR-119 — tạo database + tài khoản riêng cho dịch vụ AI trên MySQL dùng chung. Chạy bằng root, THAY mật khẩu:
--   docker exec -i procurement-mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql' < create_agent_db.sql
CREATE DATABASE IF NOT EXISTS agent_hub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'agent_hub'@'%' IDENTIFIED BY 'THAY_MAT_KHAU';
GRANT ALL PRIVILEGES ON agent_hub.* TO 'agent_hub'@'%';
-- Máy sửa mã (tài khoản agent_runner, doc/agent-hub/05) đọc / ghi bảng của bot: trỏ sang DB mới.
GRANT SELECT, INSERT, UPDATE ON agent_hub.* TO 'agent_runner'@'%';
FLUSH PRIVILEGES;
