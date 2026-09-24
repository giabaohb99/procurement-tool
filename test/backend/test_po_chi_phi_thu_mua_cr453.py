"""bao-CR-453 — chi phí thu mua BA GIAI ĐOẠN (Dự toán → Tạm tính → Quyết toán) + danh mục
loại chi phí. Thiết kế: `doc/erp/nhap-khau/02-chi-phi-thu-mua.md`.

Luật phải giữ:
1. Đơn mới ở Dự toán. Chốt lên giai đoạn trên thì cột trống được CHÉP số từ giai đoạn dưới,
   số đã gõ riêng thì giữ; không chốt xuống bằng cửa này.
1b. (bao-CR-467) Bảng gõ tự do như Excel: cả ba cột đều ghi được bất kể đơn ở giai đoạn nào,
   và gõ sẵn số Quyết toán KHÔNG sinh công nợ. Chốt xong thì dòng KHÓA — không sửa, không
   xóa, phải mở lại trước; payload trùng khít giá trị cũ vẫn đi qua êm.
2. Mở lại (lùi) phải có lý do từ 10 ký tự; dòng ĐÃ CHI giữ Quyết toán riêng dòng, nợ chưa chi
   của các dòng còn lại bị gỡ.
3. Chỉ dòng ở QUYẾT TOÁN (theo đơn hoặc riêng dòng) và loại chi phí có «sinh công nợ» mới
   thành khoản nợ. Số giai đoạn thấp hơn vẫn lên báo cáo (giai đoạn hiệu lực).
4. Đơn còn dòng chưa quyết toán thì không Hoàn thành được; đơn không có dòng nào tự chốt.
5. Danh mục: mã tự cấp từ 15, không cấp 99; mã 99 không đổi tên / ngừng dùng / xóa; loại
   đang có dòng chi phí không xóa được.
"""
import pytest
from fastapi import HTTPException

from app.modules.payable.model import Payable
from app.modules.purchase_order import cost_type as ct
from app.modules.purchase_order import service
from app.modules.purchase_order.controller import _out
from app.modules.purchase_order.model import (CostStage, ImportCostType, OrderType, POCost,
                                              POCostType, PurchaseOrder)
from app.modules.purchase_order.schema import POImportCostIn, POItemIn
from app.modules.report import import_landed_cost as ilc

RATE = 25_000.0
SRC = service.IMPORT_COST_SOURCE
REASON = "Hóa đơn hãng tàu về sai số, cần sửa lại"


def _make_po(db, seed, code="PO-CP-453", **kw):
    kw.setdefault("status", "approved")
    kw.setdefault("order_type", int(OrderType.IMPORT))
    kw.setdefault("currency", "USD")
    kw.setdefault("exchange_rate", RATE)
    po = PurchaseOrder(code=code, company_id=seed.company_id, supplier_code="NX",
                       supplier_name=seed.sup_name, order_date="2026-09-22", **kw)
    db.add(po)
    db.flush()
    service._save_items(db, po, [POItemIn(
        product_code="SP01", product_name="Hàng nhập", item_group="Nhãn", unit="cái",
        qty_request=1, qty_order=4, price=100, vat=0, required_date="2026-09-30",
        warehouse_code="KHO01")], user_id=1)
    db.flush()
    return po


def _cost_in(**kw):
    base = dict(cost_type=int(ImportCostType.OCEAN_FREIGHT), description="Cước biển",
                supplier_code="HANGTAU", supplier_name="Hãng tàu ABC",
                currency="VND", estimate_amount=1_000_000, vat=0)
    base.update(kw)
    return POImportCostIn(**base)


def _save_costs(db, po, costs):
    service._save_import_costs(db, po, costs, user_id=1)
    db.flush()


def _rows(db, po):
    return db.query(POCost).filter(POCost.po_id == po.id).order_by(POCost.id).all()


def _cost_payables(db, po):
    return (db.query(Payable).filter(Payable.po_id == po.id, Payable.ref_type == SRC)
            .order_by(Payable.ref_id).all())


