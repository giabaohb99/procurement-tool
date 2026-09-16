"""Sổ đồng bộ chung `tab_sync_log` — P0 của việc nối app đặt xe cũ vào ERP.

Ba vùng được canh ở đây, đều là chỗ hỏng thì hỏng âm thầm:

1. **Chống trùng + không ghi đè lịch sử.** `event_id` UNIQUE và mặc định là
   chuỗi rỗng — mà MySQL coi mỗi chuỗi rỗng là một GIÁ TRỊ THẬT, nên dòng thứ hai
   tạo tay là đụng khóa. Mọi dòng phải đi qua `service.py`.
2. **Chữ ký HMAC.** Sai công thức thì không ai nhận ra cho tới lúc hệ ngoài gọi
   sang thật; lỏng chốt lệch giờ thì bắt được một yêu cầu hợp lệ là phát lại
   được mãi mãi.
3. **Gộp `tab_pos_sync_run` vào sổ chung.** Bộ mã trạng thái ĐÃ ĐỔI SỐ
   (PosSyncStatus RUNNING=1 -> SyncStatus RUNNING=2). Đọc nhầm một bậc thì mọi
   lượt chạy thành công cũ hiện thành "đang chạy" — sai mà không ai báo lỗi.
"""
import pytest

from app.core.sync_signature import (HEADER_SIGNATURE, HEADER_SOURCE,
                                     HEADER_TIMESTAMP, build_signature,
                                     sign_headers, verify_signature)
from app.modules.sync_log.constants import (SIGNATURE_MAX_SKEW_SECONDS, SyncGrain,
                                            SyncStatus)
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import (SOURCE_DATXE, SOURCE_POS365, get_source,
                                           require_source)
from app.modules.sync_log.service import (add_warning, clone_for_retry, compute_hash,
                                          finish_failed, finish_ok, finish_run,
                                          is_sync_in_progress, is_unchanged,
                                          join_warnings, last_successful_run,
                                          open_entry, open_run, purge_success,
                                          recent_runs, suppress_outbound)


# ── 1. Vòng đời một dòng sổ ─────────────────────────────────────────────────────

def test_ghi_dong_cho_truoc_khi_lam(db):
    """Luật §3.2 điều 1: dòng *chờ* phải nằm dưới DB TRƯỚC khi ai kịp làm gì.

    `open_entry` tự commit. Không commit thì tiến trình chết giữa chừng là không
    để lại dấu vết nào — đúng lúc cần sổ nhất thì sổ trống.
    """
    entry = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                       legacy_id="DD000153", event_id="ev-1")
    assert entry is not None
    assert entry.status == int(SyncStatus.PENDING)
    assert entry.grain == int(SyncGrain.RECORD)
    #  Phiên khác đọc ra được = đã thật sự xuống DB, không nằm trong bộ nhớ.
    assert db.query(SyncLog).filter(SyncLog.event_id == "ev-1").count() == 1


def test_hai_dong_khong_co_event_id_van_ghi_duoc(db):
    """`event_id` UNIQUE + mặc định RỖNG là một cái bẫy: tạo tay hai dòng không
    truyền mã là dòng thứ hai đụng khóa. `open_entry` phải tự sinh mã."""
    a = open_entry(db, source=SOURCE_DATXE, entity="vehicle_booking", legacy_id="A")
    b = open_entry(db, source=SOURCE_DATXE, entity="vehicle_booking", legacy_id="B")
    assert a is not None and b is not None
    assert a.event_id and b.event_id and a.event_id != b.event_id


def test_su_kien_lap_tra_ve_none(db):
    """Hệ ngoài bắn lại đúng một sự kiện (mạng chập, nó thử lại) — không được
    tạo dòng thứ hai, và người gọi phải BIẾT là trùng để mà dừng."""
    first = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                       legacy_id="DD1", event_id="ev-trung")
    second = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                        legacy_id="DD1", event_id="ev-trung")
    assert first is not None
    assert second is None
    assert db.query(SyncLog).count() == 1


