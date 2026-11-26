# PHỤ LỤC — CÂU HỎI CẦN PHÒNG SẢN XUẤT CHỐT

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 26/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Chờ phòng Sản xuất trả lời |
| CR liên quan | — |

Gom mọi câu hỏi phát sinh khi đọc bộ tài liệu của phòng Sản xuất, để gửi một lần. Trả lời câu nào thì ghi câu trả lời và
ngày ngay dưới câu đó, rồi sửa tài liệu chức năng tương ứng ([`11`](11-san-pham.md), [`12`](12-kho.md)).

| Mục | Phạm vi | Số câu | Khi nào cần |
|---|---|---|---|
| A | Câu hỏi chặn (quyết định cấu trúc dữ liệu) | 10 | Trước khi thiết kế bảng — phase 0 |
| B | Sản phẩm: mã hàng, quy tắc, công thức, định mức | 26 | Trước phase 1 và phase 3 |
| C | Kho | 30 | Trước phase 2 và phase 4 |
| D | Sổ Quản lý nhãn mác (nguồn dữ liệu thật) | 5 | Trước khi nạp dữ liệu — phase 0 |

## A. Câu hỏi chặn

1. **Lô và hạn sử dụng:** NL / BTP có bắt buộc theo dõi số lô, ngày sản xuất, hạn sử dụng, kết quả Lab không; VTBB và thành
   phẩm có theo lô không.
2. **Tồn nội bộ và tồn thuế:** ERP giữ một sổ (nội bộ) hay cả hai sổ; sổ thuế hiện chỉ ở Misa.
3. **Khóa tồn:** tồn theo Kho + Mã hàng, hay Kho + **Thương hiệu** + Mã hàng như sổ hiện tại.
4. **Hai góc nhìn tồn BTP** (theo Sản xuất và theo Kinh doanh, chênh do đóng tối ưu thể tích): giữ cả hai hay một.
5. **Cách tính tồn có thể sản xuất** và **giá tồn**: các sheet đang dùng ba cách khác nhau, cần chọn một.
6. **Định mức hao hụt:** lấy theo hợp đồng NCC, theo loại VTBB, hay theo thực tế; hiện có bốn nguồn.
7. **Phiên bản BĐM:** một thành phẩm có nhiều phiên bản định mức cùng hiệu lực không (theo lô NL khác hàm lượng).
8. **Bản thuế của BĐM:** khác bản nội bộ ở đâu; chưa có ví dụ nào trong tài liệu.
9. **Quy tắc mã:** tiền tố mã BĐM, mã sự cố, mã đơn đang lệch giữa quy trình và sổ; cần chốt một bộ.
10. **Bảo mật công thức:** ai được xem dòng công thức thật, mã NL mã hóa (`NA`), giá vốn.

## B. Sản phẩm

