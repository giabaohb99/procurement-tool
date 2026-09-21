# ĐỒNG BỘ APP ĐẶT XE CŨ ↔ ERP (Đặt xe · Duyệt dấu)

> Bản 1.0 — 15/09/2026. Tài liệu KẾ HOẠCH, chưa có dòng mã nào được viết.
> Người duyệt phạm vi: đại ca. Người soạn: trợ lý.

---

## 1. Bối cảnh

Tập đoàn đang có **hai phần mềm cùng làm một việc**:

| | App cũ ("app đặt xe") | ERP |
|---|---|---|
| Mã nguồn | `app đặt xe/my-firebase-api` (Cloudflare Worker + TypeScript) và `app đặt xe/degoholding-app-frontend` (React + Vite) | `procurement-tool/` (FastAPI + MySQL + React) |
| Dữ liệu | **Firebase Realtime Database** — hai project tách hẳn: `api-degoholding` (dev) và `api-degoholding-com` (prod) | MySQL 8, quản lý bằng Alembic |
| Tên miền | `app.degoholding.vn` · API `api.degoholding.vn` | `thumua.degoholding.vn` · `erp.degoholding.vn` |
| Nghiệp vụ | Đặt xe công tác · Giao hàng · Đóng dấu · Wiki · Chat | Đặt xe (`vehicle_booking`), Duyệt dấu (`seal_request`) và 40+ phân hệ khác |

Phân hệ **Đặt xe** của ERP đã làm xong pha 0–6 và **đã lên cả `main` (prod) lẫn `erp-v2`** (commit `8ade5bd6`); phân hệ **Duyệt dấu** cũng đã chạy. Nghĩa là chỗ để chứa dữ liệu bên ERP **đã có sẵn**, việc còn lại thuần túy là nối hai hệ với nhau.

Tài sản đang có để làm việc này: **toàn bộ mã nguồn app cũ** và **tài khoản quản trị Firebase** — tức là sửa được cả hai đầu, không bị kẹt ở chỗ "bên kia là hộp đen".

---

## 2. Mục tiêu

**Giai đoạn 1:** người dùng tiếp tục làm việc trên app cũ như thường — tạo phiếu và **duyệt ngay ở đó** — còn ERP nhận đủ dữ liệu để điều phối và làm báo cáo. **Giai đoạn 2:** người dùng chuyển sang ERP và làm y hệt như trên app cũ, app cũ lùi về chỉ đọc rồi tắt (QĐ-J).

Xuyên suốt cả hai giai đoạn: hai bên nhìn thấy cùng một sự thật, và lúc nào cũng **tra được** một phiếu đã sang chưa, sang được hay hỏng, hỏng vì lý do gì.

> Bản đầu của mục này viết *"ERP là nơi duyệt"* — **đã sai**. QĐ-I giữ nguyên bộ máy duyệt của app cũ, nên giai đoạn 1 người ta vẫn ký ở app cũ.

Ba thứ phải đạt, xếp theo thứ tự quan trọng:

1. **Không mất phiếu.** Một phiếu tạo bên cũ mà không sang được ERP thì phải nằm lại trong sổ ở trạng thái lỗi, có người thấy, bấm chạy lại được. Tuyệt đối không có chuyện im lặng biến mất.
2. **Không đẻ phiếu trùng.** Gọi lại bao nhiêu lần cũng chỉ ra một phiếu.
3. **Không lệch trạng thái.** Phiếu "đã duyệt" bên này không được là "đang chờ" bên kia.

---

## 3. Những gì đã chốt

