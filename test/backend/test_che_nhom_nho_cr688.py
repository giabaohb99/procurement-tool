"""duoc-CR-688 — luật che nhóm nhỏ dùng chung (`core/report_small_group.py`) + A2 dùng hàm chung.

Bài thuần (không DB): dựng `data` tay rồi gọi hàm; bài A2 kỳ so sánh ở `test_bao_cao_co_cau_cr687.py`.
"""
from app.core.report_small_group import drop_unsafe_breakdown, suppress_small_groups

N, X = "ghi chú", "che thêm"


def _g(key, cur, cmp=None):
    return {"key": key, "label": key, "current": {"n": cur}, "compare": None if cmp is None else {"n": cmp}}


def _run(groups):
    data = {"groups": groups, "notes": []}
    changed = suppress_small_groups(data, lambda v: [v["n"] or 0], lambda v: v["n"] or 0, N, X)
    return data, {g["key"]: g for g in groups}, changed


def _hidden(g):
    return g.get("suppressed") is True and all(v is None for s in ("current", "compare")
                                               if g[s] for v in g[s].values())


def test_khong_nhom_nho_thi_khong_che_va_khong_ghi_chu():
    data, g, changed = _run([_g("a", 5), _g("b", 3), _g("c", 0)])
    assert not changed and data["notes"] == [] and not any(x.get("suppressed") for x in g.values())


def test_hai_nhom_nho_tong_tu_3_nguoi_la_du():
    data, g, _ = _run([_g("a", 6), _g("b", 1), _g("c", 2)])
    assert _hidden(g["b"]) and _hidden(g["c"]) and not g["a"].get("suppressed")
    assert data["notes"] == [N]


def test_mot_nhom_nho_che_them_nhom_nho_nhat_con_hien():
    data, g, _ = _run([_g("a", 9), _g("b", 4), _g("c", 1)])
    assert _hidden(g["c"]) and _hidden(g["b"]) and not g["a"].get("suppressed")
    assert data["notes"] == [N, X]


def test_hai_nhom_1_nguoi_tong_2_nguoi_phai_che_them():
    _, g, _ = _run([_g("a", 9), _g("b", 1), _g("c", 1), _g("d", 5)])
    assert _hidden(g["b"]) and _hidden(g["c"]) and _hidden(g["d"]) and not g["a"].get("suppressed")


def test_nhom_toan_0_khong_tinh_la_nhom_bi_che():
    _, g, _ = _run([_g("a", 9), _g("z", 0), _g("b", 1), _g("c", 4)])
    assert _hidden(g["c"]) and not g["z"].get("suppressed")


def test_che_ca_nhom_neu_ky_so_sanh_la_1_hoac_2():
    _, g, _ = _run([_g("a", 8, 8), _g("b", 5, 2), _g("c", 4, 4)])
    assert _hidden(g["b"]) and g["b"]["current"] == {"n": None}


def test_che_phu_xet_rieng_tung_ky():
    """Kỳ này b,c bị che đủ (2 nhóm, 6 người) nhưng kỳ trước b là 1 người, c là 0 -> kỳ trước chỉ còn MỘT
    nhóm bị che có người -> phải che thêm nhóm nhỏ nhất còn hiện của KỲ TRƯỚC (d), dù kỳ này không cần."""
    _, g, _ = _run([_g("a", 20, 20), _g("b", 1, 1), _g("c", 1, 0), _g("d", 6, 3)])
    assert _hidden(g["b"]) and _hidden(g["c"])
    assert _hidden(g["d"]) and not g["a"].get("suppressed")


def test_nhom_chi_co_o_ky_so_sanh_van_duoc_xet():
    _, g, _ = _run([_g("a", 10, 10), _g("b", 0, 2), _g("c", 5, 5)])
    assert _hidden(g["b"]) and _hidden(g["c"])        # kỳ trước: b (2 người) một mình -> che thêm c


def test_chi_con_mot_nhom_nho_thi_khong_cuu_duoc():
    data, g, res = _run([_g("a", 2)])
    assert res.changed and res.unsafe_sides == ("current",) and _hidden(g["a"])


def test_hai_nhom_1_nguoi_khong_con_nhom_de_che_them_la_khong_an_toan():
    _, _, res = _run([_g("a", 1), _g("b", 1)])
    assert res.unsafe_sides == ("current",)


def test_truong_hop_binh_thuong_khong_bao_khong_an_toan():
    _, _, res = _run([_g("a", 6), _g("b", 1), _g("c", 2)])
    assert res.changed and res.unsafe_sides == ()
    _, _, res = _run([_g("a", 9), _g("b", 4), _g("c", 1)])
    assert res.unsafe_sides == ()


def test_che_phu_chi_kich_hoat_o_ky_co_nhom_nho_that():
    """b nhỏ chỉ ở kỳ trước (1 người), kỳ này b có 50 người: kỳ này không cần bù, chỉ kỳ trước."""
    _, g, res = _run([_g("a", 20, 20), _g("b", 50, 1), _g("c", 7, 7)])
    assert _hidden(g["b"]) and _hidden(g["c"]) and res.unsafe_sides == ()    # kỳ trước: b + c (8 người) đủ


def test_bo_bang_nhom_khi_khong_an_toan():
    data = {"groups": [_g("a", 2)], "notes": [], "breakdowns": {"age_band": [{"key": "x"}]}}
    drop_unsafe_breakdown(data, "age_band", "nhóm tuổi")
    assert data["groups"] == [] and data["breakdowns"]["age_band"] == []
    assert "Không đủ người để xem theo nhóm tuổi" in data["notes"][-1]