def _mark_paid(db, payable, amount=100_000):
    payable.paid_amount = amount
    payable.remaining = float(payable.total) - amount
    db.flush()


# ── 1. Chốt lên giai đoạn ────────────────────────────────────────────────────────
def test_don_moi_o_du_toan_va_chot_len_chep_so_xuong_giai_doan_tren(db, seed):
    po = _make_po(db, seed)
    assert service.stage_of(po.cost_stage) == CostStage.ESTIMATE
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", estimate_amount=200_000)])
    row = _rows(db, po)[0]
    assert row.provisional_amount is None and row.final_amount is None

    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    assert service.stage_of(po.cost_stage) == CostStage.FINAL
    for r in _rows(db, po):
        assert float(r.provisional_amount) == float(r.estimate_amount)
        assert float(r.final_amount) == float(r.estimate_amount)
        assert float(r.final_base) == float(r.estimate_base)
    out = _out(db, po)
    assert out["cost_stage"] == int(CostStage.FINAL)
    assert out["cost_stage_label"] == "Quyết toán"


def test_go_duoc_ca_ba_cot_bat_ke_don_dang_o_giai_doan_nao(db, seed):
    # bao-CR-467: bảng gõ tự do như Excel. Số Tạm tính / Quyết toán gõ TRƯỚC khi chốt vẫn được
    # lưu, và gõ sẵn số Quyết toán KHÔNG phải là chốt — chưa chốt thì chưa nợ ai cả.
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in(provisional_amount=1_200_000, final_amount=1_300_000)])
    row = _rows(db, po)[0]
    assert float(row.provisional_amount) == 1_200_000
    assert float(row.final_amount) == 1_300_000
    assert _cost_payables(db, po) == []
    assert float(service.effective_base_of(row, po)) == 1_000_000     # vẫn đọc số Dự toán

    # Chưa chốt thì sửa lại cột nào cũng được, kể cả cột của giai đoạn thấp hơn.
    service.advance_cost_stage(db, po, int(CostStage.PROVISIONAL), user_id=1)
    _save_costs(db, po, [_cost_in(id=row.id, estimate_amount=999, provisional_amount=1_200_000,
                                  final_amount=1_300_000)])
    row = _rows(db, po)[0]
    assert float(row.estimate_amount) == 999
    assert float(row.provisional_amount) == 1_200_000                 # chốt không đè số đã gõ
    assert float(service.effective_base_of(row, po)) == 1_200_000

    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    row = _rows(db, po)[0]
    assert float(row.final_amount) == 1_300_000                       # số đã gõ, không phải số chép


