"""CR-029 / CR-030 / CR-031 — Bình luận dùng chung cho chứng từ (bảng tab_comment theo cặp entity/entity_id).

Trọng tâm:
- Bình luận phải dính đúng chứng từ: cùng entity_id nhưng khác entity thì KHÔNG lẫn sang nhau.
- Người nhận chuông = người tạo phiếu + ai đã bình luận, TRỪ người vừa gõ.
- Entity lạ bị chặn ngay ở registry (chống entity rác), không cần tới quyền.
- CR-030: luồng CHỈ 2 CẤP — trả lời một phản hồi vẫn nằm ở cấp 2, backend tự ép, không tin FE.
- CR-031: nhắc tên nhiều người bằng thẻ @[id] trong nội dung — ID không có thật bị bỏ, tự nhắc mình bị bỏ.
"""
import pytest
from fastapi import HTTPException

from app.core.comment_registry import COMMENT_POLICY, doc_model
from app.modules.comment import service
from app.modules.comment.model import Comment, CommentReaction
from app.modules.purchase_request.model import PurchaseRequest


def _pr(db, seed, user_id: int, code: str = "PYC000777"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         department="Phòng Test", purpose="Test", status="draft",
                         created_by=user_id, updated_by=user_id)
    db.add(pr)
    db.commit()
    return pr


def _roots(db, entity, entity_id, **kw):
    return [c.body for c in service.list_roots(db, entity, entity_id, **kw)]


# ── CR-029: nền tảng ────────────────────────────────────────────────────────────

def test_binh_luan_dinh_dung_chung_tu(db, seed):
    """Cùng entity_id nhưng khác entity là hai phiếu khác nhau — không được lẫn bình luận."""
    pr = _pr(db, seed, user_id=10)
    service.create_comment(db, "purchase_request", pr.id, "Ý kiến ở YCMH", user_id=10)
    service.create_comment(db, "purchase_order", pr.id, "Ý kiến ở ĐMH", user_id=10)

    assert _roots(db, "purchase_request", pr.id) == ["Ý kiến ở YCMH"]
    assert _roots(db, "purchase_order", pr.id) == ["Ý kiến ở ĐMH"]


def test_thu_tu_cu_truoc_moi_sau(db, seed):
    """Đọc như một cuộc trao đổi: cũ ở trên, mới ở dưới."""
    pr = _pr(db, seed, user_id=10)
    for t in ("một", "hai", "ba"):
        service.create_comment(db, "purchase_request", pr.id, t, user_id=10)
    assert _roots(db, "purchase_request", pr.id) == ["một", "hai", "ba"]


def test_noi_dung_rong_bi_tu_choi(db, seed):
    """Gõ toàn khoảng trắng cũng là rỗng — không tạo bình luận trắng trong phiếu."""
    pr = _pr(db, seed, user_id=10)
    for body in ("", "   ", "\n\t "):
        with pytest.raises(HTTPException) as e:
            service.create_comment(db, "purchase_request", pr.id, body, user_id=10)
        assert e.value.status_code == 400
    assert db.query(Comment).count() == 0


def test_noi_dung_qua_dai_bi_tu_choi(db, seed):
    pr = _pr(db, seed, user_id=10)
    with pytest.raises(HTTPException) as e:
        service.create_comment(db, "purchase_request", pr.id, "x" * (service.MAX_BODY + 1), user_id=10)
    assert e.value.status_code == 400
    assert db.query(Comment).count() == 0


def test_nguoi_nhan_chuong_gom_nguoi_tao_phieu_va_ai_da_binh_luan(db, seed):
    """Người tạo phiếu (10) + những ai đã bình luận (20, 30); người vừa gõ (30) không tự báo mình."""
    pr = _pr(db, seed, user_id=10)
    service.create_comment(db, "purchase_request", pr.id, "hỏi thêm", user_id=20)
    service.create_comment(db, "purchase_request", pr.id, "trả lời", user_id=30)

    assert service.recipient_ids(db, pr, "purchase_request", pr.id, author_id=30) == [10, 20]
    assert service.recipient_ids(db, pr, "purchase_request", pr.id, author_id=10) == [20, 30]


def test_khong_tu_bao_chuong_cho_chinh_minh(db, seed):
    """Người tạo phiếu tự bình luận vào phiếu mình, chưa ai tham gia → không báo cho ai."""
    pr = _pr(db, seed, user_id=10)
    service.create_comment(db, "purchase_request", pr.id, "tự ghi chú", user_id=10)
    assert service.recipient_ids(db, pr, "purchase_request", pr.id, author_id=10) == []


