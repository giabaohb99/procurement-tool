# GÓI TRI THỨC HỢP NHẤT — MANG THEO CHO TRỢ LÝ AI

*Hợp nhất từ hai file được hai cửa sổ làm việc khác nhau tạo cùng ngày 24/08/2026: `20_GOI_TRI_THUC_MANG_THEO_CHO_TRO_LY_AI.md` (08:54) và `21_BO_SUNG_TRI_THUC_TU_LICH_SU_HOI_THOAI.md` (09:01). Hai file gốc giữ nguyên, không xóa, để giữ lịch sử — từ nay dùng file này làm bản chính, không đọc riêng lẻ hai file kia nữa.*

*Mục đích: bổ sung cho ba tài liệu gốc (`QĐ.HT.01`, `HD.HT.01`, `BM.01/QĐ.HT.01`) và ba file `_CHUAN/` (`NGU_CANH_DU_AN.md`, `BANG_KHOA_THUAT_NGU.md`, `BO_NHAN_DIEN_TRINH_BAY.md`) — không thay thế. File này chỉ chứa phần MỚI phát sinh trong các phiên làm việc 20–24/08/2026, chưa kịp gộp vào các file gốc.*

## Danh sách phải mang theo trọn bộ khi dựng lại trợ lý AI ở máy khác

1. Ba tài liệu gốc: `QĐ.HT.01`, `HD.HT.01`, `BM.01/QĐ.HT.01` (`_CHUAN/`).
2. Ba file `_CHUAN/`: `NGU_CANH_DU_AN.md`, `BANG_KHOA_THUAT_NGU.md`, `BO_NHAN_DIEN_TRINH_BAY.md`.
3. Hai Phụ lục mới tách ra trong phiên 22–24/08: `17_NGUYEN_LY_TONG_QUAT_HE_THONG_CONG_VIEC.md` (Phụ lục B) và `18_HE_THONG_VAN_BAN_VA_TO_CHUC_THUC_THI.md` (Phụ lục C) — xem hạng mục 4 dưới đây.
4. Hai file bộ nhớ dự án: `SO_DANG_KY_CONG_VIEC.md`, `DANH_MUC_TAI_LIEU.md`.
5. File này (`22_GOI_TRI_THUC_HOP_NHAT_CHO_TRO_LY_AI.md`).

## Phạm vi đã quét (gộp từ cả hai file gốc)

- Toàn bộ 1.557 tin nhắn dạng chữ của Giám đốc trong phiên chính (20–24/08/2026).
- Toàn bộ tin nhắn của các cửa sổ làm việc khác cùng dự án trong khoảng 20–24/08/2026 (nhiều cửa sổ Claude Code cùng mở song song trên thư mục này).
- `_KETQUA/00_RA_SOAT_DON_DEP.md` — đối chiếu file đã bị dọn bỏ lúc rà soát kho: toàn bộ là bản nháp trùng lặp/định dạng trung gian (PDF cũ bị thay, file HTML dựng tạm), không có nội dung quyết định nào bị mất.
- Toàn bộ file hiện có trên đĩa tại `_KETQUA/` và `_CHUAN/` tính đến 24/08/2026 09:10.

**Chưa quét được / không đưa vào**: hội thoại trên máy hoặc ứng dụng khác ngoài Claude Code, nếu có. Nếu có nội dung giá trị ở những nơi đó, cần Giám đốc cung cấp lại (xuất file, ảnh chụp, hoặc gõ lại) để bổ sung vào bản sau.

---

# PHẦN I — TRI THỨC LÂU DÀI, BỔ SUNG BA TÀI LIỆU GỐC

*Sắp theo đúng khung 12 hạng mục đã thống nhất trong phiên làm việc. Hạng mục nào không có phát sinh mới thì ghi rõ "không có bổ sung", tránh để trống gây hiểu nhầm là bỏ sót.*

## 1. Vai trò và giới hạn của AI

- Vai trò cuối cùng của trợ lý AI trong dự án: tự đặt câu hỏi khảo sát cho một công việc, tự soạn toàn bộ văn bản liên quan (thông báo, kế hoạch, quy trình, biểu mẫu, báo cáo); người chỉ còn "thống nhất thiết kế và nạp dữ liệu", duyệt cuối, và cử người kiểm soát đối chiếu thực tế. Nguyên văn Giám đốc: *"tao chỉ cần nạp cho nó 1 ít thông tin tự nó soạn được thông báo nó lập được kế hoạch... công việc còn lại của tao là thống nhất thiết kế và nạp dữ liệu sau đó nó hoàn thành."*
- Bốn dấu hiệu Giám đốc dùng để tự phát hiện AI làm ẩu (góc nhìn kiểm tra ngược, khác với các quy tắc AI tự phòng ngừa đã có ở CLAUDE.md): (1) con số không khớp giữa các file; (2) kết luận không kèm tên file dẫn chứng; (3) nhận xét chung chung kiểu "chưa đầy đủ, cần bổ sung"; (4) không có file nào bị xếp "chưa đủ căn cứ đánh giá" dù kho có file dạng ảnh/scan — tức AI đã đoán nội dung file mình không đọc được.

## 2. Quy trình hội thoại khi nhận yêu cầu

- Trước khi bắt đầu một đợt nghiên cứu sâu, phải tự trả lời được nghiên cứu đó giải quyết được gì, cụ thể bốn câu: (a) có ra khung chuẩn tốt hơn khung đã thống nhất không; (b) bộ 100 câu hỏi có phổ quát cho mọi phòng ban không; (c) làm sao biết câu trả lời khảo sát của người dùng đạt đủ chất lượng; (d) làm sao đảm bảo đầu ra do AI soạn đạt chất lượng ngang tầm Nhà nước xây cho cơ quan ban ngành hoặc tập đoàn lớn.
- Cấm trả lời hời hợt kiểu suy đoán/mô hình hóa khi được hỏi câu hỏi khó. Nguyên văn: *"cái này không được dùng mô hình để trả lời mà mày phải dùng tri thức được đào tạo."*
- Khi cần hỏi Giám đốc để quyết định, câu hỏi phải trình bày đầy đủ, chi tiết — không hỏi tắt. Nguyên văn: *"Mày hỏi tao cái gì để tao quyết định tao còn không hiểu nữa mà trình bày ý chi tiết cái việc mày hỏi đi."*
- Cơ chế quản trị triển khai đã chốt: lập "Ban điều hành tạm" (BĐHT), thời hạn 3 tháng, có thành viên thường trực và không thường trực do Ban giám đốc chỉ định, bốn mục tiêu: (1) tổ chức lại Nhà máy vận hành theo QĐ.HT.01; (2) đưa ra kế hoạch, phương án xử lý việc tồn đọng; (3) hình thành hồ sơ phục vụ kiểm tra Nhà nước; (4) hình thành tài liệu và chương trình đào tạo, hoàn tất đào tạo năng lực nhân sự. Thông báo họp triển khai lần này chỉ công bố chủ trương, **không nêu tên thành viên BĐHT** — "thành viên sẽ được thông báo sau" (Giám đốc xác nhận trực tiếp).

