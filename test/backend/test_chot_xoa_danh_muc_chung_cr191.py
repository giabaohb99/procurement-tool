"""ai-CR-191 — đợt 3 xóa mềm, cụm DANH MỤC CHUNG + CẤU HÌNH (13/10/2026).

Danh mục đang được chứng từ / cấu hình tham chiếu thì CHẶN xóa (400, cùng câu của `core/reference_guard`),
chỉ cho ngưng dùng; hết tham chiếu thì xóa được như cũ. Danh mục đi qua `make_crud_router` chỉ ĐĂNG KÝ ở
`<module>/references.py`; cấu hình có đường xóa riêng (luồng duyệt, thư mục, sổ, quy tắc) gọi
`ensure_deletable` trong hàm xóa.

Mỗi ca kiểm hai nhịp: còn tham chiếu → 400 đúng câu + dòng còn nguyên; gỡ tham chiếu → xóa được, dòng mất.
Bản ghi xóa mềm vẫn giữ chân danh mục (cố ý — xem `reference_guard`).
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core import reference_guard as rg
from hdld_factory import client_as  # noqa: F401 — fixture TestClient đăng nhập giả

ACTOR = "a1"


def _grant(world, *entities):
    actor = world.actor(ACTOR)
    for entity in entities:
        actor.grant(entity, "all", actions=("read", "write", "delete", "import"))   # CR-660: cổng nhập CSV đòi `import`
    return actor


def _blocked(res, label: str, name, places: int):
    """400 đúng câu chung: «<Nhãn> «tên» đang được dùng ở n chỗ (...), chỉ có thể ngưng dùng ...»."""
    assert res.status_code == 400, res.text
    msg = res.json()["error"]["message"]
    assert f"{label} «{name}» đang được dùng ở {places} chỗ" in msg, msg
    assert "ngưng dùng" in msg and "không xóa được" in msg, msg
    return msg


def _raises_blocked(fn, label: str, name, places: int) -> str:
    with pytest.raises(HTTPException) as exc:
        fn()
    assert exc.value.status_code == 400
    msg = str(exc.value.detail)
    assert f"{label} «{name}» đang được dùng ở {places} chỗ" in msg and "ngưng dùng" in msg, msg
    return msg


def _doc(db, **over):
    from app.modules.document.model import ORIGIN_INTERNAL, Document

    values = dict(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=0, department_id=0,
                  owner_employee_id=0, title="Văn bản thử", created_by=0, updated_by=0)
    values.update(over)
    row = Document(**values)
    db.add(row)
    db.flush()
    return row


# ── Danh mục Thu mua: kho / đơn vị tính / nhóm hàng ──────────────────────────────────────────────────

def test_kho_con_dong_dmh_hoac_ycmh_thi_chan_het_thi_xoa(db, world, client_as):
    """Kho tham chiếu bằng MÃ (dòng ĐMH) lẫn bằng TÊN (dòng YCMH) — đếm cả hai."""
    from app.modules.catalog.model import Warehouse
    from app.modules.purchase_order.model import POItem
    from app.modules.purchase_request.model import PurchaseRequestItem

    client = client_as(_grant(world, "warehouse"))
    kho = Warehouse(code="KHO1", name="Kho Một")
    db.add(kho)
    db.flush()
    po_line = POItem(po_id=1, product_name="x", warehouse_code="KHO1")
    pr_line = PurchaseRequestItem(pr_id=1, product_name="x", warehouse="Kho Một")
    db.add_all([po_line, pr_line])
    db.commit()

    msg = _blocked(client.delete(f"/api/warehouses/{kho.id}"), "Kho", "KHO1", 2)
    assert "1 dòng đơn mua hàng" in msg and "1 dòng yêu cầu mua hàng" in msg
    assert db.get(Warehouse, kho.id) is not None

    db.delete(po_line)
    db.delete(pr_line)
    db.commit()
    assert client.delete(f"/api/warehouses/{kho.id}").status_code == 200
    assert db.get(Warehouse, kho.id) is None


def test_don_vi_tinh_tham_chieu_bang_ten_tren_san_pham(db, world, client_as):
    """Màn chọn ĐVT lưu `unit.name` (không phải mã DVTxxx) — sổ phải khai `key_attr="name"`."""
    from app.modules.catalog.model import Unit
    from app.modules.product.model import Product

    client = client_as(_grant(world, "unit"))
    dvt = Unit(code="DVT1", name="Cái")
    db.add(dvt)
    db.flush()
    sp = Product(code="SP1", name="Sản phẩm", unit="Cái")
    db.add(sp)
    db.commit()

    msg = _blocked(client.delete(f"/api/units/{dvt.id}"), "Đơn vị tính", "DVT1", 1)
    assert "1 sản phẩm" in msg
    assert db.get(Unit, dvt.id) is not None

    #  Sản phẩm NGƯNG DÙNG vẫn giữ chân — dữ liệu còn trong DB.
    sp.is_active = False
    db.commit()
    assert client.delete(f"/api/units/{dvt.id}").status_code == 400

    db.delete(sp)
    db.commit()
    assert client.delete(f"/api/units/{dvt.id}").status_code == 200
    assert db.get(Unit, dvt.id) is None


def test_nhom_hang_dem_ca_ten_tren_dong_va_id_tren_phan_cong(db, world, client_as):
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee
    from app.modules.purchase_request.model import PurchaseRequestItem

    client = client_as(_grant(world, "item_group"))
    nhom = ItemGroup(code="PLO1", name="Thùng")
    db.add(nhom)
    db.flush()
    line = PurchaseRequestItem(pr_id=1, product_name="x", item_group="Thùng")
    pc = CategoryAssignee(item_group_id=nhom.id, primary_employee_id=world.emp["a1"])
    db.add_all([line, pc])
    db.commit()

    msg = _blocked(client.delete(f"/api/item-groups/{nhom.id}"), "Nhóm hàng", "PLO1", 2)
    assert "1 dòng yêu cầu mua hàng" in msg and "1 phân công nhóm hàng" in msg

    db.delete(line)
    db.delete(pc)
    db.commit()
    assert client.delete(f"/api/item-groups/{nhom.id}").status_code == 200
    assert db.get(ItemGroup, nhom.id) is None


def test_thuong_hieu_khong_ai_tro_toi_xoa_tu_do(db):
    """Rà 13/10/2026: không bảng nào ghi mã thương hiệu — không đăng ký, không chặn."""
    assert not rg.registered("brand")
    assert not rg.registered("holiday")


def test_csv_hanh_dong_xoa_cung_qua_chot(db, world, client_as):
    """Nhập CSV với «Hành động = xóa» là đường vòng để xóa — phải vướng đúng chốt, cả tệp không ghi gì."""
    from app.modules.catalog.model import Unit
    from app.modules.product.model import Product

    client = client_as(_grant(world, "unit"))
    dvt = Unit(code="DVT2", name="Thùng")
    db.add(dvt)
    db.flush()
    sp = Product(code="SP2", name="Sản phẩm", unit="Thùng")
    db.add(sp)
    db.commit()

    csv_bytes = "Mã,Tên ĐVT,Hành động\nDVT2,Thùng,xóa\n".encode("utf-8")
    res = client.post("/api/units/import/csv", files={"file": ("dvt.csv", csv_bytes, "text/csv")})
    _blocked(res, "Đơn vị tính", "DVT2", 1)
    assert db.get(Unit, dvt.id) is not None

    db.delete(sp)
    db.commit()
    res = client.post("/api/units/import/csv", files={"file": ("dvt.csv", csv_bytes, "text/csv")})
    assert res.status_code == 200, res.text
    assert db.get(Unit, dvt.id) is None


# ── Văn thư: loại văn bản / đối tác ngoài ────────────────────────────────────────────────────────────

def test_loai_van_ban_con_van_ban_hoac_quy_tac_quan_he_thi_chan(db, world, client_as):
    from app.modules.doc_catalog.link_rule_model import DocTypeLinkRule
    from app.modules.doc_catalog.model import DocType

    client = client_as(_grant(world, "doc_type"))
    loai = DocType(code="TB", name="Thông báo")
    db.add(loai)
    db.flush()
    vb = _doc(db, doc_type_id=loai.id)
    rule = DocTypeLinkRule(source_type_id=loai.id, relation=1)
    db.add(rule)
    db.commit()

    msg = _blocked(client.delete(f"/api/doc-types/{loai.id}"), "Loại văn bản", "TB", 2)
    assert "1 văn bản" in msg and "1 quy tắc quan hệ (loại nguồn)" in msg
    assert db.get(DocType, loai.id) is not None

    #  Văn bản xóa mềm vẫn giữ chân loại.
    vb.is_deleted = True
    db.delete(rule)
    db.commit()
    _blocked(client.delete(f"/api/doc-types/{loai.id}"), "Loại văn bản", "TB", 1)

    db.delete(vb)
    db.commit()
    assert client.delete(f"/api/doc-types/{loai.id}").status_code == 200
    assert db.get(DocType, loai.id) is None


def test_doi_tac_ngoai_con_noi_nhan_van_ban_thi_chan(db, world, client_as):
    from app.modules.doc_catalog.model import ExternalParty
    from app.modules.document.recipient_model import DocumentRecipient

    client = client_as(_grant(world, "external_party"))
    dt = ExternalParty(code="DT1", name="Sở Công Thương")
    db.add(dt)
    db.flush()
    rcpt = DocumentRecipient(document_id=1, version_id=1, external_party_id=dt.id)
    db.add(rcpt)
    db.commit()

    msg = _blocked(client.delete(f"/api/external-parties/{dt.id}"), "Đối tác ngoài", "DT1", 1)
    assert "1 nơi nhận văn bản" in msg

    db.delete(rcpt)
    db.commit()
    assert client.delete(f"/api/external-parties/{dt.id}").status_code == 200
    assert db.get(ExternalParty, dt.id) is None


# ── Hành chính: loại dấu / xe / tài xế / phòng họp / chức vụ ────────────────────────────────────────

def test_loai_con_dau_con_phieu_duyet_dau_thi_chan(db, world, client_as):
    from app.modules.seal_request.model import SealRequest, SealType

    client = client_as(_grant(world, "seal_type"))
    loai = SealType(name="Dấu tròn")
    db.add(loai)
    db.flush()
    phieu = SealRequest(code="DD1", seal_type_id=loai.id, is_deleted=True)   # đã xóa mềm vẫn đếm
    db.add(phieu)
    db.commit()

    msg = _blocked(client.delete(f"/api/seal-types/{loai.id}"), "Loại con dấu", "Dấu tròn", 1)
    assert "1 phiếu duyệt dấu" in msg

    db.delete(phieu)
    db.commit()
    assert client.delete(f"/api/seal-types/{loai.id}").status_code == 200
    assert db.get(SealType, loai.id) is None


def test_xe_va_tai_xe_con_chuyen_thi_chan(db, world, client_as):
    from app.modules.vehicle_booking.model import Driver, Vehicle, VehicleBooking

    client = client_as(_grant(world, "vehicle", "driver"))
    xe = Vehicle(license_plate="51A-123.45")
    tx = Driver(name="Tài xế A")
    db.add_all([xe, tx])
    db.flush()
    chuyen = VehicleBooking(code="DX1", assigned_vehicle_id=xe.id, assigned_driver_id=tx.id)
    db.add(chuyen)
    db.commit()

    #  Xe / tài xế không có `code` lẫn `name` chung khuôn → câu chặn hiện id (ghi nhận ở báo cáo CR-191).
    msg = _blocked(client.delete(f"/api/vehicles/{xe.id}"), "Xe", "51A-123.45", 1)     # tên hiển thị = biển số
    assert "1 chuyến xe" in msg
    msg = _blocked(client.delete(f"/api/drivers/{tx.id}"), "Tài xế", "Tài xế A", 1)
    assert "1 chuyến xe" in msg
    assert db.get(Vehicle, xe.id) is not None and db.get(Driver, tx.id) is not None

    db.delete(chuyen)
    db.commit()
    assert client.delete(f"/api/vehicles/{xe.id}").status_code == 200
    assert client.delete(f"/api/drivers/{tx.id}").status_code == 200
    assert db.get(Vehicle, xe.id) is None and db.get(Driver, tx.id) is None


def test_phong_hop_con_phieu_dat_thi_chan_chot_cu_giu_nguyen(db, world, client_as):
    """Phòng họp đã có `before_delete` riêng (câu riêng) — CR-191 không khai thêm, chỉ canh chốt còn sống."""
    from app.modules.meeting_room.model import MeetingRoom, RoomBooking

    client = client_as(_grant(world, "meeting_room"))
    phong = MeetingRoom(code="PH1", name="Phòng họp 1")
    db.add(phong)
    db.flush()
    now = datetime(2026, 10, 13, 9, 0)
    dat = RoomBooking(code="DP1", room_id=phong.id, start_at=now, end_at=now + timedelta(hours=1))
    db.add(dat)
    db.commit()

    res = client.delete(f"/api/meeting-rooms/{phong.id}")
    assert res.status_code == 400 and "phiếu đặt" in res.json()["error"]["message"]
    assert db.get(MeetingRoom, phong.id) is not None

    db.delete(dat)
    db.commit()
    assert client.delete(f"/api/meeting-rooms/{phong.id}").status_code == 200


def test_chuc_vu_con_qua_trinh_cong_tac_thi_chan_du_khong_ai_dang_giu(db, world, client_as):
    """Chốt cũ chỉ đếm hồ sơ ĐANG giữ; CR-191 khai thêm quá trình công tác — không ai giữ nữa vẫn chặn."""
    from app.modules.employee.position_model import JobPosition
    from app.modules.employee.work_history_model import EmployeeWorkHistory

    client = client_as(_grant(world, "job_position"))
    cv = JobPosition(code="TP", name="Trưởng phòng")
    db.add(cv)
    db.flush()
    qt = EmployeeWorkHistory(employee_id=world.emp["a1"], event_type=1, from_date=date(2025, 1, 1),
                             to_date=date(2025, 12, 31), position_id=cv.id, position_label="Trưởng phòng")
    db.add(qt)
    db.commit()

    msg = _blocked(client.delete(f"/api/job-positions/{cv.id}"), "Chức vụ", "TP", 1)
    assert "1 dòng quá trình công tác" in msg

    db.delete(qt)
    db.commit()
    assert client.delete(f"/api/job-positions/{cv.id}").status_code == 200
    assert db.get(JobPosition, cv.id) is None


# ── Cấu hình có đường xóa riêng ─────────────────────────────────────────────────────────────────────

def test_luong_duyet_con_phieu_da_xong_hoac_la_mac_dinh_cua_loai_van_ban_thi_chan(db, world, client_as):
    """`_block_while_running` cũ chỉ đếm phiếu ĐANG chạy; CR-191 chặn luôn khi còn phiếu đã xong /
    loại văn bản lấy làm luồng mặc định — lịch sử phê duyệt còn đọc tên luồng."""
    from app.modules.approval.flow_model import ApprovalFlow
    from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_RUNNING,
                                                     ApprovalInstance)
    from app.modules.doc_catalog.model import DocType

    actor = _grant(world, "approval_flow")
    client = client_as(actor)
    uid = actor.user.id
    flow = ApprovalFlow(entity="document", code="VB-01", name="Luồng văn bản", is_active=True,
                        created_by=uid, updated_by=uid)
    db.add(flow)
    db.flush()
    phieu = ApprovalInstance(entity="document", entity_id=1, flow_id=flow.id, flow_version=1,
                             status=INSTANCE_APPROVED, current_seq=1, created_by=uid, updated_by=uid)
    loai = DocType(code="QD", name="Quyết định", default_flow_id=flow.id)
    db.add_all([phieu, loai])
    db.commit()

    msg = _blocked(client.delete(f"/api/approval-flows/{flow.id}"), "Luồng duyệt", "VB-01", 2)
    assert "1 phiếu duyệt (kể cả đã xong)" in msg and "1 loại văn bản lấy làm luồng mặc định" in msg
    assert db.get(ApprovalFlow, flow.id) is not None

    #  Phiếu ĐANG chạy vẫn ra câu riêng của chốt cũ (đứng trước sổ chung).
    phieu.status = INSTANCE_RUNNING
    db.commit()
    res = client.delete(f"/api/approval-flows/{flow.id}")
    assert res.status_code == 400 and "phiếu đang chạy" in res.json()["error"]["message"]

    db.delete(phieu)
    loai.default_flow_id = 0
    db.commit()
    assert client.delete(f"/api/approval-flows/{flow.id}").status_code == 200
    assert db.get(ApprovalFlow, flow.id) is None


def test_thu_muc_la_mac_dinh_cua_loai_van_ban_thi_chan_con_van_ban_trong_thu_muc_van_xoa_duoc(db, world):
    """Văn bản TRONG thư mục không chặn (đại ca chốt 25/09/2026 — xóa là gỡ/chuyển); chỉ chặn khi một
    loại văn bản còn lấy nó làm thư mục mặc định. Hộp xem trước phải báo cùng lý do."""
    from app.modules.doc_catalog import folder_root_service, folder_service
    from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
    from app.modules.doc_catalog.folder_model import DocFolder
    from app.modules.doc_catalog.folder_schema import FolderCreate
    from app.modules.doc_catalog.model import DocType

    roots = {f.company_id: f for f in folder_root_service.ensure_company_roots(db)}
    root = roots[world.co["A"]]
    tm = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hành chính"), 0)
    loai = DocType(code="CV", name="Công văn", default_folder_id=tm.id)
    db.add(loai)
    db.commit()

    _raises_blocked(lambda: folder_service.delete_folder(db, tm, 0), "Thư mục văn bản", "Hành chính", 1)
    preview = folder_service.delete_preview(db, tm)
    assert "Thư mục văn bản «Hành chính»" in preview["blocked_reason"]
    assert db.get(DocFolder, tm.id) is not None

    loai.default_folder_id = 0
    db.commit()
    vb = _doc(db, company_id=world.co["A"])
    db.add(DocumentFolderLink(document_id=vb.id, folder_id=tm.id, is_primary=True))
    db.commit()
    assert folder_service.delete_preview(db, tm)["blocked_reason"] == ""
    folder_service.delete_folder(db, tm, 0)           # văn bản rơi về thư mục pháp nhân, không chặn
    assert db.get(DocFolder, tm.id) is None
    assert db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == vb.id,
                                               DocumentFolderLink.folder_id == root.id).count() == 1


def test_so_van_ban_con_van_ban_tro_toi_thi_chan(db, world):
    from app.modules.doc_catalog import book_service
    from app.modules.doc_catalog.book_model import DocumentBook
    from app.modules.doc_catalog.book_schema import DocumentBookCreate

    so = book_service.create_book(db, DocumentBookCreate(
        name="Sổ đi", kind=1, company_id=world.co["A"], manager_ids=[world.emp["a1"]], viewer_ids=[]), 0)
    vb = _doc(db, book_id=so.id)
    db.commit()

    _raises_blocked(lambda: book_service.delete_book(db, so.id), "Sổ văn bản", so.code, 1)
    assert db.get(DocumentBook, so.id) is not None

    db.delete(vb)
    db.commit()
    book_service.delete_book(db, so.id)
    assert db.get(DocumentBook, so.id) is None


def test_quy_tac_danh_so_con_van_ban_ghi_thi_chan(db, world):
    from app.modules.doc_catalog import numbering_rule_service
    from app.modules.doc_catalog.numbering_rule_model import DocumentNumberingRule

    rule = DocumentNumberingRule(direction=1, pattern="{seq}/{year}")
    db.add(rule)
    db.flush()
    vb = _doc(db, numbering_rule_id=rule.id)
    db.commit()

    _raises_blocked(lambda: numbering_rule_service.delete_rule(db, rule.id), "Quy tắc đánh số", rule.id, 1)
    assert db.get(DocumentNumberingRule, rule.id) is not None

    db.delete(vb)
    db.commit()
    numbering_rule_service.delete_rule(db, rule.id)
    assert db.get(DocumentNumberingRule, rule.id) is None


def test_quy_tac_quan_he_con_lien_ket_da_khai_thi_chan(db, world):
    """Trước CR-191 xóa quy tắc để `tab_document_link.rule_id` trỏ vào khoảng không — nay chặn."""
    from app.modules.doc_catalog import link_rule_service
    from app.modules.doc_catalog.link_rule_model import DocTypeLinkRule
    from app.modules.doc_catalog.model import DocType
    from app.modules.document.link_model import DocumentLink

    loai = DocType(code="HD", name="Hợp đồng")
    db.add(loai)
    db.flush()
    rule = DocTypeLinkRule(source_type_id=loai.id, relation=1)
    db.add(rule)
    db.flush()
    a, b = _doc(db, doc_type_id=loai.id), _doc(db, doc_type_id=loai.id)
    link = DocumentLink(source_document_id=a.id, target_document_id=b.id, relation=1, rule_id=rule.id)
    db.add(link)
    db.commit()

    msg = _raises_blocked(lambda: link_rule_service.delete_rule(db, rule),
                          "Quy tắc quan hệ loại văn bản", rule.id, 1)
    assert "1 liên kết văn bản" in msg
    assert db.get(DocTypeLinkRule, rule.id) is not None

    db.delete(link)
    db.commit()
    link_rule_service.delete_rule(db, rule)
    assert db.get(DocTypeLinkRule, rule.id) is None


def test_so_dang_ky_du_cac_danh_muc_cua_dot(db):
    """Mỗi danh mục của đợt có mặt trong sổ với đúng entity của `make_crud_router` / `require`."""
    for entity in ("warehouse", "unit", "item_group", "doc_type", "external_party", "seal_type",
                   "vehicle", "driver", "job_position", "approval_flow", "doc_folder", "document_book",
                   "doc_numbering_rule", "doc_link_rule"):
        assert rg.registered(entity), entity