def test_nguoi_nhan_khong_gom_binh_luan_cua_phieu_khac(db, seed):
    """Bình luận ở phiếu khác không kéo người đó vào danh sách nhận chuông của phiếu này."""
    pr = _pr(db, seed, user_id=10)
    service.create_comment(db, "purchase_order", 999, "ở đơn khác", user_id=77)
    assert 77 not in service.recipient_ids(db, pr, "purchase_request", pr.id, author_id=10)


def test_entity_la_bi_chan(db):
    """Entity không nằm trong registry bị từ chối ngay, chưa cần tới quyền (user=None)."""
    with pytest.raises(HTTPException) as e:
        service.resolve_doc(db, None, "bang_khong_ton_tai", 1)
    assert e.value.status_code == 400


def test_moi_entity_trong_registry_deu_co_model():
    """Thêm dòng vào COMMENT_POLICY mà quên nhánh doc_model() thì API sẽ chết lúc chạy — chặn ở đây."""
    for entity in COMMENT_POLICY:
        assert doc_model(entity) is not None, f"thiếu nhánh doc_model cho {entity}"


def test_xoa_binh_luan_khong_dung_toi_cai_khac(db, seed):
    pr = _pr(db, seed, user_id=10)
    a = service.create_comment(db, "purchase_request", pr.id, "giữ lại", user_id=10)
    b = service.create_comment(db, "purchase_request", pr.id, "xóa đi", user_id=20)
    service.delete_comment(db, b)
    assert [c.id for c in service.list_roots(db, "purchase_request", pr.id)] == [a.id]


# ── CR-030: hai cấp + nhắc tên ──────────────────────────────────────────────────

def test_tra_loi_phan_hoi_van_nam_o_cap_2(db, seed):
    """Trả lời một phản hồi KHÔNG đẻ ra cấp 3 — bài mới treo vào chính bình luận gốc."""
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    r1 = service.create_comment(db, "purchase_request", pr.id, "phản hồi 1", user_id=20,
                                parent_id=root.id)
    r2 = service.create_comment(db, "purchase_request", pr.id, "trả lời phản hồi 1", user_id=30,
                                parent_id=r1.id)

    assert r1.parent_id == root.id
    assert r2.parent_id == root.id, "trả lời phản hồi phải kéo về gốc, không lồng thêm cấp"
    # Không có bình luận nào mà cha của nó lại là một phản hồi
    reply_ids = {r1.id, r2.id}
    assert not db.query(Comment).filter(Comment.parent_id.in_(reply_ids)).count()


def test_tra_loi_phan_hoi_tu_nhac_ten_nguoi_do(db, seed):
    """Từ cấp 3 trở đi tự @ người vừa được trả lời; trả lời thẳng gốc thì không nhắc ai."""
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    r1 = service.create_comment(db, "purchase_request", pr.id, "phản hồi 1", user_id=20,
                                parent_id=root.id)
    r2 = service.create_comment(db, "purchase_request", pr.id, "trả lời 20", user_id=30,
                                parent_id=r1.id)

    assert r1.reply_to_user_id == 0, "trả lời thẳng bình luận gốc thì không cần chip @"
    assert r2.reply_to_user_id == 20


def test_khong_tu_nhac_chinh_minh(db, seed):
    """Tự trả lời phản hồi của chính mình thì bỏ chip @ — không ai @ chính mình."""
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    r1 = service.create_comment(db, "purchase_request", pr.id, "phản hồi", user_id=20,
                                parent_id=root.id)
    r2 = service.create_comment(db, "purchase_request", pr.id, "nói thêm", user_id=20,
                                parent_id=r1.id)
    assert r2.reply_to_user_id == 0


def test_nhac_ten_truyen_tay_duoc_giu(db, seed):
    """FE gửi kèm reply_to_user_id (người dùng tự chọn) thì tôn trọng, không ghi đè."""
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    r1 = service.create_comment(db, "purchase_request", pr.id, "phản hồi", user_id=20,
                                parent_id=root.id)
    r2 = service.create_comment(db, "purchase_request", pr.id, "gọi người khác", user_id=30,
                                parent_id=r1.id, reply_to_user_id=99)
    assert r2.reply_to_user_id == 99


