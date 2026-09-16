# DANH SÁCH PHA — Đồng bộ app đặt xe cũ ↔ ERP

> Đi kèm [README.md](README.md), [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md), [doi-chieu-truong.md](doi-chieu-truong.md).
> Bản 1.0 — 15/09/2026. Tick tiến độ ở [TIEN-DO.md](TIEN-DO.md).

---

## Bản đồ chín pha

```
P0  Nền móng           ─┐
P1  Nạp lịch sử         │  bắt buộc theo thứ tự
P2  Chiều cũ → ERP      │
P3  Chiều ERP → cũ     ─┘
P4  Màn hình sổ        ─┐  làm được song song sau khi có P2
P5  Đối soát ban đêm   ─┘
P6  Tệp đính kèm       ─── độc lập, làm bất cứ lúc nào sau P1
P7  Phiếu đóng dấu     ─── cần P6 xong trước (phiếu dấu có tệp)
P8  Tắt app cũ         ─── chỉ khi có quyết định riêng
```

Ba quy tắc chung cho mọi pha:

- **Không đụng nhánh đang chạy.** Việc này làm trên nhánh riêng, cắt từ `erp-v2`.
- **Mọi pha đều có công tắc tắt.** Bật lên thấy sai thì tắt, không phải gỡ mã.
- **Xong một pha là dừng lại cho đại ca xem**, không chạy thẳng sang pha sau.

---

## P0 — Nền móng

**Mục tiêu:** dựng đủ chỗ chứa và chỗ ghi chép, nhưng **chưa bật gì cả**. Hết pha này hệ thống chạy y như cũ, không ai nhận ra có gì thay đổi.

**Việc bên ERP:**
1. Module mới `backend/app/modules/sync_log/` gồm model, schema, service, controller — bảng `tab_sync_log` theo mo-ta-ky-thuat mục 3.1.
2. Thêm model vào `app/core/all_models.py` (thiếu bước này là lệnh sinh migration không thấy bảng mới).
3. Thêm cột `legacy_id` vào bốn bảng: `tab_vehicle_booking`, `tab_seal_request`, `tab_vehicle`, `tab_driver`.
4. Thêm hai cột `source`, `external_id` vào `tab_file`.
5. Thêm entity `sync_log` vào `ENTITIES` (`core/permissions.py`) **và** vào `SCOPE_FIELDS` (`core/scoping.py`) với mốc `PUBLIC`; rà `_SYS_ENTITIES` trong `seed.py`.
6. Một migration Alembic gộp tất cả những thứ trên. Kiểm bằng `alembic heads` — phải ra đúng **một** head.
7. Khai các biến môi trường ở mo-ta-ky-thuat mục 13, `SYNC_DATXE_ENABLED` để **tắt**.
8. Hàm ký và hàm kiểm chữ ký dùng chung (mo-ta-ky-thuat mục 6).

**Việc bên app cũ:**
1. Thêm ba trường `updatedAt`, `erpId`, `syncStatus` vào bản ghi `requests`, `vehicles`, `drivers`.
2. Sửa **mọi** đường ghi để luôn cập nhật `updatedAt`. Chỗ ghi đều đi qua `fetchFirebaseDB` trong `src/utils/db.helpers.ts`, nên **đặt ở đó là gọn nhất** — nhưng phải rà lại để chắc không đường nào ghi tắt.
3. Khai `.indexOn: ["updatedAt"]` trong Rules của Realtime Database cho nhánh `requests`.
4. Nhánh `sync_logs` và màn hình quản trị xem sổ.
5. Khai hai biến bí mật `SYNC_ENABLED` (để **tắt**), `SYNC_SHARED_SECRET`.

**Xong khi:** migration chạy được cả lên lẫn xuống trên bản sao DB dev; tạo một phiếu bên app cũ thì thấy `updatedAt` nhảy; bài kiểm cho hàm ký chạy xanh; **và không có hành vi nào của hai hệ thay đổi**.

