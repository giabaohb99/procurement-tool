from collections import Counter
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session


def assert_unique_product_codes(new_codes: Iterable[str],
                                old_codes: Iterable[str] = (),
                                message: str = "") -> None:
    """Mã hàng phải DUY NHẤT trên phiếu YCMH (ĐMH KHÔNG còn dùng luật này — bao-CR-308).

    VÌ SAO: dòng ĐMH nối ngược về dòng YCMH bằng CHUỖI `product_code`, không có khóa dòng
    (`purchase_request/service.sync_from_purchase_orders`). Hàm đó cộng dồn SL đặt/nhận theo
    mã rồi ghi CÙNG một con số vào MỌI dòng YCMH trùng mã → tiến độ nhân đôi, kéo theo trạng
    thái dòng và trạng thái phiếu sai. Chiều ngược lại thì an toàn: nhiều dòng ĐMH cùng mã
    được cộng gộp đúng (giống một YCMH rải ra nhiều ĐMH), nên từ bao-CR-308 ĐMH cho phép
    trùng mã để mua theo bộ chứng từ (cùng mã, khác lô / khác Tên trên hóa đơn).

    CHỈ CHẶN TRÙNG MỚI (số lần xuất hiện của một mã tăng so với dữ liệu đang lưu). Dữ liệu đã
    trùng sẵn vẫn lưu lại được — vì dòng ĐMH `completed`/`cancelled` bị khóa, giao diện không
    cho xóa, nên chặn cứng sẽ khóa chết những đơn cũ đã lỡ trùng, không ai sửa được nữa.
    """
    def _count(codes: Iterable[str]) -> Counter:
        return Counter(c for c in ((x or "").strip() for x in codes) if c)

    before, after = _count(old_codes), _count(new_codes)
    bad = sorted(c for c, n in after.items() if n > 1 and n > before.get(c, 0))
    if not bad:
        return
    tmpl = message or ("Mã hàng bị trùng: {codes}. Mỗi mã chỉ được xuất hiện trên 1 dòng — "
                       "hãy gộp số lượng vào một dòng hoặc đổi sang mã khác.")
    raise HTTPException(400, tmpl.format(codes=", ".join(bad)))


#  CSDL có khóa hàng thật. SQLite (bộ test) không có `FOR UPDATE` — gọi vào là
#  ném lỗi cú pháp, nên phải hỏi phương ngữ trước.
_ROW_LOCK_DIALECTS = ("mysql", "postgresql")


def generate_code(db: Session, model, prefix: str) -> str:
    """Số chứng từ kế tiếp cho một tiền tố (`CTY001`, `NP027`…).

    ⚠️ **KHÓA HÀNG LỚN NHẤT trong lúc đọc.** Không khóa thì đây là "đọc rồi mới
    ghi" kinh điển: hai phiên cùng đọc ra `NP035`, cùng dựng `NP036`, và phiên
    về sau đâm vào ràng buộc UNIQUE của cột `code` → **500 Internal Server
    Error** ngay trên đường đi bình thường nhất của hệ (bấm *Lưu*).

    Dựng lại được 07/09/2026 bằng bài ép tải qua Chrome DevTools: bắn **30 lượt
    lập đơn nghỉ phép cùng lúc → chỉ 5 lượt sống, 25 lượt ăn 500**
    (`Duplicate entry 'NP035' for key 'tab_leave_request.code'`). Hàm này dùng
    ở **27 chỗ** — thu mua, văn thư, đặt xe, phòng họp, nhân sự — nên lỗi đó có
    ở mọi màn "bấm Lưu", chỉ cần hai người bấm trùng nhịp.

    Cách chữa: khóa **hàng NHỎ NHẤT** của tiền tố làm cái then cửa, rồi mới đọc
    hàng lớn nhất. Đọc-có-khóa của InnoDB luôn thấy bản GHI MỚI NHẤT (không đi
    qua ảnh chụp MVCC), nên phiên xếp sau chờ phiên trước commit rồi đọc lại là
    ra đúng số kế tiếp. Khóa giữ tới lúc commit — mọi chỗ gọi đều `add` +
    `commit` ngay sau đây.

    ⚠️ **Khóa hàng NHỎ NHẤT chứ không phải hàng lớn nhất**, dù hàng lớn nhất mới
    là hàng ta cần đọc. Bản vá đầu khóa hàng lớn nhất và đổi 500 *trùng mã*
    thành 500 *deadlock* (MySQL 1213): khóa-kèm-khoảng-trống của hàng cuối nằm
    đúng chỗ các phiên khác đang CHÈN, nên chúng vừa chờ nhau vừa chặn nhau.
    Hàng nhỏ nhất thì không ai chèn vào trước nó — mọi phiên cùng xin đúng một
    hàng đó nên xếp thành hàng đợi, không có vòng chờ để mà kẹt.

    Vẫn còn đúng một khe hẹp: bảng RỖNG thì không có hàng nào để khóa, hai phiên
    cùng ra `001`. Chấp nhận — đó là bản ghi đầu tiên của cả một danh mục, và
    người thua vẫn thấy câu lỗi rồi bấm lại.
    """
    same_prefix = db.query(model).filter(model.code.like(f"{prefix}%"))
    lockable = db.bind is not None and db.bind.dialect.name in _ROW_LOCK_DIALECTS
    if lockable:
        #  Then cửa. Kết quả không dùng tới — chỉ cần giữ khóa cho tới commit.
        same_prefix.order_by(model.code.asc()).with_for_update().first()

    last_query = same_prefix.order_by(model.code.desc())
    if lockable:
        #  ⚠️ Câu đọc SỐ LỚN NHẤT cũng phải CÓ KHÓA, không chỉ then cửa ở trên.
        #  MySQL chạy mức cô lập REPEATABLE READ: đọc thường lấy theo ẢNH CHỤP
        #  mở tại câu truy vấn ĐẦU TIÊN của giao dịch — mà trước khi tới đây,
        #  chỗ gọi đã đọc hồ sơ quyền / nhân sự, nên ảnh chụp có từ lúc đó. Kết
        #  quả: phiên xếp sau chờ then cửa xong, đọc lại vẫn ra số CŨ và lại
        #  dựng trùng mã. Đọc-có-khóa thì đi thẳng vào bản ghi mới nhất.
        #  Không sợ kẹt khóa như bản trước: then cửa đã xếp mọi phiên thành hàng
        #  nên chỉ MỘT phiên giữ khóa cuối bảng tại một thời điểm.
        last_query = last_query.with_for_update()
    last_obj = last_query.first()
    if not last_obj or not last_obj.code.startswith(prefix):
        return f"{prefix}001"

    try:
        num = int(last_obj.code[len(prefix):]) + 1
        return f"{prefix}{num:03d}"
    except ValueError:
        return f"{prefix}001"