def test_parent_khac_phieu_bi_tu_choi(db, seed):
    """Không cho treo phản hồi vào bình luận của phiếu khác (chống giả mạo parent_id)."""
    a = _pr(db, seed, user_id=10, code="PYC000777")
    b = _pr(db, seed, user_id=10, code="PYC000778")
    root = service.create_comment(db, "purchase_request", a.id, "gốc phiếu A", user_id=10)

    with pytest.raises(HTTPException) as e:
        service.create_comment(db, "purchase_request", b.id, "chen ngang", user_id=20,
                               parent_id=root.id)
    assert e.value.status_code == 400

    with pytest.raises(HTTPException) as e:
        service.create_comment(db, "purchase_request", a.id, "parent ma", user_id=20,
                               parent_id=root.id + 9999)
    assert e.value.status_code == 400


# ── CR-030: phân trang + đếm ────────────────────────────────────────────────────

def test_danh_sach_chi_lay_binh_luan_goc(db, seed):
    """Phản hồi không chen vào danh sách gốc — chúng nằm trong nhánh của gốc."""
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    service.create_comment(db, "purchase_request", pr.id, "phản hồi", user_id=20, parent_id=root.id)

    assert _roots(db, "purchase_request", pr.id) == ["gốc"]
    assert service.count_roots(db, "purchase_request", pr.id) == 1
    assert service.count_all(db, "purchase_request", pr.id) == 2   # số cạnh tiêu đề


def test_phan_trang_lay_moi_nhat_roi_doc_xuoi(db, seed):
    """Mở phiếu là thấy phần đang bàn dở (mới nhất) nhưng vẫn đọc xuôi thời gian."""
    pr = _pr(db, seed, user_id=10)
    for i in range(1, 26):
        service.create_comment(db, "purchase_request", pr.id, f"bl{i}", user_id=10)

    trang1 = service.list_roots(db, "purchase_request", pr.id, limit=10)
    assert [c.body for c in trang1] == [f"bl{i}" for i in range(16, 26)]

    # "Xem N bình luận trước" — con trỏ là id nhỏ nhất đang hiển thị
    trang2 = service.list_roots(db, "purchase_request", pr.id, limit=10, before_id=trang1[0].id)
    assert [c.body for c in trang2] == [f"bl{i}" for i in range(6, 16)]

    trang3 = service.list_roots(db, "purchase_request", pr.id, limit=10, before_id=trang2[0].id)
    assert [c.body for c in trang3] == [f"bl{i}" for i in range(1, 6)]


def test_dem_phan_hoi_theo_tung_goc(db, seed):
    pr = _pr(db, seed, user_id=10)
    a = service.create_comment(db, "purchase_request", pr.id, "gốc A", user_id=10)
    b = service.create_comment(db, "purchase_request", pr.id, "gốc B", user_id=10)
    c = service.create_comment(db, "purchase_request", pr.id, "gốc C", user_id=10)
    for i in range(3):
        service.create_comment(db, "purchase_request", pr.id, f"ph{i}", user_id=20, parent_id=a.id)
    service.create_comment(db, "purchase_request", pr.id, "một cái", user_id=20, parent_id=b.id)

    counts = service.reply_counts(db, [a.id, b.id, c.id])
    assert counts.get(a.id) == 3
    assert counts.get(b.id) == 1
    assert c.id not in counts   # gốc chưa ai trả lời thì không có khóa -> FE hiểu là 0
    assert service.reply_counts(db, []) == {}


def test_phan_hoi_tra_ve_theo_thu_tu_cu_truoc(db, seed):
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    for t in ("p1", "p2", "p3"):
        service.create_comment(db, "purchase_request", pr.id, t, user_id=20, parent_id=root.id)
    assert [c.body for c in service.list_replies(db, root.id)] == ["p1", "p2", "p3"]


# ── CR-030: lượt thích ──────────────────────────────────────────────────────────

def test_thich_roi_bam_lai_la_bo_thich(db, seed):
    """Mỗi người tối đa 1 lượt trên một bình luận; bấm lại là gỡ."""
    pr = _pr(db, seed, user_id=10)
    c = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)

    assert service.toggle_reaction(db, c.id, 20) == {"liked": True, "count": 1}
    assert service.toggle_reaction(db, c.id, 30) == {"liked": True, "count": 2}
    assert service.toggle_reaction(db, c.id, 20) == {"liked": False, "count": 1}
    assert service.reaction_user_ids(db, c.id) == [30]


