"""duoc-CR-687 — nhóm vị trí việc làm của Mẫu số 01/PLI tự suy từ cấp bậc + trình độ
(`employee/constants.job_category_of`, anh Được chốt 27/10/2026), và hai khóa báo cáo mới."""
import pytest

from app.core.report_keys import REPORT_META, ReportKey
from app.modules.employee import constants as c


@pytest.mark.parametrize("level, edu, expected", [
    (c.JOB_LEVEL_DEPUTY_MANAGER, c.EDUCATION_UNKNOWN, c.JOB_CATEGORY_MANAGER),     # quản lý thắng trình độ
    (c.JOB_LEVEL_EXECUTIVE, c.EDUCATION_HIGH_SCHOOL, c.JOB_CATEGORY_MANAGER),
    (c.JOB_LEVEL_TEAM_LEADER, c.EDUCATION_UNIVERSITY, c.JOB_CATEGORY_HIGH_SKILL),  # tổ trưởng chưa phải nhà quản lý
    (c.JOB_LEVEL_STAFF, c.EDUCATION_POSTGRADUATE, c.JOB_CATEGORY_HIGH_SKILL),
    (c.JOB_LEVEL_STAFF, c.EDUCATION_COLLEGE, c.JOB_CATEGORY_MID_SKILL),
    (c.JOB_LEVEL_STAFF, c.EDUCATION_INTERMEDIATE, c.JOB_CATEGORY_MID_SKILL),
    (c.JOB_LEVEL_STAFF, c.EDUCATION_HIGH_SCHOOL, c.JOB_CATEGORY_OTHER),
    (None, None, c.JOB_CATEGORY_OTHER),                                             # hồ sơ trống không được ném lỗi
    (0, 99, c.JOB_CATEGORY_OTHER),                                                  # mã trình độ lạ → Khác
])
def test_suy_nhom_vi_tri(level, edu, expected):
    assert c.job_category_of(level, edu) == expected


def test_moi_nhom_co_nhan():
    assert set(c.JOB_CATEGORY_LABELS) == {c.JOB_CATEGORY_MANAGER, c.JOB_CATEGORY_HIGH_SKILL,
                                         c.JOB_CATEGORY_MID_SKILL, c.JOB_CATEGORY_OTHER}


def test_hai_khoa_dot_2():
    assert REPORT_META[ReportKey.LABOR_BOOK] == ("Sổ quản lý lao động", "Nhân sự")
    assert REPORT_META[ReportKey.LABOR_USAGE_REPORT] == ("Báo cáo sử dụng lao động (01/PLI)", "Nhân sự")
    assert (int(ReportKey.LABOR_BOOK), int(ReportKey.LABOR_USAGE_REPORT)) == (19, 20)
