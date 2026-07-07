# Test Suite — Mini Tool Quản lý Thu Mua

Bộ test chia 2 phần: **backend** (pytest, SQLite in-memory, chạy trong container) và **e2e** (Playwright Python, chạy trên host).

---

## Cấu trúc

```
test/
├── backend/
│   ├── conftest.py          # fixtures db + seed (SQLite in-memory)
│   ├── test_ncc_hiding.py   # ẩn NCC + is_purchaser
│   ├── test_auto_assign.py  # resolve_for_group + auto_assign
│   ├── test_process.py      # available_survey_lines + create_option + can_process_line
│   ├── test_pipeline.py     # pipeline đầy đủ SR → PR
│   └── test_codes.py        # _gen_code + _gen_pr_code
├── e2e/
│   ├── conftest.py          # BASE_URL + login helper + fixtures vai trò
│   ├── test_smoke.py        # login + menu visibility
│   └── test_survey_ui.py    # kết quả khảo sát ẩn NCC + chọn option
├── requirements.txt
└── README.md
```

---

## Phần 1 — Backend (pytest, SQLite in-memory)

Backend test **không đụng DB thật** — dùng SQLite in-memory tạo và hủy theo từng test function.

### Cách chạy (trong container)

> Yêu cầu: container `api` đang chạy và đã mount `./test:/app/test`.

**Bước 1 — thêm volume vào `docker-compose.yml`** (service `api`):

```yaml
services:
  api:
    volumes:
      - ./backend:/app
      - ./test:/app/test    # ← thêm dòng này
```

**Bước 2 — recreate container:**

```bash
docker compose up -d api
```

**Bước 3 — cài pytest:**

```bash
docker compose exec -T api pip install pytest
```

**Bước 4 — chạy test:**

```bash
docker compose exec -T api python -m pytest test/backend -q
```

### Coverage (5 file test, ~30 case)

| File | Nội dung |
|---|---|
| `test_ncc_hiding.py` | Serializer `_out_result` ẩn `supplier_*`; `is_purchaser` các scope |
| `test_auto_assign.py` | `resolve_for_group` primary/backup/inactive; `auto_assign` set assignee |
| `test_process.py` | `available_survey_lines` lọc đúng; `create_option` seq+label+dup guard; `can_process_line` RBAC |
| `test_pipeline.py` | Pipeline SR→PR đầy đủ; guards create_prs/complete_sr/finalize |
| `test_codes.py` | `_gen_code` regex + seq tăng; `_gen_pr_code` regex + date param |

---

## Phần 2 — E2E (Playwright Python, chạy trên host)

E2E test trực tiếp lên browser, cần dev server đang chạy (`web :8080` + `api :8000`) và có tài khoản demo.

### Cài đặt (host)

```bash
pip install pytest playwright pytest-playwright
playwright install chromium
```

### Chạy

```bash
# Từ thư mục gốc dự án (có docker đang chạy)
pytest test/e2e --headed -v
```

> **Lưu ý:**
> - Phải chạy khi `docker compose up` đang hoạt động (web :8080 + api :8000).
> - Cần tài khoản demo đã tồn tại: `TESTREQ`, `DEMONV`, `DEMOTP`, `DEMO_MANAGER_PURCHASE` (password = code).
> - Test `test_survey_ui.py` tự động `pytest.skip` nếu không có phiếu "Đã khảo sát".
> - Dùng `--headed` để thấy browser; bỏ để chạy headless.

### Tài khoản demo

| Code | Vai trò |
|---|---|
| `TESTREQ` | Người yêu cầu |
| `DEMONV` | NSTM (nhân sự thu mua) |
| `DEMOTP` | Trưởng phòng |
| `DEMO_MANAGER_PURCHASE` | Quản lý thu mua |
