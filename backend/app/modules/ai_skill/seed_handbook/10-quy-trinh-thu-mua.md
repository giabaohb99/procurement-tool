# Quy trình thu mua DEGO (tri thức nền)

Đây là gói tri thức MẪU để trợ lý có ngữ cảnh nghiệp vụ. Người vận hành thay/bổ sung
bằng tài liệu thật của công ty.

## Luồng nghiệp vụ chính

Yêu cầu báo giá (YCBG) -> Khảo sát giá (NCC/Sản phẩm) -> Yêu cầu mua hàng (YCMH/PYC)
-> Đơn mua hàng (ĐMH/PO) -> Nhận hàng (GR) -> Công nợ (Payables) -> Yêu cầu thanh toán (YCTT).

- **Yêu cầu mua hàng**: với luồng khảo sát, chính **người tạo YCBG** (bộ phận có nhu cầu) chọn phương án khảo sát đã duyệt trên phiếu YCBG rồi bấm ***Tạo yêu cầu mua*** — không phải Thu mua; với luồng mua trực tiếp (đã biết rõ mặt hàng và giá), người có nhu cầu tạo YCMH thẳng. Trưởng phòng duyệt theo phòng ban.
- **Yêu cầu báo giá / Khảo sát**: thu mua thu thập báo giá nhiều nhà cung cấp, chọn
  phương án. Khảo sát được duyệt mới dùng để lên đơn.

## Ai liên hệ nhà cung cấp (rất quan trọng, đừng nói sai)

Ở DEGO, người có nhu cầu (nhân sự các phòng ban) **KHÔNG tự liên hệ, không tự gửi yêu cầu
báo giá cho nhà cung cấp**. Việc lấy báo giá, làm việc với NCC là của **bộ phận Thu mua**.

Luồng đúng khi ai đó cần xin báo giá / cần mua một mặt hàng:
1. Người có nhu cầu lập phiếu **Yêu cầu báo giá (YCBG)** trên hệ thống (mã phiếu bắt đầu bằng YCBG — ví dụ YCBG260826001; trên màn hình gọi là "Yêu cầu báo giá"): điền mặt hàng, số lượng, thông số/yêu cầu, mục đích.
2. Gửi duyệt; trưởng bộ phận phê duyệt. Phiếu được duyệt mới chuyển sang **bộ phận Thu mua**.
3. **Bộ phận Thu mua** là bên đi liên hệ nhà cung cấp, xin và so báo giá qua **Phiếu khảo
   sát**; khảo sát được duyệt thì các phương án hiện trên phiếu YCBG.
4. **Người tạo YCBG** xem các phương án trên phiếu, chọn phương án cho từng dòng rồi bấm ***Tạo yêu cầu mua***
   để sinh **Yêu cầu mua hàng (YCMH)**; YCMH được duyệt xong, **Thu mua** mới tạo **Đơn mua hàng**.

Nếu đã biết rõ mặt hàng và giá (không cần khảo sát) thì lập thẳng **Yêu cầu mua hàng (YCMH)**.

Vì vậy khi người dùng hỏi cách xin báo giá / cách mua một mặt hàng, trợ lý hướng họ **lập
phiếu Yêu cầu báo giá trên hệ thống và gửi duyệt để chuyển bộ phận Thu mua**, TUYỆT ĐỐI
không bảo họ tự soạn thư hay tự gửi yêu cầu báo giá cho nhà cung cấp — trừ khi chính người
hỏi thuộc bộ phận Thu mua. Cần các bước thao tác chi tiết thì tra HDSD (search_docs).
- **Đơn mua hàng**: chốt nhà cung cấp, số lượng, đơn giá, VAT. Có luồng duyệt riêng.
- **Nhận hàng**: ghi nhận hàng về, cập nhật tồn kho.
- **Công nợ & Thanh toán**: từ đơn/nhận hàng phát sinh công nợ; lập yêu cầu thanh toán
  để chi trả nhà cung cấp.

## Một số quy ước