def test_khong_chot_xuong_hoac_dung_giai_doan_bang_cua_chot_len(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    with pytest.raises(HTTPException) as e:
        service.advance_cost_stage(db, po, int(CostStage.ESTIMATE), user_id=1)
    assert e.value.status_code == 400 and "Mở lại" in e.value.detail


# ── 2. Mở lại ────────────────────────────────────────────────────────────────────
def test_mo_lai_can_ly_do_tu_10_ky_tu(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    with pytest.raises(HTTPException) as e:
        service.reopen_cost_stage(db, po, int(CostStage.ESTIMATE), "ngắn quá", user_id=1)
    assert e.value.status_code == 400 and "10 ký tự" in e.value.detail
    with pytest.raises(HTTPException) as e:
        service.reopen_cost_stage(db, po, int(CostStage.FINAL), REASON, user_id=1)
    assert e.value.status_code == 400 and "thấp hơn" in e.value.detail


def test_mo_lai_go_no_chua_chi_va_giu_quyet_toan_dong_da_chi(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", estimate_amount=200_000)])
    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    payables = _cost_payables(db, po)
    assert len(payables) == 2
    _mark_paid(db, payables[0])
    paid_row_id = payables[0].ref_id

    service.reopen_cost_stage(db, po, int(CostStage.ESTIMATE), REASON, user_id=1)
    assert service.stage_of(po.cost_stage) == CostStage.ESTIMATE
    rows = {r.id: r for r in _rows(db, po)}
    assert rows[paid_row_id].line_stage == int(CostStage.FINAL)
    other = next(r for r in rows.values() if r.id != paid_row_id)
    assert service.stage_of(other.line_stage) == CostStage.ESTIMATE
    assert float(other.final_amount) == 200_000        # số Quyết toán không bị xóa
    left = _cost_payables(db, po)
    assert [p.ref_id for p in left] == [paid_row_id]   # nợ chưa chi bị gỡ, nợ đã chi còn


# ── 3. Quyết toán riêng dòng ─────────────────────────────────────────────────────
def test_quyet_toan_rieng_dong_sinh_no_rieng_dong_do(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", estimate_amount=200_000)])
    first = _rows(db, po)[0]
    service.finalize_cost_line(db, po, first.id, user_id=1)
    assert first.line_stage == int(CostStage.FINAL)
    assert float(first.final_amount) == 1_000_000
    assert service.stage_of(po.cost_stage) == CostStage.ESTIMATE     # đơn vẫn ở Dự toán
    assert [p.ref_id for p in _cost_payables(db, po)] == [first.id]
    with pytest.raises(HTTPException) as e:
        service.finalize_cost_line(db, po, first.id, user_id=1)
    assert e.value.status_code == 400 and "đã ở Quyết toán" in e.value.detail

    service.reopen_cost_line(db, po, first.id, REASON, user_id=1)
    assert service.stage_of(first.line_stage) == CostStage.ESTIMATE
    assert _cost_payables(db, po) == []


def test_chot_nhieu_dong_mot_luot_va_chot_het(db, seed):
    # bao-CR-469: tick vài dòng rồi chốt một lượt, hoặc bỏ trống danh sách để chốt hết.
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", estimate_amount=200_000),
                         _cost_in(description="Khai thuê", estimate_amount=300_000)])
    rows = _rows(db, po)

    da_chot = service.finalize_cost_lines(db, po, [rows[0].id, rows[1].id], user_id=1)
    assert len(da_chot) == 2
    assert [p.ref_id for p in _cost_payables(db, po)] == sorted([rows[0].id, rows[1].id])
    assert service.stage_of(po.cost_stage) == CostStage.ESTIMATE      # đơn vẫn ở Dự toán

    # Tick lại cả bảng: dòng đã chốt bị bỏ qua chứ không báo lỗi, chỉ dòng còn lại được chốt.
    con_lai = service.finalize_cost_lines(db, po, [r.id for r in rows], user_id=1)
    assert [r.id for r in con_lai] == [rows[2].id]
    assert len(_cost_payables(db, po)) == 3

    with pytest.raises(HTTPException) as e:
        service.finalize_cost_lines(db, po, [], user_id=1)
    assert e.value.status_code == 400 and "Không còn dòng" in e.value.detail


def test_chot_het_khi_khong_tick_dong_nao(db, seed):
    po = _make_po(db, seed, code="PO-CP-453-B")
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", estimate_amount=200_000)])
    da_chot = service.finalize_cost_lines(db, po, [], user_id=1)      # rỗng = chốt hết
    assert len(da_chot) == 2
    assert all(r.line_stage == int(CostStage.FINAL) for r in _rows(db, po))

    with pytest.raises(HTTPException) as e:                           # id lạ thì chặn hẳn
        service.finalize_cost_lines(db, po, [999_999], user_id=1)
    assert e.value.status_code == 404


def test_chot_kem_bang_dang_go_thi_chot_dung_so_vua_go(db, seed, cap_quyen):
    # bao-CR-476: người dùng gõ số Quyết toán rồi bấm «Quyết toán» ngay, chưa bấm Lưu. Trước
    # đây đường chốt đọc số ĐÃ LƯU nên chốt theo số cũ — sinh công nợ sai số, còn số vừa gõ bị
    # lượt tải lại đè mất. Nay màn hình gửi kèm bảng đang gõ: lưu trước, chốt sau.
    from app.modules.purchase_order import controller as ctl
    from app.modules.purchase_order.schema import CostLinesFinalizeIn
    from app.modules.user.model import User

    po = _make_po(db, seed, code="PO-CP-476")
    _save_costs(db, po, [_cost_in()])                         # đã lưu: chỉ có Dự toán 1.000.000
    row = _rows(db, po)[0]
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True, write=True)
    user = db.get(User, seed.u_nstm_id)

    dang_go = [_cost_in(id=row.id, final_amount=1_750_000)]  # số trên màn hình, CHƯA lưu
    ctl.finalize_cost_lines(po.id, CostLinesFinalizeIn(cost_ids=[row.id], import_costs=dang_go),
                            db=db, user=user)
    row = _rows(db, po)[0]
    assert float(row.final_amount) == 1_750_000
    (pay,) = _cost_payables(db, po)
    assert float(pay.total) == 1_750_000                      # công nợ theo đúng số vừa gõ


def test_chot_khong_kem_bang_thi_giu_hanh_vi_cu(db, seed, cap_quyen):
    # Không gửi `import_costs` thì đường chốt không đụng bảng chi phí — màn hình cũ vẫn chạy.
    from app.modules.purchase_order import controller as ctl
    from app.modules.purchase_order.schema import CostLinesFinalizeIn
    from app.modules.user.model import User

    po = _make_po(db, seed, code="PO-CP-476-B")
    _save_costs(db, po, [_cost_in(), _cost_in(description="Phí cảng", estimate_amount=200_000)])
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True, write=True)
    user = db.get(User, seed.u_nstm_id)
    ctl.finalize_cost_lines(po.id, CostLinesFinalizeIn(cost_ids=[]), db=db, user=user)
    assert len(_rows(db, po)) == 2                            # không lỡ tay xóa dòng nào
    assert len(_cost_payables(db, po)) == 2