| Mã | Nội dung | Ngày |
|---|---|---|
| QĐ-A | **Đồng bộ hai chiều**, không phải cắt chuyển một lần. App cũ vẫn sống và vẫn là cửa nhập liệu — *(bổ sung 15/09: "vẫn sống" là nói giai đoạn 1; đích đến vẫn là tắt app cũ, xem QĐ-J)* | 15/09/2026 |
| QĐ-B | Phạm vi mang sang gồm **cả bốn nhóm**: danh mục xe/tài xế · phiếu đặt xe và giao hàng · phiếu đóng dấu · tệp đính kèm | 15/09/2026 |
| QĐ-C | Cơ chế nối là **webhook** (bên nào đổi thì gọi sang bên kia), **kèm sổ ghi nhận ở cả hai đầu** | 15/09/2026 |
| QĐ-D | **Tài khoản nhân sự KHÔNG đồng bộ.** Phiếu gửi kèm email, ERP tự tìm người theo email; quyền hạn dùng quyền của ERP | 15/09/2026 |
| QĐ-E | **Tệp đính kèm không chép nội dung** — ERP chỉ lưu một dòng liên kết trỏ về tệp bên app cũ (qua `tab_file` + `tab_file_link`) | 15/09/2026 |
| QĐ-F | App cũ **thêm trường thời gian cập nhật** — hiện tại hoàn toàn không có, nên không thể hỏi "có gì đổi từ hôm qua" | 15/09/2026 |
| QĐ-G | **Phiếu luôn phải có pháp nhân và phòng ban**, vì pháp nhân quyết định đơn chạy tới giám đốc nào. **Cấm `company_id = 0`.** Tra theo ba nấc: hồ sơ nhân sự → phòng ban → công ty mặc định (Dego Holding), xem [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) mục 8.3 | 15/09/2026 |
| QĐ-H | ERP **thêm trạng thái `SEAL_DELIVERED = 8` ("Đã trả hồ sơ")** để khớp một-một với app cũ. App cũ tách hai nấc văn thư — đóng dấu xong (`sealed`) và trao lại hồ sơ (`delivered_to_staff`) — ERP đang thiếu nấc sau | 15/09/2026 |
| QĐ-I | **HAI BỘ MÁY DUYỆT GIỮ NGUYÊN, KÝ ĐƯỢC Ở CẢ HAI BÊN.** Không đụng vào luồng duyệt của bên nào — app cũ đang chạy thật với người dùng thật, không đổi luồng đột ngột được. Đường nối **chỉ đồng bộ KẾT CỤC, không đồng bộ tiến trình**: chặng nào, ai ký chặng mấy là chuyện riêng của mỗi bên; chỉ khi phiếu ra kết cục (duyệt xong / từ chối / trả về / hủy) mới đẩy sang bên kia, và bên nhận **đóng phiên duyệt của mình bằng một hành động hệ thống có ghi rõ nguồn**, tuyệt đối không ký khống từng chặng. Đụng độ thì **cú sau ghi đè** (QĐ-J), so theo **giờ bấm** chứ không phải giờ tín hiệu tới. Chi tiết ở [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) mục 15 | 15/09/2026 |
| QĐ-J | **CÓ ĐÍCH ĐẾN: người dùng sẽ chuyển hẳn sang ERP.** Không phải hai app song song vĩnh viễn. **Giai đoạn 1** — người dùng vẫn thao tác trên app cũ, dữ liệu đồng bộ sang ERP. **Giai đoạn 2** — người dùng chuyển sang ERP và thao tác y như trên app cũ; app cũ lùi về vai trò chỉ đọc rồi tắt. Hệ quả: **mỗi lúc chỉ MỘT bên thao tác thật**, nên đụng độ gần như không xảy ra, và khi lỡ xảy ra thì luật là **cú sau ghi đè** (đại ca: *"có lỡ ghi trùng thì thằng nào sau thì ghi đè, lấy thằng đó"*). Chưa định mốc chuyển; điều kiện để chuyển được liệt kê ở mục 8 | 15/09/2026 |
| QĐ-K | **Mã số thuế: ERP là bên đúng, app cũ thiếu dữ liệu** (đại ca: *"mình tin hệ thống erp nhé, cái kia data bị miss"*). Áp cho hai dòng Dr.Xanh đang lệch, và áp luôn thành **luật chung**: gặp chỗ nào hai bên ghi khác nhau về hồ sơ pháp nhân thì lấy theo ERP. Hệ quả kỹ thuật: bảng tra thương hiệu → pháp nhân **khớp bằng `id` thương hiệu**, cấm khớp bằng tên hoặc bằng mã số thuế nhúng trong tên — vì tên bên app cũ nay đã biết là có thể sai, ai đi sửa lại cho đúng là bảng tra vỡ | 16/09/2026 |
| QĐ-L | **Phòng ban: tạo bên ERP cho ĐỦ với app cũ, giữ nguyên tên như app cũ đang ghi** (đại ca: *"cứ tạo như phòng ban trên app cũ, ví dụ N2AGRO-KT thì để nguyên như vậy"*). Không gộp, không diễn giải lại, không sửa tên cho "đẹp" — kể cả mấy dòng trùng tên pháp nhân. Lý do: người dùng đang chọn phòng ban theo tên họ quen, tới giai đoạn 2 mà tên đổi thì họ chọn nhầm. ERP **18 → 26** phòng ban | 16/09/2026 |
| QĐ-M | **Luồng "Mua hàng" của app cũ KHÔNG đồng bộ, bỏ hẳn ra ngoài phạm vi** (đại ca: *"mình chỉ đồng bộ đặt xe, duyệt dấu, giao hàng thôi... luồng mua hàng trên app cũ ít sử dụng lắm"*). Nhưng **không xóa trắng**: phiếu đang có bên app cũ phải được **kết xuất thành một bản tổng hợp** giao lại cho đại ca trước ngày tắt app. Đây là **kết xuất một lần ra tệp**, không phải đổ vào phân hệ Yêu cầu mua hàng của ERP | 16/09/2026 |
| QĐ-N | **34 phiếu đang chờ duyệt: để app cũ ký nốt, KHÔNG mở việc chờ bên ERP** (đại ca chốt 21/09/2026, chọn phương án A). Phiên vẫn ở `INSTANCE_RUNNING` như lúc nhập; người duyệt ký bên app cũ, kênh P2 đẩy sự kiện sang, ERP tự đóng phiên. Không phải viết thêm bước nào, và số 34 tự teo dần mỗi ngày. **Mặt mất phải nói rõ:** trong lúc đó **không ai bên ERP duyệt được 34 phiếu ấy** — chúng thấy được, tìm được, nhưng đứng im, vì phiên còn mở chiếm `running_slot` nên `block_legacy_path` khóa ba nút duyệt thẳng. Đó vừa là cái giá vừa là cái được: hai nơi cùng ký một phiếu là nguồn mâu thuẫn không gỡ nổi. **Điều kiện lật:** định tắt app cũ trước khi 34 phiếu đó ký xong thì phải làm phương án B — mở việc chờ đúng tại chặng phiếu đang đứng, không dùng lại `instance_service.start` được vì hàm đó dựng luồng từ chặng đầu. Chi tiết ở `TIEN-DO.md` §P1 |