- Đơn giá được phép tối đa 4 số lẻ; tiền hiển thị làm tròn về đồng.
- VAT lưu ở dạng tỷ lệ (0.08 nghĩa là 8%), không lưu số 8.
- Mỗi hợp đồng đứng tên một pháp nhân (công ty); phạm vi xem mặc định theo công ty.
- **Báo duyệt Đơn mua hàng / Yêu cầu thanh toán** (từ 22/10/2026): khi một ĐMH hay YCTT được **gửi duyệt**, chuông
  báo tới những người **có quyền duyệt loại phiếu đó và xem được chính phiếu đó**. Phòng tự mua thì chỉ quản lý của phòng
  ấy được báo (thu mua chung không bị báo oan). Không còn ai phù hợp thì chuông rơi về quản trị có quyền duyệt. Hỏi *"sao
  tôi không nhận chuông duyệt phiếu"* thì nguyên nhân thường là: không có quyền Duyệt với loại phiếu, hoặc phiếu nằm ngoài
  phạm vi dữ liệu của họ.
- ***Tên trên hóa đơn*** của dòng ĐMH: để **trống** thì hệ **tự điền từ danh mục Sản phẩm** (theo mã hàng) lúc lưu, lúc sao
  chép ĐMH và lúc nhập Excel. Đã gõ tên thì giữ nguyên; sản phẩm chưa khai tên trên hóa đơn thì ô vẫn trống (hệ không đoán từ tên hàng).
- **Báo cáo mua hàng gom theo phòng hiện hành**: phòng đổi tên thì báo cáo hiện tên mới, không tách thành hai dòng.
- **Nhập đơn giá sau VAT** (từ 17/11/2026): dòng hàng **Yêu cầu mua hàng** và **Đơn mua hàng** (cả giao diện cũ và mới)
  có hai ô cùng sửa được — *Đơn giá* (chưa VAT) và *Đơn giá sau VAT* (ĐMH ghi *Đơn giá (Sau VAT)*). Gõ ô nào ô kia tự tính;
  đơn giá chưa VAT tính ngược giữ 4 số lẻ. Đổi VAT %: vừa gõ ô sau VAT thì giữ giá sau VAT, còn lại giữ đơn giá chưa VAT.
  Hệ thống vẫn LƯU đơn giá chưa VAT; công nợ, bản in không đổi. Yêu cầu báo giá / phiếu khảo sát chưa có ô này.
  Người dùng nhờ trợ lý **sửa giá dòng ĐMH bằng giá đã gồm VAT** → gửi `price_after_vat` (không gửi `price`) trong `po_lines`
  của `propose_document_update`; máy tự tính đơn giá chưa VAT. **Không tự chia nhẩm** rồi gửi `price`.
- **Đơn mua hàng đã duyệt: khóa sửa, Hủy duyệt và Sửa giá sau duyệt** (Sửa giá có từ 27/11/2026, bao-CR-794): đơn *Đã
  duyệt / Đã nhận một phần / Đã nhận đủ* bị khóa nội dung. Đổi mã hàng, số lượng, VAT → người có quyền **Duyệt** đơn bấm
  ***Hủy duyệt*** (nhập lý do), đơn về Nháp, sửa rồi gửi duyệt lại; đơn **đã nhận hàng thì không Hủy duyệt được**. Chỉ đổi
  **đơn giá** → cũng người có quyền Duyệt bấm ***Sửa giá*** trên thanh nút chi tiết đơn (cạnh Hủy duyệt), hộp *Sửa giá sau
  duyệt*: gõ cột *Đơn giá mới*, nhập ***Lý do sửa giá*** (bắt buộc), bấm ***Lưu giá mới***. Dùng được **cả khi đơn đã nhận
  hàng**; đơn giữ nguyên trạng thái, không về Nháp, không duyệt lại. Sau khi lưu: thành tiền dòng và công nợ hàng tính lại
  theo số lượng đã nhận; Lịch sử mua hàng và sổ giá của cụm Giá nguyên vật liệu sản xuất đi theo giá mới; nhật ký đơn ghi giá
  cũ → giá mới kèm lý do. **Không sửa giá được khi:** đơn có yêu cầu thanh toán đã gửi duyệt / đã duyệt / đã chi (hủy phiếu
  thanh toán trước); công nợ hàng của đơn đã trả tiền; dòng đã Hoàn thành hoặc đã Hủy; đơn đã Hoàn thành / đã Hủy. Đơn chưa
  duyệt thì sửa thẳng trên đơn. Yêu cầu thanh toán còn **Nháp** có đơn này: vẫn sửa được, hệ thống nhắc mã phiếu để kiểm lại
  số tiền. **Cách thứ hai: *Sửa giá trong bảng*** (duoc-CR-797, chỉ giao diện ERP mới, cùng quyền Duyệt, cùng ba trạng
  thái): bấm ***Sửa giá trong bảng*** trên thanh nút (hoặc ***Sửa giá*** ở đầu popup chi tiết dòng), sửa thẳng các ô *SL
  đặt*, *Đơn giá*, *VAT%*, *Đơn giá (Sau VAT)* trên bảng dòng, bấm ***Lưu giá mới*** ở thanh đáy (***Thôi*** để bỏ).
  **Không hỏi lý do**, nhật ký ghi từng ô cũ → mới. SL đặt không được nhỏ hơn SL đã nhận. **Chặn theo từng dòng**, ô mờ
  và rê chuột thấy lý do: dòng Hoàn thành / đã hủy; công nợ của dòng đã có tiền trả; dòng nằm trên yêu cầu thanh toán đang
  chờ duyệt / đã duyệt / đã chi (trả phiếu đó về trước). Lưu xong công nợ, tồn kho, YCMH, Lịch sử mua hàng và sổ giá đi
  theo; yêu cầu thanh toán **Nháp** có công nợ của dòng **tự nạp lại** theo số mới. Chọn cách: chỉ đổi đơn giá, cần ghi
  lý do hoặc dùng giao diện cũ → hộp ***Sửa giá***; đổi cả SL đặt / VAT, hoặc đơn có dòng đã lên phiếu thanh toán mà dòng
  khác vẫn cần sửa → ***Sửa giá trong bảng***. **Trợ lý không sửa giá đơn đã duyệt** (không có công cụ; `propose_document_update` chỉ sửa đơn Nháp / Bị trả lại): chỉ
  đường tới nút ***Sửa giá*** / ***Sửa giá trong bảng***; người hỏi không thấy nút thì thiếu quyền Duyệt đơn mua hàng, hoặc đơn
  không còn dòng sửa được.
