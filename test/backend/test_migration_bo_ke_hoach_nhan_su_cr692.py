"""duoc-CR-692 — migration `hcplan05` (bỏ «Kế hoạch nhân sự»): hàm thuần chọn xử lý loại văn bản CCKHNS + thứ tự DROP."""
import importlib.util
from pathlib import Path

import pytest

def _find_migration() -> Path:
    """Host: <repo>/backend/migrations/...; trong container `api`: /app/migrations/... — thử cả hai."""
    for base in Path(__file__).resolve().parents:
        for rel in ("backend/migrations/versions", "migrations/versions"):
            cand = base / rel / "hcplan05_bo_ke_hoach_nhan_su.py"
            if cand.exists():
                return cand
    raise FileNotFoundError("hcplan05_bo_ke_hoach_nhan_su.py")


_PATH = _find_migration()


@pytest.fixture(scope="module")
def mig():
    spec = importlib.util.spec_from_file_location("hcplan05_under_test", _PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_chuoi_revision(mig):
    assert (mig.revision, mig.down_revision) == ("hcplan05", "hcplan04")


@pytest.mark.parametrize("so_van_ban,ky_vong", [(0, "delete"), (1, "deactivate"), (37, "deactivate")])
def test_loai_van_ban_chua_dung_thi_xoa_da_dung_thi_ngung(mig, so_van_ban, ky_vong):
    assert mig.doc_type_action(so_van_ban) == ky_vong


def test_drop_du_bay_bang_va_khong_tai_cap_khoa_bao_cao_25(mig):
    assert len(mig.DROP_ORDER) == 7 and len(set(mig.DROP_ORDER)) == 7
    assert mig.DROP_ORDER.index("tab_headcount_plan_line") < mig.DROP_ORDER.index("tab_headcount_plan")
    assert mig.DROP_ORDER.index("tab_hr_cost_template_item") < mig.DROP_ORDER.index("tab_hr_cost_template")
    assert mig.REPORT_KEY_RETIRED == 25
    from app.core.report_keys import REPORT_META, ReportKey
    from app.core.report_keys import RETIRED_REPORT_KEYS
    assert RETIRED_REPORT_KEYS == frozenset({25})
    assert 25 not in {int(k) for k in ReportKey} and 25 not in {int(k) for k in REPORT_META}
    assert len(ReportKey) == 28 and max(int(k) for k in ReportKey) == 29     # không khóa nào khác bị đổi số
