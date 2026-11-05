# Báo cáo bảo mật tổng hợp — tháng 11/2026

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1.3 | 05/11/2026 | Agent 4 (soạn), A1 Điều phối (chuyển người chủ) | Hiệu lực | bao-CR-730 |

Tài liệu này viết cho người chủ đọc, không cần biết kỹ thuật. Nó tóm lại từ hai nơi: sổ chi tiết từng lỗ
[`so-ghi-nhan-loi-bao-mat.md`](so-ghi-nhan-loi-bao-mat.md) (BM-001 đến BM-036) và sổ thay đổi `change-log-bao.md`. Trạng thái
*đã lên prod* trong báo cáo này đối chiếu thẳng với lịch sử mã của nhánh `main` ngày 05/11/2026 (bản 2.14.0), không dựa vào chữ
*chờ deploy* cũ còn sót trong sổ. Muốn xem bằng chứng của một dòng thì tra mã BM tương ứng trong sổ chi tiết.

---

## 1. Tóm tắt một trang

**Hệ đang ở mức nào.** Sau bốn đợt rà (07/09 theo từng ticket, 14/09 theo mười một lớp phòng thủ, 14–15/09 khâu tải tệp lên,
04/11 toàn ứng dụng), hệ thống **không còn lỗ mức Cao nào đang mở**, và **mọi bản vá đã làm đều đã chạy trên prod**. Những gì còn
lại là lớp tăng cường (chặn tốc độ gọi, chính sách chặn script) và rủi ro vận hành về sau, không phải cửa đang mở cho người ngoài.

**Đếm theo mức** (36 dòng trong sổ, một dòng chỉ là ghi nhận kết quả rà sạch):

| Mức | Tổng | Đã vá trọn | Vá một phần | Chấp nhận rủi ro | Còn mở |
|---|---|---|---|---|---|
| Cao | 6 | 6 | 0 | 0 | 0 |
| Trung bình | 16 | 13 | 2 (BM-003, BM-034) | 0 | 1 (BM-020) |
| Thấp | 13 | 6 | 4 (BM-006, BM-007, BM-018, BM-030) | 2 (BM-013, BM-017) | 1 (BM-035) |
| Ghi nhận | 1 | — | — | — | — |

- **Sáu lỗ mức Cao đều đã vá và đã lên prod:** nhật ký toàn hệ đọc được bằng tài khoản thường (BM-001), không thu hồi được phiên
  đăng nhập (BM-002), người nghỉ việc vẫn đăng nhập được (BM-015), gắn được tệp của người khác để tải về (BM-025), ảnh đại diện
  nhận mọi loại tệp (BM-026), bot tự tính công thức Excel bằng thư viện có lỗ chạy mã (BM-032).
- **Hai dòng vá một phần mức Trung bình:** BM-003 thực chất đã đủ (phần còn thiếu là phiên phía máy chủ, đã đóng ở BM-002; sổ
  chưa đổi chữ); BM-034 còn vài thư viện đòi nâng bản lớn, chỉ dùng trên máy lập trình và lúc dựng, không chạy ở trình duyệt người
  dùng.
- **Ba việc đáng làm tiếp:** chặn tốc độ gọi cho các đường nghiệp vụ (BM-020, đang làm ở bao-CR-729), chính sách chặn script lạ
  trên trình duyệt (BM-035), và buộc đổi các mật khẩu yếu đặt từ trước khi có chính sách mật khẩu (bao-CR-405 chỉ gác lúc đặt mới).
- **Đính chính sổ chi tiết:** các dòng còn ghi *chờ deploy* hoặc *dev chưa deploy* (BM-005, BM-019, BM-021, BM-023, BM-032,
  BM-034) nay đều đã có trên `main`. Sổ chi tiết bản 2.8 ghi lại việc này.

**Rủi ro lớn nhất về sau không còn là lỗ trong mã** mà là vận hành: dữ liệu và nhật ký phình dần, một máy chủ prod duy nhất,
phụ thuộc dịch vụ bên ngoài, và tài khoản quyền rộng. Riêng nhật ký do máy tự ghi đã chiếm hơn nửa CSDL prod (khoảng 600 trên
1.020 MB, mục 4.1). Mục 4 đi từng rủi ro, mục 5 là lộ trình ba tháng.

---

## 2. Những gì đã làm

Gom theo nhóm dễ hiểu. Cột *Prod* là đã chạy trên hệ thật hay chưa, đối chiếu nhánh `main` ngày 05/11/2026.