- **YCMH Đang mua hàng chọn nhầm Công ty nhận hóa đơn: trả về CHỈ để sửa ô đó** (từ 28/11/2026, duoc-CR-803, cả hai giao
  diện): quản lý có quyền Hủy phiếu hoặc người duyệt trong phạm vi bấm ***Trả về*** (nhập lý do) trên phiếu **Đang mua
  hàng**. Chỉ được khi mọi dòng của các ĐMH cùng mã PYC (trừ đơn hủy) **chưa nhận hàng** và các ĐMH đó **chưa có YCTT**
  (trừ phiếu hủy) **và chưa có công nợ**; không thì máy chủ báo lý do (*Đơn mua hàng ... đã có dòng nhận hàng / đã có yêu cầu
  thanh toán ... / đã phát sinh công nợ — không trả về được phiếu này*). Phiếu *Đang xử lý*, *Đã mua hàng*, *Hoàn thành*
  không dùng được; trả về thường (Chờ duyệt / Đã duyệt / Đã điều phối chưa có ĐMH) giữ như cũ. Sau khi trả: phiếu **Bị trả
  lại**, giữ NSTM và trạng thái dòng; người yêu cầu chỉ sửa được ***Công ty nhận hóa đơn*** rồi ***Gửi duyệt*** (ô khác gửi
  lên bị bỏ qua); không xóa, **không hủy / Từ chối phiếu** (nút ẩn), không đổi Đơn gấp, phân bổ, sửa trạng thái dòng, lập thêm ĐMH được. Mọi ĐMH liên quan **tạm
  khóa**: chỉ xem, in (sửa, duyệt, tiến độ, nhận hàng, chi phí, đính kèm, hủy... đều báo *Đơn mua hàng đang bị khóa...*).
  Trưởng bộ phận ***Duyệt*** như thường (chỉ sau khi người yêu cầu đã gửi lại; còn Bị trả lại thì báo *... chưa duyệt
  được*; có YCTT mới gắn mã ĐMH trong lúc khóa thì chặn, xử lý YCTT trước) → công ty mới chép xuống mọi ĐMH, mở khóa, phiếu
  tự về Đang mua hàng (không điều phối lại), NSTM nhận chuông *Đổi công ty nhận hóa đơn*. Trả về lần nữa vẫn ở chế độ chỉ
  sửa công ty. Muốn bỏ đợt sửa: người yêu cầu chọn lại công ty cũ, gửi duyệt, trưởng bộ phận duyệt. Trợ lý không trả về hộ
  (không có công cụ): chỉ đường tới nút ***Trả về***.
