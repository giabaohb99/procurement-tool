# Phase 03 — Thu sự kiện giao diện (backend), `read_at`, dọn 90 ngày

**Ưu tiên:** P1 · **Effort:** 4h · **Phụ thuộc:** 01 · **Trạng thái:** pending

## Ngữ cảnh
- `core/logging_policy.py`: `SKIP_PATH_PREFIXES` áp MỌI method (khác `SKIP_GET_PREFIXES` chỉ GET) → chỗ đúng để loại đường telemetry.
- `core/limiter.py`: KHÔNG có giới hạn toàn cục; khóa theo IP thật — cả văn phòng chung NAT nên giới hạn theo IP là chặn nhầm.
- FE gửi `Authorization: Bearer` (token-storage), **không có cookie phiên** → `navigator.sendBeacon` KHÔNG mang được token.
  ⇒ Quyết định: FE dùng `fetch(..., {keepalive: true})` (cùng cơ chế sống-sót-khi-rời-trang như beacon, gửi được header). Ghi rõ lệch so với chốt "sendBeacon".
- Mẫu dọn theo lô: `request_log/tasks.py` (lô 2.000, trần 500 lô, cảnh báo khi chạm trần).
- Thông báo: `notification/controller.py` dòng ~69 (đánh dấu 1) và ~77 (đánh dấu tất cả).

## Hợp đồng API
`POST /api/telemetry/ui-events` — mọi người đã đăng nhập (`get_current_user`), không `require(entity)`.
```json
{"events": [{"type": 1, "route": "/procurement/purchase-orders/:id", "form": 0, "duration_ms": 0,
             "result_count": null, "age_ms": 1200, "tab_key": 81723, "error": null}]}
```
- Pydantic: `events` 1..100; `type` ∈ `UiEventType`; `form` ∈ `UiForm ∪ {0}`; `route` ≤ 120, khớp `^/[A-Za-z0-9/_:\-.]*$`;
  `duration_ms` 0..86.400.000; `result_count` 0..1.000.000; `age_ms` 0..600.000 (quá thì kẹp); `tab_key` 0..2^31−1;
  `error` chỉ khi type=7: `name` ≤ 60, `message` ≤ 200. Mọi `str` có `max_length` (luật `backend-input-limits`).
- Thân > 64 KB (Content-Length) → 413 trước khi parse.
- Server **chuẩn hóa lại** route (số/uuid → `:id`, bỏ `?…`/`#…`) — FE lỗi cũng không lọt id.
- Công tắc tắt → `success({"accepted": 0})`, không ghi. Bật → MỘT câu `INSERT` nhiều dòng, trả `{"accepted": n}`.
- `session_id`: lấy từ `request_context` nếu middleware vẫn đặt khi bỏ ghi log; nếu không → từ claim `jti` (`tab_login_session.token_id`) — 1 truy vấn. Implementer kiểm middleware trước.
- Giới hạn tần suất: `@limiter.limit("30/minute", key_func=<user id từ JWT sub, fallback IP>)` — FE gửi ≤ 2 lô/phút/tab.

`/api/auth/me` thêm `"usage_tracking": bool` (đọc `app_settings.get("usage_tracking_enabled")`) — FE bật/tắt bộ thu.

## Tệp
- Tạo: `usage_profile/telemetry_schema.py`, `telemetry_service.py` (chuẩn hóa + insert), `telemetry_controller.py`, `tasks_cleanup.py`
- Sửa: `core/logging_policy.py` (+ `"/api/telemetry"` vào `SKIP_PATH_PREFIXES`, chú thích lý do NT-5 kiểu "mỗi lô đẻ 1 dòng nhật ký"),
  `notification/controller.py` (set `read_at` khi chuyển chưa-đọc → đã-đọc; mark-all `update({"is_read": True, "read_at": now})` chỉ trên dòng chưa đọc),
  `auth/controller.py` (`_me_payload` thêm `usage_tracking`), `main.py` (đăng ký router telemetry)
- Test: `test/backend/test_ho_so_lam_viec_thu_su_kien_cr641.py`, `test_ho_so_lam_viec_doc_thong_bao_cr641.py`, `test_ho_so_lam_viec_don_su_kien_cr641.py`

## Dọn 90 ngày (`usage.cleanup_ui_events`)
- Xóa `occurred_at < now − 90 ngày` theo lô 2.000 id, trần 500 lô, chạm trần → `log.warning`.
- **Không** chờ R2 như request_log: đây là dữ liệu đo dùng để gom, không phải chứng cứ; bản bền là `tab_usage_daily`.
  Ghi lý do khác biệt này trong docstring.
- `dry_run=True` chỉ đếm.

## Các bước
1. Schema + service; chuẩn hóa route dùng `usage_profile/route_pattern.normalize_route` (phase 01 tạo, 02 và 03 cùng dùng).
2. Controller + limiter + kiểm 413.
3. Logging policy + test.
4. read_at + test.
5. Cleanup task + test.
6. `/auth/me` thêm cờ.

## Todo
- [ ] telemetry_schema / service / controller
- [ ] logging_policy loại /api/telemetry
- [ ] read_at ở 2 đường đánh dấu đọc
- [ ] tasks_cleanup + test lô
- [ ] usage_tracking trong /auth/me

## Kiểm
- Chưa đăng nhập → 401. Công tắc tắt → accepted 0, bảng rỗng.
- 101 sự kiện / route 121 ký tự / type 99 / `error.message` 201 ký tự → 422 ở tầng SCHEMA (`pytest.raises(ValidationError)`, vì SQLite không ép VARCHAR).
- `/x/123/y/550e8400-e29b-41d4-a716-446655440000?q=nguyen` → `/x/:id/y/:id`.
- `age_ms=10_000_000` → occurred_at = now − 10 phút.
- 50 sự kiện → đúng 1 câu INSERT (đếm truy vấn).
- `should_log_request("POST", "/api/telemetry/ui-events") is False`; `("POST", "/api/notifications/1")` vẫn True.
- read_at: đọc lần 2 không ghi đè mốc; mark-all không đụng dòng đã đọc.
- Cleanup: 3 dòng 91 ngày + 2 dòng 10 ngày → xóa 3, còn 2; batch size 2 → 2 lô.
Chạy: `docker compose exec -T api python -m pytest test/backend/test_ho_so_lam_viec_thu_su_kien_cr641.py test/backend/test_ho_so_lam_viec_doc_thong_bao_cr641.py test/backend/test_ho_so_lam_viec_don_su_kien_cr641.py -q`

## Rủi ro
| Rủi ro | K × T | Giảm thiểu |
|---|---|---|
| Ghi kép vào request_log | Cao nếu quên × Trung bình | prefix trong SKIP_PATH_PREFIXES + test |
| Tải ghi: ~100 người × 2 lô/phút | Thấp × Thấp | 1 INSERT/lô, ~10k dòng/ngày ≈ 900k dòng/90 ngày; 2 chỉ mục |
| Lộ dữ liệu cá nhân qua thông điệp lỗi JS | Trung bình × Trung bình | trần 200 ký tự, chỉ name+message, không stack; FE bỏ chuỗi số dài |
| Token hết hạn lúc gửi lô cuối | Trung bình × Thấp | chấp nhận mất lô; FE giữ lại lô khi 401 và gửi ở nhịp sau |

## Bảo mật
Người dùng chỉ ghi được sự kiện của CHÍNH mình (user_id lấy từ token, không nhận từ body). Không nhận `user_id`, `occurred_at`, `session_id` từ client.