def test_ban_do_luot_thich_theo_tung_nguoi(db, seed):
    """Cùng một bình luận: người đã thích thấy liked=True, người khác thấy False."""
    pr = _pr(db, seed, user_id=10)
    a = service.create_comment(db, "purchase_request", pr.id, "A", user_id=10)
    b = service.create_comment(db, "purchase_request", pr.id, "B", user_id=10)
    service.toggle_reaction(db, a.id, 20)
    service.toggle_reaction(db, a.id, 30)

    m20 = service.like_map(db, [a.id, b.id], user_id=20)
    assert m20[a.id] == {"count": 2, "liked": True}
    assert m20[b.id] == {"count": 0, "liked": False}
    assert service.like_map(db, [a.id, b.id], user_id=40)[a.id] == {"count": 2, "liked": False}
    assert service.like_map(db, [], user_id=20) == {}


# ── CR-030: xóa + thông báo ─────────────────────────────────────────────────────

def test_xoa_goc_cuon_theo_phan_hoi_va_luot_thich(db, seed):
    """Giữ phản hồi mồ côi khi gốc biến mất chỉ làm luồng khó đọc — xóa gốc là xóa cả nhánh."""
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    r1 = service.create_comment(db, "purchase_request", pr.id, "ph1", user_id=20, parent_id=root.id)
    service.create_comment(db, "purchase_request", pr.id, "ph2", user_id=30, parent_id=root.id)
    khac = service.create_comment(db, "purchase_request", pr.id, "gốc khác", user_id=10)
    root_id, khac_id = root.id, khac.id
    service.toggle_reaction(db, root_id, 20)
    service.toggle_reaction(db, r1.id, 30)
    service.toggle_reaction(db, khac_id, 20)

    assert service.delete_comment(db, root) == 3   # 1 gốc + 2 phản hồi
    assert [c.id for c in service.list_roots(db, "purchase_request", pr.id)] == [khac_id]
    assert service.list_replies(db, root_id) == []
    assert [r.comment_id for r in db.query(CommentReaction).all()] == [khac_id]


def test_xoa_mot_phan_hoi_khong_dung_toi_goc(db, seed):
    pr = _pr(db, seed, user_id=10)
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10)
    r1 = service.create_comment(db, "purchase_request", pr.id, "ph1", user_id=20, parent_id=root.id)
    service.create_comment(db, "purchase_request", pr.id, "ph2", user_id=30, parent_id=root.id)

    assert service.delete_comment(db, r1) == 1
    assert [c.body for c in service.list_replies(db, root.id)] == ["ph2"]
    assert service.count_roots(db, "purchase_request", pr.id) == 1


def test_nguoi_duoc_nhac_ten_khong_nhan_them_chuong_chung(db, seed):
    """Một việc một chuông: ai đã nhận chuông "được nhắc tên" thì bỏ khỏi chuông chung."""
    pr = _pr(db, seed, user_id=10)
    service.create_comment(db, "purchase_request", pr.id, "hỏi", user_id=20)
    service.create_comment(db, "purchase_request", pr.id, "đáp", user_id=30)

    assert service.recipient_ids(db, pr, "purchase_request", pr.id, author_id=30,
                                 exclude={20}) == [10]


# ── CR-031: nhắc tên nhiều người bằng thẻ @[id] ─────────────────────────────────

def test_rut_id_nguoi_duoc_nhac_theo_thu_tu_va_bo_trung(db, seed):
    ra = service.parse_mentions("nhờ @[12] xem giúp giá của @[7], @[12] nhé")
    assert ra == [12, 7]


def test_chu_at_thuong_khong_bi_hieu_la_nhac_ten(db, seed):
    """Chỉ thẻ @[<số>] mới tính. Gõ tay "@Tên" hay email không được thành lời nhắc."""
    assert service.parse_mentions("gửi @Nguyễn Văn A và abc@degoholding.com nhé") == []
    assert service.parse_mentions("@[abc] không phải id") == []


def test_luu_nguoi_duoc_nhac_va_bo_nguoi_khong_co_that(db, seed):
    """Thẻ do FE gửi lên không được tin: ID không có tài khoản thì bỏ qua, không đẻ dòng rác."""
    pr = _pr(db, seed, user_id=seed.u_req_id)
    c = service.create_comment(db, "purchase_request", pr.id,
                               f"nhờ @[{seed.u_nstm_id}] và @[999999] xem giúp",
                               user_id=seed.u_req_id)
    assert service.mention_map(db, [c.id]) == {c.id: [seed.u_nstm_id]}


def test_khong_tu_nhac_chinh_minh_bang_the(db, seed):
    pr = _pr(db, seed, user_id=seed.u_req_id)
    c = service.create_comment(db, "purchase_request", pr.id,
                               f"@[{seed.u_req_id}] tự nhắc mình", user_id=seed.u_req_id)
    assert service.mention_map(db, [c.id]) == {}