- **Mẫu thu mua khi in phiếu đề xuất từ Đơn mua hàng** (từ 17/11/2026): màn in YCMH từ ĐMH có thêm *Mẫu thu mua – có
  chữ ký* / *không chữ ký*. Người đề xuất = người đang in, Trưởng phòng ban/bộ phận = **quản lý trực tiếp** của người đó
  (ký ô TP/BP đề xuất), NCC và bảng hàng theo **ĐMH** (SL đặt, đơn giá). Chỉ người **đọc được đơn đó** mới thấy hai mẫu;
  khi thấy thì hai mẫu này đứng đầu ô Mẫu in, nhưng mở màn vẫn chọn sẵn *Mẫu thường – có chữ ký* (muốn in mẫu thu mua thì tự chọn).
  Hỏi *"sao không có ô trưởng phòng / chữ ký"* → hồ sơ chưa gán quản lý trực tiếp hoặc người đó chưa tải chữ ký.
- **NSPT (nhân sự phụ trách mua) nói dạng *Mã · Tên*** (từ 17/11/2026): màn Tiến độ mua hàng và trường `buyer` của
  `procurement_doc_read` / `pending_procurement_approvals` trả mã nhân sự kèm tên **hiện hành** theo hồ sơ (vd *NSU209 ·
  Nguyễn Văn A*). Đơn cũ chưa gắn hồ sơ chỉ có chữ đã lưu (vd *Mr Tiên*) — đọc nguyên chữ đó, **đừng đoán** là ai. Hỏi
  *"vì sao đơn hiện mã trần / tên lạ"* thì nói: đó là đơn cũ chưa gắn hồ sơ, mở đơn chọn lại NSPT rồi lưu là xong.

## Giá nguyên vật liệu sản xuất / Giá bao bì (duoc-CR-784, từ 21/11/2026; cập nhật 27/11/2026)

Cụm màn cho Thu mua xem **nhà cung cấp đổi giá một mã chai, nắp, nhãn, nhãn thùng, thùng (VTBB) thì chi phí bao bì của
sản phẩm nào đổi theo, đổi bao nhiêu**, để quyết nhận giá / thương lượng / đổi NCC / báo xem lại giá bán. Hai giao diện cùng
chỗ: phân hệ **Thu mua**, nhóm menu **Mua hàng**, mục cha đóng mở **Giá nguyên vật liệu sản xuất** (ngay dưới *Tra cứu thị
trường*; bấm để mở / thu sáu mục con). **Mỗi màn một quyền riêng** (từ 27/11/2026, bao-CR-792; nhóm Thu mua ở màn
phân quyền vai trò, tên *Giá NVL sản xuất › <tên màn>*): Tác động giá bao bì (`packaging_impact`), Tổng hợp theo sản phẩm
(`packaging_product_summary`), Bảng giá VTBB kèm Báo giá VTBB (`packaging_price_list`), Giá mua gần nhất
(`packaging_last_price`), Lịch sử mua hàng kèm Nạp sổ Misa (`packaging_history`), Định mức bao bì (`packaging_bom`). Không có
quyền Xem của màn nào thì không thấy màn đó; không có quyền của màn nào trong cụm thì không thấy cả mục — nhờ quản trị.
- Màn (hai giao diện cùng tên): ***Tác động giá bao bì*** (chọn mã, gõ tên nhóm rồi ***Chọn tất cả***, ô ***Nhập giá*** để
  thử giá giả định; muốn biết sản phẩm tăng nhiều nhất thì xếp cột *Tăng/giảm /thùng* giảm dần; chip nhóm *Chai / Nắp / Nhãn* ở
  bảng mã đã chọn; ***Lọc nâng cao*** ở bảng sản phẩm: xu hướng, vai trò của mã, khoảng quy cách / tăng giảm /chai, /thùng /
  CP mới, chỉ dòng có cảnh báo; xếp được mọi cột kể cả *Chai*, *Nắp*, *Nhãn*; ***In***, ***Xuất Excel***) · ***Tổng hợp theo
  sản phẩm*** (mọi sản phẩm có định mức; thanh lọc một hàng: ô tìm + chip *Tăng / Giảm / Không đổi / Chưa có giá* kèm số đếm
  theo bộ lọc đang bật, nút ***Lọc nâng cao***: có mã ở vai trò, khoảng quy cách thùng, CP bao bì/chai cũ, CP bao bì/chai mới,
  tăng giảm /chai, /thùng, % chênh, chỉ sản phẩm có cảnh báo; Xuất Excel theo đúng bộ lọc) · ***Bảng giá VTBB*** (giá mua gần
  nhất, lần trước, báo giá, cũ / mới; nút ***Báo giá mới*** và ***Báo giá*** từng dòng để ghi báo giá của NCC) · ***Giá mua gần
  nhất*** (3 / 5 / 10 lần) · ***Lịch sử mua hàng*** (theo mã VTBB hoặc theo mã sản phẩm — chế độ sản phẩm mỗi dòng là một lần
  mua x một cặp (sản phẩm, thành phần), có cột *Mã SP · Tên sản phẩm · Thành phần*; chọn một mã thì có sáu thẻ số liệu và biểu
  đồ; cột ***Lần*** — **Lần 1 = lần mua gần nhất** của mã, tính trên toàn bộ lịch sử, không đổi khi lọc; cột ***Giá trị mua***
  = thành tiền chưa VAT, lần mua Sổ Misa lấy đúng số *Giá trị* của Misa, lần mua đã chốt lấy thành tiền đã chốt, còn lại giá x số lượng; cột ***Kho***; ***In***,
  ***Xuất Excel***) · ***Định mức bao bì*** (Thu mua tự khai theo mã HH, ***Nhập từ Excel*** tệp DATA_CHAI.xlsx).
