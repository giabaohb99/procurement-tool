"""DỮ LIỆU MẪU phân hệ CÔNG VIỆC (CR-218) — 3 nhóm · 5 danh sách · 41 việc · 82 việc con.

⚠️ **Chạy tay, KHÔNG nối vào `start.sh`.** Nó XÓA SẠCH mọi bảng `tab_work_*`
rồi nạp lại từ đầu:

    docker compose exec api python -m app.seed_cong_viec_demo

Vì sao cần: mở phân hệ ra với một list rỗng thì không thấy được thứ làm nên nó —
cây nhóm hai cấp, list đứng lẻ, thẻ có đủ chip ưu tiên / Tag / nhãn tùy biến,
hạn quá hạn tô đỏ, tiến độ việc con n/m, người phụ trách nhiều người. Bộ này
dựng đúng những trạng thái đó để bấm thử được ngay.

Nội dung (tên dự án, tên việc, ai làm gì) nằm ở
`app/seed_data/cong_viec_demo_corpus.py`; tệp này chỉ lo phần dựng.

Hạn chót ghi theo SỐ NGÀY so với hôm nay nên chạy vào ngày nào bộ dữ liệu cũng
có sẵn cả việc quá hạn, việc đến hạn hôm nay lẫn việc còn xa.
"""
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

#  Nạp TOÀN BỘ model trước khi chạm ORM: `Employee` khai quan hệ trỏ `User`
#  bằng chuỗi, thiếu một model là SQLAlchemy không dựng nổi mapper.
import app.core.all_models  # noqa: F401
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.work.list_config_service import (PRIORITY_KEY,
                                                  TAG_FIELD_NAME,
                                                  seed_system_label_fields)
from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTaskLabel)
from app.modules.work.model import (WorkGroup, WorkGroupMember, WorkList,
                                    WorkListMember, WorkMemberRole)
from app.modules.work.task_model import WorkSection, WorkTask, WorkTaskAssignee
from app.seed_data.cong_viec_demo_corpus import GROUPS, LISTS

#  Người "đứng tên" thao tác trong nhật ký (`created_by` của AuditMixin là
#  user_id). Lấy tài khoản admin đầu tiên cho gọn — dữ liệu mẫu, không phải
#  vết thao tác thật.
SEED_USER_ID = 1


def _employees(db: Session) -> dict[str, Employee]:
    """Tra nhân sự theo MÃ. Mã ổn định giữa các môi trường, id thì không."""
    return {e.code: e for e in db.query(Employee).filter(Employee.code.isnot(None)).all()}


def _ngay(offset: int | None) -> str:
    """Số ngày lệch → chuỗi `"YYYY-MM-DD"`. `None` = chưa đặt hạn."""
    if offset is None:
        return ""
    return (date.today() + timedelta(days=offset)).isoformat()


def _xoa_sach(db: Session) -> None:
    """Dọn trước khi nạp — chạy lại lần hai không đẻ ra bản sao.

    Xóa theo thứ tự phụ thuộc ngược, vì các bảng có khóa ngoại thật.
    """
    for model in (WorkTaskLabel, WorkTaskAssignee, WorkTask,
                  WorkLabelOption, WorkLabelField, WorkSection,
                  WorkListMember, WorkGroupMember, WorkList, WorkGroup):
        db.query(model).delete(synchronize_session=False)
    db.commit()


def _tao_nhom(db: Session, emps: dict, company_id: int) -> dict[str, WorkGroup]:
    theo_ten: dict[str, WorkGroup] = {}
    for i, spec in enumerate(GROUPS):
        cha = theo_ten.get(spec["parent"]) if spec["parent"] else None
        grp = WorkGroup(company_id=company_id, parent_id=cha.id if cha else None,
                        name=spec["name"], description=spec["desc"], sort_order=i,
                        created_by=SEED_USER_ID, updated_by=SEED_USER_ID)
        db.add(grp)
        db.flush()
        theo_ten[spec["name"]] = grp

        for code, role in spec["members"]:
            emp = emps.get(code)
            if not emp:
                continue
            db.add(WorkGroupMember(company_id=company_id, group_id=grp.id,
                                   employee_id=emp.id, role=role,
                                   created_by=SEED_USER_ID, updated_by=SEED_USER_ID))
    db.commit()
    return theo_ten


