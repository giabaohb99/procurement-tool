"""Gập dấu tiếng Việt + hạ chữ thường — DÙNG CHUNG cho mọi nơi cần so khớp
không phân biệt hoa/thường/dấu.

Tách khỏi `help_center/service.py._fold` (phase 07 tìm kiếm toàn văn văn bản,
duoc-CR-477): hai module độc lập (HDSD, Văn bản) cùng cần đúng một phép biến
đổi — viết hai lần là sớm muộn lệch nhau (bên này thêm ký tự đặc biệt nào đó
mà bên kia quên theo). `help_center/service.py` gọi lại đúng hai hàm dưới đây,
không định nghĩa lại.
"""
import unicodedata


def fold_char(ch: str) -> str:
    """Bỏ dấu MỘT ký tự, trả về ĐÚNG một ký tự — để chỉ số (offset) trong
    chuỗi đã gập vẫn ánh xạ 1:1 về đúng vị trí trong chuỗi gốc. Đây là điều
    kiện bắt buộc cho việc dựng đoạn trích tìm kiếm theo offset
    (`document/search_service.py`): tìm thấy ở vị trí X trên chuỗi đã gập thì
    phải cắt đúng vị trí X trên chuỗi gốc.

    `đ`/`Đ` xử lý riêng: hai ký tự này KHÔNG phải tổ hợp base-letter + dấu
    trong Unicode (không tách được bằng NFD), nên vòng NFD bên dưới bỏ qua
    nguyên vẹn nếu không bắt tay trước.
    """
    if ch in "đĐ":
        return "d"
    base = "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))
    return (base or ch).lower()


def fold(text: str) -> str:
    """Chuẩn hóa KHÔNG DẤU + CHỮ THƯỜNG toàn chuỗi.

    Dùng cho tìm kiếm không phụ thuộc collation MySQL: cột lưu chữ đã gập sẵn
    (xem `document/search_model.py`) rồi so/đánh FULLTEXT trên chính cột đó,
    thay vì trông cậy `utf8mb4_*_ci` tự gập dấu tiếng Việt (nó không làm vậy).

    ⚠️ NFC-hóa CẢ CHUỖI trước khi lặp từng ký tự — bắt buộc, không phải một
    bước tối ưu. `fold_char` tự NFD-tách base-letter khỏi dấu NHƯNG chỉ đúng
    khi base-letter và dấu tổ hợp còn đứng CHUNG một ký tự Unicode (dạng NFC).
    Chuỗi đã ở dạng NFD sẵn (dấu tổ hợp RỜI thành ký tự riêng, vd gõ từ một số
    bàn phím/hệ điều hành) thì vòng lặp `for c in text` tách base-letter khỏi
    dấu của nó thành HAI lần gọi `fold_char` ĐỘC LẬP — dấu tổ hợp đứng một mình
    không biết base-letter nào để ghép, `fold_char` trả nguyên nó lại, và cả
    chữ KHÔNG được bỏ dấu (dựng lại được: `"a" + "̀"` (NFD, "à" rời hai
    mã) gập SAI ra `"à"` nếu thiếu bước NFC-hóa này, đúng bằng `"à"` (NFC, một
    mã) gập ĐÚNG ra `"a"`).

    NFC-hóa có thể đổi ĐỘ DÀI chuỗi khi đầu vào là NFD thật (hai mã gộp về
    một). Nơi cần offset khớp 1:1 với văn bản gốc (`document/search_service.py`
    dựng đoạn trích) đã tự kiểm `len(đã gập) == len(gốc)` trước khi dùng —
    không khớp thì bỏ qua đúng đoạn đó, không cắt sai chỗ.
    """
    normalized = unicodedata.normalize("NFC", text or "")
    return "".join(fold_char(c) for c in normalized)