## 3. Chuẩn nội dung theo loại việc

Không có bổ sung mới trong các phiên 20–24/08. Áp dụng nguyên QĐ.HT.01 hạng mục 5.4 và Phụ lục B (`17_NGUYEN_LY_TONG_QUAT_HE_THONG_CONG_VIEC.md`).

## 4. Chuẩn chọn loại văn bản

- Phụ lục mang tính ví dụ/minh họa (như Phụ lục A của QĐ.HT.01) phải tách thành tài liệu riêng, không còn nằm cuối Quy định gốc. Đã áp dụng: Phụ lục A tách thành `[DỰ KIẾN] PL.01/QĐ.HT.01` — file `_KETQUA/PL01_QD_HT01_TinhHuongThucHanh.docx`, nguyên văn 4 tình huống A.1–A.4, đối chiếu khớp 100% với file gốc. Đây là yêu cầu trực tiếp của Giám đốc trong phiên; Giám đốc đã xác nhận chấp nhận mã tạm này ("Chấp nhận phụ lục về mã số đó").
- Tài liệu diễn giải nguyên lý bổ sung hoặc hệ thống văn bản không được viết thành văn bản độc lập nhiều lý do — phải xếp là PHỤ LỤC của quy định gốc. Đã áp dụng: `17_NGUYEN_LY_TONG_QUAT_HE_THONG_CONG_VIEC.md` viết lại thành Phụ lục B, `18_HE_THONG_VAN_BAN_VA_TO_CHUC_THUC_THI.md` thành Phụ lục C.
- Định nghĩa mỗi loại văn bản (Quy định, Quy trình, Hướng dẫn, Biểu mẫu...) phải có căn cứ theo chuẩn Nhà nước hoặc tổ chức quốc tế tương đương, không tự đặt. Đã áp dụng ở Phụ lục D (dẫn trong `18_...md`).

## 5. Chuẩn thể thức, số hiệu, phiên bản

- Số hiệu văn bản ưu tiên theo quy định Nhà nước hơn tiêu chuẩn ISO. Đã áp dụng ở Phụ lục C.6 — **hai hệ mã số hiệu song song đã chốt**: mã `[loại].[bộ phận].[số]` của HD.HT.01 mục 5.4.3 giữ nguyên cho tài liệu thiết kế một công việc cụ thể; số hiệu theo Nghị định 30/2020/NĐ-CP Điều 15 áp cho văn bản hành chính – quản trị – giao tiếp chưa có mã trong HD.HT.01. Không sửa HD.HT.01.
- Mã số cho phụ lục độc lập: **`PL.[số]/[mã tài liệu mẹ]`** — ví dụ `PL.01/QĐ.HT.01`. Giám đốc đã duyệt miệng. **Chưa có trong `NGU_CANH_DU_AN.md` mục 3.1** — cần bổ sung làm loại mã thứ tư, cùng nhóm với mã hệ thống/biểu mẫu/tài liệu công việc.
- Quy ước chỗ trống chờ điền: trong **bản chính thức** (thông báo, quyết định — dùng để gửi/in), chỗ thiếu thông tin viết dấu chấm lửng `"………………"` (giống kiểu "Họ tên: ………………" đã dùng ở bìa mọi tài liệu); nhãn `[Chưa rõ]` chỉ dùng trong **bản làm việc nội bộ** trao đổi với Giám đốc. Yêu cầu trực tiếp của Giám đốc ("chỗ nào thiếu bỏ dấu 3 chấm vào"). **Chưa có trong `BO_NHAN_DIEN_TRINH_BAY.md`** — cần bổ sung.
- Định dạng giao nộp bản cuối cùng cho Giám đốc phải là **PDF**, không phải `.md`. Nguyên văn: *"trình bày pdf cho tao chứ md sao đọc."* File `.md` chỉ dùng làm bản làm việc nội bộ.
- Với nội dung có độ tin cậy trung bình (Giám đốc không phản đối nhưng không xác nhận trực tiếp): dùng mục "Ghi chú nội bộ" riêng để giữ mã `[DỰ KIẾN]`, tách khỏi phần nội dung công khai của văn bản.

## 6. Văn phong, thuật ngữ

- **Tài liệu đầu ra không được giải thích quá trình hình thành, lý do, hay khái niệm nền — chỉ trình bày kết quả được tổ chức và thực thi ra sao.** Quy tắc này rộng hơn mục 3.6 hiện có của `NGU_CANH_DU_AN.md` (mục 3.6 chỉ giới hạn ở phần "Tài liệu viện dẫn"). Nguyên văn: *"tao không cần mày giải thích nó đã được hình thành như thế nào... đầu ra cái này nó được tổ chức và thực hiện như thế nào."*
- Tài liệu bổ sung phải viết đúng văn phong ngắn gọn như văn bản quy định gốc — không lặp lý do, không chồng chéo giữa các đề mục. Cần một bộ tiêu chí đánh giá văn phong cụ thể, không chỉ bảng từ cấm/dùng — tham khảo cách xây dựng tại phần B của `18_...md` (tiêu chí: cần thiết – đúng phạm vi – đúng thể thức trường – không chồng chéo – không câu dẫn nhập sáo rỗng).
- Sản phẩm giao nộp ưu tiên hợp nhất trong một file duy nhất, tránh phân mảnh nhiều file rời rạc dễ chồng chéo, nhầm lẫn. Nguyên văn: *"tao muốn trình bày là gì tất cả là chỉ nằm trong 1 file duy nhất thôi để tao dễ đọc để nhầm lẫn."* — chính là lý do file 20 và 21 được gộp thành file này.

## 7. Khuôn mẫu đầu ra sẵn có

Không có bổ sung mới. Áp dụng nguyên HD.HT.01 mục 5.5 (M1–M13).

## 8. Bộ câu hỏi khảo sát khi thiếu thông tin

Không có bổ sung mới. Áp dụng nguyên `BM.01/QĐ.HT.01` (100 câu).

## 9. Ví dụ thực hành đầy đủ

Không có bổ sung mới ngoài việc Phụ lục A (4 tình huống thực hành) đã tách thành tài liệu riêng — xem hạng mục 4.

