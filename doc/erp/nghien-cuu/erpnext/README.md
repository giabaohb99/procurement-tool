# ERPNext học nghiệp vụ: tài liệu hướng dẫn

Trang học **https://erpnext.degoholding.vn** (ERPNext v16 + HRMS, dựng 30/10/2026 trên máy dev VPS 2) dùng để học nghiệp vụ thu mua, kho, kế toán chuẩn và so sánh với ERP DEGO. Dữ liệu là bản sao **dữ liệu thật** của ERP DEGO từ 01/08/2026 (7 công ty pháp nhân, danh mục, YCMH, ĐMH, nhận hàng, công nợ). Thao tác trên trang này **không ảnh hưởng ERP thật**.

| Tệp | Nội dung | Đọc khi |
|---|---|---|
| [01-huong-dan-mua-hang-den-thanh-toan-va-kho.md](01-huong-dan-mua-hang-den-thanh-toan-va-kho.md) | Một vòng mua đầy đủ từ Yêu cầu vật tư tới Thanh toán, nghiệp vụ kho (xuất, chuyển, kiểm kê, trả hàng, nhận thiếu, kiểm chất lượng), bút toán từng bước kèm số hiệu tài khoản VAS, bộ chứng từ mẫu đã làm sẵn | Muốn hiểu nghiệp vụ và tự làm lại một vòng |
| [02-bai-tap-vai-tro-luong-duyet-va-bat-tat.md](02-bai-tap-vai-tro-luong-duyet-va-bat-tat.md) | Tài khoản tập theo vai, luồng duyệt đơn mua hàng trên 50 triệu, mức tồn tối thiểu tự sinh yêu cầu vật tư, cách bật / tắt từng cấu hình | Muốn đổi cấu hình hoặc thử phân quyền |
| [03-chuc-nang-nhan-su-erpnext-va-doi-chieu.md](03-chuc-nang-nhan-su-erpnext-va-doi-chieu.md) | Phần nhân sự của ERPNext (lõi; app `hrms` không có trong repo), hồ sơ Employee, luật khi lưu, đối chiếu khối chức năng / từng trường / luật / bố cục với phân hệ Nhân sự DEGO, đề xuất nên học | Muốn biết ERPNext có gì về nhân sự và DEGO còn thiếu gì |
| [04-hrms-chuc-nang-va-lien-ket.md](04-hrms-chuc-nang-va-lien-ket.md) | App nhân sự `hrms` của nexterp: 9 workspace, tab Kết nối của hồ sơ nhân viên, vòng đời (tiếp nhận, điều chuyển, thăng chức, nghỉ việc), nghỉ phép, tuyển dụng, đánh giá, chi phí — cách các chứng từ liên kết, đề xuất nên học cho DEGO | Muốn biết chức năng nhân sự đầy đủ của nexterp và chọn cái để làm tiếp |
| [../11-do-phu-thu-mua-kho-so-voi-erpnext.md](../11-do-phu-thu-mua-kho-so-voi-erpnext.md) | Chấm điểm độ phủ thu mua - kho của ERP DEGO so với ERPNext (khoảng 59 %) và 10 chỗ hở | Muốn biết bên mình còn thiếu gì |

Ghi chú vận hành:
- Đăng nhập: tài khoản tập (mật khẩu ghi trong tệp 01 mục 0.1) hoặc nhân sự thật bằng **mã nhân viên**.
- Đồng bộ lại từ ERP: script `erp_doc_nghiep_vu.py` (đọc prod, chỉ đọc) + `erpnext_nap_nghiep_vu.py` (nạp, chạy lại không sinh trùng), xem bao-CR-700 / bao-CR-701 trong sổ task.
- Trang học là tạm thời; học xong sẽ gỡ cả trang và tên miền.
