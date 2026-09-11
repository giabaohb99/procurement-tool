# Kế hoạch phát hành `erp-v2` lên prod

Bản lập 11/09/2026. Mọi con số dưới đây **đo trực tiếp trên prod và trên repo ngày 11/09/2026**,
không chép lại từ tài liệu cũ. Đo lại trước giờ chạy vì dữ liệu đổi mỗi ngày.

Tài liệu này là **kịch bản chạy**, không phải bản thiết kế. Nền v2 mô tả ở
`doc/erp/15-do-be-tong-nen-v2.md`; luật nhánh ở `doc/tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md`.

> ✅ **ĐÃ CHẠY XONG tối 11/09/2026.** Số thật khác số dự trù bên dưới vì prod còn nhận thêm
> vài đợt vá (bao-CR-367…) trong lúc soạn kịch bản. **Số chốt để trích dẫn:**
> `main` **`fbeee8b0` → `ed2ad063`** · **115** migration chạy · `alembic_version`
> **`94f0a2c4e43c` → `bee157de2ec8`** (1 head) · **60 → 141** bảng · sao lưu
> `~/proc_backups/procurement_truoc_v2_20260911_1739.sql.gz`. Diễn tập bắt được một lỗi
> đồ thị alembic, chữa ở **bao-CR-382** — không có nó thì prod mất 107 migration trong im
> lặng. Nhật ký đầy đủ: `change-log-bao.md`, bảng phát hành.
>
> ⚠️ Mọi mã commit viết trong tài liệu này là **số dự trù lúc soạn** (`c417bf64` / `1f3c7685`),
> đã cũ. Cần lùi thì dùng số chốt ở trên, đừng chép lại từ §5.

---

## 1. Việc này là gì

Đưa toàn bộ nhánh `erp-v2` lên prod: backend v2 + giao diện `frontend/` bản dev + 116 migration.

| | prod (`main`) | dev (`erp-v2`) |
|---|---|---|
| Commit | `c417bf64` | `1f3c7685` |
| Migration chưa chạy trên prod | — | **116** |
| Khóa phân quyền (`ENTITIES`) | 28 | **59** (+31) |
| Backend cụm Thu mua | — | +2.900 dòng / 31 tệp |
| `frontend/` (giao diện thumua) | — | lệch 18 tệp |
| `alembic heads` | — | **1 head** (`bee157de2ec8`) |

Hai điều làm phần **git** của đợt này gần như không có rủi ro:

- `main` **là tổ tiên trực tiếp** của `erp-v2` (đã kiểm bằng `git merge-base --is-ancestor`), nên
  đưa lên là **fast-forward** — `main` chỉ việc nhảy tới `1f3c7685`, không đụng độ, không commit gộp.
- `docker-compose.production.yml` giữa hai nhánh chỉ lệch **12 dòng** (thêm service `qdrant`, chỉ
  chạy khi bật `AI_RAG_ENABLED`). **Chưa có service `erp`** trong bộ compose prod, nghĩa là
  **giao diện ERP v2 KHÔNG lên prod trong đợt này** — `thumua.degoholding.vn` vẫn chạy `frontend/`.
  Muốn đưa v2 lên phải thêm service + tên miền + tunnel, là một đợt riêng.
- Mọi khóa cấu hình mới trong `core/config.py` đều có **mặc định an toàn**
  (`AI_ENABLED=false`, `AI_RAG_ENABLED=false`, ...), nên `.env` prod **không bắt buộc thêm gì**.

Rủi ro nằm ở **dữ liệu và phân quyền**, không nằm ở mã nguồn.

---

## 2. Rủi ro đã xác định

### R-1. Phạm vi «Công ty» sẽ trả RỖNG cho 18 Nhân viên thu mua — NẶNG NHẤT

Nền v2 áp luật B-07: phạm vi hẹp mà **không dựng nổi điều kiện** thì **chặn** (`false()`) chứ không
im lặng trả `None` (= thấy tất) như bản v1. Nhánh `company` với `company_id = 0` rơi đúng vào đó.

Đo trên prod hôm nay:

```
tab_employee: 233/235 hồ sơ có company_id = 0   (chỉ 2 hồ sơ gắn công ty 1)
vai trò có phạm vi "company":
  pur_staff    (18 người)  inventory · payable · payment_request · report
  company_head (0 người)   employee · purchase_order · purchase_request · report
vai trò có phạm vi "dept":
  dept_head    (5 người)   employee · purchase_request · report · survey_request
  pur_staff    (18 người)  employee
```

Hệ quả nếu lên nguyên trạng: **cả 18 Nhân viên thu mua mở Tồn kho · Công nợ · Yêu cầu thanh toán ·
Báo cáo đều thấy trắng bảng.** Không ai báo 403, không có gì đỏ lên, chỉ là không có dòng nào.

Thêm hai ca nhỏ cùng họ:
- Tài khoản `id=10` (`tnhuynh.idagroup@gmail.com`) **chưa gắn hồ sơ nhân sự** → nhánh `own` trên
  entity có chiều `self` cũng bị chặn.
- Phạm vi `dept`: 5 người `dept_head` và 18 `pur_staff` đều **có** `department_id`, nên nhánh này
  không dính. Kiểm lại ngay trước giờ chạy, có người mới là lệch.

**Hai đường xử, phải chốt TRƯỚC ngày chạy:**

| | Cách làm | Được | Mất |
|---|---|---|---|
| **A (khuyến nghị)** | Đổi phạm vi 4 khóa của `pur_staff` từ `company` sang `all` ngay trên màn Phân quyền, **trước** khi phát hành | Ghi đúng hành vi họ **đang có** thành cấu hình — người dùng không thấy gì khác | Phải nhớ siết lại khi thật sự bật đa pháp nhân |
| **B** | Gắn `company_id` cho 233 hồ sơ nhân sự | Đúng hướng đa pháp nhân về lâu dài | Chứng từ prod trải **8 pháp nhân** (15: 90 YCMH · 2: 13 · 11: 9 · 8: 5 · 1,3,5: 3 · 6: 2). Gắn ai vào công ty nào là **quyết định nghiệp vụ**, gắn sai là mất phiếu ngay hôm sau |

Cách A đổi được bằng UI trong 2 phút và lùi lại cũng bằng UI. Cách B nên làm thành một đợt riêng,
có danh sách nhân sự × pháp nhân do phòng Nhân sự duyệt.

### R-2. Trạng thái Thu mua bị viết lại tại chỗ (B-02…B-06)

Các migration `c1d4a7b93e56` · `d2e5b8c04f71` · `e7b3f9a15c28` · `f8c4a02b6d39` ·
`a3f7d2e51c94` · `b6e9c4801fa2` đổi chữ tiếng Việt trong cột trạng thái thành mã tiếng Anh, **ngay
trên bảng thật**. Đếm prod hôm nay:

```
tab_purchase_request_item.line_status   Đã nhận hàng 99 · Đã đặt hàng 95 · Chưa tạo đơn mua hàng 34
                                        Chưa đặt hàng 19 · Hủy đơn 2
tab_purchase_order.document_status      đã có thông tin chứng từ 150 · chưa có chứng từ 6
tab_po_item.line_status                 Chưa giao 122 · Đủ 93 · Đang giao 6
tab_po_delivery.status                  Đã nhận 103
```

Không có giá trị lạ, không có ô rỗng — **bảng ánh xạ trong migration phủ đủ toàn bộ dữ liệu prod
hiện tại**. Vẫn phải đếm lại ngay trước giờ chạy (bước 4.2), vì người dùng còn nhập tới sát giờ.

⚠️ Đây là đổi **tại chỗ**: lùi lại chỉ còn đường khôi phục bản sao lưu. Và `frontend/` bản mới
(bộ `statusLabels.ts`) **phải lên cùng chuyến** — deploy backend trước UI là cả màn Thu mua hiện
mã tiếng Anh trần.

### R-3. 31 khóa phân quyền mới, không ai được cấp

```
mailbox · doc_type · doc_template · doc_numbering_rule · doc_link_rule · external_party
document_book · document · security_level · seal_request · seal_type · vehicle_booking
vehicle · driver · approval_flow · assistant · forum_post · forum_board · work_task
leave_request · leave_balance · leave_type · holiday · room_booking · meeting_room
employee_sensitive · job_position · coffee_policy · coffee_member · coffee_ledger · pos_order
```