def _tao_list(db: Session, spec: dict, nhom: dict, emps: dict, company_id: int,
              sort_order: int) -> WorkList:
    grp = nhom.get(spec["group"]) if spec["group"] else None
    lst = WorkList(company_id=company_id, group_id=grp.id if grp else None,
                   name=spec["name"], description=spec["desc"], color=spec["color"],
                   sort_order=sort_order,
                   created_by=SEED_USER_ID, updated_by=SEED_USER_ID)
    db.add(lst)
    db.flush()

    #  Chủ sở hữu trước, rồi mới tới thành viên — giữ bất biến "đúng một OWNER".
    chu = emps.get(spec["owner"])
    if chu:
        db.add(WorkListMember(company_id=company_id, list_id=lst.id, employee_id=chu.id,
                              role=int(WorkMemberRole.OWNER),
                              created_by=SEED_USER_ID, updated_by=SEED_USER_ID))
    for code, role in spec["members"]:
        emp = emps.get(code)
        if not emp or (chu and emp.id == chu.id):
            continue
        db.add(WorkListMember(company_id=company_id, list_id=lst.id, employee_id=emp.id,
                              role=role, created_by=SEED_USER_ID, updated_by=SEED_USER_ID))
    db.commit()
    return lst


def _tao_cau_hinh(db: Session, lst: WorkList, spec: dict, company_id: int):
    """Cột kanban · trường nhãn tùy biến của một list (Tag là một trong số đó)."""
    sections = []
    for i, (ten, mau) in enumerate(spec["sections"]):
        s = WorkSection(company_id=company_id, list_id=lst.id, name=ten, color=mau,
                        sort_order=i, created_by=SEED_USER_ID, updated_by=SEED_USER_ID)
        db.add(s)
        sections.append(s)

    #  Độ ưu tiên và Tag: hai trường tùy biến nạp sẵn, y như list tạo qua API.
    seed_system_label_fields(db, lst.id, company_id, SEED_USER_ID)
    db.flush()

    #  Tag nay là GIÁ TRỊ của trường "Tag" chứ không còn bảng riêng.
    tag_field = (db.query(WorkLabelField)
                 .filter(WorkLabelField.list_id == lst.id,
                         WorkLabelField.name == TAG_FIELD_NAME).first())
    tags = {}
    for i, (ten, mau) in enumerate(spec["tags"]):
        o = WorkLabelOption(field_id=tag_field.id, name=ten, color=mau, sort_order=i,
                            created_by=SEED_USER_ID, updated_by=SEED_USER_ID)
        db.add(o)
        tags[ten] = o

    field = WorkLabelField(company_id=company_id, list_id=lst.id,
                           name=spec["label_field"]["name"], sort_order=2,
                           created_by=SEED_USER_ID, updated_by=SEED_USER_ID)
    db.add(field)
    db.flush()

    options = {}
    for i, (ten, mau) in enumerate(spec["label_field"]["options"]):
        o = WorkLabelOption(field_id=field.id, name=ten, color=mau, sort_order=i,
                            created_by=SEED_USER_ID, updated_by=SEED_USER_ID)
        db.add(o)
        options[ten] = o

    db.commit()
    return sections, tags, field, options, _priority_options(db, lst.id)


def _priority_options(db: Session, list_id: int) -> dict[int, WorkLabelOption]:
    """Bậc ưu tiên 1…4 → dòng giá trị tương ứng của list này."""
    field = (db.query(WorkLabelField)
             .filter(WorkLabelField.list_id == list_id,
                     WorkLabelField.system_key == PRIORITY_KEY).first())
    if not field:
        return {}
    rows = (db.query(WorkLabelOption).filter(WorkLabelOption.field_id == field.id)
            .order_by(WorkLabelOption.sort_order).all())
    return {i + 1: o for i, o in enumerate(rows)}