- **Công thức:** CP bao bì / chai = chai + nắp + nhãn + (nhãn thùng + thùng) / quy cách thùng; CP / thùng = CP / chai x
  quy cách. Giá **VNĐ, chưa VAT** theo ĐVT danh mục (màn nào cũng ghi chú đơn vị này dưới tiêu đề).
- **Giá lấy từ đâu:** sổ giá tự gom, không ai nhập tay. **Đơn mua hàng trên ERP:** mỗi dòng ĐMH **đã duyệt** là MỘT lần mua
  trong sổ suốt đời — còn mở thì màn ghi nhãn *ĐMH đang mở*, sửa đơn thì cập nhật, dòng bị hủy / đơn bị hủy duyệt thì rời sổ;
  dòng hoàn thành thì giá được **chốt** theo số lúc hoàn thành và không đổi nữa (kể cả đơn bị hủy sau đó). Đơn nháp / chờ
  duyệt chưa tính. **Lịch sử mua hàng cũ** (nạp Excel trước khi có ERP): ghi một lần. **Sổ Misa** (sổ chi tiết mua hàng Misa
  2025 tới **30/06/2026**, cùng số với báo cáo giá NVL bản HTML của Thu mua; Misa không ghi VAT nên ô VAT để trống): tới mốc
  30/06/2026 chỉ dùng Sổ Misa, sau mốc chỉ dùng **đơn mua hàng thật trên ERP**; lịch sử cũ nạp từ tệp khảo sát không còn tính.
  Dòng đơn giá 0 đếm vào số lần mua nhưng không làm giá. Giá lọc theo **pháp nhân** người hỏi được xem — hai người có thể thấy
  giá khác nhau. Hỏi *"sao giá trên ERP khác bản HTML"* → mã đó đã có đơn mua hàng sau 30/06/2026 (giá mới hơn); ở Lịch sử
  mua hàng, dòng có mã đơn ở cột *Nguồn* là lần mua trên ERP, dòng để trống ô Nguồn là Sổ Misa / lịch sử cũ (tệp Excel ghi rõ
  chữ *Sổ Misa*, *Lịch sử mua hàng*, *Dòng đơn mua hàng*).
- **Giá cũ / mới:** có báo giá → mới = báo giá mới nhất (kể cả ngày hiệu lực ở tương lai), cũ = lần mua có giá gần nhất;
  không báo giá → mới = lần mua có giá gần nhất, cũ = lần trước đó; mới mua một lần → cũ = mới. Số **tăng hiện đỏ, giảm
  hiện xanh**. **Không còn ngưỡng giá sàn / trần** (đã bỏ hẳn 25/11/2026: không nút, cột, ô lọc hay cảnh báo nào về ngưỡng);
  Min / Max là giá thấp nhất / cao nhất tự tính từ sổ giá. Đừng hướng dẫn người dùng đặt ngưỡng.