**Rủi ro:**
- Quên khai `SCOPE_FIELDS` → chặn sạch mọi truy cập, có bài kiểm bắt đỏ. Đây là lỗi lặp đi lặp lại của repo.
- Vai trò đang chạy không tự có khóa quyền mới — phải tick tay ở màn Phân quyền sau khi lên.
- Cột `legacy_id` unique: MySQL không cho nhiều dòng chuỗi rỗng. Chốt cách xử lý **trước khi** viết migration (mo-ta-ky-thuat mục 2.1).

---

## P1 — Nạp lịch sử một lần

**Mục tiêu:** đổ toàn bộ dữ liệu đang có bên app cũ sang ERP, **một chiều**, chạy tay, có bản thử trước.

**Việc:**
1. Script `backend/scripts/import_datxe.py`, theo khuôn các script sẵn có (`import_ncc.py`, `import_legacy_data.py`).
2. Bắt buộc có cờ `--dry-run`: đọc, dịch, in ra sẽ tạo bao nhiêu, sửa bao nhiêu, vướng bao nhiêu — **không ghi gì**.
3. Bắt buộc có cờ `--entity` để chạy từng nhóm: `vehicle`, `driver`, `booking`, `seal`.
4. Thứ tự chạy **không được đảo**: xe → tài xế → bảng tra người dùng → phiếu.
5. Xuất một tệp CSV liệt kê mọi chỗ vướng: không tra ra người, không tra ra phòng ban, xe trống biển số, chuỗi bị cắt vì quá dài, trạng thái lạ.
6. Chạy được **nhiều lần**: lần hai chỉ cập nhật chứ không đẻ thêm (nhờ `legacy_id`).
7. **Tắt thông báo và tắt email** trong lúc nạp — câu hỏi H-02.

**Trình tự thật:**
- chạy `--dry-run` trên dev, đọc CSV vướng, sửa dữ liệu hoặc sửa quy tắc dịch;
- chạy thật trên dev, đối chiếu vài chục phiếu bằng mắt;
- sao lưu DB prod;
- chạy `--dry-run` trên prod, đọc lại CSV;
- chạy thật trên prod.

**Xong khi:** số phiếu mỗi bên khớp theo từng tháng và từng trạng thái; 20 phiếu lấy ngẫu nhiên soi bằng mắt thấy đúng; CSV vướng đã được xem hết và mỗi dòng đều có kết luận (sửa, hoặc chấp nhận).

**Rủi ro:**
- Dữ liệu thật có khóa mà định nghĩa kiểu không khai (đã bắt được ca `itemWeight`) → **phải đọc dữ liệu thật trước khi viết mã dịch**, xem doi-chieu-truong mục 4.
- Chạy nhầm trên prod khi chưa sao lưu.
- Bộ sinh mã phiếu: nạp vài nghìn phiếu cùng lúc mà mỗi lần lại quét tìm số lớn nhất thì rất chậm — cấp trước một dải mã trong bộ nhớ.

---

## P2 — Chiều app cũ → ERP

**Mục tiêu:** phiếu tạo hoặc sửa bên app cũ tự sang ERP trong vài giây.

**Việc bên ERP:**
1. Đường nhận `POST /api/sync/datxe/events` — kiểm chữ ký, ghi dòng sổ *chờ*, xử, cập nhật sổ, trả lời.
2. Tra `event_id` để không xử trùng; tra `legacy_id` để không đẻ phiếu trùng.
3. Quy tắc nhận ở mo-ta-ky-thuat mục 9 — **đặc biệt là điểm 4**: chỉ ghi đè những ô app cũ làm chủ.
4. Viết danh sách "trường app cũ làm chủ" thành **một hằng số duy nhất**, mọi chỗ dùng chung.

**Việc bên app cũ:**
1. Sau khi ghi `requests` thành công thì gọi sang ERP — đặt ở tầng service, phía trên `requests.db.ts`.
2. Gọi hỏng thì **không làm hỏng việc của người dùng**: vẫn trả về thành công cho họ, chỉ ghi dòng sổ *lỗi*.
3. Nhận `erpId` trả về thì ghi ngược vào bản ghi.
4. Cờ chặn: lượt ghi đến từ đường `/sync/erp-events` thì **không bắn chuông**.

**Xong khi:** trên dev, tạo một phiếu xe bên app cũ thì trong 5 giây thấy nó bên ERP đúng nội dung; sửa phiếu thì nội dung đổi theo mà **trạng thái ERP không bị đổi**; tắt ERP rồi tạo phiếu thì app cũ vẫn tạo được và sổ có dòng lỗi.