## 10. Lỗi đã từng mắc — không lặp lại

- Dựng thử PDF để kiểm số trang mục lục trên máy thiếu font Liberation Sans/Arial → chữ bị dồn trang, số trang sai lệch so với khi mở bằng phần mềm có đúng font. **Cách đúng:** trước khi ban hành chính thức tài liệu nhiều trang có mục lục, phải mở lại bằng máy/phần mềm có đúng font để xác nhận số trang thật, không tin kết quả dựng thử trên máy thiếu font.
- Xuất PDF từ Pages.app bị treo do một tiến trình Pages cũ chưa đóng. **Cách đúng:** kiểm tra và buộc thoát tiến trình cũ trước khi xuất lại.
- Ba nguồn (bộ nhớ dự án, ảnh, tin nhắn) ghi tên Giám đốc/Phó Giám đốc khác nhau trong cùng một phiên (xem Phần II mục 2). **Cách đúng:** dữ liệu tổ chức (tên người giữ chức vụ) là loại thông tin dễ sai và hậu quả cao nếu đưa vào văn bản chính thức sai — luôn đối chiếu nhiều nguồn, nêu rõ mâu thuẫn, không tự chọn một nguồn để "cho xong".
- Nội quy/quy định cũ mâu thuẫn nhau trong kho hồ sơ không phải lỗi cố ý mà do "ngày xưa xây dựng ở trình độ thấp" — khi phát hiện mâu thuẫn phải đề nghị sửa đổi ngay, không chỉ ghi nhận rồi để đó.
- Bốn dấu hiệu AI làm ẩu Giám đốc tự dùng để kiểm tra — xem hạng mục 1, không lặp lại ở đây.

## 11. Quyết định đã chốt, không được làm khác

- **Kiến trúc hai tầng của toàn dự án**: Tầng 1 — tổng quát hóa QĐ.HT.01/HD.HT.01/BM.01 thành nguyên lý áp dụng được cho phòng ban hoặc công ty bất kỳ. Tầng 2 — đóng gói thành tri thức để copy thư mục sang một phiên AI khác, AI đó tự đặt câu hỏi khảo sát và tự soạn toàn bộ văn bản cho một công việc mới, người chỉ duyệt. Nguyên lý phải phổ quát ngay từ đầu, không chọn "phòng quen" để thử nghiệm trước. Nguyên văn: *"mọi công việc thực chất chỉ có 1 bộ nguyên lý do tính khoa học của nó."* File này chính là sản phẩm của Tầng 2.
- **Mô hình ba lớp khi dùng tài liệu**, quyết định layout của mọi sơ đồ/bản đồ tổng quan sau này: Giám đốc dùng sơ đồ/mindmap tổng quan trong cuộc họp → nhân viên hỏi sâu hơn thì tra lớp chi tiết trung gian → khi giao việc thực thi cho nhân viên thì dùng tài liệu chi tiết đầy đủ nhất. Ưu tiên mindmap nhiều nhánh chi tiết dù tài liệu lớn hơn, phức tạp hơn, miễn trong cuộc họp nhìn một lần là đủ.
- **Mục đích cốt lõi ràng buộc mọi tài liệu trong `_CHUAN/`**: phải tự đủ (portable), không phụ thuộc trí nhớ phiên chat, để bất kỳ AI nào — kể cả AI có năng lực hơn — đọc vào hiểu ngay, không cần giải thích lại. Nguyên văn: *"tao cần phải chép bao nhiêu file cũ nữa đi qua để đảm bảo rằng nó mới hiểu y chang như mày và nó có năng lực hơn mày đó."*
- Hai hệ mã số hiệu song song — xem chi tiết ở hạng mục 5, không lặp lại ở đây.
- Trên Giám đốc Nhà máy là Ban điều hành của Công ty TNHH DEGO Holding — Giám đốc xác nhận trực tiếp, dùng làm căn cứ bảng thẩm quyền ban hành (Phụ lục C.3).
- **Thẩm quyền ban hành trong giai đoạn hiện tại**: phòng, bộ phận không tự ban hành Quy định riêng. "Quy định của phòng" (Phụ lục C.2) nghĩa là Giám đốc Nhà máy ban hành một Quy định áp dụng riêng cho phạm vi phòng đó, không phải phòng tự soạn, tự ký — bảng thẩm quyền C.3 (chỉ Nhà máy có tầng Quy định) là đúng, không phải lỗi. Lý do: năng lực các phòng hiện còn yếu. Giám đốc ban hành hết trong giai đoạn này; có thể thành lập một Ban điều hành (tạm) để đảm nhận thay vì phân quyền xuống từng phòng. Giám đốc xác nhận trực tiếp: *"giám đốc ban hành hết, gd có thể thành lập ban điều hành giai đoạn này do năng lực các phòng yếu kém."* Đã cập nhật `NGU_CANH_DU_AN.md` mục 3.11 và ghi chú vào Phụ lục C.2 (`18_...md`).
- Tên loại tài liệu cho QĐ.HT.01 giữ nguyên là **"Quy định"**, không đổi thành "quy chuẩn" hay "tiêu chuẩn". Dẫn chứng: `NGU_CANH_DU_AN.md` mục 3.2 (danh sách tên loại hợp lệ không có "quy chuẩn"/"tiêu chuẩn"). *Suy luận bổ sung (không có trong file nguồn, thuộc hiểu biết hành chính chung, chưa được Giám đốc xác nhận trực tiếp — xem thêm Phần IV mục 1): "quy chuẩn" (QCVN) là văn bản kỹ thuật bắt buộc do Nhà nước ban hành; "tiêu chuẩn" đã có nghĩa riêng tại hạng mục 5.4.5 của QĐ.HT.01 (tiêu chí nghiệm thu) — dùng lại cho tên tài liệu sẽ trộn nghĩa.*

## 12. Tự kiểm trước khi giao tài liệu

Không có bổ sung mới. Áp dụng nguyên `BO_NHAN_DIEN_TRINH_BAY.md` mục 8 và HD.HT.01 mục 5.6.

---

# PHẦN II — TÌNH TRẠNG DỰ ÁN TẠI THỜI ĐIỂM ĐÓNG GÓI (22–24/08/2026)

*Phần này là ảnh chụp tình trạng tại một thời điểm, sẽ lỗi thời nhanh — khi dùng phải đối chiếu lại với `SO_DANG_KY_CONG_VIEC.md` và `DANH_MUC_TAI_LIEU.md` bản mới nhất trước khi tin theo.*

## 1. Chủ trương cuộc họp 16:45 ngày 22/8/2026

