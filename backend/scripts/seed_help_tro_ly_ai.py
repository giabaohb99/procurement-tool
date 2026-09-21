# -*- coding: utf-8 -*-
"""Seed bài Trung tâm trợ giúp: TRỢ LÝ AI — bài cha của cụm trợ lý AI (bao-CR-445).

Bài «Trợ lý AI» (nhóm «Các chức năng khác») vốn được nạp tay từ bảng Excel, không thuộc
script nào. Từ bao-CR-445 script này NHẬN SỞ HỮU nội dung bài đó: sửa bài là sửa ở đây rồi
chạy lại trên từng môi trường, không sửa tay trên giao diện quản trị nữa.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_tro_ly_ai.py

Idempotent, và KHÁC các seed bài con ở một điểm: bài này CÓ BÀI CON thuộc script khác
(`seed_help_tro_ly_ai_lap_bo_tai_khoan.py` — bao-CR-441, và
`seed_help_lap_bo_tai_khoan_phong_tu_mua.py` — bao-CR-444), nên KHÔNG xóa-chèn-lại.
Đã có bài cùng tiêu đề dưới «Các chức năng khác» thì CẬP NHẬT TẠI CHỖ (giữ id, sort_order,
giữ nguyên các bài con). Chưa có thì tạo mới ở cuối nhóm. Không thấy nhóm cha thì DỪNG.

Thứ tự nạp trên DB trống: chạy script này TRƯỚC, rồi mới chạy hai seed bài con (chúng tìm
bài cha theo tiêu đề «Trợ lý AI»).

⚠️ Bảng «Nhóm câu hỏi» phải khớp bộ tool của trợ lý (`app/modules/assistant/tools/`) và bài
`doc/ai/` tương ứng; dòng «Lập bộ tài khoản thu mua» khớp tool T49 (bao-CR-435). Đổi tool
thì sửa bảng này.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.help_center.model import HelpArticle  # noqa: E402

PARENT_TITLE = "Các chức năng khác"
ARTICLE_TITLE = "Trợ lý AI"
PREVIOUS_TITLE = "Comment trên phiếu"
AI_SETUP_TITLE = "Lập bộ tài khoản thu mua bằng Trợ lý AI"
MANUAL_SETUP_TITLE = "Lập bộ tài khoản phòng tự mua hàng"


# --------------------------------------------------------------------------- #
#  LIÊN KẾT NỘI BỘ — slug sinh y hệt slugify() của help-center (help-slug.tsx).
#  Tiêu đề đích phải DUY NHẤT trong tab_help_article, không thì portal gắn hậu tố "-{id}".
# --------------------------------------------------------------------------- #
def slugify(value: str) -> str:
    value = value.replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFD", value)
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"^-+|-+$", "", value)


def ref(target_title: str, label: str) -> str:
    return (
        f'<a href="/{slugify(target_title)}" '
        'style="color:var(--primary,#2563eb);font-weight:600;text-decoration:underline">'
        f"{label}</a>"
    )


SUMMARY = "HD dùng AI tra cứu quy trình, tóm tắt phiếu và gợi ý thao tác"

CONTENT = f"""<h2>I. Giới thiệu</h2>
<p>Hệ thống tích hợp <strong>trợ lý AI</strong> giúp bạn tra cứu quy trình, tóm tắt phiếu và gợi ý thao tác kế tiếp — thay vì phải nhớ hết các bước hoặc hỏi đồng nghiệp.</p>

<h2>II. Các bước thao tác</h2>
<h3>Bước 1 — Mở trợ lý AI</h3>
<ul>
<li>Nhấn vào <strong>bong bóng trợ lý AI</strong> ở góc dưới bên phải màn hình, hoặc chọn phân hệ <strong>Trợ lý AI</strong> từ màn chọn phân hệ.</li>
<li>Khung chat mở ra, bạn nhập câu hỏi bằng tiếng Việt bình thường.</li>
</ul>