`seed_prod` **cố ý không ghi đè** phân quyền đã chỉnh tay (D-018), nên 31 khóa này sẽ trống trơn.
Thu mua **không hỏng** (khóa cũ giữ nguyên), nhưng phân hệ mới nào cũng 403 tới khi tick.

⚠️ **Đừng chữa bằng `SEED_FORCE_SYNC=true`** — nó đè sạch phân quyền đang chỉnh tay trên UI, kể cả
cách A của R-1. Nếu buộc phải dùng thì phải xuất phân quyền hiện tại ra trước.

### R-4. Lọc pháp nhân trên phạm vi `proc` (CR-312 P1)

`_proc_status_cond` AND thêm `company_id` của người xem vào nhánh `proc`, **nhưng chỉ khi
`company_id != 0`**. Với dữ liệu prod hôm nay (233/235 hồ sơ bằng 0) nhánh này **nằm im**, trừ 2 hồ
sơ gắn công ty 1. Rủi ro thật sự chỉ xuất hiện khi làm cách B của R-1 — làm B là phải rà lại đúng
chỗ này.

### R-5. Sáu phân hệ chưa nghiệm thu lên prod cùng lúc

Văn thư · Duyệt dấu · Nghỉ phép · Đặt xe · Đặt phòng họp · Diễn đàn · Công việc · Trợ lý AI. Chúng
**ẩn sau phân quyền** (R-3) nên không tự hiện ra với người dùng, nhưng mã, bảng và tác vụ nền của
chúng chạy thật trên prod. Chốt trước: đợt này **chỉ bật Thu mua như cũ**, phân hệ khác để nguyên
không cấp quyền, bật dần sau khi nghiệm thu từng cái.

⚠️ **CẤM chạy `seed_help_dien_dan.py` trên prod.**

### R-6. Đảo luật nhánh một chiều

`quy-trinh-nhanh-va-deploy.md` ghi «merge chỉ một chiều `main` → `erp-v2`». Đợt này đi ngược. Vì là
fast-forward nên về kỹ thuật sạch, nhưng **sau đợt này hai nhánh bằng nhau**, và luật trong tài liệu
đó phải viết lại (bước 7). Không sửa tài liệu thì lần sau có người merge ngược không ai chặn.

---

## 3. Chốt trước ngày chạy

- [ ] **Chọn cách xử R-1** (A hay B). Chưa chốt thì không chạy.
- [ ] Chốt: đợt này **không** đưa giao diện ERP v2 lên prod (giữ `frontend/`).
- [ ] Chốt: 31 khóa mới **để trống**, không bật phân hệ mới.
- [ ] Báo người dùng khung giờ ngưng (15 phút, thực tế thường 5).

---

## 4. Kịch bản chạy

Chọn **một** trong hai khung:

| Khung | Bắt đầu | Ưu | Nhược |
|---|---|---|---|
| **Chiều nay 11/09** | 16:00 chuẩn bị · **17:00 chạy** | Cuối giờ làm, ít người đang thao tác; còn cả buổi tối để chữa | Phải xong bài chạy thử (4.1) trước 16:00, khá gấp |
| **Sáng mai 12/09** | 07:00 chuẩn bị · **07:30 chạy, xong trước 08:00** | Có cả tối nay để chạy thử trên bản sao và chốt R-1 | Hỏng là kẹt nguyên ngày làm việc |

Khuyến nghị: **sáng mai, bắt đầu 07:00**, và **tối nay chạy xong bài 4.1**. Nếu bài 4.1 xong sớm
trước 16:00 hôm nay thì khung chiều nay cũng dùng được.

### 4.1. Chạy thử trên BẢN SAO dữ liệu prod (bắt buộc, làm trước ngày chạy)

Đây là bước tách bạch «migration có chạy nổi trên dữ liệu prod không» khỏi giờ phát hành thật.