- **Báo giá:** mỗi (mã, mã NCC, ngày hiệu lực) chỉ một báo giá (bỏ trống Mã NCC cũng tính là một NCC); lưu trùng thì hệ thống
  báo *Đã có báo giá cùng mã, NCC và ngày hiệu lực* → sửa báo giá đang có hoặc đổi ngày hiệu lực. Màn danh sách *Báo giá VTBB*
  (ẩn khỏi menu, mở từ Bảng giá) có cột **Nguồn**: *Nhập tay* hoặc *Nhập Excel (lô #N)* (bấm mở trang lô). Báo giá không thành
  lần mua.
- **Ghi chú cảnh báo:** *Thiếu giá chai* (CP để trống, xu hướng *Chưa có giá* → nhập báo giá cho mã chai) · *Thiếu giá
  thành phần: Nhãn* (phần đó tính 0) · *Chưa khai mã thành phần* · *Thiếu quy cách thùng* · *ĐVT mua khác ĐVT danh mục*.
- **Giới hạn:** một chai một bộ chai / nắp / nhãn; mỗi mã HH một định mức (chưa có phiên bản); đơn giá hiểu là giá một
  cái theo ĐVT danh mục; Sổ Misa mới tới 30/06/2026.
- **Nhập Excel (kèm tệp mẫu, nút *Tải tệp mẫu* trong hộp):** ***Nhập báo giá*** ở Bảng giá VTBB (Mã VTBB, Đơn giá, Ngày hiệu
  lực, Mã NCC, VAT, Ghi chú; trùng mã + NCC + ngày thì sửa) · ***Nạp sổ Misa*** ở Lịch sử mua hàng (Sổ chi tiết mua hàng xuất
  từ Misa; chỉ thay dữ liệu Misa trong khoảng ngày của tệp, mốc tự dời; cần quyền **Sửa** của màn Lịch sử mua hàng) · ***Nhập từ Excel*** ở
  Định mức bao bì. Cả ba: ***Chạy thử*** → xem nhật ký ở trang lô Quản lý Import → ***Ghi thật***. Ba loại lô này không có
  *Hoàn tác*; ghi thật nhầm thì mở trang lô (ERP mới: *Quản trị › Nhập dữ liệu*; giao diện cũ: *Hệ thống › Quản lý Import*)
  rồi bấm ***Xóa dữ liệu của lô này***: hộp xem trước số dòng sẽ xóa, dòng đã sửa tay sau khi nhập mặc định giữ lại (tick
  *Xóa luôn … dòng đã sửa tay* nếu muốn), bấm ***Xóa N dòng***; không đảo ngược được. Định mức / báo giá mà lô tạo mới hoặc
  ghi đè lần cuối bị xóa hẳn (không quay về bản cũ); lô Sổ Misa chỉ xóa lần mua lô đó thêm và tự tính lại mốc. Cần quyền
  **Xóa** của màn giữ dữ liệu lô (lô định mức: Định mức bao bì; lô báo giá: Bảng giá VTBB; lô Sổ Misa: Lịch sử mua hàng) +
  quyền xem Quản lý Import. Nhập báo giá cần quyền **Tạo** của Bảng giá VTBB; Nhập từ Excel cần quyền **Tạo** của Định mức bao bì.
- **In / Excel:** bản in A4 ngang và tệp Excel trình bày như báo cáo HTML (tiêu đề *BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT*,
  ngày xuất, đơn vị VNĐ chưa VAT, ô tăng đỏ giảm xanh), theo đúng bộ lọc đang xem; Excel tối đa 5.000 dòng.
- Giao diện cũ là ứng dụng cài được: cập nhật xong mà màn chưa đổi thì bấm ***Tải lại*** ở hộp *Đã có phiên bản mới*.
- Hỏi số cụ thể → dùng công cụ giá nguyên vật liệu bao bì nếu có trong danh sách công cụ: `packaging_price_impact` ("nắp X lên 350 đ thì
  sản phẩm nào tăng bao nhiêu", nhận giá giả định), `packaging_price_lookup` (giá cũ / mới, lần mua gần nhất của một mã VTBB),
  `packaging_product_cost` (chi phí bao bì / chai, / thùng của một mã HH — truyền mã HH ở tham số `fg_codes`, kết quả trả
  `fg_code` / `fg_name`). Kết quả không còn trường giá sàn / trần. Mỗi công cụ cần quyền Xem của màn tương ứng (Tác động giá bao bì /
  Bảng giá VTBB, kèm Giá mua gần nhất nếu hỏi các lần mua gần nhất / Tổng hợp theo sản phẩm). Không có công cụ hoặc người hỏi
  thiếu quyền thì nói rõ cần quyền của màn nào và chỉ màn ***Tác động giá bao bì***. **Không tự nhẩm** chi phí từ lịch sử mua, đừng đoán giá. Trợ lý không xóa / nhập được dữ
  liệu của cụm (chỉ trên màn web).
  Bước thao tác chi tiết: HDSD *Hướng dẫn sử dụng Giá nguyên vật liệu sản xuất* (search_docs).

## Tên nút trên màn Thu mua (từ 09/11/2026, giao diện mới và cũ ghi giống nhau)

Chỉ đường cho người dùng thì gọi đúng chữ trên nút dưới đây, đừng dùng tên cũ của giao diện mới (*Thêm mới*,
*Lưu & gửi duyệt*, *Duyệt điều phối*, *Tạo đơn*, *Hủy đơn*, *Xem cả chuỗi chứng từ*).
- Bốn danh sách YCMH, YCBG, Phiếu khảo sát, ĐMH: ***Thêm*** để lập phiếu; ***Nhân bản*** ở đầu trang bật cột *Thao tác*,
  bấm ***Nhân bản*** trên dòng rồi đồng ý, xong bấm ***Xong***; tick dòng thì nút thành ***Xuất Excel (n)*** và chỉ xuất
  phiếu đã tick (YCMH, ĐMH, YCBG).
- Chi tiết YCMH: ***Lưu*** · ***Gửi duyệt*** (lưu rồi gửi) · ***Duyệt*** (trưởng bộ phận duyệt; thu mua bấm ***Duyệt*** lần
  hai để điều phối, hộp tên *Duyệt điều phối*) · ***Tạo đơn mua hàng*** · ***Xóa phiếu***. Phiếu *Bị trả lại* / *Đã từ chối*
  có ***Tạo yêu cầu báo giá*** (mở form YCBG điền sẵn dòng). Dòng hàng có ***Nhân đôi***, dưới bảng ***Thêm nhiều dòng***.
  Sản phẩm đã đặt đủ thì hộp hỏi ***Chỉ SP còn thiếu*** hay ***Vẫn mua thêm***.
- Chi tiết YCBG: ***Tạo yêu cầu mua*** · ***Xóa phiếu***; dòng có ***Nhân đôi***, ***Chi tiết / hình ảnh***. Màn
  *Xử lý khảo sát*: tick nhiều báo giá rồi ***Thêm n dòng đã chọn làm option***; ***Xóa option***; ***Quay lại***; chốt
  khi còn dòng rỗng bấm ***Chốt (n chốt rỗng)***.
- Chi tiết Phiếu khảo sát: ***Duyệt*** (hộp hỏi lại, nút ***Duyệt phiếu***) · ***Bổ sung*** · ***Tải file lên*** · ***Xóa phiếu***.
- Chi tiết ĐMH: đơn mới bấm ***Tạo***; ***Hủy*** (ẩn khi đơn có dòng Hoàn thành) · ***Xóa đơn*** · ***Hoàn thành*** /
  ***Mở lại*** luôn hỏi lại; đơn đã duyệt có ***Hủy duyệt*** (ẩn khi đã nhận hàng), ***Sửa giá*** và ***Sửa giá trong
  bảng*** (người có quyền Duyệt); ***Thêm nhiều*** ở thẻ dòng hàng. *Hồ sơ chứng từ* chọn ở tiêu đề thẻ chứng từ (bấm ra menu).
  Thẻ chứng từ có ***Chuỗi chứng từ (PYC/PKS)*** và ***Upload thêm file cho mục này***. Thẻ chi phí thu mua: ***Tạo YCTT***;
  NCC chưa có khoản nợ hiện *Chưa thành công nợ*. Hộp tạo YCTT có tab ***Chi phí thu mua***.

## Ranh giới của trợ lý

- Trợ lý CHỈ trả lời trong phạm vi dữ liệu và tài liệu mà người hỏi được phép xem.
- Khi chưa chắc chắn hoặc thiếu dữ liệu, nói rõ là chưa đủ căn cứ, không bịa số liệu.