## 4. Nguyên tắc, năm điều

**Một — mỗi ô dữ liệu chỉ có một ông chủ.** Hai chiều không có nghĩa là hai bên cùng được sửa mọi thứ. Xem bảng ở mục 5.

**Hai — sổ quan trọng hơn chuông.** Webhook chỉ là cái chuông và nó **sẽ có ngày rơi**. Quyển sổ mới là thứ cho phép phát hiện và sửa. Dựng sổ trước, dựng chuông sau.

**Ba — nhận lại một việc đã làm thì không làm lại.** Mọi đường nhận đều tra theo mã bên kia trước; đã có thì cập nhật, chưa có mới tạo. Nhờ vậy nút "Chạy lại" dùng được mà không sợ hỏng thêm.

**Bốn — ghi vì lệnh của bên kia thì không báo ngược lại bên kia.** Đây là cách chặn vòng lặp vô hạn.

**Năm — lỗi phải ồn ào.** Không nuốt lỗi, không `try/except` trống. Dòng lỗi nằm lại trong sổ và hiện lên màn hình quản trị.

---

## 5. Ai làm chủ cái gì

| Nhóm dữ liệu | Chủ | Bên kia làm gì |
|---|---|---|
| Nội dung phiếu lúc vừa tạo — đi đâu, mấy giờ, mấy người, chở gì, ai liên hệ, điểm dừng | **App cũ** | ERP nhận và ghi xuống, không tự sửa |
| Trạng thái phiếu, duyệt / từ chối / trả về | **CẢ HAI** (QĐ-I) — mỗi bên giữ bộ máy duyệt riêng, ký ở đâu cũng được | Bên kia nhận **kết cục** rồi đóng phiên duyệt của mình, ghi rõ "xử lý bên <tên app>". Không ký khống từng chặng |
| Điều phối — gán xe, gán tài xế | **ERP** | App cũ hiển thị tên xe · biển số · tên tài xế · SĐT (nhận sẵn dạng chữ, không cần tra danh mục) |
| Tài xế nhận chuyến, bắt đầu, hoàn thành, số km, chi phí | **ERP** | App cũ hiển thị lại |
| Danh mục xe và tài xế | **ERP** (sau đợt nạp đầu tiên lấy từ app cũ) | App cũ không cần biết, vì đã nhận sẵn dạng chữ |
| Tài khoản nhân sự, phân quyền | **Mỗi bên tự giữ của mình** | Nối nhau bằng **email**, không đồng bộ |
| Tệp đính kèm | **App cũ** giữ tệp thật | ERP chỉ giữ đường dẫn |