```bash
# trên VPS
set -a; . ~/procurement-db/.env; set +a
docker exec procurement-mysql mysqldump -urootdegoHolding -p"$DB_ROOT_PASSWORD" \
  --single-transaction --routines --triggers procurement | gzip > ~/proc_backups/procurement_thu_v2.sql.gz
docker exec procurement-mysql mysql -urootdegoHolding -p"$DB_ROOT_PASSWORD" \
  -e "DROP DATABASE IF EXISTS procurement_thu; CREATE DATABASE procurement_thu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
gunzip -c ~/proc_backups/procurement_thu_v2.sql.gz | docker exec -i procurement-mysql \
  mysql -urootdegoHolding -p"$DB_ROOT_PASSWORD" procurement_thu
```

Rồi chạy 116 migration lên bản sao đó bằng mã của `erp-v2` (worktree dev đã ở đúng commit):

```bash
cd ~/procurement-tool-dev
docker compose -f docker-compose.dev.yml --env-file .env.dev run --rm -e DB_NAME=procurement_thu api alembic upgrade head
```

Nghiệm thu bài chạy thử:
- [ ] Kết thúc không lỗi, `alembic current` ra `bee157de2ec8`.
- [ ] Bốn cột ở R-2 không còn giá trị tiếng Việt và **tổng số dòng không đổi**.
- [ ] Ghi lại **thời gian chạy** — đó là con số để đặt cửa sổ ngưng thật.
- [ ] Xóa bản sao sau khi xong: `DROP DATABASE procurement_thu`.

### 4.2. Ngay trước giờ chạy (T-15 phút)

- [ ] `git fetch` hai worktree, xác nhận `origin/main` vẫn là `c417bf64`, `origin/erp-v2` là
      `1f3c7685` (có ai đẩy thêm thì phải đọc lại phần đó trước).
- [ ] Đếm lại 4 cột của R-2, đối chiếu với bảng ánh xạ — có giá trị lạ thì **dừng**.
- [ ] Đếm lại `company_id`/`department_id` của người giữ phạm vi `company`/`dept` (R-1).
- [ ] Nếu chọn cách A: đổi 4 khóa của `pur_staff` sang `all` **bây giờ**, và xác nhận trên UI.
- [ ] Báo người dùng ngưng thao tác.

### 4.3. Sao lưu (T-5 phút)

```bash
set -a; . ~/procurement-db/.env; set +a
docker exec procurement-mysql mysqldump -urootdegoHolding -p"$DB_ROOT_PASSWORD" \
  --single-transaction --routines --triggers procurement \
  | gzip > ~/proc_backups/procurement_truoc_v2_$(date +%Y%m%d_%H%M).sql.gz
ls -lh ~/proc_backups | head -3
```

Ổ đĩa còn 21G, dư sức. **Không có tệp này thì không chạy tiếp.**

### 4.4. Đưa `main` lên (máy local)

```bash
cd "D:/New folder/thuthapykien/procurement-main"
git fetch origin && git checkout main && git merge --ff-only origin/erp-v2
GIT_SSH_COMMAND='ssh -i "C:/Users/Dego Admin/.ssh/id_ed25519_github" -o BatchMode=yes' git push origin main
```

`--ff-only` là chốt an toàn: không fast-forward được nghĩa là có người vừa đẩy lên `main`, lệnh sẽ
từ chối thay vì đẻ ra một merge commit không ai rà.

### 4.5. Deploy prod (T-0)

```bash
cd ~/procurement-tool
git fetch origin && git reset --hard origin/main && git status --short   # phải RỖNG
docker compose -f docker-compose.production.yml up -d --build api celery-worker celery-beat web
```

- `api` khởi động sẽ tự chạy `alembic upgrade head` (116 migration) rồi `seed_prod`. **Xem log
  ngay**: `docker compose -f docker-compose.production.yml logs -f api`.
- `web` phải build lại vì `frontend/` lệch 18 tệp — **không được bỏ**.
- `help` không đổi, không cần đụng.
- `qdrant` chỉ dựng khi bật `AI_RAG_ENABLED`; đợt này **để tắt**, không cần khởi động.

### 4.6. Nghiệm thu (T+10)

