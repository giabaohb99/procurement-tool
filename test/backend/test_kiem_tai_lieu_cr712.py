"""bao-CR-712 P5: cổng kiểm tài liệu — `backend/scripts/kiem_tai_lieu.py` phải không có lỗi MỚI (ngoài tệp nền).

Lỗi đã có lúc bật chế độ chặn nằm trong `backend/scripts/kiem_tai_lieu_nen.txt` (chỉ báo); lỗi ngoài nền làm đỏ bài này.
Sửa xong lỗi trong nền thì chạy `python backend/scripts/kiem_tai_lieu.py --cap-nhat-nen` để bớt dòng.

Gốc repo: biến `KIEM_TAI_LIEU_ROOT` (container api mount cả repo chỉ-đọc ở /repo, xem docker-compose.yml), không có thì
lấy thư mục cha của `test/`. Không thấy `doc/` + `CLAUDE.md` (container dựng từ compose cũ chưa có mount) thì skip.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(os.environ.get("KIEM_TAI_LIEU_ROOT") or Path(__file__).resolve().parents[2])
#  Chạy ĐÚNG bản script nằm cạnh mã đang kiểm: container api có nó ở /app/scripts (gốc repo /repo có thể là checkout
#  khác, cũ hơn); máy thật thì ở <gốc>/backend/scripts.
_HERE = Path(__file__).resolve().parents[2]
SCRIPT = next((p for p in (_HERE / "scripts" / "kiem_tai_lieu.py", _HERE / "backend" / "scripts" / "kiem_tai_lieu.py")
               if p.is_file()), ROOT / "backend" / "scripts" / "kiem_tai_lieu.py")


@pytest.mark.skipif(not ((ROOT / "doc").is_dir() and (ROOT / "CLAUDE.md").is_file() and SCRIPT.is_file()),
                    reason="không thấy gốc repo (doc/ + CLAUDE.md) — container api chưa có mount /repo")
def test_tai_lieu_khong_co_loi_moi():
    run = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=120)
    assert run.returncode == 0, "Bài kiểm tài liệu có lỗi MỚI (dòng đánh dấu MỚI):\n" + run.stdout[-4000:] + run.stderr[-2000:]
