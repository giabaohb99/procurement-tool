"""ai-CR-235 — bốn cẩm nang văn phòng (đặt xe, duyệt dấu, diễn đàn, kho) trong bộ SYS-HANDBOOK.

Canh: cẩm nang chỉ được nhắc công cụ CÓ THẬT (đổi tên công cụ mà quên sửa cẩm nang thì trợ lý gọi công cụ ma), không
emoji, không ngoặc kép góc.
"""
import re

import pytest

from app.modules.ai_skill import handbook_seed
from app.modules.assistant.tools import _active_specs

OFFICE_SLUGS = [s for _f, s, _sum in handbook_seed.SKILLS if s in ("dat-xe", "duyet-dau", "dien-dan", "kho")]
#  Chữ trong `...` trông như tên công cụ: draft_* / confirm_* / *_read.
TOOL_LIKE = re.compile(r"`((?:draft|confirm)_[a-z_]+|[a-z_]+_read)`")
MCP_ONLY = {"confirm_draft"}   # chỉ cổng MCP có, sổ Trợ lý không có
FORBIDDEN = re.compile("[«»☀-➿\U0001f300-\U0001faff]")


def _bodies() -> dict[str, str]:
    return {slug: body for slug, _t, _s, body in handbook_seed.seed_files() if slug in OFFICE_SLUGS}


def test_cam_nang_van_phong_co_trong_bo_hat_giong():
    assert OFFICE_SLUGS, "chưa khai cẩm nang văn phòng nào trong SKILLS"


@pytest.mark.parametrize("slug", OFFICE_SLUGS)
def test_chi_nhac_cong_cu_co_that(slug):
    real = {s.name for s in _active_specs()} | MCP_ONLY
    named = set(TOOL_LIKE.findall(_bodies()[slug]))
    assert named, f"{slug}: cẩm nang không nhắc công cụ nào"
    assert named <= real, f"{slug}: nhắc công cụ không có thật {sorted(named - real)}"


@pytest.mark.parametrize("slug", OFFICE_SLUGS)
def test_khong_emoji_khong_ngoac_goc(slug):
    assert not FORBIDDEN.search(_bodies()[slug])