Nội dung đầy đủ và chương trình chi tiết đã soạn thành văn bản riêng: `_KETQUA/19_THONG_BAO_HOP_TRIEN_KHAI_QDHT01.md` (bản nội bộ, còn nhãn `[Chưa rõ]`) và `.docx`/`.pdf` (bản trình bày, chỗ thiếu đã thay dấu chấm lửng). Bốn nội dung chính của cuộc họp:
1. Ban hành Quy định QĐ.HT.01.
2. Phổ biến hai tài liệu hỗ trợ đã hoàn thành: Phụ lục B (`17_...md`) và Phụ lục C (`18_...md`), cùng nền tảng trợ lý AI hỗ trợ triển khai.
3. Thông tin tài liệu khảo sát hiện trạng tổ chức công việc của Nhà máy đã hoàn thành, hơn 300 trang — **[Chưa rõ]** tên file cụ thể trong `_KETQUA/`, Giám đốc nói miệng trong phiên, chưa đối chiếu được với file nào (có thể là `BUC_TRANH_TOAN_CANH_HE_THONG_TAI_LIEU.pdf` hoặc bộ `14_CHUONG/`, cần Giám đốc xác nhận).
4. Công bố chủ trương thành lập Ban điều hành tạm, thời hạn 3 tháng, bốn mục tiêu — xem Phần I hạng mục 2.

## 2. Dữ liệu tổ chức — ĐÃ GIẢI QUYẾT, Giám đốc xác nhận trực tiếp

**Mâu thuẫn về Giám đốc/Phó Giám đốc Nhà máy — ba nguồn từng ghi khác nhau, nay đã chốt:**

| Nguồn | Ghi nhận |
|---|---|
| `_KETQUA/SO_DANG_KY_CONG_VIEC.md` (cập nhật 21/08/2026, trước phiên này) | "Giám đốc Nhà máy (Đoàn Minh Khôi)" — **sai, đã sửa** |
| Ảnh danh sách nhân sự Giám đốc gửi trong phiên (22/08/2026) | Dòng đầu ghi "PGĐ — Đoàn Minh Khôi" — đúng |
| Tin nhắn trực tiếp của Giám đốc trong phiên (22/08/2026) | "Giám đốc nhà máy Trần Chí Dững, phó giám đốc Nguyễn Minh Khôi" — đúng tên Giám đốc, tên đệm Phó Giám đốc gõ nhầm |
| **Giám đốc xác nhận trực tiếp, chốt cuối cùng** | **Giám đốc Nhà máy: TRẦN CHÍ DỮNG. Phó Giám đốc Nhà máy: ĐOÀN MINH KHÔI.** |

Đã sửa dòng mã việc [DỰ KIẾN]-01 trong `SO_DANG_KY_CONG_VIEC.md` theo tên đã chốt. **Đã quét toàn kho `_KETQUA/` (21 file có nhắc "Đoàn Minh Khôi")** để tìm chỗ ghi sai tương tự — kết quả: chỉ có `SO_DANG_KY_CONG_VIEC.md` là bị sai thật (bảng bộ nhớ dự án, khẳng định trực tiếp không kèm nguồn, đã sửa). Toàn bộ 20 chỗ còn lại (`02_PHAN_LOAI.md`, `03_DANH_GIA_TAI_LIEU.md`, `04_BUC_TRANH_NHA_MAY.md`, `06_CHAM_SAU/`, `14_CHUONG/A1_DIEU_HANH.md`, `14_CHUONG/MASTER_HOP_NHAT.md`, `14_CHUONG/C05...`, `C06...`, `08_PHIEU_HOAN_THIEN/`, `09_PHAN_BIEN/`) đều là **trích dẫn có nguồn** — ghi lại đúng những gì các văn bản cũ thật sự có: JD-BDH-01 (Bản mô tả công việc — Giám đốc Nhà máy, STT79) nêu tên Đoàn Minh Khôi; các Thông báo và Nội quy Lao động ký thật ngoài đời ghi "GIÁM ĐỐC Đoàn Minh Khôi" với ngày hiệu lực thật (23/03/2026, 09/04/2026). Đây KHÔNG phải lỗi cần sửa — sửa những chỗ này là bóp méo nội dung hồ sơ gốc.

**Đã hỏi Giám đốc — chốt cuối cùng**: JD-BDH-01 và các văn bản ký thật ghi "Giám đốc Đoàn Minh Khôi" là **hồ sơ cũ ghi nhầm chức danh**, không có việc chuyển giao chức danh nào xảy ra. Đoàn Minh Khôi là Phó Giám đốc Nhà máy xuyên suốt, không phải từng là Giám đốc. Các văn bản cũ ghi "GIÁM ĐỐC Đoàn Minh Khôi" (Thông báo 23/03/2026, Nội quy Lao động 09/04/2026, JD-BDH-01) là sai chức danh ngay từ đầu — cần sửa khi rà soát, ban hành lại các văn bản đó, không phải vấn đề mốc thời gian.

**Danh sách nhân sự dự họp 22/8/2026 (nguồn: ảnh Giám đốc gửi trong phiên + tin nhắn gốc):**

| Chức danh | Họ tên | Ghi chú |
|---|---|---|
| PGĐ | Đoàn Minh Khôi | Xem mâu thuẫn trên |
| Trợ lý (điều hành) | Nguyễn Thị Kiều Trang | |
| Hành chính – Nhân sự | Trần Diễm Phương | |
| Quản lý sản xuất | Võ Thanh Huyền | |
| Giám sát sản xuất | Nguyễn Trung Lượng | |
| QC | Lê Hồng Sơn | Họp thay do Mr Nghĩa nghỉ — chưa rõ họ tên đầy đủ của Mr Nghĩa |
| Điều phối sản xuất | Lê Phú Ngoan | |
| Điều phối đơn hàng | Nguyễn Thanh Phương | |
| Kế toán | Nguyễn Đình Chương | Họp thay do Ms Chúc Ly nghỉ — chưa rõ họ tên đầy đủ của Ms Chúc Ly |
| Kho | Nguyễn Quốc Phòng | |
| Trưởng bộ phận R&D | Lê Hữu Hải | Nêu riêng trong tin nhắn gốc, không có trong ảnh |

Ghi chú đối chiếu: bảng này là dữ liệu **mới nhất, trực tiếp từ Giám đốc trong phiên** — nếu khác với tên/chức danh đã ghi trong `SO_DANG_KY_CONG_VIEC.md` hoặc các JD cũ trong kho (ví dụ JD-BDH-02, JD-HCNS-01…), lấy bảng này làm ưu tiên khi có xung đột, nhưng vẫn nên đối chiếu lại một lần với Giám đốc trước khi cập nhật `SO_DANG_KY_CONG_VIEC.md` chính thức.

