# P3 — Chiều ERP → app đặt xe cũ (bản dựng)

> Bản 1.0 — 05/10/2026, bao-CR-596. Đi kèm [mo-ta-ky-thuat.md](mo-ta-ky-thuat.md) §5.2, §7, §15.
> Tệp này ghi những gì **thực sự dựng**, và chỗ nào lệch bản vẽ gốc thì nói rõ vì sao.

## 1. Đại ca chốt ngày 05/10/2026

| # | Chốt |
|---|---|
| 1 | Làm **đủ** P3: gửi sang kết cục duyệt, điều phối, trạng thái tài xế, km/chi phí, đóng dấu |
| 2 | Phiếu **tạo trên ERP cũng phải hiện bên app cũ** — lệch bản vẽ gốc (gốc: "phiếu ERP tự tạo không bắn sang") |
| 3 | Mã viết xong nhưng **khóa bằng công tắc**, mặc định tắt. Chưa triển khai, không có hạn |
| 4 | **Không** gửi thông báo từ phía ERP cho người dùng app cũ — họ nhận thông báo của app cũ như cũ |
| 5 | Chưa làm «Bước 0» (chặn chiều nhận ghi đè kết quả ERP) — làm sau khi mã đồng bộ xong |
| 6 | Tài xế dùng app cũ lâu dài; khi chuyển hẳn thì vẫn hai chiều, quy định thao tác ở app nào |

## 2. Hình dạng

```
ERP: người dùng bấm (duyệt / điều phối / tài xế / km / đóng dấu / tạo phiếu)
  │  bộ nghe ORM gom id phiếu đã đổi (before_flush), bỏ qua khi đang xử tín hiệu NHẬN về
  ▼  after_commit: công tắc bật? → giao Celery `legacy_datxe.push_outbound`
Celery: đọc phiếu HIỆN TẠI → dựng ẢNH CHỤP → băm → trùng lần gửi thành công trước thì bỏ
  │  ghi sổ (OUTBOUND, chờ) → ký HMAC → POST {base}/v1/sync/erp-events
  ▼  2xx: phiếu mới thì ghi `legacy_id` app cũ trả về (trong suppress_outbound) → sổ thành công
Worker app cũ: kiểm chữ ký + công tắc nhận → ghi Firebase bằng quyền tài khoản dịch vụ
     • phiếu đã có: đặt trạng thái, một mục lịch sử «Xử lý trên ERP», điều phối, km/chi phí
     • phiếu chưa có: tạo bản ghi mới (chống trùng qua nhánh `erpRefs`), trả khóa mới
     • KHÔNG bắn chuông/email, KHÔNG gọi ngược sang ERP, KHÔNG đóng dấu `updatedAt`
```

**Vì sao gửi ẢNH CHỤP chứ không gửi từng thao tác.** Gửi lại bao nhiêu lần cũng ra cùng kết quả,
tới lệch thứ tự cũng không hỏng (cú tới sau vẫn mang trạng thái mới nhất lúc gửi), và một lần
bấm sinh ba lần flush cũng chỉ ra một lần gửi.

**Vì sao nghe ở tầng ORM.** Cùng lý do `core/change_tracker.py`: cắm tay ở từng service là hơn
chục chỗ (duyệt, trả về, từ chối, hủy, điều phối, tài xế bốn nút, km/chi phí, đóng dấu, tạo,
sửa), chỗ nào sót thì im lặng.

## 3. Công tắc

| Phía | Khóa | Mặc định | Ý |
|---|---|---|---|
| ERP | `sync_datxe_outbound_enabled` (`SYNC_DATXE_OUTBOUND_ENABLED`) | tắt | Tắt = bộ nghe không giao việc, không ghi sổ, không gửi |
| ERP | `sync_datxe_enabled` (đã có) | — | Cầu dao tổng: tắt là ngắt cả hai chiều |
| App cũ | `ERP_INBOUND_ENABLED` (biến thường, `wrangler.jsonc`) | `"false"` | Khác `"true"` thì đường nhận trả 503 |

## 4. Hợp đồng

`POST {sync_legacy_api_base}/v1/sync/erp-events` — **không có tiền tố `/api`**: Worker phục vụ
đường ở gốc tên miền (`dev-api.degoholding.vn/v1/...`). Header như chiều nhận
(`X-Sync-Source: erp`, `X-Sync-Timestamp`, `X-Sync-Signature`), chữ ký
`HMAC-SHA256(secret, "<ts>.<path>.<body>")`, `path` = `/v1/sync/erp-events`. Đường này đứng
**trước** `withAppCheck` (máy gọi máy, không có App Check).

Thân (`schema: 1`):