Vì sao chọn cách chia này: app cũ là chỗ người dùng quen tay nên để họ tạo phiếu ở đó; còn điều phối, báo cáo thì ERP mạnh hơn hẳn (phân quyền theo phạm vi, chống trùng giờ xe, thống kê đội xe).

**Một ngoại lệ cố ý, phải nói thẳng:** sau QĐ-I thì dòng *trạng thái duyệt* **có hai ông chủ**. Đây là đánh đổi đã cân nhắc chứ không phải sơ suất — đổi luồng duyệt của một app đang chạy thật là việc không làm liền được, và giá của nó lớn hơn giá của mấy giới hạn ở mục 8. Mọi dòng còn lại vẫn giữ đúng luật một chủ. Cách kìm rủi ro của ô ngoại lệ đó nằm trọn ở [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) mục 15.

---

## 6. Trong phạm vi và ngoài phạm vi

**Trong phạm vi:**
- Nạp một lần toàn bộ lịch sử: xe, tài xế, phiếu đặt xe, phiếu giao hàng, phiếu đóng dấu.
- Webhook hai chiều cho phiếu đặt xe và giao hàng.
- Sổ đồng bộ ở hai đầu, màn hình xem sổ và nút chạy lại trong ERP.
- Đối soát định kỳ ban đêm.
- Tệp đính kèm dạng liên kết.
- Phiếu đóng dấu (một đợt riêng, sau khi rà xong bảng đối chiếu trường).

**Ngoài phạm vi, lần này không làm:**
- Wiki và Chat của app cũ. ERP có Trung tâm HDSD và Diễn đàn riêng, hai bên không nối.
- Thông báo đẩy FCM của app cũ. Mỗi bên tự báo người của mình.
- Đồng bộ danh sách người dùng và phân quyền (QĐ-D).
- Chép tệp thật sang kho ERP — **việc bắt buộc**, nhưng ở đợt riêng (P8), không phải đợt này.
- Tắt app cũ — **đợt riêng P8**, sau mốc chuyển giai đoạn của QĐ-J.
- **Luồng "Mua hàng" 2 cấp của app cũ (QĐ-M).** Không đồng bộ, không dựng lại bên ERP. Phạm vi đồng bộ đúng ba thứ: **đặt xe · duyệt dấu · giao hàng**. Kèm theo một việc nhỏ **vẫn phải làm**: kết xuất bản tổng hợp phiếu Mua hàng đang có bên app cũ ra tệp giao lại đại ca, trước ngày tắt app — xem mục 8.

> ⚠️ Cập nhật 15/09 theo QĐ-J: hai dòng trên trước đây ghi là *"chỉ làm khi nào quyết định tắt"* và *"nếu sau này muốn tắt"*. **Sai rồi** — đã có đích đến, nên chúng là **việc chắc chắn phải làm**, chỉ là chưa tới lượt. Khác nhau ở chỗ: việc "có thể không bao giờ làm" thì được phép thiết kế cẩu thả, việc "chắc chắn làm" thì không.

---

## 7. Bộ tài liệu này gồm