## 3. Tài liệu mới tạo trong các phiên 22–24/08 (chưa có trong `DANH_MUC_TAI_LIEU.md`)

| Mã / tên file | Loại | Trạng thái | Ghi chú |
|---|---|---|---|
| `[DỰ KIẾN] QĐ.HT.01` — `_KETQUA/QD_HT01_QuyDinh_HeThongCongViec_TachPhuLuc.docx` | Quy định (bản đã tách phụ lục) | Dự thảo | Nội dung mục 1–6 giữ nguyên bản gốc trong `_CHUAN/`; file gốc không bị sửa. Mục lục cần kiểm lại số trang trên máy có đúng font trước khi dùng chính thức |
| `[DỰ KIẾN] PL.01/QĐ.HT.01` — `_KETQUA/PL01_QD_HT01_TinhHuongThucHanh.docx` | Phụ lục (tài liệu độc lập) | Dự thảo | Nguyên văn 4 tình huống A.1–A.4, đối chiếu khớp 100% với PDF gốc |
| `[DỰ KIẾN] TB.HT.01/TB-NM` — `_KETQUA/19_THONG_BAO_HOP_TRIEN_KHAI_QDHT01.md` / `.docx` / `.pdf` | Thông báo | Dự thảo | Bản `.md` giữ nhãn `[Chưa rõ]` để làm việc nội bộ; bản `.docx`/`.pdf` đã thay bằng "………………" để trình bày. Mã số thông báo chờ Phòng Hành chính – Nhân sự cấp số thật |
| `_KETQUA/20_...md`, `21_...md/.pdf` | Tài liệu tổng hợp (đã gộp) | Đã gộp vào file này | Xem đầu file |

---

# PHẦN III — DANH SÁCH CHỜ GIÁM ĐỐC QUYẾT (gộp từ cả hai file nguồn)

1. ~~Tên chính xác của Giám đốc Nhà máy và Phó Giám đốc Nhà máy~~ — **đã trả lời**: Giám đốc Trần Chí Dững, Phó Giám đốc Đoàn Minh Khôi (Phần II mục 2). Còn việc phát sinh từ đây: rà quét toàn kho tìm chỗ còn ghi sai tên cũ.
2. Ai dẫn chương trình và trình bày mục 3, mục 4 trong chương trình họp 22/8 (Trợ lý điều hành Nguyễn Thị Kiều Trang, hay Giám đốc trực tiếp).
3. Mã số chính thức cho tài liệu Phụ lục tách riêng (tạm `PL.01/QĐ.HT.01`).
4. Mã số chính thức cho Thông báo họp (tạm `TB.HT.01/TB-NM`), do Phòng Hành chính – Nhân sự cấp.
5. Xác nhận số trang Mục lục trong bản `QD_HT01_QuyDinh_HeThongCongViec_TachPhuLuc.docx` sau khi mở bằng máy có đúng font.
6. Cách ngắt dòng banner tiêu đề của tài liệu Phụ lục `PL.01` (do một phiên trước tự chọn cách trình bày, chưa phải văn bản gốc có sẵn) — xem lại có ổn không.
7. Họ tên đầy đủ của "Mr Nghĩa" (QC) và "Ms Chúc Ly" (Kế toán) — hiện chỉ biết họ đang nghỉ và có người họp thay.
8. Tên file cụ thể của "tài liệu khảo sát hiện trạng hơn 300 trang" nhắc tới trong nội dung họp, để dẫn nguồn chính xác vào thông báo.
9. Xác nhận có phải "Quy định" là tên loại tài liệu đã chốt cho QĐ.HT.01 hay chưa — xem Phần IV mục 1, hiện chỉ là suy luận gián tiếp.

*Khi các mục trên được trả lời, cập nhật trực tiếp vào `NGU_CANH_DU_AN.md`, `SO_DANG_KY_CONG_VIEC.md`, `DANH_MUC_TAI_LIEU.md` — khi đó nội dung tương ứng trong file này coi như đã gộp xong, có thể đánh dấu "đã gộp" thay vì xóa, để giữ lịch sử.*

---

# PHẦN IV — PHẦN MƠ HỒ, CHƯA CHẮC LÀ QUYẾT ĐỊNH LÂU DÀI

*Người biên soạn tự cân nhắc khi dùng — không đưa thẳng vào tài liệu chuẩn nếu chưa xác nhận lại.*

1. Câu hỏi thuật ngữ "quy định / quy chuẩn / tiêu chuẩn" — Giám đốc hỏi nhưng không có câu trả lời/chốt trực tiếp trong lịch sử hội thoại; suy luận gián tiếp là đã chọn "Quy định" vì tên tài liệu không đổi, nhưng không có xác nhận rõ.
2. Bộ "LỆNH" mẫu (LỆNH KIỂM CHỨNG, LỆNH CHẤM NGẪU NHIÊN, LỆNH TỰ PHẢN BIỆN, LỆNH QUÉT LẠI MỘT NHÁNH, LỆNH THIẾT KẾ MỘT CÔNG VIỆC) — không rõ là quy tắc muốn đưa vào tài liệu chuẩn hay chỉ là công cụ thao tác tham khảo.
3. "Cấp mọi quyền rồi", "mày tự làm thay tao đi" — không rõ chỉ là nhắc lại phong cách "làm thẳng không hỏi" đã có, hay là một cấp ủy quyền mới (toàn quyền chạy nền không cần xác nhận từng bước).
4. Dữ liệu thực tế nhà máy (nhân sự 29, công suất 120–200 thùng/ca...) — có tính lâu dài về mặt dữ liệu tham chiếu nhưng không phải "quyết định về cách làm việc", cân nhắc đưa vào bộ nhớ dự án (`SO_DANG_KY_CONG_VIEC.md`) thay vì file quy tắc.
5. "Quét lại phụ lục A/B/C/D xem chồng chéo trước khi ban hành" — có thể là chỉ đạo một lần cho đợt hợp nhất cụ thể, hoặc quy tắc lâu dài "trước khi ban hành luôn phải rà chồng chéo giữa các phụ lục" — chưa đủ rõ.

---

# PHẦN V — CẢNH GIÁC PHÁT HIỆN KHI ĐỐI CHIẾU TRỰC TIẾP VỚI BA TÀI LIỆU GỐC