def test_nhac_duoc_nhieu_nguoi_trong_mot_binh_luan(db, seed):
    pr = _pr(db, seed, user_id=seed.u_req_id)
    c = service.create_comment(db, "purchase_request", pr.id,
                               f"@[{seed.u_nstm_id}] và @[{seed.u_req_id}] cùng xem",
                               user_id=999)   # người viết là tài khoản khác nên cả hai đều được nhắc
    assert sorted(service.mention_map(db, [c.id])[c.id]) == sorted([seed.u_nstm_id, seed.u_req_id])


def test_chuong_doi_the_thanh_ten_nguoi(db, seed):
    """Chuông là chữ thuần — không được để lọt "@[12]" ra thông báo."""
    ra = service.strip_mentions(db, f"nhờ @[{seed.u_nstm_id}] xem giúp")
    assert "@[" not in ra
    assert ra.startswith("nhờ @")


def test_xoa_binh_luan_cuon_theo_loi_nhac(db, seed):
    from app.modules.comment.model import CommentMention
    pr = _pr(db, seed, user_id=seed.u_req_id)
    root = service.create_comment(db, "purchase_request", pr.id,
                                  f"@[{seed.u_nstm_id}] gốc", user_id=999)
    service.create_comment(db, "purchase_request", pr.id,
                           f"@[{seed.u_req_id}] phản hồi", user_id=999, parent_id=root.id)

    assert db.query(CommentMention).count() == 2
    service.delete_comment(db, root)
    assert db.query(CommentMention).count() == 0


def test_nhac_qua_nhieu_nguoi_bi_cat_bot(db, seed):
    """Chặn spam chuông: một bình luận nhắc tối đa MAX_MENTIONS người."""
    pr = _pr(db, seed, user_id=seed.u_req_id)
    body = " ".join(f"@[{i}]" for i in range(1, service.MAX_MENTIONS + 10))
    c = service.create_comment(db, "purchase_request", pr.id, body, user_id=999)
    # Chỉ những ID vừa có thật vừa nằm trong ngưỡng mới được ghi
    assert len(service.mention_map(db, [c.id]).get(c.id, [])) <= service.MAX_MENTIONS


# ── CR-033: đính kèm tệp trong bình luận ────────────────────────────────────────

def _file(db, user_id: int, name: str = "baogia.pdf", ctype: str = "application/pdf"):
    """Một dòng tab_file như vừa upload xong qua /api/attachments/upload-file."""
    from app.modules.attachment.model import StoredFile
    f = StoredFile(filename=name, file_key=f"test/{name}", url=f"http://x/{name}",
                   content_type=ctype, size=1024, created_by=user_id, updated_by=user_id)
    db.add(f)
    db.commit()
    return f


def test_gan_tep_vao_binh_luan(db, seed):
    """Tệp gắn theo bài, đọc ra qua file_map — ảnh được đánh dấu để hiện thẳng ra."""
    pr = _pr(db, seed, user_id=10)
    pdf = _file(db, 10)
    anh = _file(db, 10, "mau-bao-bi.jpg", "image/jpeg")
    c = service.create_comment(db, "purchase_request", pr.id, "Gửi anh xem", user_id=10,
                               file_ids=[pdf.id, anh.id])

    ra = service.file_map(db, [c.id])[c.id]
    assert [f["filename"] for f in ra] == ["baogia.pdf", "mau-bao-bi.jpg"]
    assert [f["is_image"] for f in ra] == [False, True]


def test_bai_chi_co_tep_van_gui_duoc(db, seed):
    """Kéo file vào rồi bấm Gửi mà không gõ chữ là chuyện thường — không bắt phải viết."""
    pr = _pr(db, seed, user_id=10)
    f = _file(db, 10)
    c = service.create_comment(db, "purchase_request", pr.id, "", user_id=10, file_ids=[f.id])
    assert c.body == ""
    assert len(service.file_map(db, [c.id])[c.id]) == 1

    # Không chữ mà cũng không tệp thì vẫn là bài trống
    with pytest.raises(HTTPException) as e:
        service.create_comment(db, "purchase_request", pr.id, "", user_id=10, file_ids=[])
    assert e.value.status_code == 400


