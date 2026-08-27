"""CHÈN BƯỚC vào luồng duyệt — chỗ `UNIQUE(flow_id, seq, branch_key)` bắt gặp.

Lỗi thật đã xảy ra: luồng đang có bước ở chặng 1, người dùng bấm dấu «+» phía
TRÊN bước đó để chèn một chặng mới, giao diện gửi `seq = 1` và cả request nổ
500 — `Duplicate entry '4-1-' for key 'uq_approval_node_seq'`. Bước mới không
được lưu, người dùng chỉ thấy một dòng đỏ không nói được phải làm gì.

Chèn bước là thao tác cơ bản nhất của màn khai luồng nên mọi ngả chèn đều phải
có bài canh ở đây.
"""
import pytest

from app.modules.approval import flow_service
from app.modules.approval.flow_model import ApprovalFlow, ApprovalNode

ACTOR = 1


def _buoc(name: str, seq: int) -> dict:
    return {"seq": seq, "branch_key": "", "name": name, "node_kind": 1,
            "flow_role": 4, "approver_kind": 1, "approver_ref": "1",
            "multi_mode": 1, "quorum_percent": 50, "condition": "",
            "is_default_branch": False, "skip_duplicate": 1, "sla_hours": 0,
            "fallback_employee_id": None, "on_no_approver": 3}


@pytest.fixture()
def flow(db):
    flow = ApprovalFlow(entity="purchase_order", code="PO_TEST", name="Luồng thử",
                        description="", is_active=True, priority=0, condition="",
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    flow_service.add_step(db, flow.id, _buoc("Bước 1", 1), ACTOR)
    db.commit()
    return flow


def _theo_thu_tu(db, flow_id) -> list[tuple[int, str, str]]:
    return [(node.seq, node.branch_key, node.name)
            for node in flow_service.nodes_of(db, flow_id)]


def test_chen_chang_moi_vao_dau_day_buoc_cu_xuong(db, flow):
    #  Đây chính là ca nổ 500: chặng 1 đang có người ở đó.
    flow_service.add_step(db, flow.id, _buoc("Bước mới", 1), ACTOR)
    db.commit()

    assert _theo_thu_tu(db, flow.id) == [(1, "", "Bước mới"), (2, "", "Bước 1")]


def test_chen_vao_giua_chi_day_cac_buoc_tu_do_tro_di(db, flow):
    flow_service.add_step(db, flow.id, _buoc("Bước 2", 2), ACTOR)
    flow_service.add_step(db, flow.id, _buoc("Bước 3", 3), ACTOR)
    db.commit()

    flow_service.add_step(db, flow.id, _buoc("Chèn giữa", 2), ACTOR)
    db.commit()

    assert _theo_thu_tu(db, flow.id) == [
        (1, "", "Bước 1"),
        (2, "", "Chèn giữa"),
        (3, "", "Bước 2"),
        (4, "", "Bước 3"),
    ]


def test_them_vao_cuoi_khong_dong_cham_buoc_nao(db, flow):
    flow_service.add_step(db, flow.id, _buoc("Bước 2", 2), ACTOR)
    db.commit()

    assert _theo_thu_tu(db, flow.id) == [(1, "", "Bước 1"), (2, "", "Bước 2")]


def test_them_nhanh_song_song_thi_ca_chang_duoc_danh_khoa_lai(db, flow):
    #  Hai nhánh cùng chặng phải khác `branch_key`, nếu không cũng đâm vào đúng
    #  ràng buộc đó — nhánh cũ đang mang khóa rỗng nên phải đánh lại thành n1.
    flow_service.add_step(db, flow.id, _buoc("Nhánh 2", 1), ACTOR, is_branch=True)
    db.commit()

    assert _theo_thu_tu(db, flow.id) == [
        (1, "n1", "Bước 1"),
        (1, "n2", "Nhánh 2"),
    ]


def test_them_nhanh_thu_ba_van_chay(db, flow):
    flow_service.add_step(db, flow.id, _buoc("Nhánh 2", 1), ACTOR, is_branch=True)
    flow_service.add_step(db, flow.id, _buoc("Nhánh 3", 1), ACTOR, is_branch=True)
    db.commit()

    assert [key for _, key, _ in _theo_thu_tu(db, flow.id)] == ["n1", "n2", "n3"]


def test_them_nhanh_vao_chang_chua_co_gi_thi_giu_khoa_rong(db, flow):
    #  Chặng trống thì "nhánh" đầu tiên chính là bước thường — đánh khóa `n1`
    #  cho nó là bịa ra một nhánh không có gì song song.
    node = flow_service.add_step(db, flow.id, _buoc("Bước lẻ", 5), ACTOR, is_branch=True)
    db.commit()

    assert (node.seq, node.branch_key) == (5, "")


def test_seq_khong_hop_le_bi_keo_ve_1(db, flow):
    node = flow_service.add_step(db, flow.id, _buoc("Bước 0", 0), ACTOR)
    db.commit()

    assert node.seq == 1
    assert db.query(ApprovalNode).filter(ApprovalNode.flow_id == flow.id).count() == 2
