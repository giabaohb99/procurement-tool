"""Nạp nội dung Trung tâm Hướng dẫn (bài viết + câu hỏi thường gặp) từ file JSON xuất sẵn.

Nguồn: app/seed_data/help-center-content.json (nằm trong image, không cần copy tay).
Nội dung Help Center nằm trong DB chứ không phải file repo, nên soạn ở máy này xong không
tự có ở dev/prod — file JSON là bản mang đi, script này là bản nạp.

HAI CÁCH KHỚP — chọn theo việc đang làm:

**Mặc định: khớp theo TIÊU ĐỀ** (và theo CÂU HỎI với FAQ). Dùng khi mang một BỘ BÀI MỚI sang
môi trường chưa có gì, hoặc chỉ muốn bổ sung.
  - Đã có  -> cập nhật nội dung / mô tả / icon / thứ tự / cha.
  - Chưa có -> tạo mới.
  - Bài viết trong DB mà file không có -> GIỮ NGUYÊN, chỉ liệt kê ra để người chạy tự quyết.
Không xóa gì cả. **Cái bẫy:** đổi tên bài ở nguồn (bỏ số thứ tự "1. ", "2. "…) thì bên đích
coi đó là bài MỚI — bộ cũ nằm song song bộ mới, phải xóa tay trên giao diện. Dính thật ở
CR-052 khi nạp file Excel lên prod.

**`--theo-id`: khớp theo ID** — dùng khi ĐỒNG BỘ hai môi trường vốn cùng một gốc (dev -> prod).
Id hai bên trùng nhau vì cùng sinh ra từ một bản seed, nên khớp theo id thì đổi tiêu đề vẫn
nhận ra là cùng một bài, không đẻ bản sao. Thêm `--xoa-thua` thì xóa nốt bài bên đích không
có trong file -> bên đích thành BẢN SAO Y HỆT nguồn. Xóa là không hoàn tác: xuất bản hiện tại
ra file bằng `scripts.export_help_content` trước đã.
Ảnh minh hoạ từng bước (`tab_help_article_slide`) gắn theo id bài, nên khớp theo id là cách
DUY NHẤT giữ được ảnh — khớp theo tiêu đề mà bài bị đổi tên thì bài cũ (mang ảnh) bị bỏ lại.

`parent_id` trong file trỏ tới `id` trong CHÍNH file đó, KHÔNG phải id của môi trường đích,
nên phải tạo cha trước rồi map id cũ -> id mới (file đã sắp sẵn cha trước con).

Chạy thử (mặc định, không ghi gì):
    docker exec -w /app <api> python -m scripts.import_help_content
Nạp thật:
    docker exec -w /app <api> python -m scripts.import_help_content --nap
Đồng bộ y hệt nguồn:
    docker exec -w /app -e HELP_JSON=/app/help-dev.json <api> \
        python -m scripts.import_help_content --theo-id --xoa-thua --nap
"""
import json
import os
import sys

from sqlalchemy import func, text

import app.core.all_models  # noqa: F401  (đăng ký mapper)
from app.core.database import SessionLocal
from app.modules.faq.model import Faq
from app.modules.help_center.model import HelpArticle
from app.modules.role.model import Role
from app.modules.user.model import UserRole

JSON_PATH = os.environ.get("HELP_JSON", "/app/app/seed_data/help-center-content.json")
NAP = "--nap" in sys.argv
THEO_ID = "--theo-id" in sys.argv
XOA_THUA = "--xoa-thua" in sys.argv


def actor_id(db) -> int:
    """Người thực hiện = một tài khoản quản trị bất kỳ (cột created_by/updated_by)."""
    role = db.query(Role).filter(Role.code == "admin").first()
    ur = db.query(UserRole).filter(UserRole.role_id == role.id).first() if role else None
    return ur.user_id if ur else 1