def test_chot_dong_roi_thi_khoa_ca_sua_lan_xoa(db, seed):
    # bao-CR-467: chốt là sinh công nợ, nên từ đó dòng đóng lại. Màn hình gửi lại CẢ bảng mỗi
    # lần lưu nên payload trùng khít phải đi qua êm — chỉ thay đổi THẬT mới bị chặn.
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    row = _rows(db, po)[0]
    service.finalize_cost_line(db, po, row.id, user_id=1)
    assert len(_cost_payables(db, po)) == 1

    _save_costs(db, po, [_cost_in(id=row.id, final_amount=1_000_000)])
    assert float(_rows(db, po)[0].final_amount) == 1_000_000

    for doi in (dict(final_amount=1_500_000), dict(final_amount=1_000_000, supplier_code="KHAC"),
                dict(final_amount=1_000_000, vat=10), dict(final_amount=1_000_000, note="ghi thêm")):
        with pytest.raises(HTTPException) as e:
            _save_costs(db, po, [_cost_in(id=row.id, **doi)])
        assert e.value.status_code == 400 and "không sửa được" in e.value.detail

    with pytest.raises(HTTPException) as e:          # bỏ dòng khỏi payload = xóa
        _save_costs(db, po, [])
    assert e.value.status_code == 400 and "không xóa được" in e.value.detail

    service.reopen_cost_line(db, po, row.id, REASON, user_id=1)
    _save_costs(db, po, [_cost_in(id=row.id, final_amount=1_500_000)])
    assert float(_rows(db, po)[0].final_amount) == 1_500_000