- [ ] `docker compose -f docker-compose.production.yml ps` — bảy container Up.
- [ ] Log `api` có `Application startup complete`, không có `ERROR` / `scope thieu khai`.
- [ ] Đăng nhập bằng một tài khoản **Nhân viên thu mua** (không phải admin): mở Yêu cầu mua hàng ·
      Đơn mua hàng · Tồn kho · Công nợ · Yêu cầu thanh toán · Báo cáo — **mỗi màn phải ra dòng**.
      Đây là bài kiểm trực tiếp của R-1.
- [ ] Mở một YCMH và một ĐMH đang chạy dở: trạng thái dòng hiện **tiếng Việt** (mã mới + nhãn),
      không hiện chuỗi tiếng Anh trần.
- [ ] In thử một YCMH và một ĐMH — chữ ký duyệt còn đủ.
- [ ] Tạo một phiếu nháp rồi xóa, để chắc đường ghi còn thông.
- [ ] `grep "scope chan" ` trong log api 15 phút đầu — có dòng nào thì đó là danh sách người đang bị
      chặn oan, xử ngay theo R-1.

---

## 5. Đường lùi

Ngưỡng quyết định: **quá 20 phút chưa xong bước 4.5, hoặc nghiệm thu 4.6 hỏng một mục từ Thu mua trở đi** → lùi, đừng chữa nóng.

```bash
# 1) mã nguồn về đúng bản đang chạy sáng nay
#    SỐ THẬT của đợt 11/09/2026: fbeee8b0 (bản dự trù `c417bf64` đã cũ trước giờ chạy)
cd ~/procurement-tool && git reset --hard fbeee8b0
docker compose -f docker-compose.production.yml up -d --build api celery-worker celery-beat web

# 2) dữ liệu về bản sao lưu ở bước 4.3
set -a; . ~/procurement-db/.env; set +a
gunzip -c ~/proc_backups/procurement_truoc_v2_20260911_1739.sql.gz \
  | docker exec -i procurement-mysql mysql -urootdegoHolding -p"$DB_ROOT_PASSWORD" procurement
```

⚠️ Phải lùi **cả hai**. Lùi mã mà giữ dữ liệu đã đổi mã trạng thái thì giao diện cũ đọc không ra
trạng thái nào; lùi dữ liệu mà giữ mã mới thì ngược lại.

⚠️ Nhánh `main` trên GitHub lúc đó đã trỏ `1f3c7685`. **Đừng ép đẩy ngược** — cứ để đó, prod chạy
bằng commit cũ là đủ, lần sau lên lại chỉ việc `reset --hard origin/main`.

---

## 6. Sau khi lên xong

- [x] Đánh dấu đợt này trong `change-log-bao.md`, ghi commit + giờ + tệp sao lưu.
- [x] Viết lại luật nhánh trong `quy-trinh-nhanh-va-deploy.md` (R-6): §A.2 nay ghi rõ luật một
      chiều đã hết hiệu lực, và ghi câu hỏi **còn phải chốt** — hai nhánh bằng nhau rồi thì còn
      tách ra làm gì. `CLAUDE.md` sửa theo.
- [x] Cách A của R-1 đã chọn → mở dòng nợ **N-019** trong `change-log.md`.
- [ ] Giữ bản sao lưu ít nhất **7 ngày** — `~/proc_backups/procurement_truoc_v2_20260911_1739.sql.gz`,
      giữ tới **18/09/2026**.
- [ ] Bật từng phân hệ mới sau khi khách nghiệm thu, mỗi lần một cái, bằng cách tick khóa quyền.
      Sau `seed_prod`, **cả 59 khóa đều có ít nhất một vai trò giữ**, nhưng các phân hệ mới chỉ nằm
      ở `admin` + một vai trò chuyên trách **chưa gán cho ai**: `forum_admin` · `coffee_admin` ·
      `hr_profile` · `help_admin` · `vanban_sua` · `pur_manager`. Chưa gán thì chưa ai thấy.
- [x] ~~Gắn hồ sơ nhân sự cho 1 tài khoản `pur_staff` đang thiếu~~ — **rà lại: không cần làm.**
      Tài khoản đó (`id=10`) đã bị khóa từ trước và là tài khoản **duy nhất trên cả prod** thiếu
      hồ sơ, nên không ai bị chặn. Xem N-019.