1. **Ai là chủ danh mục mã hàng khi lên ERP?** Hiện mã do P TCKT tạo trên Misa rồi các bộ phận kéo về. Phương án A: ERP là gốc, có phiếu khai báo và duyệt, xuất tệp cho kế toán nhập Misa. Phương án B: Misa vẫn là gốc, ERP chỉ nhập về và bổ sung thuộc tính. Gợi ý: A, vì thuộc tính sản xuất không có chỗ trên Misa.
2. **Danh mục HH lấy từ đâu?** Sổ *Quản lý nhãn mác* của Thiết kế (khoảng sáu nghìn dòng) hay sheet *Data HH* (đang trống)? Thiết kế có tiếp tục là người khai HH trên ERP không?
3. **Tiền tố mã BĐM**: theo quy trình (`BDMBTP_`, `BDMVT_`, `BDMTP_`) hay theo sổ đang dùng (không tiền tố, `VT_`, `BĐMTP_` có dấu)? Gợi ý: dùng bản không dấu của quy trình để in và tìm kiếm ổn định.
4. **Mã BĐM BTP có nên chứa tên pháp lý viết tắt và màu?** Viết tắt tự đặt (ABB, ASPG, CT3.6) dễ trùng và không có danh mục. Có chấp nhận mã do hệ thống sinh (mã BTP + số phiên bản) không?
5. **Cấu thành thuế khác cấu thành nội bộ ở những điểm nào cụ thể?** Khác mã vật tư, khác số lượng, hay chỉ khác công ty đứng tên và luồng hóa đơn? Cần một ví dụ thật mà hai bộ khác nhau. Khi nào thì *chỉ còn một bảng dùng chung*?
6. **BĐM TP theo mã HH hay theo mã HH + NCC GC?** Cùng một mã HH làm ở hai NCC có cấu thành khác nhau (NCC này lo thùng, NCC kia không) thì là hai BĐM hay hai mã HH?
7. **Các ô ký trên phiếu BĐM** (duyệt bao bì, duyệt pháp lý, duyệt giá, kế toán trưởng) có thành các bước duyệt trên hệ thống không, hay chỉ QLSX duyệt và in ra ký giấy?
8. **Ranh giới mã HH mới và phiên bản BĐM mới**: đổi chai sang màu khác, đổi thùng, đổi NCC in nhãn — trường hợp nào khai HH mới, trường hợp nào chỉ lên phiên bản BĐM VTBB?
9. **Hao hụt để ở đâu?** Cả ba tầng BĐM không có cột hao hụt. Có thêm *% hao hụt định mức* trên dòng BĐM không, hay giữ ở chính sách NCC theo nhóm vật tư và chỉ dùng lúc quyết toán?
10. **BĐM BTP có cần đủ mọi thành phần không?** Sổ chỉ ghi hoạt chất chính; dung môi, phụ gia (mã `NA`), chất mang, màu chưa có dòng. Giá BTP và xuất kho NL có cần các dòng này không? Nếu công thức đầy đủ là bí mật của Lab thì ai được nhập?
11. **Công thức giá NL trong BTP** ở sheet *3.1* đang chia cho *lượng BTP cần phối* (ra số gấp đôi khi phối 500 lít). Xác nhận công thức đúng là chia cho 1.000?
12. **Tỷ lệ chênh lệch khi test mẫu**: có dòng chia cho hàm lượng đăng ký, có dòng chia cho 1.000 hoặc 100. Chuẩn là chia cho hàm lượng đăng ký (sai số tương đối) đúng không? Với hàm lượng trên 500 g/kg thì dùng sai số tuyệt đối ±25 g/kg?
13. **Tỷ trọng**: nhiều BĐM ghi *chưa tính tỷ trọng*. Thuốc dạng lỏng đăng ký theo g/l thì định mức tính trên 1.000 lít hay 1.000 kg? Ai cấp tỷ trọng (Lab hay NCC) và khi nào phải có?
14. **Sai số phối chế nội bộ**: quy định *tối đa 50% ngưỡng Nhà nước* áp cho mọi sản phẩm hay chỉ một số? Ai được duyệt ngoại lệ?
15. **Thể tích chốt đóng** (vd 440 ml cho chai 450 ml): BĐM TP ghi lượng ruột theo thể tích trên nhãn hay theo thể tích chốt đóng? Phần chênh hạch toán cho ai (sổ ghi có trường hợp đưa vào chi phí Kinh doanh)?
16. **Định mức bao bì đang có trên ERP** (do Thu mua nhập để tính giá) có được coi là BĐM VTBB đã duyệt của Sản xuất không, hay Sản xuất rà lại rồi mới duyệt?
17. **BTPM dự kiến bỏ năm 2027**: các mã BTPM đang dùng chuyển sang BTPR thế nào? Các loại *Phí phạt*, *Chiết khấu*, *BTPNL* có trong sổ khai báo nhưng không có trong quy tắc — có phải loại mã chính thức không?
18. **Mã đơn vị xuất hóa đơn** thiếu số III: đã bỏ hay sót?
19. **Bảng đồng bộ mã DEGO - mã NCC** mới có một NCC và ghi *chưa chốt*: ai nhập cho các NCC còn lại, và NCC có gửi danh mục mã của họ không?
20. **Bảo mật công thức**: liệt kê cụ thể nhóm người được xem (a) lượng NL trong BĐM BTP, (b) dòng công thức phía NCC, (c) tên thật của mã `NA`. Kinh doanh có được xem BĐM VTBB và cấu thành không?
21. **Khảo sát công nghệ**: số bộ mẫu gửi (11 bộ / 4-5 bộ) là quy định cố định theo NCC hay tùy lần? Kết quả khảo sát có hạn hiệu lực không (đổi máy, đổi lô chai thì khảo sát lại)?
22. **Cọc nhãn**: sổ ghi ba NCC, quy trình ghi bốn. Danh sách đúng? Tiền cọc tính theo mã nhãn hay theo hợp đồng? Phần bị trừ khi hoàn cọc tính theo công thức nào?
23. **Mẫu cho tặng** không quản lý tồn: nếu mẫu đạt và được dùng thật thì chuyển sang mã chính thức bằng bước nào?
24. **Thuộc tính VTBB**: *kích thước lọt lòng* thùng hiện thiếu, sổ ghi cần làm lại với Thiết kế. Ai nhập, và có bắt buộc trước khi duyệt BĐM VTBB không?
25. **Phân bón và thuốc BVTV** có dùng chung một mẫu BĐM BTP không? Phân bón do Lab phối theo mã riêng của Lab và tính theo tỷ trọng; cần mẫu ví dụ của phân bón (sổ chỉ có ví dụ thuốc).
26. **NCC GC có được xem / xác nhận BĐM trên ERP không** (vd cổng cho NCC), hay vẫn gửi tệp qua Zalo?