def test_nguon_chua_khai_thi_nem_loi(db):
    """Gõ sai mã nguồn phải nổ ngay, đừng ghi vào sổ một mã rác rồi để người sau
    đi tra xem 'pos356' là hệ nào."""
    with pytest.raises(ValueError):
        open_entry(db, source="khong-co-that", entity="x")


def test_chay_lai_sinh_dong_moi_giu_dong_cu(db):
    """Luật §3.2 điều 2: một dòng = một sự kiện. Lần thử thứ hai là sự kiện
    KHÁC — phải nhìn thấy cả hai, không ghi đè lên dấu vết lần hỏng."""
    entry = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                       legacy_id="DD9", event_id="ev-hong")
    finish_failed(db, entry, "POS bên kia trả 500")
    fresh = clone_for_retry(db, entry, user_id=7)

    assert fresh.id != entry.id
    assert fresh.status == int(SyncStatus.PENDING)
    assert fresh.event_id != entry.event_id
    assert fresh.legacy_id == entry.legacy_id
    #  Dòng cũ còn nguyên trạng thái lỗi và câu lỗi nguyên văn.
    db.refresh(entry)
    assert entry.status == int(SyncStatus.FAILED)
    assert entry.message == "POS bên kia trả 500"


def test_dong_thanh_cong_van_mang_duoc_co_canh_bao(db):
    """Cờ cảnh báo KHÔNG phải trạng thái lỗi. Phiếu nạp xong nhưng thiếu người
    yêu cầu vẫn là *thành công* — cờ mới là đường lọc lại dữ liệu bịa sau này."""
    entry = open_entry(db, source=SOURCE_DATXE, entity="vehicle_booking",
                       legacy_id="V1", event_id="ev-co")
    finish_ok(db, entry, "Đã tạo phiếu", local_id=42, warnings=["no_employee"])
    assert entry.status == int(SyncStatus.SUCCESS)
    assert entry.local_id == 42
    assert "no_employee" in entry.warning_list


# ── 2. Cờ cảnh báo ──────────────────────────────────────────────────────────────

def test_co_canh_bao_khu_trung_va_giu_thu_tu():
    assert join_warnings(["a", "b", "a", "", None, "c"]) == "a,b,c"


def test_co_canh_bao_cat_o_ranh_gioi_khong_cat_giua_co():
    """Cắt cho vừa String(255) nhưng KHÔNG được cắt giữa một cờ — đọc ra sẽ là
    một cờ không tồn tại, và chỗ này tồn tại chính để lọc theo cờ."""
    flags = [f"warning_flag_number_{i:03d}" for i in range(40)]
    text = join_warnings(flags)
    assert len(text) <= 255
    assert all(part in flags for part in text.split(","))


def test_add_warning_khong_lam_mat_co_cu(db):
    entry = open_entry(db, source=SOURCE_DATXE, entity="vehicle_booking",
                       legacy_id="V2", event_id="ev-co2", warnings=["no_employee"])
    add_warning(entry, "no_department")
    assert entry.warning_list == ["no_employee", "no_department"]


# ── 3. Băm nội dung và "có đổi gì không" ────────────────────────────────────────

def test_bam_khong_phu_thuoc_thu_tu_khoa():
    """Cùng nội dung, khác thứ tự khóa phải ra cùng mã băm — không thì lần nào
    cũng tưởng có thay đổi và sổ đầy dòng vô nghĩa."""
    assert compute_hash({"a": 1, "b": 2}) == compute_hash({"b": 2, "a": 1})
    assert compute_hash({"a": 1}) != compute_hash({"a": 2})


def test_lan_truoc_loi_thi_van_phai_lam_lai(db):
    """`is_unchanged` CHỈ tính dòng thành công. Lần trước lỗi mà nội dung y hệt
    thì vẫn phải thử lại — không thì một lỗi tạm thời khóa luôn bản ghi đó."""
    digest = compute_hash({"x": 1})
    hong = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                      legacy_id="DD7", event_id="ev-h1", content_hash=digest)
    finish_failed(db, hong, "mạng chập")
    assert is_unchanged(db, SOURCE_DATXE, "seal_request", "DD7", digest) is False

    ok = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                    legacy_id="DD7", event_id="ev-h2", content_hash=digest)
    finish_ok(db, ok, "xong", content_hash=digest)
    assert is_unchanged(db, SOURCE_DATXE, "seal_request", "DD7", digest) is True