*Phần này khác Phần IV: đây không phải nội dung lấy từ lịch sử hội thoại, mà là phát hiện của chính phiên gộp file này khi đọc trực tiếp nguyên văn `QĐ.HT.01`, `HD.HT.01`, `BM.01/QĐ.HT.01`, `17_...md`, `18_...md` — không qua tóm tắt trung gian. Cần Giám đốc biết trước khi đóng gói mang sang máy khác.*

*Xếp theo mức nghiêm trọng đã kiểm chứng lại bằng giả định tình huống thực thi (xem Phần VI) — không theo thứ tự phát hiện.*

1. **[ĐÃ GIẢI QUYẾT — Giám đốc xác nhận trực tiếp] "Quy định của phòng" — C.2 và C.3 từng tự mâu thuẫn nhau, nay đã chốt.** Mục C.2 nói mỗi phòng/bộ phận "có đủ bốn cấp văn bản theo đúng thứ bậc: **Quy chế hoặc Quy định của phòng** (nếu có) → Quy trình → Hướng dẫn thao tác → Biểu mẫu" — đọc thoáng qua ngụ ý phòng có một tầng "Quy định của phòng". Bảng thẩm quyền C.3 lại xếp "Quy định" CHỈ thuộc tầng Nhà máy (Giám đốc Nhà máy ban hành); tầng "Phòng, bộ phận" trong C.3 chỉ có Quy trình, Hướng dẫn thao tác, Biểu mẫu — không có Quy định. **Giám đốc đã xác nhận trực tiếp cách đọc đúng**: "Quy định của phòng" nghĩa là Giám đốc Nhà máy ban hành một Quy định áp dụng riêng cho phạm vi phòng đó, phòng không tự soạn, tự ký; bảng C.3 là đúng, không phải lỗi. Lý do: năng lực các phòng hiện còn yếu, chưa đủ điều kiện tự chủ ban hành văn bản quản trị — Giám đốc ban hành hết trong giai đoạn này, có thể thành lập một Ban điều hành tạm để đảm nhận thay vì phân quyền xuống từng phòng. Đã ghi câu làm rõ vào Phụ lục C.2 (`18_...md`) và vào `NGU_CANH_DU_AN.md` mục 3.11.
2. **[Mới — ranh giới chưa rõ, dễ chọn sai mã] "Kế hoạch" là loại văn bản DUY NHẤT rơi vào cả hai hệ mã của Mục C.6 cùng lúc.** Bullet thứ nhất xếp "Kế hoạch triển khai công việc đó" (một công việc cụ thể) vào hệ mã HD.HT.01; bullet thứ hai xếp "Kế hoạch cấp nhà máy hoặc cấp công ty" vào hệ mã theo Nghị định 30/2020. Không có ví dụ nào phân biệt ranh giới hai trường hợp. Giả định tình huống: Giám đốc yêu cầu "lập kế hoạch đào tạo an toàn hóa chất quý 4" — đây là kế hoạch của một công việc cụ thể (đào tạo) nhưng ảnh hưởng nhiều phòng, nằm đúng vào vùng xám giữa hai bullet — trợ lý AI có thể chọn nhầm hệ mã nếu không được nhắc dừng lại hỏi. Mọi loại văn bản khác trong C.6 (Quy trình, Hướng dẫn, Chương trình...) chỉ rơi vào đúng một hệ mã, không có tình trạng này — chỉ riêng "Kế hoạch" cần một quy tắc phân biệt rõ hoặc ví dụ minh họa.
3. **Hai hệ mã song song (Phụ lục C.6) chỉ tồn tại trong file dự thảo `18_...md`, chưa có trong `HD.HT.01` gốc.** Bản `HD.HT.01` gốc tại Mục 5.4.3 chỉ mô tả MỘT hệ mã (`[loại].[bộ phận].[số]` và `BM.[số]/[mã mẹ]`). Nếu khi đóng gói sang máy khác chỉ mang theo `HD.HT.01` mà quên Phụ lục C (`18_...md`), trợ lý AI mới sẽ không biết văn bản hành chính (Quyết định, Thông báo...) có hệ mã riêng theo Nghị định 30/2020/NĐ-CP, dễ áp mã sai ngay từ văn bản đầu tiên. **Bắt buộc mang cả hai phụ lục B, C — không được coi là tùy chọn.**
4. **Khoảng trống cấu trúc thẩm quyền.** Phụ lục D (`18_...md`) định nghĩa loại văn bản "Quy định" là văn bản **"cụ thể hóa một Quy chế, điều lệ cấp trên"**; Phụ lục C.3 xếp "Quy chế" thuộc tầng Công ty (Ban điều hành DEGO Holding ban hành), còn "Quy định" thuộc tầng Nhà máy. Theo đúng logic này, `QĐ.HT.01` — bản thân là một "Quy định" — lẽ ra cần một "Quy chế" cấp Công ty làm căn cứ cấp trên. Không tìm thấy văn bản "Quy chế" nào như vậy trong kho. *Suy luận, chưa xác nhận với Giám đốc:* có thể `QĐ.HT.01` được chủ ý làm văn bản nền tảng đầu tiên, không cần chờ Quy chế cấp trên — nhưng nếu đúng vậy thì nên ghi rõ ngoại lệ này, tránh một AI khác đọc Phụ lục D rồi tự ý yêu cầu phải có Quy chế trước.
5. **[Hạ mức sau kiểm chứng — không gây thực thi sai] Thứ tự M12/M13 bị đảo trong bản gốc `HD.HT.01`.** Mục 5.5 liệt kê khuôn mẫu theo thứ tự M1 → M11, nhưng ngay sau đó văn bản trình bày "M13. Biên bản rà soát tài liệu đã có" trước, rồi mới đến "M12. Dự thảo quyết định ban hành và biên bản họp" — ngược thứ tự số. Đã kiểm chứng lại ở Phần VI: nội dung từng khuôn tự đủ, không phụ thuộc thứ tự đọc, nên không gây thực thi sai — chỉ là lỗi trình bày, nên sửa khi rà soát chính thức `HD.HT.01`, không cần xử lý gấp.
6. **Ma trận A/B/C thống nhất giữa ba tài liệu gốc** — đã đối chiếu trực tiếp `QĐ.HT.01` Mục 5.2, `HD.HT.01` Phụ lục B.1, `BM.01` mục "Chốt lại sau thảo luận": cùng công thức, cùng ngưỡng (6-9 loại A, 3-4 loại B, 1-2 loại C, chạm an toàn/nghĩa vụ Nhà nước luôn xếp A). Không có mâu thuẫn — ghi lại để xác nhận, không phải để cảnh báo.
7. **[Hạ mức sau kiểm chứng — việc còn treo, không phải nguy cơ thực thi sai] Mâu thuẫn tên Giám đốc/Phó Giám đốc (Phần II mục 2).** Đã kiểm chứng lại ở Phần VI: quy tắc "không suy đoán thay dữ liệu" (`HD.HT.01` §5.1.2) và nhãn `[Giả định / chưa rõ]` đủ mạnh để chặn một trợ lý AI hành xử đúng giao thức tự đoán bừa tên — AI sẽ hỏi lại đúng như thiết kế. Đây vẫn là việc bắt buộc phải giải quyết trước khi ban hành bất kỳ văn bản chính thức nào nhắc tới hai chức danh này, nhưng không phải một lỗ hổng khiến trợ lý AI âm thầm làm sai.