**Rủi ro:**
- Ghi đè mất việc điều phối viên vừa làm — đây là lỗi nặng nhất của cả dự án. Phải có bài kiểm riêng cho nó.
- Dữ liệu từ bên ngoài không có gì bảo đảm ngắn: mọi trường chuỗi phải khai trần độ dài ở tầng schema, không trông chờ DB. Bài kiểm chạy trên SQLite **không bắt được** lỗi này.

---

## P3 — Chiều ERP → app cũ

**Mục tiêu:** duyệt hoặc điều phối bên ERP thì người dùng bên app cũ thấy ngay.

**Việc bên ERP:**
1. Chỗ phát tín hiệu: sau khi đổi trạng thái, duyệt, từ chối, trả về, gán xe/tài xế, tài xế đổi trạng thái, nhập km/chi phí.
2. **Không gọi HTTP ngay trong lượt của người dùng.** Ghi dòng sổ *chờ*, Celery đẩy đi sau.
3. Chỉ phát cho phiếu **có `legacy_id`** — phiếu tự tạo trên ERP không bắn sang.
4. Gói dữ liệu gửi kèm **tên xe, biển số, tên tài xế, SĐT dạng chữ** — để app cũ không phải tra danh mục.
5. Biến ngữ cảnh `sync_in_progress`: đang xử lệnh của app cũ thì không phát ngược.

**Việc bên app cũ:**
1. Đường nhận `POST /api/v1/sync/erp-events`, kiểm chữ ký.
2. Ghi xuống `requests` kèm cờ "đến từ ERP" để không bắn chuông ngược.
3. Màn hình hiển thị thông tin xe/tài xế lấy từ chữ nhận về.

**Xong khi:** trên dev, duyệt một phiếu bên ERP thì app cũ đổi trạng thái trong 30 giây; gán xe thì app cũ hiện đúng biển số và tên tài xế; **và sổ không phình lên** — mỗi lần đổi chỉ sinh đúng một dòng ở mỗi bên.

**Rủi ro:**
- **Vòng lặp vô hạn.** Đặt van chặn: một phiếu sinh quá 20 dòng sổ trong một giờ thì tự dừng và cảnh báo.
- Celery: deploy backend phải dựng lại cả `celery-worker` và `celery-beat`, không chỉ `api`.
- App cũ chết thì dòng sổ dồn lại — phải xem được và chạy lại được hàng loạt.

---

## P4 — Màn hình sổ đồng bộ

**Mục tiêu:** có chỗ nhìn, không phải mở DB lên soi.

**Việc:** màn `/system/sync-log` trong `frontend-v2` theo mo-ta-ky-thuat mục 12 — danh sách lọc được, xem chi tiết nguyên cục JSON và nguyên văn lỗi, nút chạy lại, thẻ đếm, bộ lọc "chưa gắn được người".

Thêm một cảnh báo hằng ngày: sáng 08:00 nếu có dòng lỗi quá 24 giờ chưa ai đụng thì bắn thông báo cho nhóm quản trị.

**Xong khi:** một dòng lỗi cố ý tạo ra hiện đúng trên màn; bấm chạy lại thì nó chuyển sang thành công mà không đẻ phiếu trùng.

**Rủi ro:**
- Cột `payload` chứa cả cục JSON — danh sách **không được** trả cột này về, kẻo tải nặng. Chỉ trả khi xem chi tiết.
- Nút chạy lại là quyền ghi, không phải quyền đọc.

---

## P5 — Đối soát ban đêm

**Mục tiêu:** cái lưới hứng những gì chuông làm rơi.

**Việc:** ba việc chạy nền ở mo-ta-ky-thuat mục 11 — quét theo `updatedAt`, đếm đối chiếu, gọi lại việc hỏng. Mỗi đêm ghi một dòng tổng kết.

**Xong khi:** cố ý tắt chuông bên app cũ, tạo ba phiếu, chạy tay việc đối soát → ba phiếu đó xuất hiện bên ERP và sổ ghi rõ là "vá bởi đối soát".