| Tệp | Nội dung |
|---|---|
| [README.md](README.md) | Tệp này — tóm gọn yêu cầu, quyết định, nguyên tắc |
| [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) | Mô tả kỹ thuật: sổ đồng bộ, hợp đồng webhook, chống lặp, khớp người, tệp, đối soát, cấu hình |
| [doi-chieu-truong.md](doi-chieu-truong.md) | Dò từng ô một: trường nào bên cũ sang trường nào bên ERP, trạng thái ánh xạ ra sao, chỗ nào mất dữ liệu |
| [danh-sach-phase.md](danh-sach-phase.md) | Chín pha, mỗi pha có mục tiêu, việc từng bên, tiêu chí xong, rủi ro |
| [TIEN-DO.md](TIEN-DO.md) | Bảng tick tiến độ, cập nhật trong lúc làm |

Thứ tự đọc cho người mới: README → danh sách phase → mô tả kỹ thuật → đối chiếu trường.

---

## 8. Ba điều phải lường trước

**Ngày app cũ tắt thì mọi tệp đính kèm chết theo.** Vì ERP chỉ giữ đường dẫn chứ không giữ tệp (QĐ-E). Trước khi tắt app cũ bắt buộc có một đợt chép tệp thật sang kho ERP. Ghi ra đây để lúc đó không ai bất ngờ.

> ⚠️ **QĐ-J nâng điều này từ "lường trước" lên "đã lên lịch".** Trước đây việc tắt app cũ chỉ là khả năng, nên đợt chép tệp là chuyện xa. Nay đã có đích đến thì nó nằm trên đường đi bắt buộc. Thêm một chỗ phải để ý: liên kết R2 của app cũ là **liên kết ký hạn một giờ** — nếu ERP lỡ lưu nguyên đường dẫn đã ký thay vì lưu khóa tệp thì sau một giờ mọi liên kết chết, không cần đợi tới ngày tắt app. Xem mục 10 của [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md).

### Điều kiện để chuyển sang giai đoạn 2 (QĐ-J)

Chưa định mốc, nhưng điều kiện thì liệt kê được ngay — và đây chính là thứ biến ba câu hỏi còn treo thành **việc phải làm**, thay vì "có thể bỏ qua". *(Cập nhật 16/09: ba câu H-09/H-10/H-11 đã có trả lời, nên hai dòng giữa chuyển từ "phải quyết" sang "phải làm xong".)*

| Điều kiện | Trạng thái |
|---|---|
| ERP làm được **mọi** thao tác người dùng đang làm trên app cũ (tạo phiếu, duyệt, điều phối, tài xế nhận chuyến) | **Chưa rà lượt nào.** Đây giờ là điều kiện nặng nhất còn lại |
| Ba luồng duyệt ACTIVE trong phạm vi có chỗ đáp bên ERP | Luồng thứ tư — *Mua hàng* — đã **bỏ khỏi phạm vi** theo QĐ-M, đổi lại phải có bản tổng hợp |
| **26 phòng ban đã tạo đủ bên ERP**, tên giữ nguyên như app cũ | QĐ-L — việc làm được ngay, không chờ ai |
| Danh sách người duyệt hai bên trùng nhau | Việc rà quyền một lần, xem [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) mục 15.4 |
| Tệp đính kèm đã chép thật sang kho ERP | P8 |
| ~~Bản tổng hợp phiếu Mua hàng đã kết xuất và giao~~ **BỎ 16/09** | Đo ra **0 phiếu** trên luồng đó (mục 10.8, C-1). Không có gì để kết xuất, điều kiện này tự tiêu |

**Phiếu đóng dấu khớp kém hơn phiếu đặt xe rất nhiều.** ERP có tiêu đề phiếu, số bản đóng dấu, mốc văn thư hoàn thành, và cho một phiếu gắn nhiều công ty — app cũ không có gì trong số đó. Ngược lại app cũ có danh sách tệp đính kèm, cờ bỏ qua duyệt, nhảy thẳng tới cấp duyệt nào, và thương hiệu liên quan — ERP không có. Nối thẳng là mất dữ liệu ở cả hai chiều. Chi tiết ở [doi-chieu-truong.md](doi-chieu-truong.md) mục 6.