### 2.1 Đăng nhập và phiên

| Việc | Vì sao quan trọng | Lỗ / CR | Prod |
|---|---|---|---|
| Mỗi lần đăng nhập là một phiên ghi ở máy chủ; đăng xuất, đá phiên, bắt đăng nhập lại có hiệu lực thật; có màn xem phiên | Trước đây vé đăng nhập lộ ra là không thu hồi được | BM-002 · bao-CR-358, 360, 395 | Có |
| Đổi hồ sơ nhân sự sang *Nghỉ việc* là khóa tài khoản và cắt phiên ngay | Trước đây người nghỉ vẫn dùng tiếp được | BM-015 · bao-CR-400 | Có |
| Giới hạn số lần thử đăng nhập theo từng địa chỉ máy, chỉ tin địa chỉ do Cloudflare báo | Chặn đoán mật khẩu, không cho kẻ gian tự khai địa chỉ giả | BM-004, BM-014 · bao-CR-313, 394 | Có |
| Chính sách mật khẩu chung cho cả năm cửa đặt mật khẩu; cấm đặt trùng mã nhân viên | Tên đăng nhập chính là mã nhân viên, mật khẩu trùng mã chỉ cần đoán một lần | BM-016 · bao-CR-405 | Có |
| Thư viện ký vé đăng nhập đổi sang PyJWT, chỉ nhận một thuật toán | Thư viện cũ có lỗ lẫn thuật toán | BM-034 · bao-CR-725 | Có (2.14.0) |
| Xác thực hai lớp | Lớp tăng cường, chưa làm | BM-017 · chấp nhận rủi ro 14/09 | — |

### 2.2 Phân quyền và phạm vi dữ liệu

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Nhật ký thao tác chỉ đọc được đúng phân hệ mình có quyền, đúng phạm vi bản ghi | BM-001 · bao-CR-313 | Có |
| Mọi nút xuất / nhập tệp đòi quyền *Xuất* / *Nhập* riêng, cùng phạm vi với màn danh sách | duoc-CR-660, 675 | Có |
| Màn Phân quyền khóa ô phạm vi của danh mục dùng chung (Nhà cung cấp, ...) để không ai tưởng đã thu hẹp được | bao-CR-716 | Có |
| Trợ lý AI lập bộ tài khoản đi qua đúng bộ chốt của màn Phân quyền, không tự nâng quyền | bao-CR-435 | Có |

### 2.3 Nhật ký và truy vết

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Ghi mọi lượt gọi kèm địa chỉ máy và mã lượt gọi, kể cả lượt đọc và lượt bị từ chối | BM-007, BM-009 · bao-CR-312, 346 | Có |
| Lưu giá trị trước / sau của từng cột khi sửa dữ liệu | BM-005 · bao-CR-402 | Có |
| Che dữ liệu thật trong chi tiết lỗi; ghi việc đổi phân quyền và tài khoản | BM-008, BM-010 · bao-CR-346 | Có |
| Đóng gói nhật ký ra kho R2 hằng tháng; dọn nhật ký quá 16 tháng sau khi đã có bản ngoài | BM-011 · bao-CR-346, 448 | Có |
| Quét bất thường mỗi 15 phút (địa chỉ lạ, đổi thiết bị giữa phiên, xóa hàng loạt, dồn dập bị từ chối), báo chuông quản trị | bao-CR-448 | Có |

### 2.4 Tệp tải lên và tải xuống

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Chỉ gắn được tệp do chính mình tải lên; trước đây một tài khoản thường đọc được mọi tệp trong hệ | BM-025 · bao-CR-408 | Có |
| Một chốt chung cho mọi cửa tải lên: kiểm đuôi, dung lượng, và đọc mấy byte đầu để biết tệp thật là gì; cấm SVG | BM-026, 027, 028 · bao-CR-408 | Có |
| Chống tên tệp phá thư mục khi giải nén, trần độ dài tên và số tệp mỗi lượt, dọn tệp bỏ dở sau 7 ngày | BM-029, 030, 031 · bao-CR-408 | Có |
| Gỡ thư mục tệp công khai không kiểm quyền | BM-021 · bao-CR-655 | Có |