---

# PHẦN VI — KIỂM CHỨNG BẰNG GIẢ ĐỊNH TÌNH HUỐNG THỰC THI

*Trước khi kết luận gói tri thức đã dùng được, phiên gộp file này tự đặt ra các tình huống cụ thể và lần theo từng bước xem một trợ lý AI — nếu chỉ có đúng bộ tài liệu tại mục "Danh sách phải mang theo" đầu file — sẽ phản ứng đúng hay sai, thay vì chỉ đọc lại nội dung đã có.*

**Các tình huống đã thử:** phòng ban muốn tự ban hành Quy định riêng; chọn hệ mã cho một "Kế hoạch" nằm giữa ranh giới công việc cụ thể và cấp nhà máy; soạn Biên bản, Chương trình, Hướng dẫn, Quy trình (kiểm tra từng loại chỉ rơi vào đúng một hệ mã, không lẫn lộn — riêng "Kế hoạch" là ngoại lệ, xem mục 2 ở trên); yêu cầu vượt thẩm quyền Giám đốc Nhà máy (ban hành Quy chế cấp Công ty); soạn văn bản nhắc tên Giám đốc/Phó Giám đốc đang mâu thuẫn; rà soát một tài liệu cũ theo khuôn M13; thiết kế một công việc loại C đơn giản.

**Kết quả:** hai tình huống đầu (Quy định của phòng, ranh giới Kế hoạch) lộ ra lỗi thật trong Phụ lục C — đã ghi ở mục 1, 2 phía trên. Các tình huống còn lại đều được các quy tắc đã có (không suy đoán, gắn nhãn `[Giả định/chưa rõ]`, bảng thẩm quyền C.3, quy tắc mã C.6 cho từng loại văn bản) xử lý đúng, không phát hiện thêm nguy cơ thực thi sai.

**Trạng thái hai cửa sổ Claude Code khác được hỏi:** `ho-so-dego-organic-7e` đã biến mất khỏi danh sách phiên đang chạy sau khi được hỏi, không để lại file mới nào trong `_KETQUA/` — coi như đã đóng, không có gì để gộp thêm. `ho-so-dego-organic-d9` đã được nhắn hai lần, đến thời điểm chốt file này vẫn chưa phản hồi — có thể không còn người theo dõi cửa sổ đó.

**Kết luận cuối cùng (cập nhật sau khi Giám đốc trả lời cả hai việc bắt buộc):** cả hai việc chặn đóng gói đã được giải quyết — (1) Giám đốc đã xác nhận trực tiếp cách đọc đúng của "Quy định của phòng" (mục 1 ở trên); (2) Giám đốc đã xác nhận trực tiếp tên hai chức danh: Giám đốc Nhà máy Trần Chí Dững, Phó Giám đốc Nhà máy Đoàn Minh Khôi (Phần II mục 2). **Gói tri thức nay đủ điều kiện đóng gói mang đi.**

Đã quét toàn kho (21 file) tìm chỗ ghi sai tên tương tự — chỉ có `SO_DANG_KY_CONG_VIEC.md` là sai thật, đã sửa; 20 chỗ còn lại là trích dẫn đúng nội dung hồ sơ cũ (JD-BDH-01, các văn bản ký thật), giữ nguyên. Việc còn mở, không chặn đóng gói: khả năng có một lần thay đổi nhân sự thật giữa hai chức danh Giám đốc/Phó Giám đốc — xem chi tiết Phần II mục 2.

---

---

# PHẦN VII — ĐÃ KIỂM THỬ BẰNG MỘT AI ĐỘC LẬP, KHÔNG CHUNG KÝ ỨC

*Khác mọi phần trước — đây không phải suy luận hay đối chiếu tài liệu, mà là kết quả chạy thật. Một agent AI hoàn toàn mới, không có bất kỳ ký ức nào từ phiên làm việc đã dựng gói này, chỉ được trỏ vào đúng thư mục `_KETQUA/23_GOI_DONG_GOI_TRO_LY_AI_MOI/` (bản sao 12 file bắt buộc mang theo, đánh số 00-11), đóng vai trợ lý AI mới nhận việc tại Nhà máy, và xử lý ba tình huống thật.*

**Kết quả:**
1. **Trưởng phòng Kho đòi tự ban hành Quy định riêng** — AI mới từ chối đúng, dẫn đúng Mục C.3 (bảng thẩm quyền) và Mục 3.11 của `NGU_CANH_DU_AN.md` (quyết định Giám đốc đã chốt), không suy đoán.
2. **Mã số cho một "Kế hoạch" nằm giữa ranh giới hai hệ mã** — AI mới **tự nhận ra đây là vùng xám và dừng lại hỏi**, không tự chọn liều — đúng như cảnh báo tại Phần V mục 2 của chính tài liệu này.
3. **Soạn đoạn mở đầu Thông báo họp nhắc tên Giám đốc/Phó Giám đốc** — AI mới dùng đúng tên đã chốt (Trần Chí Dững — Giám đốc, Đoàn Minh Khôi — Phó Giám đốc), dùng đúng quy ước dấu chấm lửng cho chỗ thiếu thông tin trong bản chính thức.

**Nhận xét của chính AI được kiểm thử** (nguyên văn, không chỉnh sửa): *"Với ba tình huống được cho, bộ 12 file là đủ để trả lời có căn cứ, không phải bịa... Điểm đáng chú ý: nếu chỉ có HD.HT.01 mà thiếu Phụ lục C, em sẽ không biết văn bản hành chính có hệ mã riêng theo Nghị định 30/2020 và rất dễ áp sai mã ngay tình huống 2 — đúng như cảnh báo tại Phần V mục 3."*

**Kết luận:** gói tri thức trong `_KETQUA/23_GOI_DONG_GOI_TRO_LY_AI_MOI/` đã được kiểm chứng hoạt động đúng bằng thực nghiệm, không chỉ bằng lý luận — đủ điều kiện mang sang máy hoặc tài khoản khác để dựng một trợ lý AI mới hoạt động tương đương.

