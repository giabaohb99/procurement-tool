-- 12 TÀI KHOẢN TEST VĂN THƯ PHÁP NHÂN CON
-- Sinh ngày: 21/08/2026
-- Chỉ dùng cho DEV/UAT. Mật khẩu đoán được, TUYỆT ĐỐI không nạp production.
--
-- Điều kiện trước khi chạy:
--   1. Đích đã chạy `alembic upgrade head`.
--   2. Đích đã có 12 pháp nhân với `issue_code` tương ứng bên dưới.
--   3. Đích đã có phòng ban đang hoạt động tên chính xác `Phòng Hành chính`.
--   4. Sau khi nạp, restart API để xóa permission cache đang giữ trong process.
--
-- File idempotent: chạy lại sẽ cập nhật đúng dữ liệu test, không đẻ tài khoản trùng.
-- Mật khẩu của mỗi tài khoản = chính mã đăng nhập, ví dụ VTSAM / VTSAM.

SET NAMES utf8mb4;
SET @OLD_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

DROP TEMPORARY TABLE IF EXISTS tmp_van_thu_test_account;
CREATE TEMPORARY TABLE tmp_van_thu_test_account (
    issue_code VARCHAR(20) NOT NULL PRIMARY KEY,
    employee_code VARCHAR(25) NOT NULL UNIQUE,
    login_email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

INSERT INTO tmp_van_thu_test_account
    (issue_code, employee_code, login_email, password_hash)
VALUES
    ('ABA',         'VTABA',         'vtaba@dego.test',         '$2b$12$uGRNyNna2BZnyL0cK25mJuaOoLWlGeEhkjOHixQjX.gp9EWybOGHa'),
    ('AGRIPLANT',   'VTAGRIPLANT',   'vtagriplant@dego.test',   '$2b$12$X0M/bhxmcLsjpLRwq50JROSEWyx5Gu8/eaPooYQ8XAWeeoLUtrwcq'),
    ('BAMBOO',      'VTBAMBOO',      'vtbamboo@dego.test',      '$2b$12$Srla8lBnf2zmELVuiaNyDu1xoCM3dg9z9WurxXVsEYq6GYaTuclGy'),
    ('DEGOHOLDING', 'VTDEGOHOLDING', 'vtdegoholding@dego.test', '$2b$12$VomDMGzfKCXCVDn7slG/u.SAj5IZC2fJHvNRrz2ZjUGbsJ/wIOdmK'),
    ('DRXANH',      'VTDRXANH',      'vtdrxanh@dego.test',      '$2b$12$81xz6vfY3k8tUZ.LiLab2uTHe5PbGwUhRhDhZNByYiwcv9mLarOjm'),
    ('HKDDRXANH',   'VTHKDDRXANH',   'vthkddrxanh@dego.test',   '$2b$12$/8hTKHCnFxt0JdR.ldQlM.HZnwPk.2XVPxNPuMHL/KEF1nDcmooWK'),
    ('ICARE',       'VTICARE',       'vticare@dego.test',       '$2b$12$B9NgglH1giHXYwrEIX5giOMqlkpnkIId8VkxwPb9VH1dBZZ9R8wdu'),
    ('IDA',         'VTIDA',         'vtida@dego.test',         '$2b$12$Go6w0T3Z6O7rmhNDuPHGnO7Lcr5SSsaZHjP.yilY/wdAoniV2HAN.'),
    ('N2SBIO',      'VTN2SBIO',      'vtn2sbio@dego.test',      '$2b$12$KebJpv/o6Y48s.EGqaI0T.Ndh4ZXEmUerbwtEaBPTbC7q3gh1B28.'),
    ('NNABA',       'VTNNABA',       'vtnnaba@dego.test',       '$2b$12$1/.ko8927osUQpKQep0ykuT2O/omoxpcI.KsNASXT4GJ.D/i5OVX6'),
    ('NNDEGO',      'VTNNDEGO',      'vtnndego@dego.test',      '$2b$12$eT6bXscW9MMu8/wgDNuXyeogKyUA/cGTZRW/asG7fn5jFFVFCaSd.'),
    ('SAM',         'VTSAM',         'vtsam@dego.test',         '$2b$12$SH.FPnmBtanqhuQnGAxeH.TwKA8RUutYKthULKClEgYhpXsmCrcXq');

START TRANSACTION;

SET @actor_id = COALESCE(
    (SELECT MIN(id) FROM tab_user WHERE email IN ('admin', 'DEGO0001')),
    0
);

-- Vai trò riêng cho văn thư pháp nhân con.
INSERT INTO tab_role
    (code, name, description, created_by, updated_by)
VALUES
    ('vanthu_phapnhan', 'Văn thư pháp nhân con (Demo)',
     'Tài khoản test DEV/UAT cho luồng nhận bản clone và tự ban hành tại pháp nhân con.',
     @actor_id, @actor_id)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    updated_at = CURRENT_TIMESTAMP,
    updated_by = @actor_id;

SET @role_id = (
    SELECT id FROM tab_role WHERE code = 'vanthu_phapnhan' LIMIT 1
);

-- Ghi đè đúng bộ quyền do tài khoản test này quản lý.
DELETE FROM tab_permission WHERE role_id = @role_id;

INSERT INTO tab_permission
    (role_id, entity,
     can_read, can_create, can_write, can_delete,
     can_approve, can_cancel, can_print, can_export,
     scope, created_by, updated_by)
VALUES
    (@role_id, 'document',      1, 1, 1, 0, 1, 0, 1, 1, 'company', @actor_id, @actor_id),
    (@role_id, 'doc_type',      1, 0, 0, 0, 0, 0, 0, 0, 'all',     @actor_id, @actor_id),
    (@role_id, 'company',       1, 0, 0, 0, 0, 0, 0, 0, 'all',     @actor_id, @actor_id),
    (@role_id, 'department',    1, 0, 0, 0, 0, 0, 0, 0, 'all',     @actor_id, @actor_id),
    (@role_id, 'employee',      1, 0, 0, 0, 0, 0, 0, 0, 'all',     @actor_id, @actor_id),
    (@role_id, 'doc_book',      1, 0, 0, 0, 0, 0, 0, 0, 'all',     @actor_id, @actor_id),
    (@role_id, 'approval_flow', 1, 0, 0, 0, 0, 0, 0, 0, 'all',     @actor_id, @actor_id);

SET @department_id = (
    SELECT id
    FROM tab_department
    WHERE name = 'Phòng Hành chính' AND is_active = 1
    ORDER BY id
    LIMIT 1
);

-- Không tìm thấy pháp nhân/phòng thì SELECT không sinh dòng, tránh gán sai ID.
INSERT INTO tab_employee
    (code, full_name, email, phone,
     company_id, department_id, position, role_name, status, is_active,
     created_by, updated_by)
SELECT
    source.employee_code,
    CONCAT('Văn thư ', source.issue_code),
    source.login_email,
    '',
    company.id,
    department.id,
    'Văn thư',
    '',
    'Chính thức',
    1,
    @actor_id,
    @actor_id
FROM tmp_van_thu_test_account AS source
JOIN tab_company AS company
    ON company.issue_code = source.issue_code
   AND company.is_active = 1
JOIN tab_department AS department
    ON department.id = @department_id
ON DUPLICATE KEY UPDATE
    full_name = VALUES(full_name),
    email = VALUES(email),
    company_id = VALUES(company_id),
    department_id = VALUES(department_id),
    position = VALUES(position),
    status = VALUES(status),
    is_active = 1,
    updated_at = CURRENT_TIMESTAMP,
    updated_by = @actor_id;

-- Nếu tài khoản đã tồn tại theo email hoặc nhân sự thì cập nhật thay vì tạo trùng.
UPDATE tab_user AS account
JOIN tab_employee AS employee
    ON account.employee_id = employee.id
JOIN tmp_van_thu_test_account AS source
    ON source.employee_code = employee.code
SET
    account.email = source.login_email,
    account.google_sub = '',
    account.password_hash = source.password_hash,
    account.is_active = 1,
    account.updated_at = CURRENT_TIMESTAMP,
    account.updated_by = @actor_id;

UPDATE tab_user AS account
JOIN tmp_van_thu_test_account AS source
    ON source.login_email = account.email
JOIN tab_employee AS employee
    ON employee.code = source.employee_code
SET
    account.employee_id = employee.id,
    account.google_sub = '',
    account.password_hash = source.password_hash,
    account.is_active = 1,
    account.updated_at = CURRENT_TIMESTAMP,
    account.updated_by = @actor_id;

INSERT INTO tab_user
    (email, google_sub, password_hash, employee_id, avatar, signature, is_active,
     created_by, updated_by)
SELECT
    source.login_email,
    '',
    source.password_hash,
    employee.id,
    '',
    '',
    1,
    @actor_id,
    @actor_id
FROM tmp_van_thu_test_account AS source
JOIN tab_employee AS employee
    ON employee.code = source.employee_code
WHERE NOT EXISTS (
    SELECT 1
    FROM tab_user AS existing
    WHERE existing.employee_id = employee.id
       OR existing.email = source.login_email
);

-- Mỗi tài khoản test chỉ mang vai trò văn thư demo và scope đúng pháp nhân mình.
DELETE role_grant
FROM tab_user_role AS role_grant
JOIN tab_user AS account ON account.id = role_grant.user_id
JOIN tab_employee AS employee ON employee.id = account.employee_id
JOIN tmp_van_thu_test_account AS source ON source.employee_code = employee.code;

DELETE data_scope
FROM tab_user_scope AS data_scope
JOIN tab_user AS account ON account.id = data_scope.user_id
JOIN tab_employee AS employee ON employee.id = account.employee_id
JOIN tmp_van_thu_test_account AS source ON source.employee_code = employee.code;

INSERT INTO tab_user_role
    (user_id, role_id, created_by, updated_by)
SELECT
    account.id,
    @role_id,
    @actor_id,
    @actor_id
FROM tmp_van_thu_test_account AS source
JOIN tab_employee AS employee ON employee.code = source.employee_code
JOIN tab_user AS account ON account.employee_id = employee.id;

INSERT INTO tab_user_scope
    (user_id, role_id, entity, dim, value, is_exclude, created_by, updated_by)
SELECT
    account.id,
    @role_id,
    '',
    'company',
    CAST(company.id AS CHAR),
    0,
    @actor_id,
    @actor_id
FROM tmp_van_thu_test_account AS source
JOIN tab_company AS company
    ON company.issue_code = source.issue_code
   AND company.is_active = 1
JOIN tab_employee AS employee ON employee.code = source.employee_code
JOIN tab_user AS account ON account.employee_id = employee.id;

COMMIT;

SET FOREIGN_KEY_CHECKS = @OLD_FOREIGN_KEY_CHECKS;

-- Kết quả phải là 12/12. Nếu `status = THIẾU PHÁP NHÂN` thì nạp danh mục công ty
-- trước rồi chạy lại nguyên file này.
SELECT
    source.employee_code AS username,
    source.employee_code AS password,
    company.name AS company_name,
    CASE
        WHEN company.id IS NULL THEN 'THIẾU PHÁP NHÂN'
        WHEN account.id IS NULL THEN 'CHƯA TẠO ĐƯỢC TÀI KHOẢN'
        ELSE 'OK'
    END AS status
FROM tmp_van_thu_test_account AS source
LEFT JOIN tab_company AS company
    ON company.issue_code = source.issue_code
   AND company.is_active = 1
LEFT JOIN tab_employee AS employee
    ON employee.code = source.employee_code
LEFT JOIN tab_user AS account
    ON account.employee_id = employee.id
ORDER BY source.employee_code;

DROP TEMPORARY TABLE IF EXISTS tmp_van_thu_test_account;
