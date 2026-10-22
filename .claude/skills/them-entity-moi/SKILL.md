---
name: them-entity-moi
description: Thêm một entity (khóa phân quyền) mới vào ERP mà không làm đỏ các bài kiểm canh — bảy sổ đăng ký phải khai cùng lúc ở backend, seed vai trò và giao diện v2. Dùng khi phân hệ mới cần quyền riêng (read / create / write / ...) hoặc tách quyền khỏi entity cũ.
---

# Thêm entity (khóa phân quyền) mới

## Khi nào dùng
Phân hệ mới cần khóa quyền riêng, hoặc tách một việc khỏi khóa cũ (ví dụ `ai_skill`, `ai_mcp_key_admin` ở bao-CR-621).
Entity là trục 1 của phân quyền (vai trò × hành động); phạm vi là trục 2 (`SCOPE_FIELDS`). Thiếu một sổ là có bài
kiểm đỏ, và tệ hơn là lỗ hổng im lặng (entity vắng `SCOPE_FIELDS` nay bị `false()` chặn hết, không phải thấy tất).

## Bảy sổ phải khai (đúng thứ tự, mỗi sổ có bài kiểm canh)
1. `backend/app/core/permissions.py` — thêm vào `ENTITIES` (danh sách chuẩn) và `ENTITY_LABELS` (nhãn tiếng Việt).
   Hành động dùng từ `ACTIONS` có sẵn (read · create · write · delete · approve · cancel · print · export), không thêm.
2. `backend/app/core/scoping.py` — khai `SCOPE_FIELDS[entity]`: cột thật (`owner` / `dept_id` / `dept_name` /
   `company` / `handler_dept`...) hoặc `PUBLIC` khi cố ý không lọc theo dòng. Entity nghiệp vụ có chủ sở hữu thì KHÔNG
   `PUBLIC`. Bài canh: `test/backend/test_pham_vi_khai_du_b07.py` đếm `len(ENTITIES) == len(SCOPE_FIELDS)` (đang 78) →
   sửa cả hai số đếm trong bài đó. `test_pham_vi_luat_bat_bien.py` (BB-1..BB-4): controller không lọc phạm vi phải nằm
   trong danh sách miễn trừ kèm lý do.
3. `backend/app/core/entity_models.py` — `ENTITY_MODEL_PATHS[entity] = ("app.modules.<m>.model", "<Lớp>")`, giữ đúng thứ
   tự `SCOPE_FIELDS`; entity `PUBLIC` thì KHÔNG khai ở đây (xem docstring tệp). Dùng cho chỗ chỉ cầm tên entity dạng
   chuỗi (nhật ký thao tác).
4. `backend/app/seed.py` — `STD_ROLES`: gán entity cho vai trò nào, hành động gì, phạm vi gì; luật một vai trò = một chức
   năng (CR-428). Nhớ `seed_prod.py` không ghi đè phân quyền đã sửa tay → ghi vào sổ việc tick tay trên prod.
   Bài canh seed / vai trò chạy cùng `test_pham_vi_khai_du_b07.py` (89 bài canh luật chung ở bao-CR-621).
5. Giao diện v2 — `frontend-v2/src/core/authorization/permission-types.ts` (mảng `ENTITIES` gõ tay, phải khớp backend) và
   `frontend-v2/src/modules/system/config/permission-groups.ts` (xếp entity vào nhóm trên màn Phân quyền). Bài canh:
   `test/backend/test_dong_bo_giao_dien_v2.py` (frontend khớp backend, không trùng, actions khớp cộng thêm `process`).
6. Hành động ghi nhật ký — mọi mã `action` mới dùng trong `audit.record(...)` phải có nhãn ở
   `backend/app/core/action_catalog.py` (`ACTION_CATALOG`). Bài canh: `test/backend/test_bo_ma_hanh_dong_cr358.py`
   (mọi mã có nhãn + nhóm; mọi hành động trong bảng quyền có mã; mã truyền qua hàm trung gian phải khai).
7. Schema ghi — cột `String(n)` của model mới phải có `max_length` ở schema (`Str20`, `Str255`... hoặc `Field(max_length=)`),
   kiểm ở tầng schema vì SQLite không ép độ dài. Bài canh: `test/backend/test_canh_do_dai_o_chu_cr538.py` — phân hệ mới
   có cột chữ thì thêm vào `MODULES` + `TARGETS` (schema ghi → bảng) của bài đó, nếu không `test_every_module_with_string_columns_is_covered` đỏ.

Và một luật xuyên suốt: lấy MỘT bản ghi theo id phải qua `get_scoped(...)`, không `db.get(Model, id)` trong controller.
Thêm một lần `db.get(` vào controller là `test/backend/test_pham_vi_duong_vong.py` (bảng `DB_GET_TRONG_CONTROLLER`) đỏ
và bắt phân loại (nhãn an toàn / cần sửa) — phân loại thật, đừng gắn nhãn cho qua.

## Các bước
1. Model + migration (`alembic revision --autogenerate`, model phải có trong `core/all_models.py`; `alembic heads` một đầu).
2. Khai bảy sổ ở trên trong CÙNG một commit với controller `require(entity, action)` + `apply_scope` / `get_scoped`.
3. Nếu entity bảo vệ báo cáo: thêm `ReportKey` ở `core/report_keys.py` + `require_report` (lớp gác thứ ba), chạy
   `gen_status_ts.py`.