**Rủi ro:**
- Pha này **phụ thuộc hoàn toàn** vào `updatedAt` của P0. Nếu còn đường ghi nào bỏ sót `updatedAt` thì đối soát mù ở đúng chỗ đó.
- Quên khai `.indexOn` → mỗi đêm kéo về cả cây dữ liệu.
- Quét xong đừng bắn thông báo cho người dùng, giống P1.

---

## P6 — Tệp đính kèm dạng liên kết

**Mục tiêu:** người ERP mở được tệp đang nằm bên app cũ, không cần biết nó ở đâu.

**Việc bên app cũ:** đường `GET /api/v1/sync/files/{id}/url` cấp đường dẫn mới cho ERP, xác thực bằng chữ ký như các đường khác.

**Việc bên ERP:** nạp `tab_file` + `tab_file_link` theo doi-chieu-truong mục 8; đường tải xuống thấy `source = "datxe"` thì xin đường dẫn mới hoặc kéo nội dung về trả thẳng cho trình duyệt.

**Xong khi:** bấm xem một tệp cũ trên ERP thì mở được; **để qua hôm sau bấm lại vẫn mở được** (đây mới là phép thử thật — nó bắt lỗi lưu đường dẫn hết hạn).

**Rủi ro:**
- Lưu nhầm đường dẫn ký sẵn vào cột `url` → hôm sau hỏng hàng loạt và rất khó lần ra.
- Phân quyền: ai xem được phiếu thì xem được tệp của phiếu. Đừng để đường tải xuống hở — sổ lỗi bảo mật của repo đã có sẵn một ca đúng kiểu này ở khâu tệp.
- Ngày tắt app cũ là ngày mọi tệp này chết. Ghi vào lịch, đừng để quên.

---

## P7 — Phiếu đóng dấu

**Mục tiêu:** đưa phiếu đóng dấu vào cuộc, sau khi phiếu xe đã chạy êm.

**Việc trước khi viết mã** (bắt buộc):
1. Mở dữ liệu thật, đếm xem trong các phiếu dấu đang có: bao nhiêu phiếu dùng `isSkipApproval`, bao nhiêu dùng `skipApprovalToLevel`, bao nhiêu có `brandId`, bao nhiêu đang ở `sealed` và bao nhiêu ở `delivered_to_staff`.
2. Nạp danh mục loại dấu và dựng bảng tra.

**Việc mở nấc bàn giao hồ sơ (QĐ-H)** — làm trước, vì nó đụng vào ERP:
1. Thêm `SEAL_DELIVERED = 8` và nhãn "Đã trả hồ sơ" vào `seal_request/model.py`;
2. Thêm hai cột `delivered_at`, `delivered_by`, kèm migration;
3. Thêm hành động "Bàn giao hồ sơ" cho văn thư, chỉ bấm được từ `SEAL_COMPLETED`;
4. **Rà hết chỗ đang coi `SEAL_COMPLETED` là trạng thái cuối** — báo cáo, bộ lọc, thống kê, luồng duyệt. Giờ nó không còn là cuối. Đổi sang so với một bộ trạng thái kết thúc, đừng so một số.

**Việc chính:** nạp lịch sử phiếu dấu; chiều cũ → ERP; chiều ERP → cũ.

**Xong khi:** tạo phiếu dấu bên app cũ thì sang ERP đủ nội dung và **kèm tệp đính kèm mở được**; văn thư đóng dấu bên ERP thì app cũ đổi trạng thái theo.

**Rủi ro:**
- Điểm 4 của QĐ-H là chỗ **dễ sót nhất cả pha**: mọi chỗ hỏi "phiếu xong chưa" bằng `status == SEAL_COMPLETED` sẽ bỏ sót phiếu đã trả hồ sơ. Phải tìm bằng tìm kiếm toàn mã nguồn, không dựa trí nhớ.
- ERP phải bịa tiêu đề và số bản. Dữ liệu bịa trông như dữ liệu thật — ghi cờ `title_generated` vào sổ để sau lọc ra được.
- Pháp nhân: phiếu dấu bên ERP lọc phạm vi theo **bảng nối công ty**. Nạp thiếu dòng bảng nối thì phiếu tàng hình với văn thư.