def _tao_viec(db: Session, lst: WorkList, spec: dict, sections, tags, field, options,
              priority_options, emps: dict, company_id: int) -> tuple[int, int]:
    """Việc và việc con của một list. Trả `(số việc, số việc con)`."""
    so_viec = so_viec_con = 0

    for i, t in enumerate(spec["tasks"]):
        pic_codes = t["pic"]
        nguoi_tao = emps.get(pic_codes[0]) if pic_codes else emps.get(spec["owner"])
        task = WorkTask(
            company_id=company_id, list_id=lst.id,
            section_id=sections[t["section"]].id,
            title=t["title"], description="", status=t["status"],
            start_date="", due_date=_ngay(t["due"]), sort_order=(i + 1) * 1000,
            creator_employee_id=nguoi_tao.id if nguoi_tao else 0,
            created_by=SEED_USER_ID, updated_by=SEED_USER_ID,
        )
        #  Việc đã hoàn thành phải có dấu hoàn thành, không thì báo cáo đếm
        #  "xong trong 7 ngày" ra số 0 dù bảng đầy thẻ xong.
        if t["status"] == 2:
            task.completed_at = datetime.utcnow() - timedelta(days=1)
            task.completed_by = nguoi_tao.id if nguoi_tao else 0
        db.add(task)
        db.flush()
        so_viec += 1

        for code in pic_codes:
            emp = emps.get(code)
            if emp:
                db.add(WorkTaskAssignee(task_id=task.id, employee_id=emp.id, kind=1,
                                        created_by=SEED_USER_ID, updated_by=SEED_USER_ID))
        for code in t["followers"]:
            emp = emps.get(code)
            if emp and code not in pic_codes:
                db.add(WorkTaskAssignee(task_id=task.id, employee_id=emp.id, kind=2,
                                        created_by=SEED_USER_ID, updated_by=SEED_USER_ID))

        for ten_tag in t["tags"]:
            tag = tags.get(ten_tag)
            if tag:
                db.add(WorkTaskLabel(task_id=task.id, field_id=tag.field_id,
                                     option_id=tag.id,
                                     created_by=SEED_USER_ID, updated_by=SEED_USER_ID))

        bac = priority_options.get(t["priority"])
        if bac is not None:
            db.add(WorkTaskLabel(task_id=task.id, field_id=bac.field_id, option_id=bac.id,
                                 created_by=SEED_USER_ID, updated_by=SEED_USER_ID))

        option = options.get(t["label"]) if t["label"] else None
        if option:
            db.add(WorkTaskLabel(task_id=task.id, field_id=field.id, option_id=option.id,
                                 created_by=SEED_USER_ID, updated_by=SEED_USER_ID))

        for j, (ten_con, xong) in enumerate(t["subtasks"]):
            #  Việc con: `section_id = NULL` và mang `list_id` của cha (C-05) —
            #  đặt cột cho nó là nó lọt ra kanban thành thẻ riêng.
            con = WorkTask(
                company_id=company_id, list_id=lst.id, section_id=None, parent_id=task.id,
                title=ten_con, description="", status=2 if xong else 1,
                start_date="", due_date="", sort_order=(j + 1) * 1000,
                creator_employee_id=nguoi_tao.id if nguoi_tao else 0,
                created_by=SEED_USER_ID, updated_by=SEED_USER_ID,
            )
            if xong:
                con.completed_at = datetime.utcnow() - timedelta(days=1)
                con.completed_by = nguoi_tao.id if nguoi_tao else 0
            db.add(con)
            so_viec_con += 1

    db.commit()
    return so_viec, so_viec_con


def seed(db: Session) -> None:
    emps = _employees(db)
    thieu = {code for spec in LISTS for code, _ in spec["members"]} | {s["owner"] for s in LISTS}
    thieu = sorted(c for c in thieu if c not in emps)
    if thieu:
        print(f"⚠️  Không thấy {len(thieu)} mã nhân sự, việc của họ sẽ để trống: {thieu}")

    chu_dau = emps.get(LISTS[0]["owner"])
    company_id = chu_dau.company_id if chu_dau else 1

    _xoa_sach(db)
    nhom = _tao_nhom(db, emps, company_id)

    tong_viec = tong_con = 0
    for i, spec in enumerate(LISTS):
        lst = _tao_list(db, spec, nhom, emps, company_id, i)
        sections, tags, field, options, bac_uu_tien = _tao_cau_hinh(db, lst, spec, company_id)
        viec, con = _tao_viec(db, lst, spec, sections, tags, field, options, bac_uu_tien,
                              emps, company_id)
        tong_viec += viec
        tong_con += con
        print(f"  · {spec['name']}: {len(sections)} cột · {viec} việc · {con} việc con")

    print(f"\nXong: {len(nhom)} nhóm · {len(LISTS)} danh sách · {tong_viec} việc "
          f"· {tong_con} việc con (pháp nhân #{company_id}).")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