def test_khong_gan_duoc_tep_cua_nguoi_khac(db, seed):
    """Chỉ gắn được tệp CHÍNH MÌNH vừa tải lên — chống đoán file_id để lôi file người khác ra."""
    pr = _pr(db, seed, user_id=10)
    cua_nguoi_khac = _file(db, 99, "mat.pdf")
    c = service.create_comment(db, "purchase_request", pr.id, "thử", user_id=10,
                               file_ids=[cua_nguoi_khac.id])
    assert service.file_map(db, [c.id]) == {}


def test_khong_gan_duoc_tep_dang_dung_cho_khac(db, seed):
    """Tệp đã gắn ở chứng từ khác thì không kéo sang bình luận được.

    Nếu cho phép, link mới sẽ mang quyền của phiếu đang bình luận — hở file sang người
    chỉ được xem phiếu này mà không được xem phiếu gốc.
    """
    from app.modules.attachment.model import FileLink
    pr = _pr(db, seed, user_id=10)
    f = _file(db, 10, "hopdong.pdf")
    db.add(FileLink(file_id=f.id, entity="contract", entity_id=555,
                    created_by=10, updated_by=10))
    db.commit()

    c = service.create_comment(db, "purchase_request", pr.id, "thử", user_id=10, file_ids=[f.id])
    assert service.file_map(db, [c.id]) == {}


def test_qua_so_tep_cho_phep_bi_chan(db, seed):
    pr = _pr(db, seed, user_id=10)
    ids = [_file(db, 10, f"f{i}.pdf").id for i in range(service.MAX_FILES + 1)]
    with pytest.raises(HTTPException) as e:
        service.create_comment(db, "purchase_request", pr.id, "nhiều quá", user_id=10, file_ids=ids)
    assert e.value.status_code == 400


def test_xoa_binh_luan_go_luon_dinh_kem(db, seed):
    """Xóa gốc là cuốn theo phản hồi, nên tệp của cả nhánh phải đi theo, không để rác."""
    from app.modules.attachment.model import FileLink, StoredFile
    pr = _pr(db, seed, user_id=10)
    f1, f2 = _file(db, 10, "a.pdf"), _file(db, 10, "b.pdf")
    root = service.create_comment(db, "purchase_request", pr.id, "gốc", user_id=10, file_ids=[f1.id])
    service.create_comment(db, "purchase_request", pr.id, "phản hồi", user_id=10,
                           parent_id=root.id, file_ids=[f2.id])
    assert db.query(FileLink).filter(FileLink.entity == "comment").count() == 2

    service.delete_comment(db, root)
    assert db.query(FileLink).filter(FileLink.entity == "comment").count() == 0
    # Không còn ai dùng -> dọn luôn file, khỏi để rác trên storage
    assert db.query(StoredFile).filter(StoredFile.id.in_([f1.id, f2.id])).count() == 0


def test_chinh_sach_tep_binh_luan_giong_o_chung_tu(db, seed):
    """Đuôi cho phép của bình luận phải bằng ô đính kèm chứng từ — người dùng khỏi phải nhớ 2 luật."""
    from app.core.file_registry import policy
    parent, exts, max_mb = policy("comment")
    _, exts_pyc, max_pyc = policy("purchase_request")
    assert exts == exts_pyc and max_mb == max_pyc
    # Cha là __self__: quyền thật do API bình luận kiểm theo chứng từ đang treo
    assert parent == "__self__"


def test_tep_binh_luan_kiem_quyen_theo_chung_tu_cha(db, seed):
    """Tải tệp trong bình luận phải qua cửa quyền của CHÍNH chứng từ đang treo.

    `FILE_POLICY["comment"]` để `__self__` (chỉ cần đăng nhập) cho bước tải tệp tạm, nên nếu
    endpoint tải về không hỏi lại chứng từ cha thì ai đăng nhập cũng đọc được tệp trong bình
    luận của phiếu người khác — đây là chốt chặn đó.
    """
    from app.modules.attachment.controller import _check_comment
    from app.modules.user.model import User

    pr = _pr(db, seed, user_id=10)
    f = _file(db, 10)
    c = service.create_comment(db, "purchase_request", pr.id, "gửi anh", user_id=10, file_ids=[f.id])

    nguoi_la = User(email="NGUOILA", password_hash="x", is_active=True)   # không có vai trò nào
    db.add(nguoi_la)
    db.commit()
    with pytest.raises(HTTPException) as e:
        _check_comment(db, nguoi_la, c.id, "read")
    assert e.value.status_code == 403

    with pytest.raises(HTTPException) as e:
        _check_comment(db, nguoi_la, 999999, "read")
    assert e.value.status_code == 404
