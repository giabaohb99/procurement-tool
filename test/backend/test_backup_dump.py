"""Kiểm thử phần dựng lệnh dump của module sao lưu (CR-059).

Bối cảnh: CSDL chuyển từ MariaDB sang MySQL 8.4. Client trong image api là MariaDB,
nên (1) phải tắt xác thực chứng chỉ tự ký của MySQL, (2) phải cắt dòng "sandbox mode"
mà mariadb-dump chèn vào, nếu không bản backup không phục hồi được sang MySQL.
"""
from app.modules.backup.service import _bo_dong_sandbox


SANDBOX = b"/*!999999\\- enable the sandbox mode */"


def test_cat_dong_sandbox_o_dau_file():
    sql = SANDBOX + b"\n-- MariaDB dump\nCREATE TABLE a (id INT);\n"
    ra = _bo_dong_sandbox(sql)
    assert b"sandbox mode" not in ra
    assert b"CREATE TABLE a (id INT);" in ra


def test_giu_nguyen_dump_khong_co_sandbox():
    sql = b"-- MySQL dump\nCREATE TABLE a (id INT);\n"
    assert _bo_dong_sandbox(sql) == sql


def test_khong_dung_toi_du_lieu_tieng_viet():
    sql = SANDBOX + b"\nINSERT INTO t VALUES ('Th\xc3\xb9ng carton \xc4\x91\xe1\xbb\xa7 d\xe1\xba\xa5u');\n"
    ra = _bo_dong_sandbox(sql)
    assert ra.decode("utf-8").strip() == "INSERT INTO t VALUES ('Thùng carton đủ dấu');"


def test_chi_cat_dong_sandbox_khong_cat_dong_khac():
    sql = SANDBOX + b"\nA\nB\nC\n"
    assert _bo_dong_sandbox(sql).count(b"\n") == sql.count(b"\n") - 1
