"""Bộ mã sổ VIỆC CHẠY NGẦM (bao-CR-703) — trạng thái lần chạy + nhóm việc. Số đã cấp KHÔNG ĐỔI, KHÔNG TÁI DÙNG.

Thuần stdlib: `code_sets.py` phải nạp được khi chạy `scripts/gen_status_ts.py`.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class JobRunStatus(IntEnum):
    """Kết cục một lần chạy việc nền — cột `tab_job_run.status` (SMALLINT)."""

    RUNNING = 1      # đang chạy (chưa có tín hiệu kết thúc)
    SUCCESS = 2      # chạy xong
    FAILED = 3       # ném lỗi
    SKIPPED = 4      # việc tự báo bỏ qua (công tắc tắt, chưa cấu hình, không có gì để làm theo luật của nó)


JOB_RUN_STATUS_LABELS = {JobRunStatus.RUNNING: "Đang chạy", JobRunStatus.SUCCESS: "Thành công",
                         JobRunStatus.FAILED: "Lỗi", JobRunStatus.SKIPPED: "Bỏ qua"}

#  Nhóm việc (mã chuỗi, chỉ để lọc / hiển thị).
JOB_GROUP_LABELS = {
    "cleanup": "Dọn dữ liệu",
    "backup": "Sao lưu / lưu trữ",
    "sync": "Đồng bộ hệ thống khác",
    "reminder": "Nhắc việc / thông báo",
    "stats": "Thống kê / gom số",
    "monitor": "Giám sát / cảnh báo",
    "bot": "Bot / trợ lý AI",
}

JOB_RUN_STATUS_SET = register(CodeSet(
    "job_run_status", "Trạng thái việc chạy ngầm",
    [Code(str(int(k)), v, sort_order=int(k), key=k.name) for k, v in JOB_RUN_STATUS_LABELS.items()]))
JOB_GROUP_SET = register(CodeSet(
    "job_group", "Nhóm việc chạy ngầm", [Code(k, v, sort_order=i) for i, (k, v) in enumerate(JOB_GROUP_LABELS.items())]))
