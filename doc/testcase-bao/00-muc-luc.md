# Bộ kịch bản kiểm thử — dải `bao`

Kịch bản kiểm thử **thủ công** cho phần việc thuộc dải CR `bao`. Tách hẳn khỏi
`doc/testcase/` (bộ cũ, viết cho giao diện `frontend/` cổng 8080) vì ba lẽ:

 · bộ này nhắm **giao diện mới `frontend-v2`** (cổng 8083 dưới máy, `deverp` trên dev);
 · một thư mục riêng thì hai phiên làm việc song song không giẫm lên nhau;
 · mỗi ca kiểm gắn thẳng số CR, tra ngược `change-log-bao.md` ra ngay lý do.

## Mục lục

| Tệp | Phạm vi | CR |
|---|---|---|
| [01-chung-tu-lien-quan-ycmh.md](01-chung-tu-lien-quan-ycmh.md) | Thẻ *Chứng từ liên quan* trên phiếu yêu cầu mua hàng | bao-CR-422 |
| [02-nut-tao-don-va-in-phieu.md](02-nut-tao-don-va-in-phieu.md) | Một nút *Tạo đơn*, một nút *In phiếu*, hộp hỏi trước khi gom thêm | bao-CR-420 · bao-CR-421 |
| [03-phuong-an-va-chuong.md](03-phuong-an-va-chuong.md) | Chuông luồng phương án, mốc chốt xong lựa chọn | bao-CR-419 |
| [04-pham-vi-va-bang-rong.md](04-pham-vi-va-bang-rong.md) | Phạm vi dữ liệu và câu chữ khi bảng rỗng | bao-CR-414 · liên đới 422 |
| [05-vai-tro-va-pham-vi.md](05-vai-tro-va-pham-vi.md) | Màn Vai trò & quyền, hộp thoại Phạm vi dữ liệu, cảnh báo tự loại trừ phòng mình | bao-CR-427 · bao-CR-428 · bao-CR-430 |

## Môi trường

| Nơi | Giao diện mới | Giao diện cũ | Ghi chú |
|---|---|---|---|
| Máy dưới | http://localhost:8083 | http://localhost:8080 | dữ liệu demo đầy đủ |
| Dev | https://deverp.degoholding.vn | https://devthumua.degoholding.vn | cả 7 CR (tệp 01-05) đã lên, dev = `f7698f10` 19/09 |
| Prod | chưa có | https://thumua.degoholding.vn | **đang tạm dừng deploy** |

Chạy dưới máy thì stack phải lên đủ (`docker compose ps` thấy `erp`, `api`, `db`).

## Tài khoản

Quy ước dữ liệu demo: **tên đăng nhập = mật khẩu = mã nhân viên**.

| Tài khoản | Vai trò | Dùng để kiểm |
|---|---|---|
| `admin` | quản trị, thấy tất cả | mốc so sánh — cái gì admin cũng phải thấy |
| `DEMONV` | nhân viên, phạm vi hẹp | người yêu cầu: KHÔNG có `purchase_order:create`, không đọc được đơn mua hàng |
| `TESTREQ` | người yêu cầu (phòng Kế toán) | luồng lập phiếu |
| `DEMOTP` | trưởng phòng | duyệt phiếu |
| `DEMO_MANAGER_PURCHASE` | quản lý thu mua | tạo đơn, in bản tách theo nhà cung cấp |

Trên dev thì **chọn tài khoản theo VAI TRÒ chứ đừng chép thẳng tên ở bảng trên** —
dữ liệu dev khác dữ liệu demo dưới máy. Cột "dùng để kiểm" mới là thứ phải khớp.

## Cách ghi kết quả

Mỗi ca có một dòng `Kết quả:` — điền `Đạt` hoặc `Không đạt + mô tả thấy gì`.
Không đạt thì chụp màn hình kèm mã phiếu, vì phần lớn ca ở đây phụ thuộc **dữ liệu
của đúng phiếu đó** (phiếu gom từ mấy yêu cầu báo giá, đã có mấy đơn).

Ký hiệu trong bảng ma trận: `x` = thấy/bấm được · `-` = không thấy.

## Ca đã có máy chạy thay

Đừng kiểm tay những chỗ này, đã có bài kiểm tự động canh:

| Chỗ | Bài kiểm | Chạy bằng |
|---|---|---|
| Phiếu gom từ nhiều yêu cầu báo giá, khử trùng, bỏ phiếu nguồn đã xóa | `test_lien_ket_ycmh_cr317_318.py` | `docker compose exec -T api pytest test/backend/test_lien_ket_ycmh_cr317_318.py` |
| Chuông phương án hai chiều, mốc chốt lựa chọn | `test_chuong_phuong_an_cr419.py` | `docker compose exec -T api pytest test/backend/test_chuong_phuong_an_cr419.py` |
| Thẻ *Chứng từ liên quan* dựng đúng bốn trạng thái | `purchase-request-linked-documents-card.test.tsx` | `docker compose exec -T erp npx vitest run src/modules/procurement` |
| Đi một vòng bằng tài khoản hẹp | `test/e2e/test_v2_pham_vi_giao_dien.py` | `python -m pytest test/e2e/test_v2_pham_vi_giao_dien.py` |
| Màn Vai trò & quyền + hộp thoại Phạm vi: dịch bậc ra lời, chip phân hệ, nhóm gập, câu vàng tự loại trừ, sửa mô tả | `src/modules/system/**/*.test.ts(x)` (6 tệp, xem tệp 05) | `docker compose exec -T erp npx vitest run src/modules/system` |
| Kéo đổi thứ tự / đổi tên vai trò | `test_sap_xep_vai_tro.py` | `docker compose exec -T api pytest test/backend/test_sap_xep_vai_tro.py` |

Hai lần đo gần nhất (19/09/2026): pytest hai tệp trên **29 xanh**; vitest phân hệ
thu mua **418 xanh / 40 tệp**; E2E **6 xanh · 1 bỏ qua**.

**Nhưng bài kiểm tự động không thay được bộ này.** Bài Vitest dựng thẻ bằng dữ liệu
bịa — nó chứng minh "cho vào mảng rỗng thì hiện đúng câu rỗng", không chứng minh
được "máy chủ có trả đúng mảng đó cho người đang đăng nhập hay không". Đúng khe hở
ấy là chỗ ca `TC-422-09` và cả tệp 04 nhắm vào.