### 2.5 Xuất Excel / CSV

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Ô chữ mở đầu bằng dấu bằng, cộng, trừ, a còng không thành công thức khi mở tệp — ở mọi tệp xuất (tra cứu thị trường, báo cáo mua hàng, sổ lao động, phúc lợi, tệp mẫu nhập, tệp Trợ lý dựng, CSV danh mục và CSV xuất tập trung); nạp lại CSV vẫn đúng dữ liệu | BM-033 · bao-CR-723, 726 | Có |

### 2.6 Bí mật và khóa

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Đo khóa ký vé của prod: không phải giá trị mặc định, đủ dài; CORS chỉ một tên miền thật | BM-018, BM-022 · đo 14/09 | Có |
| Dev có khóa riêng, không còn dùng chung với prod | BM-024 · 14/09 | Có |
| Giải mã bí mật hỏng thì báo lỗi thay vì im lặng (trước đây sao lưu R2 có thể chết mà không ai biết) | BM-023 · bao-CR-655 | Có |
| Quét lịch sử mã nguồn tìm khóa bị lộ: không có khóa thật | BM-036 · bao-CR-723 | — |

### 2.7 Bot, cổng MCP và AI

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Bot không tự tính công thức của tệp Excel lạ (thư viện pycel có lỗ chạy mã, chưa có bản vá) | BM-032 · bao-CR-723 | Có |
| Cổng dịch vụ AI và đồng bộ đặt xe ký từng lượt gọi; 66 đường không đòi đăng nhập đều có chủ đích | BM-036 | Có |
| Cổng MCP có khóa riêng từng người, OAuth, nhật ký từng lượt; công cụ sửa tệp văn phòng tắt mặc định | ai-CR-063, 218..225 | Có |
| Liên kết chat Telegram hết hạn thì không còn nhận bản tin hay việc | ai-CR-234 | Có (2.14.0) |

### 2.8 Thư điện tử

| Việc | Lỗ / CR | Prod |
|---|---|---|
| Thư đặt lại mật khẩu và thư cấp tài khoản không bao giờ được lưu thân thư; gửi lại thư cần quyền quản trị nhật ký và có trần | bao-CR-727 | Có (2.14.0) |
| Bài kiểm tự động không còn gửi được thư thật ra ngoài | bc9df758 · BM-036 | Có |

### 2.9 Hạ tầng

| Việc | CR / ngày | Prod |
|---|---|---|
| Prod và dev tách hai máy chủ riêng, mỗi bên một CSDL MySQL riêng (13/10) | Hạ tầng | Có |
| Máy chủ chỉ cho đăng nhập SSH bằng khóa, không bằng mật khẩu; đường vào đi qua Cloudflare | Hạ tầng | Có |
| Sao lưu CSDL ERP lên R2 hai lần mỗi ngày (01:00 và 13:00), giữ 30 bản gần nhất (khoảng 15 ngày) | Celery beat | Có |
| Header bảo mật cho trình duyệt: HSTS, chống đoán kiểu tệp, chống nhúng khung lạ, chính sách nguồn giới thiệu | BM-019 · bao-CR-655 | Có |
| Trang tài liệu API chỉ mở trên dev, prod trả 404 | bao-CR-713 | Có |
| Nâng thư viện có lỗ: backend từ 13 gói có lỗ còn 1 (pycel, đã tắt); giao diện mới từ 61 còn 17 | BM-034 · bao-CR-725 | Có (2.14.0) |

---

## 3. Còn mở và việc kế tiếp