def test_don_da_quyet_toan_thi_moi_dong_deu_khoa(db, seed):
    # Khóa theo giai đoạn HIỆU LỰC: dòng không có `line_stage` riêng nhưng cả đơn đã Quyết
    # toán thì cũng đóng — nếu không, chốt cả đơn xong vẫn sửa được từng dòng như thường.
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    row = _rows(db, po)[0]
    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    with pytest.raises(HTTPException) as e:
        _save_costs(db, po, [_cost_in(id=row.id, final_amount=2_000_000)])
    assert e.value.status_code == 400 and "không sửa được" in e.value.detail


def test_mo_lai_dong_dang_theo_don_hoac_da_chi_thi_chan(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    row = _rows(db, po)[0]
    with pytest.raises(HTTPException) as e:
        service.reopen_cost_line(db, po, row.id, REASON, user_id=1)
    assert e.value.status_code == 400 and "mở lại cả đơn" in e.value.detail

    service.finalize_cost_line(db, po, row.id, user_id=1)
    _mark_paid(db, _cost_payables(db, po)[0])
    with pytest.raises(HTTPException) as e:
        service.reopen_cost_line(db, po, row.id, REASON, user_id=1)
    assert e.value.status_code == 400 and "đã có tiền chi" in e.value.detail


# ── 4. Giai đoạn hiệu lực + số quy đổi ───────────────────────────────────────────
def test_giai_doan_hieu_luc_va_so_quy_doi(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in(currency="USD", estimate_amount=100, estimate_rate=RATE, vat=8)])
    row = _rows(db, po)[0]
    assert service.filled_stage_of(row, po) == CostStage.ESTIMATE
    assert float(service.effective_base_of(row, po)) == pytest.approx(100 * 1.08 * RATE)
    # Đơn lên Tạm tính nhưng dòng chưa có số Tạm tính → vẫn đọc số Dự toán
    po.cost_stage = int(CostStage.PROVISIONAL)
    row.provisional_amount = None
    db.flush()
    assert service.effective_stage_of(row, po) == CostStage.PROVISIONAL
    assert service.filled_stage_of(row, po) == CostStage.ESTIMATE
    empty = POCost(po_id=po.id, cost_type=int(ImportCostType.OTHER))
    assert service.filled_stage_of(empty, po) is None
    assert service.effective_base_of(empty, po) == 0.0


# ── 5. Công nợ chỉ sinh ở Quyết toán và theo «sinh công nợ» của loại ─────────────
def test_loai_khong_sinh_cong_no_thi_khong_thanh_no(db, seed):
    db.add(POCostType(code=int(ImportCostType.OCEAN_FREIGHT), name="Cước biển", creates_payable=True))
    db.add(POCostType(code=int(ImportCostType.OTHER), name="Chi phí khác", creates_payable=False))
    db.flush()
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in(), _cost_in(cost_type=int(ImportCostType.OTHER),
                                              description="Chi nội bộ", estimate_amount=50_000)])
    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    payables = _cost_payables(db, po)
    assert [p.supplier_code for p in payables] == ["HANGTAU"]
    summary = _out(db, po)["import_cost_summary"]
    assert summary["cost_total"] == 1_050_000.0        # báo cáo vẫn cộng cả hai dòng