---

## P8 — Chép tệp thật và tắt app cũ

**VIỆC CHẮC CHẮN PHẢI LÀM** — QĐ-J đã chốt đích đến là tắt app cũ, nên pha này nằm trên đường đi, chỉ là chưa tới lượt. *(Bản trước ghi "chỉ làm khi có quyết định riêng" — đã hết hiệu lực 15/09.)*

**Việc:**
1. Đọc `tab_file` lọc `source = "datxe"`, tải nội dung về, đẩy lên kho R2 của ERP, ghi lại `file_key`, tính `sha256`, dựng ảnh thu nhỏ, xóa cờ `source`.
2. Đối chiếu số tệp và tổng dung lượng hai bên.
3. Chuyển người dùng sang tạo phiếu trên ERP.
4. Tắt chuông hai chiều, đóng băng app cũ ở chế độ chỉ đọc một thời gian, rồi mới tắt hẳn.
5. Giữ một bản kết xuất toàn bộ Realtime Database làm bằng chứng lưu trữ.
6. ~~Giao bản tổng hợp phiếu luồng "Mua hàng" (QĐ-M).~~ **BỎ 16/09/2026 — đo ra 0 phiếu.** Luồng `wf_purchase_01` có khai trong `approval_workflows` nhưng chưa ai từng nộp phiếu nào qua nó. Không có gì để kết xuất. Xem [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.8, C-1.

**Xong khi:** không còn dòng nào trong `tab_file` mang `source = "datxe"`; mở ngẫu nhiên 20 tệp cũ trên ERP đều tải về được **sau khi app cũ đã tắt**.

**Rủi ro:** làm sai bước là mất tệp vĩnh viễn. Bước 5 là chốt chặn cuối, không được bỏ — và nay nó **gánh luôn vai của bước 6 đã bỏ**: bản kết xuất lưu trữ chính là bản sao cuối cùng của mọi thứ không đồng bộ sang ERP.

---

## Việc phải làm trước khi bắt tay vào P0

| Việc | Vì sao |
|---|---|
| ~~Trả lời các câu hỏi còn treo ở README mục 9~~ | **XONG 16/09 — cả 11 câu H-01…H-11 đã đóng**, không còn gì chờ đại ca |
| ~~Kết xuất Firebase một lượt~~ **XONG 16/09/2026** | Đại ca kết xuất **toàn bộ** cơ sở dữ liệu (9,82 MB, 13 nhánh). Cả bốn số đo đã có, ghi ở [doi-chieu-truong.md](doi-chieu-truong.md) mục 10.8. Còn phải kết xuất **lần nữa** ngay trước đợt nạp thật |
| **Chạy script tạo 8 phòng ban bên ERP** (QĐ-L) | Tên chép nguyên văn app cũ, `company_id = 0`, mang `legacy_id`. Dev trước prod sau. Không gõ tay |
| **H-06: chốt Dego Holding là `id 1` hay `id 16`** | `tab_company` có hai dòng trùng tên. Chọn sai là hàng nghìn phiếu gắn nhầm pháp nhân |
| **H-07: có điền pháp nhân trước khi nạp lịch sử không** | Đo thật 15/09: 237/262 nhân sự **và 0/18 phòng ban** đang để `0` → hôm nay **cả nấc 1 lẫn nấc 2 đều trượt**, 100% phiếu rơi xuống mặc định. Đề xuất điền `company_id` cho 18 phòng ban (hứng 241/262 người) |
| Chốt cách xử `legacy_id` unique (NULL hay index thường) | chặn migration của P0 |
| Chốt có thêm trường `notes` vào `StopItem` không | chặn quy tắc dịch của P1 |
| Chốt `on_leave` của tài xế đổi thành gì bên ERP | chặn P1 nhóm tài xế |
| Lấy được **số lượng thật**: bao nhiêu phiếu mỗi loại, bao nhiêu xe, tài xế, tệp, tổng dung lượng R2 | quyết định P1 chạy bao lâu và P8 nặng cỡ nào |
| Kết xuất một bản dữ liệu thật để soi cấu trúc | đã chứng minh là cần — định nghĩa kiểu của app cũ không đầy đủ |