<h3>Bước 2 — Đặt câu hỏi</h3>
<table><thead><tr><th>Nhóm câu hỏi</th><th>Ví dụ</th></tr></thead><tbody><tr><td><strong>Tra cứu quy trình</strong></td><td>"Làm sao tạo phiếu yêu cầu báo giá?" · "Phiếu bị trả lại thì tôi phải làm gì?"</td></tr><tr><td><strong>Hiểu trạng thái</strong></td><td>"Trạng thái Đã điều phối nghĩa là gì?" · "Vì sao phiếu chưa tự hoàn thành?"</td></tr><tr><td><strong>Tra cứu dữ liệu mua hàng</strong></td><td>"Thùng carton 5 lớp hay mua của NCC nào, giá gần nhất bao nhiêu?" · "Hợp đồng với NCC X còn hiệu lực không?" · "Tháng 7 chi tiêu nhiều nhất cho mặt hàng gì?"<br><em>Lưu ý: kết quả tra cứu tuân theo phân quyền — người không có quyền xem NCC sẽ không thấy thông tin NCC.</em></td></tr><tr><td><strong>Công nợ & thanh toán</strong></td><td>"NCC A còn nợ bao nhiêu, khoản nào sắp tới hạn?" · "Liệt kê các khoản nợ có hóa đơn trong tháng 8" · "Phiếu thanh toán PR-xxx có duyệt được không?" · "NCC B còn tiền treo trả trước không?"</td></tr><tr><td><strong>Gợi ý thao tác</strong></td><td>"Tôi cần mua 1.000 thùng carton, nên tạo phiếu gì?"</td></tr><tr><td><strong>Soạn phiếu yêu cầu báo giá</strong></td><td>"Soạn phiếu yêu cầu báo giá mua 500 thùng carton 5 lớp cho tháng 9" · "Tôi cần mua máy in cho văn phòng, giúp tôi tạo yêu cầu báo giá"</td></tr><tr><td><strong>Soạn đề nghị thanh toán</strong></td><td>"Lập đề nghị thanh toán các khoản tới hạn tuần này của NCC A"</td></tr><tr><td><strong>Soạn nội dung</strong></td><td>"Viết giúp tôi mục đích mua hàng cho nhu cầu bổ sung bao bì tháng 8"</td></tr><tr><td><strong>Lập bộ tài khoản thu mua</strong> (dành cho quản trị)</td><td>"Lập bộ tài khoản nhân viên thu mua cho Nguyễn Văn A, loại trừ phòng Dego Organic" · "Gán vai trò Quản lý thu mua của phòng cho Trần Thị B"<br><em>Trợ lý chỉ gán vai trò có sẵn và khai ô Loại trừ phòng ban cho tài khoản đã có; không tạo tài khoản, không đặt mật khẩu. Xem bài {ref(AI_SETUP_TITLE, AI_SETUP_TITLE)}.</em></td></tr></tbody></table>

<h3>Bước 3 — Kiểm chứng và thao tác</h3>
<ul>
<li>AI trả lời kèm <strong>liên kết tới bài hướng dẫn</strong> hoặc <strong>phiếu liên quan</strong> — nhấn để xem chi tiết.</li>
<li>AI có thể soạn sẵn nội dung phiếu <strong>Yêu cầu báo giá</strong>: mô tả nhu cầu trong khung chat, trợ lý soạn nháp rồi hiện nút <strong>Tạo yêu cầu báo giá</strong> — bấm nút để mở form đã điền sẵn, rà lại và tự bấm Tạo. Phiếu chỉ được ghi vào hệ thống khi bạn bấm Tạo. Các thao tác khác (duyệt phiếu, sửa phiếu...) bạn vẫn tự thực hiện trên màn hình.</li>
<li>Tương tự với <strong>Đề nghị thanh toán</strong>: nhờ trợ lý gom các khoản nợ cần trả, bấm nút <strong>Tạo đề nghị thanh toán</strong> để mở form đã chọn sẵn khoản nợ. Nhà cung cấp còn <strong>tiền treo trả trước</strong> thì trợ lý chia sẵn luôn cột <strong>Cấn trừ trả trước</strong> (ưu tiên khoản tới hạn sớm) — số này chỉ là đề xuất, bạn sửa hay bỏ từng dòng được; phần cấn trừ chỉ trừ thật vào công nợ khi phiếu được <strong>Duyệt</strong>.</li>
<li>Với phiếu thanh toán <strong>đang chờ duyệt</strong> có phần cấn trừ, hỏi trợ lý là biết trước phiếu <strong>có duyệt được không</strong> — trợ lý soát cùng bộ luật với lúc Duyệt và chỉ ra chỗ vướng (tiền treo không còn đủ, khoản nợ đã đổi...).</li>
<li>Với <strong>bộ tài khoản thu mua</strong>: trợ lý dò hồ sơ, tài khoản và vai trò đang có rồi hiện <strong>thẻ đề xuất</strong> từng dòng thêm / bỏ / không đổi. Chỉ khi bạn bấm <strong>Xác nhận</strong> hệ thống mới gán vai trò và ghi phạm vi. Thẻ có hạn 15 phút — chi tiết ở bài {ref(AI_SETUP_TITLE, AI_SETUP_TITLE)}; muốn làm tay đủ bốn bước thì xem bài {ref(MANUAL_SETUP_TITLE, MANUAL_SETUP_TITLE)}.</li>
</ul>