| Việc | Mức | Vì sao còn | Việc kế | Ưu tiên |
|---|---|---|---|---|
| **BM-020** — chưa có trần tốc độ gọi cho đường nghiệp vụ. Một tài khoản hợp lệ (hoặc vé bị lộ) rút được toàn bộ dữ liệu trong phạm vi của mình ở tốc độ tối đa; chỉ 4 đường đăng nhập có trần | Trung bình | Đặt trần sai là tự chặn người dùng thật, phải đo nhịp thật trước | Đang làm ở **bao-CR-729**: lấy đỉnh thật trong nhật ký request rồi nhân hệ số | 1 |
| **Mật khẩu yếu đặt từ trước** — chính sách mật khẩu chỉ gác lúc đặt mới, mật khẩu cũ yếu (kể cả trùng mã nhân viên) vẫn còn | Trung bình | Không đọc được mật khẩu cũ để kiểm (chỉ lưu bản băm) | Kiểm lúc đăng nhập: mật khẩu vừa gõ không đạt chính sách thì bắt đổi ngay | 2 |
| **BM-035** — chưa có chính sách chặn script lạ trên trình duyệt. Phiên đăng nhập nằm ở bộ nhớ trình duyệt, nên nếu có một chỗ chèn script lọt thì lấy được phiên ngay | Thấp | Giao diện có trình soạn thảo, biểu đồ, PDF, đăng nhập Google — đặt chặt tay là hỏng màn | Thêm ở chế độ *chỉ báo* trên dev, đọc báo cáo vi phạm một tuần, rồi mới bật chặn | 3 |
| **BM-018** — khóa ký vé hiện an toàn, nhưng mã chưa có chốt *không cho chạy* khi khóa còn là mặc định | Thấp | Chỉ nguy khi dựng một môi trường mới mà quên đặt khóa | Vài dòng ở cấu hình; tuyệt đối không xoay khóa prod | 4 |
| **BM-030 phần ba** — giới hạn dung lượng tệp chỉ kiểm sau khi đã nhận hết, trần thật là 100 MB ở nginx | Thấp | Phải chặn ở tầng web server | Hạ trần nginx theo từng đường (đính kèm, ảnh) | 5 |
| **BM-034 đợt hai** — zod 4, vite 6, quill 2, minimatch 11; pycel chưa có bản vá | Thấp | Đổi bản lớn, đổi cách viết mã | Làm theo nhịp rà thư viện hằng tháng (mục 4.4) | 6 |
| **BM-023 phần màn hình** — lỗi giải mã bí mật mới ghi vào nhật ký, chưa có màn *sức khỏe hệ thống* cho quản trị thấy | Thấp | Việc giao diện | Gộp với chốt *lần sao lưu thành công gần nhất* (mục 4.3) | 4 |
| **BM-017** — xác thực hai lớp | Thấp | Chấp nhận rủi ro 14/09 | Nên xem lại riêng cho nhóm quản trị (mục 4.6) | 5 |
| **Vùng chưa rà** — tích hợp ngoài: Cloudflare tunnel, R2, Brevo, Lark SMTP, webhook | — | Sổ chi tiết §4 ghi chưa ai nhìn | Một đợt rà riêng trong tháng 12 | 4 |

---

## 4. Rủi ro tương lai

Mỗi rủi ro ghi: khả năng xảy ra, hậu quả, dấu hiệu sớm để nhận ra, việc nên làm, mức ưu tiên (1 là làm trước). Số đo lấy từ tài
liệu, mã nguồn và lượt đo 05/11/2026 của A1; không chạy truy vấn nặng trên prod.

### 4.1 Dữ liệu lớn dần

**Số đo 05/11/2026** (A1 đo; prod chỉ đọc số ước lượng của MySQL, không chạy truy vấn đếm nặng). CSDL prod khoảng **1.020 MB**;
đĩa máy chủ 56 GB, đã dùng 27 GB (**51%**); thư mục sao lưu trên máy 2,0 GB, mỗi bản sao lưu nén khoảng 90 MB. Dung lượng R2
chưa đo.

| Bảng (prod) | Dòng | Dung lượng | Đang dọn chưa |
|---|---|---|---|
| Dòng hàng tra cứu thị trường (`tab_customs_line`) | ~317 nghìn | 306 MB | Dữ liệu nghiệp vụ, không dọn; tăng theo mỗi lần nạp tờ khai (bao-CR-718 đã làm nhanh tìm kiếm và xuất) |
| Nhật ký request (`tab_request_log`) | ~333 nghìn (326 nghìn là lượt đọc, 150 nghìn đã quá 30 ngày) | 197 MB | Có: lượt đọc dọn sau **30 ngày** từ bao-CR-731 (trước 90), còn lại sau 16 tháng |
| Nhật ký nạp tệp (`tab_import_log`) | ~187 nghìn, gần hết ở mức INFO trong 30 ngày qua | 183 MB | Từ bao-CR-731: dòng Thông tin của mọi loại nạp dọn sau 30 ngày; cảnh báo / lỗi giữ; dòng kết cục lô hải quan theo luật riêng |
| Sổ đồng bộ đặt xe (`tab_sync_log`) | ~82–98 nghìn, trong đó 61 nghìn dòng *bỏ qua* (mỗi phút một dòng không có gì mới, từ 28/09) | 173 MB | Từ bao-CR-731: *Bỏ qua* 14 ngày, *Thành công* 90 ngày, giữ dòng mới nhất mỗi đối tượng, lỗi giữ mãi |
| Nhật ký thay đổi (`tab_change_log`) | ~71 nghìn | 54 MB | Có, sau 16 tháng. Từ bao-CR-731 thôi ghi (và xóa dòng cũ) cho bảng nhật ký máy — trước đó có 7.461 dòng của `tab_sync_log` và 4.677 dòng của `tab_email_log` |
| Nhật ký thao tác (`tab_audit_log`) | ~26 nghìn | 13 MB | Có: đóng gói R2 hằng tháng, xóa khỏi CSDL sau 16 tháng |
| Nhật ký thư (`tab_email_log`) | ~6.240 (từ 01/08/2026) | nhỏ | Từ bao-CR-731: nội dung thư dọn sau 90 ngày, dòng nhật ký giữ 16 tháng |