```json
{
  "schema": 1, "event_id": "datxe.vehicle_booking.<legacy>.2.<rand>",
  "occurred_at": 1759650000000,
  "entity": "vehicle_booking", "erp_id": 123, "erp_code": "DX000123", "legacy_id": "-Oabc...",
  "data": {
    "type": "CAR_BOOKING", "status": "dispatched",
    "created_by_uid": "<uid app cũ hoặc rỗng>", "created_at": 1759600000000,
    "requester": {"name": "...", "email": "...", "phone": "..."},
    "details": { "...các ô theo đúng tên trường app cũ (doi-chieu-truong.md)..." },
    "approval": {"outcome": "approved", "by_name": "...", "by_email": "...", "at": 1759610000000},
    "dispatch": {"assignedVehicleId": "<khóa app cũ>", "assignedDriverId": "<khóa app cũ>",
                 "vehicle": {"license_plate": "...", "model": "...", "type": "..."},
                 "driver": {"name": "...", "phone": "..."},
                 "dispatchedAt": 0, "dispatchedByName": "...", "driverStatus": "accepted",
                 "actualStartTime": 0, "actualEndTime": 0, "distanceKm": 0, "cost": 0},
    "seal": {"completed_at": 0, "completed_by_name": "..."}
  }
}
```

Trả về phong bì `{success, data: {legacy_id, status}}`. ERP chỉ ghi `legacy_id` khi nó khác rỗng.

## 5. Ánh xạ

- Trạng thái: **đúng bảng ngược của chiều nhận** (`builder.*_STATUS_FROM_LEGACY`), để một trạng
  thái đi sang rồi đồng bộ về vẫn ra y như cũ. `BK_DRAFT`/`SEAL_DRAFT` không gửi.
  Phiếu dấu: `SEAL_APPROVED → fully_approved`, `SEAL_COMPLETED → completed` (app cũ thật sự
  dùng `completed` khi duyệt xong — `approval.service.ts:243`; `sealed`/`delivered_to_staff`
  có trong mã nhưng luồng thực tế không đi qua).
- Người / phòng ban / công ty / xe / tài xế: ngược cột `legacy_id` (và `USER_MANUAL_MAP` cho người).
  Không có khóa app cũ thì gửi rỗng kèm CHỮ (tên, biển số…) để app cũ vẫn hiển thị.
- Giờ: `start_time`/`end_time` là giờ Việt Nam; mốc do máy chủ đóng (`approved_at`,
  `dispatched_at`, `actual_*`, `completed_at`) là UTC — đổi sang mili giây đúng múi.

## 6. Chống lặp

1. ERP: đang xử tín hiệu NHẬN về (`suppress_outbound`) thì bộ nghe không gom.
2. ERP: băm ảnh chụp; trùng lần gửi thành công gần nhất thì bỏ, không ghi sổ.
3. ERP: van — một phiếu quá 20 dòng sổ gửi đi trong một giờ thì dừng, ghi dòng lỗi.
4. App cũ: đường nhận ghi thẳng tầng DB, không qua service có móc `pushRequestToErp`, không
   đóng dấu `updatedAt` (ERP không cần thấy lại thứ chính nó vừa gửi).

## 7. Còn để sau (ghi nhận)

- «Bước 0»: chiều nhận đang ghi đè hết (`builder.copy_legacy_fields`, `full_sweep` chạy `force`).
  Trước khi cho ai thao tác thật trên ERP với phiếu đồng bộ phải làm.
- Tệp đính kèm của phiếu dấu tạo trên ERP chưa sang app cũ (app cũ chỉ thấy ghi chú «xem tệp trên ERP»).
- `SEAL_DELIVERED` (QĐ-H) chưa làm — luồng thật của app cũ không dùng tới.
- Hiển thị km/chi phí trên giao diện app cũ (`degoholding-app-frontend`): dữ liệu đã nằm trong
  `details.dispatch`, màn hình chưa vẽ.

## 8. Chạy thử trên dev — 05/10/2026

Đẩy app cũ lên nhánh `dev` (Worker dev tự deploy), bật tạm hai công tắc, chạy 6 tình huống rồi đọc thẳng Firebase dev:

| # | Tình huống | Kết quả |
|---|---|---|
| 1 | Phiếu xe từ app cũ: duyệt → điều phối → tài xế nhận → hoàn thành + km/chi phí | Đúng trạng thái, khóa xe/tài xế, chữ, km, chi phí; mỗi bước một dòng lịch sử; nội dung người tạo giữ nguyên |
| 2 | Phiếu xe tạo trên ERP: tạo → duyệt → điều phối → hoàn thành | App cũ tạo `erp_vb_936`, ERP ghi ngược khóa |
| 3 | Phiếu dấu tạo trên ERP: tạo → duyệt → đóng dấu | App cũ tạo `erp_sr_869`, công ty → `brandId` đúng |
| 4 | Phiếu dấu từ app cũ: duyệt → đóng dấu | Đúng |
| 5 | Trả về sửa | `needs_correction` + một dòng lịch sử |
| 6 | Từ chối | `rejected` + một dòng lịch sử |

17 lượt gửi đều thành công, mỗi phiếu tối đa 4 lượt, chiều nhận không kéo ngược (2 dòng «bỏ qua»), không vòng lặp.
Lỗi bắt được và đã vá: «đã điều phối» → «hoàn thành» từng ghi thêm dòng «approved» thừa (đường nhận nay chỉ ghi khi
kết cục đổi). Thử xong đã TẮT cả hai công tắc. Kho Firebase dev khác prod nên khóa tài xế trên dev (tra theo bảng gán
tay của prod) có thể không trỏ vào tài xế có thật bên dev — đường ống đúng, dữ liệu danh mục thì prod mới chứng minh được.