<h2>III. Mẹo hỏi hiệu quả</h2>
<ul>
<li><strong>Nêu rõ bối cảnh:</strong> "Tôi là người yêu cầu, phiếu đang ở trạng thái Đã khảo sát, tôi cần làm gì?" — cụ thể hơn "làm gì tiếp theo?".</li>
<li><strong>Kèm mã phiếu</strong> khi hỏi về một phiếu cụ thể: "Phiếu YCBG06082607 đang chờ ai xử lý?"</li>
<li><strong>Hỏi tiếp trong cùng đoạn chat</strong> — AI nhớ ngữ cảnh câu hỏi trước đó.</li>
</ul>
<p>⚠️</p><p><strong>Giới hạn cần biết</strong></p><p>AI hỗ trợ tra cứu và giải thích, <strong>không thay thế quyết định nghiệp vụ</strong>. Với các nội dung quan trọng (giá, nhà cung cấp, số lượng đặt hàng), hãy đối chiếu lại với dữ liệu thực tế trên phiếu và xác nhận với người phụ trách.</p>
<p>💡</p><p><strong>Không tìm thấy câu trả lời?</strong></p><p>Nếu AI chưa trả lời được, hãy dùng thanh <strong>tìm kiếm</strong> ở Trung tâm Hướng dẫn (phím tắt <code>Ctrl + K</code>) hoặc liên hệ Team DX để được hỗ trợ trực tiếp.</p>
<h2>IV. Điều hướng</h2><ul><li><strong>Thuộc thư mục:</strong> {PARENT_TITLE}</li><li><strong>Bài trước:</strong> {ref(PREVIOUS_TITLE, PREVIOUS_TITLE)}</li><li><strong>Bài con:</strong> {ref(AI_SETUP_TITLE, AI_SETUP_TITLE)} · {ref(MANUAL_SETUP_TITLE, MANUAL_SETUP_TITLE)}</li></ul><p>Hai bài con ở trên dành cho người quản trị lập bộ tài khoản thu mua. Cảm ơn bạn đã theo dõi — chúc bạn sử dụng hệ thống thuận lợi!</p>"""


def find_parent(db):
    """Nhóm «Các chức năng khác»; nếu trùng tiêu đề thì ưu tiên bài ở gốc (không có cha)."""
    candidates = db.query(HelpArticle).filter(HelpArticle.title == PARENT_TITLE).all()
    if not candidates:
        return None
    for art in candidates:
        if not art.parent_id:
            return art
    return candidates[0]


def main():
    db = SessionLocal()
    try:
        parent = find_parent(db)
        if parent is None:
            print(f"Không thấy nhóm cha «{PARENT_TITLE}» — dừng, không tạo nhóm mới.")
            sys.exit(1)

        art = (
            db.query(HelpArticle)
            .filter(HelpArticle.title == ARTICLE_TITLE, HelpArticle.parent_id == parent.id)
            .first()
        )
        if art is not None:
            #  Cập nhật tại chỗ: bài này có bài con thuộc script khác, KHÔNG xóa-chèn-lại.
            changed = art.content != CONTENT or art.summary != SUMMARY
            art.summary = SUMMARY
            art.content = CONTENT
            db.commit()
            children = (
                db.query(HelpArticle.id)
                .filter(HelpArticle.parent_id == art.id)
                .count()
            )
            state = "đã cập nhật nội dung" if changed else "nội dung không đổi"
            print(f"Bài «{ARTICLE_TITLE}» (id={art.id}, sort_order={art.sort_order}) {state}; "
                  f"giữ nguyên {children} bài con.")
            return

        max_order = (
            db.query(HelpArticle.sort_order)
            .filter(HelpArticle.parent_id == parent.id)
            .order_by(HelpArticle.sort_order.desc())
            .first()
        )
        order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0
        art = HelpArticle(
            parent_id=parent.id,
            title=ARTICLE_TITLE,
            summary=SUMMARY,
            content=CONTENT,
            sort_order=order,
        )
        db.add(art)
        db.commit()
        print(f"Đã dựng bài «{ARTICLE_TITLE}» (id={art.id}) dưới «{parent.title}» "
              f"(id={parent.id}, sort_order={order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
