# TIẾN ĐỘ — Công cụ Import (Khảo sát + Đơn mua hàng)

Nhánh làm việc: **`import-tool`** (off `bao`). Cập nhật ô trạng thái khi xong.
Ký hiệu: `[ ]` chưa làm · `[~]` đang làm · `[x]` xong.

## Chạy local để test
```bash
# Bật hạ tầng nền (Redis + Worker). Beat KHÔNG cần (import chạy on-demand).
docker compose up -d redis celery-worker
# (tuỳ chọn) xem hàng đợi:  docker compose up -d redisinsight   -> http://localhost:5540
# Test worker sống:
docker compose exec celery-worker python -c "from app.tasks.debug import ping; print(ping.delay().get(timeout=15))"
# Web: http://localhost:8080  ·  API: http://localhost:8000/docs
```

---

## PHA 0 — Hạ tầng Import (dùng chung)
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Merge Celery (redis/worker/beat) vào `bao` | đã cherry-pick |
| [x] | Model `import_batch` + `import_log` (+ IntEnum level/status/module/mode) | module `import_tool`, verify ORM OK |
| [x] | Migration 2 bảng | `2bad028f037a` — đã dọn drift, apply local OK |
| [x] | Lưu file .xlsx qua StoredFile (`file_id`) | service.save_upload |
| [x] | API upload + tạo batch + đẩy Celery task (trả `batch_id` ngay) | controller + router `/api/imports` |
| [~] | Trang **Quản lý Import**: list (tên file text) + chi tiết (tải file + tab log) | đang làm FE |
| [x] | Chuông báo khi worker xong -> link `/import-batches/{id}` | task `_notify` |

## PHA 1 — Import KHẢO SÁT
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Parser openpyxl sheet 3+4 (header dòng 5) + chuẩn hoá ngày/số/text | survey_import.py |
| [x] | Resolve NCC: SP->tên viết tắt, NCC->MST; xung đột->text-only+log | mst_conflict/ncc_text_only |
| [x] | Upsert Supplier (tạo mới / điền field trống) | _upsert_supplier |
| [x] | Gom (Phân loại + NCC) -> upsert Survey + supplier_lines + product_lines | import_key idempotent |
| [x] | Celery task `import_survey` (dry-run + apply) + ghi import_log | dùng chung run_import |
| [~] | Nút "Import Excel" ở trang Phiếu khảo sát (dry-run -> xác nhận) | đang làm FE |
| [x] | Test end-to-end với file mẫu | dry/apply/re-import OK; +cắt field dài, ngày rác |

## PHA 2 — Import ĐƠN MUA HÀNG
| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | Parser sheet 6 (header dòng 4): gom Misa -> Số HĐ -> lần giao | |
| [ ] | Resolve NCC/SP; thiếu Mã hàng->tạo Product tạm; NSPT mặc định của lô | |
| [ ] | Upsert PurchaseOrder + POItem + PODelivery | |
| [ ] | Trạng thái "Hoàn thành" -> done + tạo YCTT + ghi ĐÃ CHI; khác -> chỉ công nợ | |
| [ ] | Celery task `import_purchase_order` + ghi log | |
| [ ] | Nút "Import Excel" ở trang Đơn mua hàng | |
| [ ] | Test end-to-end | |

## PHA 3 — Hoàn thiện & Deploy
| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | Danh sách "cần rà soát" + đối chiếu giá trị text về tập chuẩn | |
| [ ] | Deploy hạ tầng Celery lên VPS prod + `REDIS_URL` trong `.env` | |
| [ ] | Chạy import thật + rà soát log | |
| [ ] | Merge `import-tool` -> `bao` | |

---
Đặc tả chi tiết: [import-khao-sat.md](import-khao-sat.md) · [import-don-mua-hang.md](import-don-mua-hang.md) · [quan-ly-import.md](quan-ly-import.md) · [README.md](README.md)
