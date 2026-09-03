# TỪ ĐIỂN DỮ LIỆU ERP V2 — CHỈ MỤC

Bản 1.0 — 28/08/2026, cập nhật 03/09/2026 (F13a thêm `tab_forum_board`). Từ điển đang tả **102 bảng**.
CHÚ Ý (03/09/2026): mã nguồn đã có 114 `__tablename__` — chênh lệch chủ yếu là cụm bảng phân hệ
Công việc (CR-216) chưa có mục từ điển; ai làm tài liệu Công việc thì bổ sung và sửa con số ở đây. Từ điển chia 5 tệp theo cụm — mỗi bảng liệt kê đủ cột, kiểu, ý nghĩa,
khóa nối và logic nghiệp vụ chính rút từ `service.py`:

| Tệp | Cụm | Bảng tiêu biểu |
|---|---|---|
| [05a-du-lieu-thu-mua.md](05a-du-lieu-thu-mua.md) | Chứng từ Thu mua (14 bảng) | YCBG + phương án, khảo sát, YCMH, ĐMH + dòng, nhận hàng, lịch sử mua |
| [05b-du-lieu-tai-chinh-danh-muc-kho.md](05b-du-lieu-tai-chinh-danh-muc-kho.md) | Tài chính · Danh mục · Kho (14 bảng) | Công nợ, YCTT, NCC, hợp đồng, sản phẩm (SKU), ĐVT/phân loại, tồn kho, snapshot báo cáo |
| [05c-du-lieu-to-chuc-he-thong.md](05c-du-lieu-to-chuc-he-thong.md) | Tổ chức · Tài khoản · Hạ tầng (21 bảng) | User, vai trò + ma trận quyền, nhân sự, phòng ban, pháp nhân, file đính kèm, import/export, audit |
| [05d-du-lieu-van-thu-duyet.md](05d-du-lieu-van-thu-duyet.md) | Văn thư · Bộ máy duyệt · Duyệt dấu (30 bảng) | Văn bản + phiên bản + chữ ký + clone, sổ/loại/cấp mật, luồng duyệt + phiếu duyệt + ủy quyền |
| [05e-du-lieu-cong-tac-ho-tro.md](05e-du-lieu-cong-tac-ho-tro.md) | Cộng tác · Hỗ trợ · Thông báo (23 bảng) | Diễn đàn (kèm nhóm/box chuyên mục F13a), bình luận, phiếu hỗ trợ, HDSD, trợ lý AI, thông báo + hộp thư gửi, đặt xe |

Cộng đúng **14 + 14 + 21 + 30 + 23 = 102 bảng** — mỗi bảng đã tả có đúng một mục. Thêm bảng mới
thì thêm mục ở đúng tệp cụm và sửa con số ở đây.

## Cách đọc và cách giữ đúng

- **Nguồn sự thật là `model.py`** của từng module. Từ điển này chép Ý NGHĨA (thứ mã không nói) —
  khi lệch nhau về cột/kiểu thì mã đúng, từ điển sai, và phải sửa từ điển trong cùng đợt CR.
- Cột trạng thái có hai khuôn (QĐ-9/QĐ-11): chứng từ Thu mua cũ dùng **mã chuỗi tiếng Anh**
  (`draft | submitted | approved`...), bảng mới dùng **SMALLINT + IntEnum** — giá trị enum liệt kê
  ngay tại bảng đó. Bộ mã khai tập trung ở `backend/app/core/status_catalog.py`.
- Nhiều chỗ nối bằng **chuỗi mã** thay vì FK (nặng nhất là `product_code` — 7 bảng, luật D-025,
  xem [mo-hinh-du-lieu-san-pham.md](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md)); từng tệp
  có mục «Quan hệ trong cụm» chỉ rõ chỗ nào FK thật, chỗ nào nối chuỗi.
- Bản LLD v1 ([thiet-ke-ky-thuat-chi-tiet.md](../../tai-lieu-ky-thuat/thiet-ke-ky-thuat-chi-tiet.md),
  39 bảng thời điểm viết) vẫn giữ làm tài liệu tham chiếu lịch sử; bộ 05a–05e này là bản hiện trạng.