**Điểm chính:** bốn bảng nhật ký do máy tự ghi (request, nạp tệp, đồng bộ, thay đổi) đã chiếm khoảng **600 MB, hơn nửa CSDL
prod**, và tăng theo ngày chứ không theo việc kinh doanh. Riêng phần ghi thừa (dòng đồng bộ *bỏ qua*, dòng nạp tệp mức INFO,
thay đổi của bảng máy) dọn được khoảng **200 MB ngay** mà không mất thông tin có ích. Đã làm ở **bao-CR-731** (dev 05/11): lịch tự dọn 04:00 hằng đêm, kèm script đếm trước `backend/scripts/don_nhat_ky_may.py` để chạy lần đầu trên prod sau khi người chủ xem số.

- **Khả năng:** chắc chắn — dữ liệu chỉ tăng.
- **Hậu quả:** màn tìm kiếm và báo cáo chậm dần; bản sao lưu to lên nên mỗi lần sao lưu lâu hơn, tốn chỗ hơn, và khôi phục khi
  có sự cố cũng lâu hơn; ổ đĩa máy chủ đầy thì CSDL dừng ghi, cả hệ đứng.
- **Dấu hiệu sớm:** bản sao lưu nén vượt 150 MB; ổ đĩa máy chủ vượt 70%; màn tra cứu thị trường hay nhật ký chậm hơn 1 giây.
- **Việc nên làm:** đưa bao-CR-731 lên prod và chạy lần dọn đầu (đếm trước, gật rồi mới xóa, sau đó `OPTIMIZE TABLE`
  vào giờ vắng); tối ưu sao lưu (bao-CR-732); một tin vận hành hằng tuần báo dung lượng các bảng lớn nhất và ổ đĩa; khi tra cứu thị trường qua khoảng 1 triệu dòng thì xem lại chia bảng theo năm.
- **Ưu tiên:** 1.

### 4.2 Hiệu năng và quá tải do chính người dùng hợp lệ

- **Khả năng:** trung bình. Không cần kẻ xấu: một người bấm xuất toàn bộ nhiều lần, một bộ lọc tìm kiếm rộng, một tệp nạp rất
  lớn là đủ làm chậm mọi người khác.
- **Hậu quả:** cả công ty thấy hệ chậm hoặc treo trong lúc đó; việc nền (gửi thư, sao lưu) bị trễ.
- **Đã có:** xuất toàn bộ tra cứu thị trường chạy nền, mỗi người một lô, nghỉ giữa các khối; xuất danh sách thường có trần
  5.000 dòng; tệp tải lên có trần dung lượng và số tệp.
- **Dấu hiệu sớm:** nhật ký request có lượt gọi trên 5 giây; một tài khoản chiếm phần lớn lượt gọi trong một giờ.
- **Việc nên làm:** BM-020 (bao-CR-729) là việc chính; thêm trần thời gian cho truy vấn tìm kiếm nặng; hạ trần dung lượng tải
  lên theo từng đường.
- **Ưu tiên:** 1.

### 4.3 Một máy chủ prod duy nhất

- **Khả năng:** thấp mỗi tháng, nhưng một năm thì đáng kể (hỏng ổ, nhà cung cấp VPS sự cố, lỗi cập nhật).
- **Hậu quả:** cả hệ ngừng tới khi dựng lại máy mới và nạp bản sao lưu; mất tối đa dữ liệu khoảng 12 giờ (khoảng cách giữa hai
  lần sao lưu).