def test_bam_rong_khong_bao_gio_la_khong_doi(db):
    """Chưa băm được (`""`) phải coi là CÓ thay đổi. Coi rỗng bằng rỗng thì mọi
    bản ghi chưa băm đều bị bỏ qua im lặng."""
    assert is_unchanged(db, SOURCE_DATXE, "seal_request", "DD8", "") is False


# ── 4. Dọn sổ — chỉ dọn dòng thành công ─────────────────────────────────────────

def test_don_so_khong_bao_gio_dung_dong_loi(db):
    """Luật §3.2 điều 3. Sổ mất dòng lỗi thì lúc đi tra một sự cố cũ không còn
    gì để đọc, mà đó đúng là lúc người ta mở sổ ra."""
    from datetime import datetime, timedelta

    cu = datetime.now() - timedelta(days=400)
    ok = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                    legacy_id="C1", event_id="ev-cu-ok")
    finish_ok(db, ok, "xong")
    hong = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                      legacy_id="C2", event_id="ev-cu-hong")
    finish_failed(db, hong, "hỏng từ đời nào")
    for row in (ok, hong):
        row.created_at = cu
    db.commit()

    assert purge_success(db, months=6) == 1
    con_lai = db.query(SyncLog).all()
    assert [r.event_id for r in con_lai] == ["ev-cu-hong"]


def test_don_so_chua_den_han_thi_khong_dung_gi(db):
    ok = open_entry(db, source=SOURCE_DATXE, entity="seal_request",
                    legacy_id="C3", event_id="ev-moi")
    finish_ok(db, ok, "xong")
    assert purge_success(db, months=6) == 0
    assert db.query(SyncLog).count() == 1


# ── 5. Chống dội ngược (§7) ─────────────────────────────────────────────────────

def test_co_chong_doi_nguoc_tra_ve_dung_trang_thai_cu():
    """Lồng nhau phải trả về đúng giá trị trước đó, không phải cứng `False` —
    thoát khỏi lớp trong mà tắt cờ là lớp ngoài bắt đầu bắn ngược."""
    assert is_sync_in_progress() is False
    with suppress_outbound():
        assert is_sync_in_progress() is True
        with suppress_outbound():
            assert is_sync_in_progress() is True
        assert is_sync_in_progress() is True
    assert is_sync_in_progress() is False


# ── 6. Chữ ký HMAC ──────────────────────────────────────────────────────────────

def test_chu_ky_doi_theo_tung_manh():
    """Đủ ba mảnh (giờ · đường dẫn · thân) mới ra chữ ký. Bỏ sót mảnh nào thì
    kẻ bắt được một yêu cầu đổi được mảnh đó mà chữ ký vẫn đúng."""
    base = build_signature("bi-mat", "1000", "/api/sync/push", '{"a":1}')
    assert base != build_signature("bi-mat", "1001", "/api/sync/push", '{"a":1}')
    assert base != build_signature("bi-mat", "1000", "/api/sync/pull", '{"a":1}')
    assert base != build_signature("bi-mat", "1000", "/api/sync/push", '{"a":2}')
    assert base != build_signature("khac", "1000", "/api/sync/push", '{"a":1}')


