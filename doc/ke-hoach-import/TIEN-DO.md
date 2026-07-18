# TIẾN ĐỘ — Công cụ Import (Khảo sát + Đơn mua hàng)

Nhánh làm việc: **`import-tool`** (off `bao`). Cập nhật ô trạng thái khi xong.
Ký hiệu: ⬜ chưa làm · 🟨 đang làm · ✅ xong.

## Chạy local để test
```bash
# Bật hạ tầng nền (Redis + Worker). Beat KHÔNG cần (import chạy on-demand).
docker compose up -d redis celery-worker
# (tuỳ chọn) xem hàng đợi:  docker compose up -d redisinsight   → http://localhost:5540
# Test worker sống:
docker compose exec celery-worker python -c "from app.tasks.debug import ping; print(ping.delay().get(timeout=15))"
# Web: http://localhost:8080  ·  API: http://localhost:8000/docs
```

---

## PHA 0 — Hạ tầng Import (dùng chung)
| | Việc | Ghi chú |
|---|---|---|
| ✅ | Merge Celery (redis/worker/beat) vào `bao` | đã cherry-pick |
| ⬜ | Model `import_batch` + `import_log` (+ IntEnum level/status/module/mode) | §5 quan-ly-import.md |
| ⬜ | Migration 2 bảng | |
| ⬜ | Lưu file .xlsx qua StoredFile (`file_id`) | |
| ⬜ | API upload + tạo batch + đẩy Celery task (trả `batch_id` ngay) | |
| ⬜ | Trang **Quản lý Import**: list (tên file text) + chi tiết (tải file + tab log) | |
| ⬜ | Chuông báo khi worker xong → link `/import-batches/{id}` | dùng trigger_notification |

## PHA 1 — Import KHẢO SÁT
| | Việc | Ghi chú |
|---|---|---|
| ⬜ | Parser openpyxl sheet 3+4 (header dòng 5) + chuẩn hoá ngày/số/text | |
| ⬜ | Resolve NCC: SP→tên viết tắt, NCC→MST; xung đột→text-only+log | |
| ⬜ | Upsert Supplier (tạo mới / điền field trống) | |
| ⬜ | Gom (Phân loại + NCC) → upsert Survey + supplier_lines + product_lines | khoá dòng: MST / (NCC+Mã VTBB) |
| ⬜ | Celery task `import_survey` (dry-run + apply) + ghi import_log | |
| ⬜ | Nút "Import Excel" ở trang Phiếu khảo sát (dry-run → xác nhận) | |
| ⬜ | Test end-to-end với file mẫu | |

## PHA 2 — Import ĐƠN MUA HÀNG
| | Việc | Ghi chú |
|---|---|---|
| ⬜ | Parser sheet 6 (header dòng 4): gom Misa → Số HĐ → lần giao | |
| ⬜ | Resolve NCC/SP; thiếu Mã hàng→tạo Product tạm; NSPT mặc định của lô | |
| ⬜ | Upsert PurchaseOrder + POItem + PODelivery | |
| ⬜ | Trạng thái "Hoàn thành" → done + tạo YCTT + ghi ĐÃ CHI; khác → chỉ công nợ | |
| ⬜ | Celery task `import_purchase_order` + ghi log | |
| ⬜ | Nút "Import Excel" ở trang Đơn mua hàng | |
| ⬜ | Test end-to-end | |

## PHA 3 — Hoàn thiện & Deploy
| | Việc | Ghi chú |
|---|---|---|
| ⬜ | Danh sách "cần rà soát" + đối chiếu giá trị text về tập chuẩn | |
| ⬜ | Deploy hạ tầng Celery lên VPS prod + `REDIS_URL` trong `.env` | |
| ⬜ | Chạy import thật + rà soát log | |
| ⬜ | Merge `import-tool` → `bao` | |

---
Đặc tả chi tiết: [import-khao-sat.md](import-khao-sat.md) · [import-don-mua-hang.md](import-don-mua-hang.md) · [quan-ly-import.md](quan-ly-import.md) · [README.md](README.md)