- **Đã có:** sao lưu hai lần mỗi ngày lên R2, nằm ngoài máy chủ; có công cụ khôi phục (`backend/scripts/restore_backup.py`). Từ bao-CR-732
  (dev 05/11): sao lưu ghi theo luồng (bộ nhớ không tăng theo cỡ CSDL), bảng nhật ký máy chỉ giữ cấu trúc, dữ liệu tra cứu thị
  trường tách bản riêng mỗi sáng; khôi phục = bản chính + bản tra cứu thị trường mới nhất.
  CSDL của dịch vụ AI có lượt **khôi phục thử tự động mỗi tuần**. CSDL ERP chính: **người chủ đã tự khôi phục thử ngày
  05/11/2026, đạt**; chưa có lịch lặp lại.
- **Dấu hiệu sớm:** sao lưu thất bại hoặc dung lượng bản sao lưu tụt bất thường; máy chủ báo lỗi ổ đĩa.
- **Việc nên làm:** lặp lại khôi phục thử CSDL ERP mỗi tháng (lên máy dev), ghi thời gian khôi phục; có chốt *quá 24 giờ chưa có bản
  sao lưu thành công thì báo*; viết một trang các bước dựng lại prod từ đầu và đo thử một lần.
- **Ưu tiên:** 1.

### 4.4 Thư viện cũ dần

- **Khả năng:** chắc chắn — mỗi tháng đều có lỗ mới được công bố ở các thư viện đang dùng.
- **Hậu quả:** lỗ đã công bố là lỗ có người biết cách khai thác. Đợt 04/11 gặp 13 gói backend có lỗ, trong đó có lỗ làm sập máy
  chủ khi phân tích form tải lên.
- **Dấu hiệu sớm:** chạy `pip-audit` và `npm audit` ra số tăng so với lần trước.
- **Việc nên làm:** đặt nhịp rà thư viện mỗi tháng một lần (đầu tháng), nâng bản vá nhỏ ngay, bản lớn gom một CR; ghi số
  trước / sau vào sổ.
- **Ưu tiên:** 2.

### 4.5 Khóa và bí mật dùng chung

- **Khả năng:** thấp đến trung bình.
- **Hậu quả:** khóa ký vé của prod đồng thời là khóa mã hóa mật khẩu SMTP và khóa R2 trong CSDL. Lộ một khóa này là lộ cùng lúc
  quyền ký vé và các bí mật kia. Đổi khóa thì phải mã hóa lại bí mật theo đúng thứ tự, làm sai là mất bí mật trong im lặng —
  vì thế sổ cấm xoay khóa prod khi chưa có kế hoạch.
- **Dấu hiệu sớm:** tệp `.env` bị chép ra ngoài máy chủ; có người rời nhóm từng giữ khóa.
- **Việc nên làm:** tách hai vai trò của khóa (một khóa ký vé, một khóa mã hóa bí mật) trong một CR riêng có kế hoạch mã hóa
  lại; ghi danh sách ai đang giữ khóa nào; đổi khóa của các dịch vụ ngoài (R2, SMTP, trạm model) khi có người rời nhóm.
- **Ưu tiên:** 3.

### 4.6 Con người và quyền rộng

- **Khả năng:** trung bình — phần lớn sự cố thực tế ở doanh nghiệp đến từ tài khoản quyền rộng bị lộ hoặc dùng nhầm, không phải
  từ lỗ trong mã.
- **Hậu quả:** tài khoản quản trị xem được nhật ký toàn hệ, sửa phân quyền, xóa dữ liệu. Không có xác thực hai lớp, nên chỉ cần
  lộ mật khẩu là đủ.
- **Đã có:** màn phiên đăng nhập (đá phiên lạ), quét bất thường 15 phút, chốt xóa hàng loạt cần gật đúng số, nhật ký trước /
  sau từng cột.
- **Dấu hiệu sớm:** chuông bất thường báo địa chỉ lạ hoặc xóa hàng loạt; số tài khoản có vai trò quản trị tăng.
- **Việc nên làm:** rà danh sách tài khoản quản trị mỗi quý, bỏ tài khoản dùng chung, mỗi người một tài khoản đứng tên; làm xác
  thực hai lớp cho riêng nhóm quản trị; mật khẩu yếu cũ buộc đổi (mục 3).
- **Ưu tiên:** 2.

### 4.7 Phụ thuộc dịch vụ bên ngoài

