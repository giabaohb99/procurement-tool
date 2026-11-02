"""bao-CR-708 — các chế độ BHXH tách thành loại nghỉ riêng (02/11/2026).

Ba chốt:
1. Mọi mã trong `seed_nghi_phep.LEAVE_TYPES` phải có trong `LEAVE_TYPE_SET` — mã đó ghi sang
   metadata giấy GNP, lệch một ký tự là giấy mang loại nghỉ vô nghĩa (đọc ở `type_metadata`).
2. Năm loại mới mang đúng thuộc tính luật: giới tính, trần ngày, tính / không tính ngày lễ,
   cần giấy tờ, không trừ quỹ phép năm, ghi chú "BHXH chi trả" kèm căn cứ.
3. Seed chạy lại được: lần hai không thêm dòng, loại đã có không bị ghi đè.
"""
from app.core.leave_codes import LEAVE_TYPE_SET
from app.modules.document.type_metadata import _string_in_set
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import GENDER_FEMALE, GENDER_UNKNOWN
from app.seed_nghi_phep import LEAVE_TYPE_NOTES, LEAVE_TYPES, seed_leave_types

NEW_CODES = {"prenatal", "miscarriage", "contraception", "child_sick", "recuperation"}


def test_every_seeded_code_is_in_the_gnp_code_set():
    codes = {row[0] for row in LEAVE_TYPES}
    assert NEW_CODES <= codes
    assert codes <= LEAVE_TYPE_SET.values


def test_every_bhxh_type_has_a_legal_note():
    for code in NEW_CODES:
        note = LEAVE_TYPE_NOTES[code]
        assert note.startswith("BHXH chi trả")
        assert "Luật BHXH 2024" in note
        assert len(note) <= 500          # cột note String(500)


def test_seed_creates_bhxh_types_with_legal_attributes(db):
    seed_leave_types(db)
    by_code = {t.code: t for t in db.query(LeaveType).all()}
    assert NEW_CODES <= set(by_code)

    expect = {
        #  code: (giới tính, trần/lần, trừ lễ + cuối tuần, cần giấy)
        "prenatal": (GENDER_FEMALE, 2.0, True, True),
        "miscarriage": (GENDER_FEMALE, 50.0, False, True),
        "contraception": (GENDER_UNKNOWN, 15.0, False, True),
        "child_sick": (GENDER_UNKNOWN, 20.0, True, True),
        "recuperation": (GENDER_UNKNOWN, 10.0, False, False),
    }
    for code, (gender, cap, exclude, attach) in expect.items():
        t = by_code[code]
        assert t.gender == gender, code
        assert t.max_days_per_request == cap, code
        assert t.exclude_holiday is exclude, code
        assert t.require_attachment is attach, code
        assert t.counts_balance is False, code          # không trừ quỹ phép năm
        assert t.annual_quota_days == 0.0, code
        assert t.note == LEAVE_TYPE_NOTES[code]


def test_seed_is_rerunnable_and_does_not_overwrite(db):
    seed_leave_types(db)
    t = db.query(LeaveType).filter_by(code="child_sick").one()
    t.max_days_per_request = 15.0          # quản trị sửa tay ở màn danh mục
    t.note = "sua tay"
    db.flush()
    assert seed_leave_types(db) == 0
    t = db.query(LeaveType).filter_by(code="child_sick").one()
    assert t.max_days_per_request == 15.0
    assert t.note == "sua tay"


def test_gnp_metadata_accepts_the_new_codes():
    for code in NEW_CODES:
        #  Đúng cửa kiểm ô `leave_type` của giấy GNP (`_check_leave`).
        assert _string_in_set(code, LEAVE_TYPE_SET, "Loại nghỉ", "annual") == code