4. Chạy đúng cụm bài canh (không chạy cả `test/backend`):
   ```bash
   docker compose exec -T api python -m pytest -p no:cacheprovider -q -n 3 \
     test/backend/test_pham_vi_khai_du_b07.py test/backend/test_pham_vi_luat_bat_bien.py \
     test/backend/test_dong_bo_giao_dien_v2.py test/backend/test_bo_ma_hanh_dong_cr358.py \
     test/backend/test_canh_do_dai_o_chu_cr538.py test/backend/test_pham_vi_duong_vong.py
   docker compose exec -T erp npm run typecheck && docker compose exec -T erp npx vitest run src/core/authorization src/modules/system
   ```
5. Ghi sổ: entity mới, vai trò nào được gì, việc tick tay trên prod (seed không ghi đè).

### Chạy bài kiểm khi cây chung đứng sau origin (Agent khác đang sửa dở)
Không rebase / reset / checkout cây chung. Clone tạm rồi chạy bằng ảnh api local, commit + push thẳng từ clone (repo thật,
không cần index tạm), xong xóa clone (20/10/2026, bao-CR-647 — Agent 1 chỉ cách):
```bash
cd D:/tmp && git clone -q --branch erp-v2 --single-branch --depth 300 git@github.com:giabaohb99/procurement-tool.git fix-x
MSYS_NO_PATHCONV=1 docker run --rm --memory=3g -e PYTHONPATH=/app -e TZ=UTC \
  -v "D:/tmp/fix-x/backend:/app" -v "D:/tmp/fix-x/test:/app/test" -w /app procurement-tool-api:latest \
  sh -c 'pip install -q pytest pytest-xdist >/dev/null 2>&1; python -m pytest -p no:cacheprovider -q -n 3 test/backend/<tệp>...'
```
(`GIT_SSH_COMMAND` khóa `D:/pem/id_ed25519_github` khi clone / push; `MSYS_NO_PATHCONV=1` để Git Bash không đổi `/app`.)
Sổ `nhat-ky-task.md` / `change-log-bao.md` sửa ngay trong clone là sạch, không lẫn khối dở của người khác.

**Bẫy chuỗi lệnh khi đẩy từ clone (20/10/2026, bao-CR-650 — đã đẩy nhầm dấu `<<<<<<<` lên erp-v2):** viết lệnh
`git commit -a` / `git push` SAU một heredoc là chúng chạy vô điều kiện dù `git rebase` trước đó kẹt xung đột. Luật:
mở đầu bằng `set -e`; mỗi bước git một lệnh riêng; sau rebase chạy `git status` + `git grep -nE '^(<<<<<<<|>>>>>>>)'`
rồi mới push; push chỉ khi `git rev-parse origin/erp-v2` đúng là `HEAD~n` dự kiến; sau khi đẩy, grep lại dấu trên
`origin/erp-v2`. Giải xung đột bảng change-log: hàng của mình lên trên, hàng bên kia giữ ĐÚNG MỘT bản (bản mới nhất).

Hai bẫy khi chạy bộ kiểm (Agent 1, 20/10/2026): **luôn `--timeout=120`** (`pip install pytest-timeout`); stack
`procurement-tool` local bị PAUSED thì bài gọi Redis treo vô hạn; container cô lập không có stack thì nhóm phát hành
văn bản mỗi bài chờ hết trần — nên thêm `--network procurement-tool_default` để `redis` phân giải được khi stack đang chạy.

## Bẫy đã gặp
- 20/10/2026 bao-CR-647: hai đợt mã của anh Dược (duoc-CR-628 nhập Excel nhân sự, duoc-CR-641 hồ sơ cách làm việc) làm
  đỏ cr358 (hai hàm truyền `action` động chưa khai vào `DYNAMIC_ACTION_SITES`) và cr538 (phân hệ mới có cột `String(n)`
  + schema ghi mà chưa vào `MODULES`). Hai sổ đó thuộc BÀI KIỂM, không phải mã nghiệp vụ — thêm module / entity mới
  là phải mở hai bài kiểm khai luôn, không đợi đỏ. Sổ thứ 8 của cr538: schema không ghi cột chữ (chỉ bọc danh sách, chỉ
  mang id / cờ, lồng trong JSON) thì khai `NO_TARGET` kèm lý do; schema tên khớp model (bỏ đuôi In / Create...) thì tự ghép.
- 17/10/2026 bao-CR-621: thêm `ai_skill` + `ai_mcp_key_admin` làm số đếm B-07 nhảy 77 → 78 và `permission-types.ts`
  thiếu một dòng; cả hai bắt ngay bằng bài canh, không phải lúc chạy thật.
- Entity đặt `PUBLIC` cho tiện rồi quên: người có `read` thấy toàn hệ. Chỉ `PUBLIC` cho danh mục dùng chung (đơn vị,
  nhóm hàng...), ghi lý do trong `SCOPE_FIELDS`.
- Phạm vi `proc` cố ý không lọc pháp nhân / phòng (CR-434); phòng tự mua dùng `dept_proc`. Đừng tự chế scope mới — đúng 7
  scope trong `SCOPES` của `permissions.py`.
- `perm_cache_clear(user_id)` sau mọi thay đổi vai trò / quyền, không thì 60 giây sau mới thấy.

## Kiểm xong
- Cụm 6 bài canh trên xanh, typecheck v2 0 lỗi; `alembic heads` một đầu.
- Màn Phân quyền v2 hiện entity ở đúng nhóm với nhãn tiếng Việt; vai trò mẫu nhận quyền sau `python -m app.seed` local.
- Sổ ghi rõ việc tick tay prod và ảnh hưởng người dùng (ai mất / thêm quyền).