| Dịch vụ | Hỏng thì sao | Dấu hiệu sớm | Việc nên làm |
|---|---|---|---|
| Cloudflare (đường vào, tên miền) | Không ai vào được hệ dù máy chủ vẫn chạy | Trang báo lỗi của Cloudflare | Ghi sẵn cách vào thẳng máy chủ cho quản trị khi Cloudflare hỏng |
| R2 (tệp, sao lưu) | Không mở được đính kèm; sao lưu thất bại | Lỗi tải tệp; tin vận hành sao lưu hỏng | Chốt báo sao lưu quá hạn (mục 4.3); cân nhắc một bản sao lưu thứ hai ở nơi khác mỗi tuần |
| Brevo / Lark SMTP (thư) | Thư duyệt không tới, người duyệt không biết | Nhật ký thư có nhiều dòng lỗi | Màn nhật ký thư đã có (bao-CR-721); thêm cảnh báo khi tỷ lệ lỗi cao |
| Trạm model AI | Bot, Trợ lý, MCP trả lời chậm hoặc không trả lời; tốn tiền nếu bị lạm dụng | Chi phí trạm tăng bất thường | Theo dõi chi phí ngày; trần lượt gọi mỗi người |
| GitHub (kho mã) | Không đẩy được bản vá, chậm phát hành (đã chập chờn 04/11) | Lỗi đẩy mã | Giữ bản sao kho mã trên máy chủ dev |

- **Ưu tiên chung:** 3.

### 4.8 AI và bot đọc tệp lạ

- **Khả năng:** trung bình — ai gửi được tệp cho bot hoặc cổng MCP là đưa được nội dung lạ vào máy chủ.
- **Hậu quả:** lỗ trong thư viện đọc tệp (PDF, Excel, Word) có thể làm sập tiến trình hoặc tệ hơn là chạy mã (đúng loại BM-032);
  nội dung tệp có thể chứa câu lệnh dụ AI làm việc ngoài ý người dùng.
- **Đã có:** pycel tắt; thư viện đọc PDF đã nâng; dịch vụ AI tách khỏi ERP và chỉ đụng dữ liệu ERP qua một cổng có ký
  (ai-CR-119); thao tác ghi qua AI đều dựng bản nháp, người bấm xác nhận mới ghi.
- **Dấu hiệu sớm:** tiến trình dịch vụ AI khởi động lại nhiều lần; tệp gửi bot có dung lượng bất thường.
- **Việc nên làm:** giữ nguyên luật *AI đề xuất, người xác nhận* cho mọi thao tác ghi; đưa thư viện đọc tệp vào nhịp rà hằng
  tháng; trần dung lượng tệp gửi bot.
- **Ưu tiên:** 3.

---

## 5. Lộ trình đề xuất ba tháng

| Tháng | Việc | Liên quan |
|---|---|---|
| **11/2026** | Bật trần tốc độ gọi cho đường nghiệp vụ (bao-CR-729) | BM-020, mục 4.2 |
| | bao-CR-731 dọn nhật ký máy + lịch tự dọn (khoảng 200 MB ngay); bao-CR-732 tối ưu sao lưu | Mục 4.1 |
| | Khôi phục thử CSDL ERP: đã thử 05/11 (người chủ), lặp lại mỗi tháng; chốt báo sao lưu quá 24 giờ | Mục 4.3 |
| | Bắt đổi mật khẩu yếu cũ lúc đăng nhập | Mục 3 |
| **12/2026** | Chính sách chặn script ở chế độ chỉ báo trên dev, đọc báo cáo, rồi bật trên prod | BM-035 |
| | Chốt không cho chạy khi khóa ký vé là mặc định; màn sức khỏe hệ thống (giải mã bí mật, sao lưu, ổ đĩa, bảng lớn) | BM-018, BM-023, mục 4.1 |
| | Đợt rà vùng tích hợp ngoài (Cloudflare, R2, Brevo, Lark, webhook) | Mục 3 |
| | Rà thư viện tháng 12, đợt hai của BM-034 | Mục 4.4 |
| **01/2027** | Xác thực hai lớp cho nhóm quản trị; rà danh sách tài khoản quản trị | BM-017, mục 4.6 |
| | Kế hoạch tách khóa ký vé khỏi khóa mã hóa bí mật | Mục 4.5 |
| | Hạ trần dung lượng tải lên theo từng đường ở nginx | BM-030 |
| | Rà thư viện tháng 1; khôi phục thử CSDL tháng 1; trang dựng lại prod từ đầu | Mục 4.3, 4.4 |