def test_ky_va_kiem_khop_nhau(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.SYNC_SHARED_SECRET", "khoa-test")
    monkeypatch.setattr("app.core.config.settings.SYNC_DATXE_ENABLED", True)
    headers = sign_headers(SOURCE_DATXE, "/api/sync/push", '{"id":1}')
    assert headers[HEADER_SOURCE] == SOURCE_DATXE
    ok, reason = verify_signature(
        SOURCE_DATXE, "/api/sync/push", '{"id":1}',
        headers[HEADER_TIMESTAMP], headers[HEADER_SIGNATURE])
    assert (ok, reason) == (True, "")


def test_lech_gio_qua_nam_phut_bi_tu_choi(monkeypatch):
    """Không chốt lệch giờ thì bắt được một yêu cầu hợp lệ là PHÁT LẠI được mãi
    mãi — chữ ký vẫn đúng vì nội dung không đổi."""
    monkeypatch.setattr("app.core.config.settings.SYNC_SHARED_SECRET", "khoa-test")
    monkeypatch.setattr("app.core.config.settings.SYNC_DATXE_ENABLED", True)
    timestamp = "1000000"
    sig = build_signature("khoa-test", timestamp, "/p", "")

    trong_han = 1000000 + SIGNATURE_MAX_SKEW_SECONDS
    assert verify_signature(SOURCE_DATXE, "/p", "", timestamp, sig, now=trong_han)[0]
    qua_han = trong_han + 1
    ok, reason = verify_signature(SOURCE_DATXE, "/p", "", timestamp, sig, now=qua_han)
    assert ok is False and reason == "Dấu thời gian lệch quá xa"
    #  Lệch về QUÁ KHỨ lẫn TƯƠNG LAI đều chặn: đồng hồ bên kia chạy nhanh cũng là
    #  một cách phát lại.
    assert verify_signature(SOURCE_DATXE, "/p", "", timestamp, sig,
                            now=1000000 - qua_han + 1000000)[0] is False


def test_chua_co_khoa_thi_khong_ky_bang_chuoi_rong(monkeypatch):
    """Thiếu khóa phải NỔ lúc gửi. Ký bằng chuỗi rỗng thì mọi yêu cầu vẫn đi và
    bên kia vẫn nhận — chữ ký biến thành trang trí."""
    monkeypatch.setattr("app.core.config.settings.SYNC_SHARED_SECRET", "")
    #  Phải bật nguồn thì mới tới được chốt khóa: `verify_signature` gác cờ bật
    #  TRƯỚC, nên để nguyên mặc định là nhận câu "Hệ nguồn đang tắt đồng bộ".
    monkeypatch.setattr("app.core.config.settings.SYNC_DATXE_ENABLED", True)
    with pytest.raises(ValueError):
        sign_headers(SOURCE_DATXE, "/p")
    ok, reason = verify_signature(SOURCE_DATXE, "/p", "", "1", "x", now=1)
    assert ok is False and reason == "Hệ nguồn chưa cấu hình khóa ký"


def test_nguon_dang_tat_thi_tu_choi(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.SYNC_SHARED_SECRET", "khoa-test")
    monkeypatch.setattr("app.core.config.settings.SYNC_DATXE_ENABLED", False)
    ok, reason = verify_signature(SOURCE_DATXE, "/p", "", "1", "x", now=1)
    assert ok is False and reason == "Hệ nguồn đang tắt đồng bộ"


def test_ly_do_tu_choi_khong_chi_cho_ke_do(monkeypatch):
    """Câu lý do ghi thẳng vào sổ, nên nó cố ý KHÔNG nói chữ ký sai ở chỗ nào.

    Chữ ký ở đây CÓ DẤU là cố ý, đừng sửa thành chuỗi thuần ASCII: bản đầu so bằng
    `hmac.compare_digest` trên chuỗi, mà hàm đó ném TypeError khi gặp ký tự ngoài
    ASCII — gửi một header rác là đổ 500 thay vì bị từ chối gọn (sửa 16/09/2026).
    """
    monkeypatch.setattr("app.core.config.settings.SYNC_SHARED_SECRET", "khoa-test")
    monkeypatch.setattr("app.core.config.settings.SYNC_DATXE_ENABLED", True)
    ok, reason = verify_signature(SOURCE_DATXE, "/p", "", "1000000", "sai-be-bét",
                                  now=1000000)
    assert ok is False and reason == "Chữ ký không khớp"


# ── 7. Cầu dao NGẮT của POS365 (cờ ngược chiều) ─────────────────────────────────

def test_cau_dao_pos365_la_co_nguoc(monkeypatch):
    """`POS365_HARD_OFF` bật = TẮT đồng bộ — ngược chiều `SYNC_DATXE_ENABLED`.
    Đọc cùng chiều thì cầu dao ngắt hóa ra lại là công tắc bật."""
    source = require_source(SOURCE_POS365)
    monkeypatch.setattr("app.core.config.settings.POS365_HARD_OFF", True)
    assert source.is_enabled() is False
    monkeypatch.setattr("app.core.config.settings.POS365_HARD_OFF", False)
    assert source.is_enabled() is True


def test_pos365_khong_ky_hmac():
    """ERP gọi RA POS365 bằng tài khoản của nó, không có đường ai gọi ngược vào
    — nên nguồn này cố ý không khai khóa ký."""
    assert require_source(SOURCE_POS365).secret() == ""


# ── 8. Lượt chạy (grain = RUN) — phần POS365 vừa gộp vào ────────────────────────

def test_mo_luot_chay_ghi_ngay_trang_thai_dang_chay(db):
    run = open_run(db, SOURCE_POS365, "pull_orders", entity="pos_order", user_id=3)
    assert run.grain == int(SyncGrain.RUN)
    assert run.status == int(SyncStatus.RUNNING)
    assert run.last_tried_at  # mốc bắt đầu, không để trống
    assert run.created_by == 3
    assert run.job_label == "Kéo đơn hàng"


def test_cong_viec_chua_khai_thi_nem_loi(db):
    """Gõ sai mã công việc phải nổ, không thì `last_successful_run` đi tìm một
    mã không ai ghi và mốc kéo lặng lẽ tụt về đầu ngày hôm qua mỗi chu kỳ."""
    with pytest.raises(ValueError):
        open_run(db, SOURCE_POS365, "keo_don_hang")


def test_con_tro_chi_tien_khi_luot_chay_thanh_cong(db):
    """Hệ ngoài sập thì chu kỳ sau phải KÉO BÙ, nên lượt lỗi không được để lại
    con trỏ. Lấy cả lượt lỗi là mất trắng khoảng thời gian đó."""
    hong = open_run(db, SOURCE_POS365, "pull_orders")
    finish_run(db, hong, SyncStatus.FAILED, message="POS365 trả 502",
               cursor_to="2026-09-16 08:00:00")
    assert last_successful_run(db, SOURCE_POS365, "pull_orders") is None

    tot = open_run(db, SOURCE_POS365, "pull_orders")
    finish_run(db, tot, SyncStatus.SUCCESS, fetched=10, written=4, skipped=6,
               cursor_from="2026-09-16 07:00:00", cursor_to="2026-09-16 09:00:00")
    last = last_successful_run(db, SOURCE_POS365, "pull_orders")
    assert last is not None and last.cursor_to == "2026-09-16 09:00:00"
    assert (last.fetched, last.written, last.skipped) == (10, 4, 6)


def test_luot_chay_thanh_cong_khong_con_tro_thi_khong_tinh(db):
    """Vòng đối chiếu cũng chạy dưới `pull_orders`? Không — nhưng lượt thành
    công mà KHÔNG có con trỏ (vd chạy thử) thì không được làm mốc kéo."""
    run = open_run(db, SOURCE_POS365, "pull_orders")
    finish_run(db, run, SyncStatus.SUCCESS, fetched=0)
    assert last_successful_run(db, SOURCE_POS365, "pull_orders") is None


def test_chi_tiet_luot_chay_luu_thanh_json(db):
    """Bảng lệch của vòng đối chiếu đi vào `payload`; màn hình `JSON.parse` nó.
    Phải là CHUỖI JSON, không phải `str(dict)` kiểu Python (dấu nháy đơn)."""
    import json

    run = open_run(db, SOURCE_POS365, "reconcile")
    finish_run(db, run, SyncStatus.SUCCESS,
               detail={"mismatches": [{"day": "2026-09-15", "diff": -3}], "unmatched": 2})
    assert json.loads(run.payload)["unmatched"] == 2


def test_dem_chuoi_loi_lien_tiep_bo_qua_luot_bi_bo(db):
    """Cảnh báo D-06 đếm 3 lượt LỖI liên tiếp. `Pos365Disabled` (cầu dao) là *bỏ
    qua* — chủ ý, không phải sự cố — nên không được cắt chuỗi cũng không được
    tính vào chuỗi. `recent_runs` lọc sẵn bằng `statuses`."""
    for _ in range(3):
        run = open_run(db, SOURCE_POS365, "check_voids")
        finish_run(db, run, SyncStatus.FAILED, message="lỗi")
    bo_qua = open_run(db, SOURCE_POS365, "check_voids")
    finish_run(db, bo_qua, SyncStatus.SKIPPED, message="cầu dao")

    gan_nhat = recent_runs(db, SOURCE_POS365, "check_voids", 3,
                           statuses=(SyncStatus.SUCCESS, SyncStatus.FAILED))
    assert len(gan_nhat) == 3
    assert all(r.status == int(SyncStatus.FAILED) for r in gan_nhat)


def test_luot_chay_cua_nguon_khac_khong_lan_vao(db):
    """Cùng một bảng thì phải lọc theo nguồn, không thì POS365 đọc trúng con trỏ
    của app đặt xe."""
    run = open_run(db, SOURCE_POS365, "pull_orders")
    finish_run(db, run, SyncStatus.SUCCESS, cursor_to="2026-09-16 09:00:00")
    assert last_successful_run(db, SOURCE_DATXE, "pull_orders") is None


# ── 9. Bộ mã trạng thái sau khi gộp bảng ────────────────────────────────────────

def test_ma_trang_thai_moi_lui_mot_bac_so_voi_bo_cu():
    """Chốt bằng SỐ, cố ý. Migration `e5a1b9c73d04` đổi 1->2, 2->3, 3->4, 4->5 khi
    chuyển `tab_pos_sync_run` sang; giao diện cũng gõ tay bảng màu theo số này.
    Đổi giá trị enum mà quên hai chỗ kia thì mọi lượt chạy thành công cũ hiện
    thành "đang chạy" và không chỗ nào đỏ lên."""
    assert (int(SyncStatus.PENDING), int(SyncStatus.RUNNING), int(SyncStatus.SUCCESS),
            int(SyncStatus.FAILED), int(SyncStatus.SKIPPED)) == (1, 2, 3, 4, 5)


def test_serialize_luot_chay_pos365_giu_nguyen_hinh_dang_cu(db):
    """`/api/coffee/sync/runs` đổi bảng ở dưới nhưng KHÔNG được đổi hình dạng trả
    ra — màn Nhật ký đồng bộ trong Sổ điểm & đối soát đang đọc đúng mấy khóa này."""
    from app.modules.coffee_point.service import serialize_sync_run

    run = open_run(db, SOURCE_POS365, "reconcile", entity="pos_order", user_id=5)
    finish_run(db, run, SyncStatus.SUCCESS, fetched=3, written=1, skipped=2,
               cursor_from="A", cursor_to="B", detail={"unmatched": 0})
    data = serialize_sync_run(run)

    assert set(data) == {"id", "kind", "kind_label", "status", "status_label",
                         "started_at", "finished_at", "cursor_from", "cursor_to",
                         "fetched", "written", "skipped", "error", "detail",
                         "created_by"}
    #  `kind` là SỐ cũ mà giao diện gửi lên khi bấm «Chạy ngay» (RECONCILE = 4),
    #  dù dưới sổ nay lưu mã chữ.
    assert data["kind"] == 4
    assert data["kind_label"] == "Đối chiếu"
    assert data["status"] == int(SyncStatus.SUCCESS)
    assert data["started_at"] == run.last_tried_at
    assert data["error"] == ""
    assert data["created_by"] == 5


def test_nhan_cua_nguon_la_va_khong_no(db):
    """Dòng sổ mang mã nguồn không còn trong registry (nguồn cũ đã gỡ) thì các
    nhãn phải rơi về chính mã đó, đừng ném lỗi giữa màn danh sách."""
    row = SyncLog(source="nguon-da-go", entity="x", job="y", event_id="ev-la")
    assert row.source_label == "nguon-da-go"
    assert row.entity_label == "x"
    assert row.job_label == "y"
    assert get_source("nguon-da-go") is None