def test_chan_hoan_thanh_khi_con_dong_chua_quyet_toan(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    with pytest.raises(HTTPException) as e:
        service.block_complete_not_final_costs(db, po)
    assert e.value.status_code == 400 and "còn 1 dòng đang ở Dự toán" in e.value.detail
    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    service.block_complete_not_final_costs(db, po)      # không ném

    po2 = _make_po(db, seed, code="PO-CP-453B")
    service.block_complete_not_final_costs(db, po2)     # không dòng nào → tự chốt
    assert service.stage_of(po2.cost_stage) == CostStage.FINAL


# ── 6. Báo cáo giá vốn theo giai đoạn ────────────────────────────────────────────
def test_bao_cao_doc_theo_giai_doan_va_so_lech(db, seed):
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    eff = ilc.compute(db, po_ids=[po.id])
    assert eff["stage"] == ilc.STAGE_EFFECTIVE
    assert eff["orders"][0]["cost_total"] == 1_000_000.0
    assert eff["orders"][0]["variance"] is None          # chưa Quyết toán thì chưa so
    # Xem riêng cột Quyết toán khi chưa có số → 0, không mượn số Dự toán
    assert ilc.compute(db, po_ids=[po.id], stage=int(CostStage.FINAL))["orders"][0]["cost_total"] == 0.0

    # bao-CR-467: gõ số Quyết toán TRƯỚC rồi mới chốt — chốt xong là dòng khóa, hết sửa.
    row = _rows(db, po)[0]
    _save_costs(db, po, [_cost_in(id=row.id, final_amount=1_300_000)])
    service.advance_cost_stage(db, po, int(CostStage.FINAL), user_id=1)
    done = ilc.compute(db, po_ids=[po.id])
    assert done["orders"][0]["cost_total"] == 1_300_000.0
    assert done["orders"][0]["variance"] == 300_000.0
    assert done["totals"]["variance"] == 300_000.0
    # Cột Dự toán vẫn đọc được để so
    assert ilc.compute(db, po_ids=[po.id], stage=int(CostStage.ESTIMATE))["orders"][0]["cost_total"] == 1_000_000.0


def test_bao_cao_mo_don_trong_nuoc_khi_duoc_hoi(db, seed):
    po = _make_po(db, seed, order_type=int(OrderType.DOMESTIC), currency="VND", exchange_rate=1)
    _save_costs(db, po, [_cost_in()])
    assert ilc.compute(db, po_ids=[po.id])["orders"] == []
    rows = ilc.compute(db, po_ids=[po.id], include_domestic=True)["orders"]
    assert [r["po_id"] for r in rows] == [po.id]


# ── 7. Danh mục loại chi phí ─────────────────────────────────────────────────────
def _seed_types(db):
    for code, name in ((1, "Cước biển"), (14, "Phí kiểm dịch"), (99, "Chi phí khác")):
        db.add(POCostType(code=code, name=name))
    db.flush()


def test_ma_tu_cap_tu_15_va_khong_cap_99(db):
    assert ct.next_cost_type_code(db) == 15
    _seed_types(db)
    assert ct.next_cost_type_code(db) == 15
    db.add(POCostType(code=98, name="Phí thử"))
    db.flush()
    assert ct.next_cost_type_code(db) == 100

    data = ct.POCostTypeCreate(name="Phí lưu kho ngoại quan")
    ct._assign_code(db, data)
    assert data.code == 100
    with pytest.raises(HTTPException) as e:
        ct._assign_code(db, ct.POCostTypeCreate(code=99, name="Trùng mã khác"))
    assert e.value.status_code == 400 and "Mã 99" in e.value.detail


def test_ma_99_khong_doi_ten_khong_ngung_dung_khong_xoa(db):
    _seed_types(db)
    other = db.query(POCostType).filter(POCostType.code == 99).one()
    with pytest.raises(HTTPException):
        ct._protect_other(db, other, {"is_active": False})
    with pytest.raises(HTTPException):
        ct._protect_other(db, other, {"name": "Tên mới"})
    ct._protect_other(db, other, {"name": "Chi phí khác", "note": "giữ nguyên tên"})   # không ném
    with pytest.raises(HTTPException) as e:
        ct._block_delete_in_use(db, other)
    assert "không xóa được" in e.value.detail


def test_loai_dang_co_dong_chi_phi_thi_khong_xoa(db, seed):
    _seed_types(db)
    po = _make_po(db, seed)
    _save_costs(db, po, [_cost_in()])
    freight = db.query(POCostType).filter(POCostType.code == 1).one()
    assert ct.count_costs_using(db, 1) == 1
    with pytest.raises(HTTPException) as e:
        ct._block_delete_in_use(db, freight)
    assert "đang có 1 dòng chi phí" in e.value.detail
    unused = db.query(POCostType).filter(POCostType.code == 14).one()
    ct._block_delete_in_use(db, unused)       # không ném