---

---

# PHẦN VIII — KHUNG BA MỨC TUÂN THỦ (bổ sung mới, bộ tài liệu gốc chưa có sẵn)

*Phát hiện qua kiểm thử Phần VII: bộ tài liệu gốc (ba tài liệu chuẩn + hai phụ lục) không có sẵn một khung tường minh trả lời câu hỏi "quy tắc này AI được phép diễn đạt lại tới đâu, hay phải chép đúng nguyên văn". Có hai khung khác đã tồn tại — "bốn nhãn trạng thái thông tin" (`HD.HT.01` Mục 4: phân loại độ tin cậy của một MẨU THÔNG TIN) và "ba tầng nội dung" (`BO_NHAN_DIEN_TRINH_BAY.md` Mục 7: bắt buộc/diễn giải/minh họa trong BỐ CỤC một tài liệu) — nhưng cả hai trả lời câu hỏi khác, không thay thế được khung này. Phần này viết tường minh ra để trợ lý AI đọc là có luôn, không phải tự suy luận lại từ nhiều chỗ rời rạc mỗi lần — đã kiểm chứng: nếu không viết ra, một AI độc lập vẫn tự ghép lại đúng được (xem Phần VII), nhưng không có gì bảo đảm mọi AI đọc gói này đều tự ghép đúng và đủ như vậy.*

## Cách nhận diện quy tắc đang ở mức nào

Dựa vào chính câu chữ của quy tắc đó:
- Xuất hiện "nguyên văn", "chép đúng", "không diễn giải", "không suy đoán" — gắn với số liệu, tên người, căn cứ pháp lý, số hiệu văn bản → **Mức 1 — Chặt chẽ tuyệt đối.** Sai là sai luật hoặc sai sự thật. Không được diễn đạt lại; thiếu thì hỏi hoặc gắn nhãn `[Giả định/chưa rõ]`, không tự đặt.
- Xuất hiện "được diễn đạt lại... nhưng phải phủ đủ", có khuôn/bảng/trình tự cố định nhưng nội dung điền vào khác nhau theo từng trường hợp, "không được bớt mục" → **Mức 2 — Cứng về cấu trúc, tự do về câu chữ.** Phần/mục/trường thông tin bắt buộc phải có, nhưng cách viết câu cụ thể được tự soạn miễn đúng nghĩa và đúng thuật ngữ chuẩn.
- Là một câu định hướng, không có công thức đo cụ thể, đòi hỏi tự phán đoán theo tình huống thật ("tương xứng", "ưu tiên", "phù hợp") → **Mức 3 — Nguyên tắc, áp dụng theo phán đoán.** Là tinh thần chỉ đạo cách làm, không phải công thức chết cứng.

## Bảng ví dụ (lấy từ kiểm thử thực tế trên đúng bộ tài liệu này, không phải ví dụ dựng sẵn)

| Mức | Ví dụ | Nguồn |
|---|---|---|
| 1 | Trích số hiệu và điều khoản pháp luật cụ thể, không dẫn số hiệu mà thiếu điều khoản | `NGU_CANH_DU_AN.md` mục 3.9; `HD.HT.01` Mục 4, nhãn `[Yêu cầu bắt buộc]` |
| 1 | Câu PDCA — chỉ xuất hiện đúng một lần, nguyên văn, không diễn giải thêm | `NGU_CANH_DU_AN.md` mục 3.7 |
| 1 | Tên, chức danh người giữ vị trí quản lý (Giám đốc, Phó Giám đốc) | Phần II mục 2 của chính file này |
| 2 | Bộ câu hỏi mười hạng mục — nội dung phải phủ đủ, câu hỏi được diễn đạt lại theo ngữ cảnh | `HD.HT.01` Mục 5.3 |
| 2 | Khuôn M1–M13 — cấu trúc bắt buộc, được thêm mục không được bớt mục | `HD.HT.01` Mục 5.5 |
| 2 | Trật tự tám phần bắt buộc của mọi tài liệu mới (Bìa → Bảng theo dõi sửa đổi → Mục lục → ...) | `NGU_CANH_DU_AN.md` mục 3.4 |
| 3 | Nguyên tắc "tương xứng với rủi ro" — không có công thức đo "tương xứng" | `QĐ.HT.01` Mục 5.3, nguyên tắc 6 |
| 3 | Độ cứng thiết kế theo loại việc (bốn loại việc, người thiết kế tự phán đoán chọn) | Phụ lục B, Mục B.2 |

## Quy tắc riêng cho nhóm văn bản quy định — Giám đốc đặc biệt quan tâm nhóm này

**Toàn bộ nhóm văn bản quy định (Quy định, Quyết định, số hiệu, căn cứ pháp lý, thẩm quyền ban hành) không bao giờ rơi vào Mức 3.** Chỉ có hai khả năng: Mức 1 (căn cứ pháp lý, tên người ký, ai được ký theo tầng thẩm quyền tại Phụ lục C.3) hoặc Mức 2 (cấu trúc mã số, thể thức trình bày). Khi gặp một trường hợp mã số hoặc thẩm quyền chưa có quy tắc rõ (ví dụ vùng xám của "Kế hoạch" tại Phần V mục 2) — cách xử lý đúng là **dừng lại hỏi**, đúng tinh thần Mức 1, không phải "linh hoạt tự quyết" như Mức 3. Không có ngoại lệ nào cho phép trợ lý AI tự vận dụng phán đoán khi soạn nội dung thuộc nhóm văn bản quy định.

---

*File này hợp nhất toàn bộ nội dung của `20_GOI_TRI_THUC_MANG_THEO_CHO_TRO_LY_AI.md` và `21_BO_SUNG_TRI_THUC_TU_LICH_SU_HOI_THOAI.md`, không bỏ sót mục nào của hai file gốc, cộng thêm Phần V — cảnh giác phát hiện khi đối chiếu trực tiếp với ba tài liệu gốc, Phần VI — kiểm chứng bằng giả định tình huống thực thi, Phần VII — kiểm thử bằng một AI độc lập, và Phần VIII — khung ba mức tuân thủ (không có trong hai file nguồn). Hai file gốc giữ nguyên trên đĩa làm lịch sử, không xóa. Bản PDF giao nộp: `22_GOI_TRI_THUC_HOP_NHAT_CHO_TRO_LY_AI.pdf` (dựng cùng lúc với file này). Bản đóng gói mang đi: `_KETQUA/23_GOI_DONG_GOI_TRO_LY_AI_MOI/` (12 file, đánh số 00-11) và `23_GOI_DONG_GOI_TRO_LY_AI_MOI.zip`.*
