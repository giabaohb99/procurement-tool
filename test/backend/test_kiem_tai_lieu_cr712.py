"""bao-CR-712 P5: cổng kiểm tài liệu — `backend/scripts/kiem_tai_lieu.py` phải không có lỗi MỚI (ngoài tệp nền).

Lỗi đã có lúc bật chế độ chặn nằm trong `backend/scripts/kiem_tai_lieu_nen.txt` (chỉ báo); lỗi ngoài nền làm đỏ bài này.
Sửa xong lỗi trong nền thì chạy `python backend/scripts/kiem_tai_lieu.py --cap-nhat-nen` để bớt dòng.

Container api chỉ mount `backend/` + `test/` (không có `doc/`) → bài tự skip; chạy ở máy thật / CI:
`python -m pytest test/backend/test_kiem_tai_lieu_cr712.py -q`.
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend" / "scripts" / "kiem_tai_lieu.py"


@pytest.mark.skipif(not ((ROOT / "doc").is_dir() and (ROOT / "CLAUDE.md").is_file() and SCRIPT.is_file()),
                    reason="không thấy gốc repo (doc/ + CLAUDE.md) — container api không mount doc/")
def test_tai_lieu_khong_co_loi_moi():
    run = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=300)
    assert run.returncode == 0, "Bài kiểm tài liệu có lỗi MỚI (dòng đánh dấu MỚI):\n" + run.stdout[-4000:] + run.stderr[-2000:]