> Cập nhật 15/09: hai chỗ đã gỡ được. Nấc bàn giao hồ sơ giải bằng QĐ-H. Còn thương hiệu thì **có thể không mất gì** nếu nó chính là pháp nhân — xem [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.

**Hai bộ máy duyệt không giống nhau.** App cũ chụp lại luồng duyệt ngay trong phiếu; ERP có bộ máy duyệt riêng kèm bảng việc, thông báo, dấu vết. Không cố dựng lại phiên duyệt của phiếu cũ trong ERP — lịch sử duyệt cũ đổ vào nhật ký dạng chữ, phiếu nạp vào ở đúng trạng thái cuối cùng của nó.

> Cập nhật 15/09 (QĐ-I): điều này **đúng cả cho phiếu mới**, không riêng phiếu lịch sử. Hai bộ máy chạy song song, đường nối chỉ chuyển kết cục. Bốn giới hạn phải chấp nhận — báo cáo "ai ký chặng 2" chỉ đúng ở bên người ta thực bấm · có cửa sổ vài giây hai bên hiện khác nhau · phiếu đang giữa chừng thì bên kia chỉ thấy "chờ duyệt" chứ không thấy đang ở chặng mấy · người có quyền duyệt bên cũ mà bên ERP không có vẫn duyệt được qua cửa app cũ. Đầy đủ ở [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) mục 15.4.

---

## 9. Câu hỏi còn treo

| Mã | Câu hỏi | Ai trả lời |
|---|---|---|
| ~~H-01~~ | ~~Sau khi nối xong, người duyệt ký ở đâu?~~ **ĐÓNG 15/09** — đại ca chốt: *"2 app vẫn hoạt động, nhưng có đường đồng bộ qua lại thôi, không thay đổi gì ở luồng được, cứ cái đang hoạt động bình thường kiểu đổi thì ai đâu mà đổi liền được."* Thành **QĐ-I** ở mục 3 | Đã chốt |
| ~~H-09~~ | ~~Hai dòng Dr.Xanh lệch mã số thuế giữa hai hệ.~~ **ĐÓNG 16/09 — ERP đúng.** Đại ca: *"mình tin hệ thống erp nhé, cái kia data bị miss"*. Vậy `578010406` (NPP) và `578005750` (HKD) là mã đúng; hai chuỗi trong tên thương hiệu app cũ là dữ liệu hỏng, **không dùng để đối chiếu**. Thành **QĐ-K**, kèm hệ quả: bảng tra khớp bằng **`id` thương hiệu**, không khớp bằng tên hay MST | Đã chốt |
| ~~H-10~~ | ~~Phòng ban hai bên lệch nhau (app cũ 22, ERP 18).~~ **ĐÓNG 16/09 — tạo đủ 8 phòng còn thiếu bên ERP, giữ nguyên tên app cũ.** Đại ca: *"có thể thêm phòng ban cho đủ với app cũ, cứ tạo như phòng ban trên app cũ, ví dụ như N2AGRO-KT thì để nguyên như vậy"*. Không gộp, không sửa tên. Thành **QĐ-L** | Đã chốt |
| ~~H-11~~ | ~~Luồng "Mua hàng" 2 cấp của app cũ.~~ **ĐÓNG 16/09 — bỏ khỏi phạm vi, nhưng phải kết xuất bản tổng hợp.** Đại ca: *"có thể bỏ luôn cái luồng mua hàng đó ra, nhưng đơn hoặc phiếu đó có thì tổng hợp lại giúp tôi là được... mình chỉ đồng bộ đặt xe, duyệt dấu, giao hàng thôi"*. Thành **QĐ-M** | Đã chốt |
| ~~H-02~~ | **ĐÃ TRẢ LỜI 15/09/2026: nạp lịch sử KHÔNG gửi thông báo.** Tắt cả chuông lẫn email trong suốt đợt nạp | — |
| ~~H-03~~ | **ĐÃ TRẢ LỜI 15/09/2026: nạp thử trên dev trước.** Chạy dev, soi kết quả, ổn rồi mới đẩy lên prod — cùng nếp "v1 trước rồi mới port" của repo | — |
| ~~H-04~~ | **ĐÃ TRẢ LỜI 15/09/2026.** Phiếu bắt buộc có công ty và phòng ban (đơn chạy tới giám đốc công ty đó). Không được để `0`; tra không ra thì gán Dego Holding. Thành QĐ-G. **Nhưng đẻ ra H-06 và H-07 bên dưới** | — |
| ~~H-06~~ | **ĐÃ TRẢ LỜI 15/09/2026: công ty mặc định là `id 1`** (mã `DEGO`). Lưu ý `tab_company` vẫn còn dòng trùng tên `id 16` mã `DEGO HOLDING` (ghi ở `modules/work/membership_service.py:80`) — **chưa dọn**, đẻ ra H-08 | — |
| ~~H-08~~ | **ĐÃ TRẢ LỜI 15/09/2026: tạm dùng `id 1`, dọn dòng trùng `id 16` sau** trong một đợt riêng. Trong lúc chờ, mã đồng bộ coi `1` và `16` là **cùng một công ty thật** khi so sánh và đếm đối chiếu | — |
| ~~H-07~~ | **ĐÃ TRẢ LỜI 15/09/2026 — không cần điền pháp nhân cho nhân sự.** Đại ca: *"nhân viên có công ty hay không thì có vấn đề gì đâu, nhân viên có thuộc phòng ban hoặc thương hiệu nào thì có"*. Đúng, vì **phiếu tự mang `brandId`** và thương hiệu khớp 11/11 với pháp nhân ERP → thành **nấc 0**, không phải suy luận từ hồ sơ người tạo nữa. Hồ sơ nhân sự thiếu `company_id` không còn chặn gì | — |
| ~~H-05~~ | **ĐÃ TRẢ LỜI 15/09/2026 — thương hiệu CHÍNH LÀ pháp nhân.** Màn quản trị app cũ gọi thẳng là "Quản lý Công ty", tên có kèm mã số thuế, và app cũ **không có collection `companies` nào khác**. Đối chiếu ra **11/11 khớp `tab_company`** (9 khớp bằng mã số thuế, 2 dòng Dr.Xanh khớp bằng tên). Xem [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.5–10.6 | — |

**Không còn câu hỏi nào chờ đại ca.** Cả 11 câu H-01…H-11 đã đóng, và câu H-12 mở ra rồi tự đóng ngay trong ngày 16/09 khi đối chiếu số đo với thiết kế sẵn có.

**Bốn thứ thiếu DỮ LIỆU đã ĐO XONG 16/09/2026** trên bản kết xuất toàn bộ Firebase. Chi tiết ở [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.8; tóm tắt:

| Thiếu gì | Kết quả đo |
|---|---|
| `id` của 11 thương hiệu | **Có đủ.** Bảng tra `brandId` → pháp nhân đã dựng, khớp bằng khóa Firebase đúng QĐ-K |
| `id` của 22 phòng ban | **Có đủ.** Kèm một phát hiện: khóa `dept_kinh_doanh` nay mang tên *"Pháp Lý"* — tên phòng ban đã từng bị đổi, khóa thì không. `legacy_id` là bắt buộc, không còn là lựa chọn |
| Tỷ lệ phiếu có `brandId` | **1 313/1 313 = 100%**, không tham chiếu chết nào. Nấc 0 của QĐ-G là đường chính; ba nấc dự phòng tụt xuống vai trò lưới an toàn cho phiếu mới |
| Số phiếu luồng "Mua hàng" | **0 phiếu.** Luồng `wf_purchase_01` có khai nhưng chưa ai từng dùng. **Nghĩa vụ kết xuất bản tổng hợp của QĐ-M tự tiêu** — không có gì để tổng hợp |

Đo xong thì đẻ ra **một câu hỏi mới, và nó nặng**:

| Mã | Câu hỏi | Ai trả lời |
|---|---|---|
| ~~H-12~~ | ~~Một phiếu thuộc nhiều pháp nhân thì ERP lưu thế nào?~~ **TỰ ĐÓNG TRONG NGÀY — không phải câu hỏi.** `brandId` là mảng và 123/1 313 phiếu thuộc 2..9 pháp nhân, nhưng ERP **đã có sẵn** bảng nối `tab_seal_request_company` và `core/scoping.py` lọc phạm vi phiếu dấu **theo bảng nối** chứ không theo cột → **121/123 ca không mất gì**. Còn đúng **2 phiếu giao hàng**, xử theo cách đã chốt từ trước (lấy phần tử đầu + cờ `multi_brand` vào sổ). Xem [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.9 | — |

Hai số đo phụ tự đóng hai câu kỹ thuật em định tự quyết: **`StopItem` phải có `notes`** (59 điểm dừng, 25 điểm có ghi chú thật) và **`driver.status` chỉ có đúng một giá trị `available`** nên ánh xạ kiểu gì cũng không mất dữ liệu.

---

## 10. Kết xuất Firebase — các bước đại ca làm

> **XONG 16/09/2026 (dev/prod hiện tại).** Đại ca đã kết xuất **toàn bộ** cơ sở dữ liệu `api-degoholding-com` thành một tệp 9,82 MB thay vì hai nhánh lẻ. Số đo rút ra nằm ở [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.8. Các bước dưới đây **giữ lại** vì còn phải kết xuất **lần nữa** ngay trước lúc chạy đợt nạp thật — bản 16/09 chỉ dùng để dựng bảng tra và đo phạm vi, không phải bản để nạp.

Chốt 16/09/2026: **đại ca tự bấm Export JSON trên Firebase Console.** Không cấp
service account cho ai, không viết script gọi API, không đưa mật khẩu cho ai.
Nút Export chỉ **tải về**, không ghi gì xuống cơ sở dữ liệu, nên đây cũng là
đường ít rủi ro nhất.

### 10.1. Hai nhánh nhỏ — làm ngay, gỡ chỗ chặn P0

| Bước | Làm gì |
|---|---|
| 1 | Mở `console.firebase.google.com`, chọn project **`api-degoholding-com`**. Đây là bản **prod**. Project `api-degoholding` là **dev** — lấy nhầm thì `id` không khớp dữ liệu thật |
| 2 | Menu trái → **Realtime Database** → tab **Data** |
| 3 | Trong cây dữ liệu bấm vào nhánh **`brands`** cho nó mở ra |
| 4 | Góc phải trên khung dữ liệu có nút **ba chấm dọc** → **Export JSON**. Trình duyệt tải về một tệp |
| 5 | Lặp lại bước 3–4 với nhánh **`departments`** |
| 6 | Chép hai tệp vào `D:\New folder\thuthapykien\_ketxuat\`, đổi tên thành `brands-YYYYMMDD.json` và `departments-YYYYMMDD.json` |

Hai nhánh này rất nhỏ — 11 và 22 dòng — nên tải về trong một giây.

### 10.2. Nhánh `requests` — làm sau, nặng hơn

Nhánh này chứa toàn bộ phiếu từ ngày mở app, chưa biết bao nhiêu. Nó chỉ cần cho
**hai con số đếm** (tỷ lệ điền `brandId` và số phiếu luồng Mua hàng), không chặn
P0. Nếu Console tải chậm hoặc lỗi thì còn đường khác nhẹ hơn: hỏi riêng danh sách
khóa bằng `?shallow=true` để đếm trước, rồi mới quyết có kéo cả nhánh về không.

### 10.3. Ba điều phải nhớ

**Cạnh nút Export JSON có nút Import JSON — nút đó GHI ĐÈ dữ liệu thật.** Trong
cả đợt này không ai có việc gì phải bấm vào nó.

**Tệp kết xuất là dữ liệu thật** — họ tên, email, số điện thoại nhân sự, nội dung
phiếu. Để ở `_ketxuat/` **ngoài kho mã nguồn**, không commit, xong việc thì xóa.
Lý do đầy đủ ghi trong `_ketxuat/DOC-FILE-NAY.md`.

**Ghi ngày vào tên tệp.** App cũ vẫn đang chạy, dữ liệu vẫn đổi. Bảng tra dựng từ
bản kết xuất ngày nào thì phải biết là ngày nào.

### 10.4. Có hai tệp rồi thì làm gì tiếp

1. Đối chiếu 11 `id` thương hiệu với `tab_company` → dựng **bảng tra cố định**,
   ghi thẳng vào [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.5. Khớp bằng
   `id`, không khớp bằng tên hay mã số thuế (QĐ-K).
2. Đối chiếu 22 phòng ban với 18 dòng `tab_department` → chốt danh sách **8 dòng
   phải tạo** kèm `legacy_id` từng dòng, rồi viết script tạo (QĐ-L, mục 10.7 của
   cùng tệp).