---

## C. Kho

1. **Hai sổ nội bộ và thuế:** ERP giữ cả tồn nội bộ lẫn tồn thuế, hay chỉ giữ tồn nội bộ còn tồn thuế vẫn ở Misa Thuế? Gợi ý: giai đoạn đầu chỉ làm sổ nội bộ, thêm ô xác nhận *đủ tồn thuế* do kế toán tích.
2. **Thương hiệu và pháp nhân:** thương hiệu trên sổ kho (IDA, ABA, DEGO, DR XANH, BAMBOO, N2SBIO, LAB, Dùng chung) có ứng một-một với pháp nhân không? Việc gom DEGO AGROCHEM, DEGO, BAMBOO về IDA ở sổ BTP là quy tắc cố định hay tạm thời?
3. **Tồn có thể sản xuất tính thế nào?** Ba nguồn ghi ba cách: (a) sổ tồn: tồn thực tế = đầu kỳ + nhập thực tế − xuất thực tế, tồn tạm tính riêng; (b) báo cáo VTBB: tồn thực tế + tồn tạm; (c) mẫu 9.10: tồn − xuất tạm − đơn chờ xuất. Gợi ý: lấy (c) làm chuẩn, hiển thị đủ ba thành phần.
4. **Phương pháp tính giá tồn:** bình quân gia quyền cả kỳ, bình quân sau mỗi lần nhập, hay trung bình cộng các lần nhập như mục lục sổ VTBB ghi? Tính theo từng kho hay gộp các kho? Theo từng thương hiệu hay gộp?
5. **Giá nhập kho trước hay sau VAT?** Sổ VTBB lấy giá đã gồm VAT và vận chuyển; ERP đang tính theo đơn giá ĐMH cộng chi phí thu mua phân bổ. Cần một quy ước cho giá vốn.
6. **Xuất âm kho:** chặn cứng hay chỉ cảnh báo? Gợi ý: chặn với xuất thực tế, cho phép giữ hàng vượt tồn khi có người duyệt (thành *đơn chờ xuất*).
7. **Thời điểm ghi xuất:** xác nhận quy tắc *xuất nội bộ khi NCC có thành phẩm*. Khi nhận TP về kho DEGO khác số NCC báo có hàng thì trừ vật tư theo số nào?
8. **Định mức hao hụt chuẩn:** đang có bốn nguồn khác nhau (theo NCC GC trong danh mục, theo loại VTBB ở báo cáo, mặc định 2% ở phân tích TP, điều khoản hợp đồng). Nguồn nào dùng để cấn trừ NCC? Tỷ lệ hao hụt tính trên số lượng nhập hay giá trị xuất?
9. **Hao hụt có vào BĐM không?** BĐM hiện không có cột hao hụt; phần dư khi gửi NCC là mẫu Lab. Vật tư NCC dùng vượt định mức được ghi nhận lúc nào: theo từng đơn hay chỉ khi đối chiếu cuối tháng?
10. **Số lần NCC có thành phẩm:** sổ giới hạn 3 lần cho một đơn. Thực tế có đơn giao hơn 3 lần không?
11. **Cột xuất VTBB:** hướng dẫn ghi số xuất thực tế đọc từ cột AF, AG, AH và xuất tạm từ cột AI, nhưng sheet hiện đặt ở AG, AH, AI và AJ. Bản nào đúng với sổ đang chạy?
12. **Mẫu Lab cộng thêm:** phía VTBB cộng theo số mẫu (ví dụ 200 thành 202), phía BTP cộng cố định 1. Quy tắc chung là gì, có theo quy cách sản phẩm không?
13. **Nhập đổ thu, dư sau sản xuất:** quy trình ghi *sẽ xây dựng sau*. Hiện dư vật tư sau đơn được xử lý thế nào: để lại kho NCC cho đơn sau hay NCC xuất trả?
14. **Hàng cho tặng nhập kho:** ghi giá 0 hay giá ước tính? Có tính vào giá trị tồn không?
15. **Kho lỗi:** mỗi NCC GC một kho lỗi riêng như danh mục, hay dùng nhóm tồn *lỗi* trong cùng kho? Các kho lỗi ghi *Bổ sung kho sau* đã có mã Misa chưa?
16. **Kiểm kê thực tế:** DEGO có cử người đếm tại kho NCC GC không, hay chỉ dựa biên bản của NCC? Nếu có: chu kỳ, ai đếm, ai duyệt chênh lệch.
17. **Chu kỳ đối chiếu:** hằng tuần, hằng tháng hay theo đơn? Ngày chốt số? NCC nào bắt buộc gửi báo cáo, NCC nào không gửi thì làm thế nào?
18. **Bảng ánh xạ mã NCC GC:** hiện mới đủ cho Hà Long. Ai giữ và cập nhật cho các NCC còn lại? NCC nào dùng luôn mã DEGO?
19. **Mẫu biên bản:** cần mẫu *Biên bản xác nhận tồn kho cuối kỳ* và *Biên bản kiểm tra và giải trình chênh lệch* (mục lục ghi chưa xác định phiếu in).
20. **Min và MOQ:** đặt theo mã + kho hay theo mã + kho + thương hiệu? Khi KD xác nhận định mức tồn thì cộng định mức các thương hiệu như mục lục ghi? Ngưỡng 500 / 200 ở sổ NL / BTP có bỏ không?
21. **Hai sổ tồn SX và KD:** có giữ cả hai trên ERP không? Nếu giữ, sổ nào là sổ gốc đối chiếu với NCC? Chênh lệch đóng tối ưu thể tích hạch toán ra sao?
22. **Lô và hạn dùng:** bắt buộc số lô cho NL, BTP, TP; VTBB có cần lô không (nhãn in theo đợt)? Có áp dụng xuất lô hết hạn trước không? Cảnh báo trước hạn bao nhiêu ngày (báo cáo ghi 90 ngày)?
23. **Thành phẩm:** kho TP do phòng Sản xuất hay kho Dr.Xanh quản trên ERP? TP nằm tại kho NCC GC sau khi sản xuất có tính là tồn của DEGO từ ngày nào (ngày NCC báo có hàng hay ngày nhận hóa đơn)?
24. **Xuất bán nội bộ giữa thương hiệu:** đơn giá do ai quyết, có luồng duyệt không? Trường hợp chỉ chuyển số liệu (hàng không di chuyển) có cần phiếu in không?
25. **Phí lưu kho:** danh sách NCC đang tính phí và cách tính từng NCC; phân bổ về thương hiệu theo tiêu chí nào (giá trị tồn, số pallet)? Con số ước tính 1,5% mỗi tháng có còn dùng khi đã có số thực tế?
26. **Quyền duyệt phiếu kho:** loại phiếu nào QLSX duyệt, loại nào cần thêm KD hoặc kế toán? Có hạn mức giá trị không?
27. **Chốt kỳ:** có cần khóa sổ kho theo tháng không, ai được mở lại?
28. **Số dư đầu kỳ khi lên ERP:** lấy số tại ngày nào, nguồn nào là chuẩn (sổ Drive, Misa nội bộ hay biên bản NCC), có đơn giá đầu kỳ cho VTBB không?
29. **Loại VTBB suy từ ba ký tự đầu của mã** có còn dùng khi ERP đã có phân loại trên danh mục sản phẩm không? Mã `VT0` và các mã lạ xếp vào đâu?
30. **Danh mục kho:** `KHO SX_VTBB` là kho gì? Hai tên *Agri Future* và *kho nhà cung cấp AGRIFUTURE* có gộp không? NCC có trong danh sách chính sách nhưng chưa có kho (ví dụ Việt Thắng xuất hiện ở sổ sự cố) thì bổ sung thế nào?

## D. Sổ Quản lý nhãn mác

1. Sheet *DANH SÁCH TỔNG* còn là nguồn gốc duy nhất của mã HH không, hay đã chuyển sang drive *DRIVE ĐẦU VÀO SX*?
2. *Bang chi tiet dinh muc* còn được cập nhật không (bản 2023 và bản hiện tại lệch nhau)? Dòng `#N/A` là chưa khai hay mã
   đã ngưng?
3. Mã HH có hậu tố (`HH0223.1`) là biến thể bao bì của cùng sản phẩm hay sản phẩm khác?
4. *VTBB khác 1–3* gồm những loại nào ngoài cốc đong, seal?
5. Tồn nhãn có nhập chung vào kho VTBB không, hay Thiết kế tiếp tục quản riêng?