def main() -> None:
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    db = SessionLocal()
    me = actor_id(db)
    print(f"File: {JSON_PATH} (xuất từ {data.get('exported_from')}) — "
          f"{len(data['articles'])} bài viết, {len(data['faqs'])} câu hỏi")
    print(f"Chế độ: {'NẠP THẬT' if NAP else 'CHẠY THỬ (không ghi gì)'} — người thực hiện: user #{me}")
    print("-" * 78)

    # ---------------------------------------------------------------- bài viết
    cu = db.query(HelpArticle).all()
    ten_cu = {a.title: a for a in cu}
    id_cu = {a.id: a for a in cu}
    id_map: dict[int, int] = {}          # id trong file -> id thật ở môi trường này
    them = capnhat = 0
    for a in data["articles"]:
        cha = id_map.get(a["parent_id"]) if a.get("parent_id") else None
        obj = id_cu.get(a["id"]) if THEO_ID else ten_cu.get(a["title"])
        if obj:
            capnhat += 1
            doi_ten = " -> " + a["title"] if THEO_ID and obj.title != a["title"] else ""
            print(f"  ~ cập nhật  #{obj.id:<4} {obj.title}{doi_ten}")
            if NAP:
                # Khớp theo id thì tiêu đề cũng là thứ phải đồng bộ (đổi tên bài ở nguồn).
                # Khớp theo tiêu đề thì tiêu đề CHÍNH LÀ khoá — không đụng vào.
                if THEO_ID:
                    obj.title = a["title"]
                obj.parent_id = cha
                obj.content = a.get("content") or ""
                obj.sort_order = a.get("sort_order") or 0
                obj.summary = a.get("summary")
                obj.icon = a.get("icon")
                obj.updated_by = me
                db.flush()
            id_map[a["id"]] = obj.id
        else:
            them += 1
            print(f"  + thêm mới  {'#' + str(a['id']) if THEO_ID else '     '} {a['title']}")
            if NAP:
                obj = HelpArticle(
                    parent_id=cha, title=a["title"], content=a.get("content") or "",
                    sort_order=a.get("sort_order") or 0, summary=a.get("summary"),
                    icon=a.get("icon"), created_by=me, updated_by=me)
                # Khớp theo id: giữ NGUYÊN id của nguồn, để hai bên soi gương được và để
                # lần đồng bộ sau vẫn nhận ra nhau (id tự sinh thì lệch ngay từ lần đầu).
                if THEO_ID:
                    obj.id = a["id"]
                db.add(obj)
                db.flush()
                id_map[a["id"]] = obj.id
            else:
                id_map[a["id"]] = a["id"] if THEO_ID else -a["id"]   # chạy thử: giữ chỗ

    if THEO_ID:
        thua = [o for i, o in id_cu.items() if i not in {a["id"] for a in data["articles"]}]
        if thua:
            print(f"\n  Bài viết CÓ trong DB mà file không có ({len(thua)}) — "
                  f"{'XÓA' if XOA_THUA else 'giữ nguyên, thêm --xoa-thua để xóa'}:")
            for o in thua:
                print(f"    {'-' if XOA_THUA else '?'} #{o.id} {o.title}")
            if NAP and XOA_THUA:
                # Xóa SAU khi con đã được chuyển sang cha mới ở vòng lặp trên, nếu không
                # khóa ngoại parent_id chặn. Xóa từ lá lên gốc cho chắc.
                for o in sorted(thua, key=lambda x: -(x.parent_id or 0)):
                    db.delete(o)
                db.flush()
    else:
        du = sorted(set(ten_cu) - {a["title"] for a in data["articles"]})
        if du:
            print(f"\n  Bài viết CÓ trong DB mà file không có ({len(du)}) — giữ nguyên:")
            for t in du:
                print(f"    ? {t}")

    # ------------------------------------------------------------- câu hỏi FAQ
    print("")
    hoi_cu = {q.question: q for q in db.query(Faq).all()}
    f_them = f_capnhat = 0
    for q in data["faqs"]:
        obj = hoi_cu.get(q["question"])
        if obj:
            f_capnhat += 1
            if NAP:
                obj.answer = q.get("answer") or ""
                obj.sort_order = q.get("sort_order") or 0
                obj.is_active = bool(q.get("is_active", True))
                obj.updated_by = me
        else:
            f_them += 1
            if NAP:
                db.add(Faq(question=q["question"], answer=q.get("answer") or "",
                           sort_order=q.get("sort_order") or 0,
                           is_active=bool(q.get("is_active", True)),
                           created_by=me, updated_by=me))
    print(f"  Câu hỏi thường gặp: thêm {f_them}, cập nhật {f_capnhat}")

    if NAP:
        db.commit()
        if THEO_ID:
            # Chèn id tay không làm AUTO_INCREMENT nhảy theo -> bài tạo trên giao diện sau đó
            # sẽ đụng id đã có. Đẩy mốc lên quá id lớn nhất.
            mx = db.query(func.max(HelpArticle.id)).scalar() or 0
            db.execute(text(f"ALTER TABLE tab_help_article AUTO_INCREMENT = {mx + 1}"))
            db.commit()
            print(f"  (đặt lại AUTO_INCREMENT của tab_help_article = {mx + 1})")
    print("-" * 78)
    print(f"Bài viết: thêm {them}, cập nhật {capnhat}. "
          f"{'ĐÃ GHI VÀO DB.' if NAP else 'Chạy thử — chưa ghi gì.'}")
    print(f"Tổng sau khi chạy: {db.query(HelpArticle).count()} bài viết, "
          f"{db.query(Faq).count()} câu hỏi")
    db.close()


if __name__ == "__main__":
    main()
