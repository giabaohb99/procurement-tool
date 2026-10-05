# AGENT HUB — VẬN HÀNH VPS QUA BOT: SỔ MÔI TRƯỜNG, THAO TÁC CÓ DUYỆT, TỰ VẬN HÀNH

**Bản 1.0 · 05/10/2026** · ai-CR-067 · ai-CR-068 · ai-CR-069 · Phase 6 (nhóm V) + phase 7 (nhóm O) của
[`04-danh-sach-tinh-nang.md`](./04-danh-sach-tinh-nang.md). Luồng tổng xem [`07-quy-trinh-va-so-do.md`](./07-quy-trinh-va-so-do.md) §4.4.

Đại ca chốt 05/10/2026: bot code được vào VPS 1 xem và sửa, **qua cổng**. Xem dev tự do. Xem prod cần «đúng».
Sửa dev cần «đúng», sao lưu trước, ghi nhật ký, có lệnh hoàn tác. Sửa prod cần «đúng» cộng OTP; **OTP tạm bỏ qua**
theo lệnh đại ca, làm sau (V-04).

## 1. Ai làm phần nào

| Phần | Chạy ở đâu | Tệp |
|---|---|---|
| Nhận câu lệnh, kiểm lan can, ghi sổ, hỏi «đúng», giao vé | Bot trên dev (poller + worker) | `agent_hub/ops.py` |
| Gõ health mỗi phút, mở sự cố, giao chẩn đoán | Worker + beat của bot trên dev | `ops.check_health` |
| Chạy lệnh trên VPS qua SSH, sao lưu, hoàn tác, chẩn đoán, tự chữa, báo tài nguyên | Máy sửa mã có **cờ deploy** (có khóa SSH) | `agent_hub/ops_runner.py` |
| Lan can: lệnh đọc/sửa/cấm, SQL đọc/sửa/cấm, che bí mật, danh sách tệp cấm | Cả hai | `agent_hub/guardrails.py` |
| Đưa một commit lên một môi trường | VPS (đi qua SSH bằng stdin) | `backend/scripts/deploy/deploy.sh` |

Ba bảng mới: `tab_agent_env` (sổ môi trường, nạp sẵn `dev` + `prod`), `tab_agent_op` (nhật ký thao tác),
`tab_agent_incident` (sổ sự cố). Migration `e8a3c5f1d7b2`, nối sau `wkhist01`.

## 2. Câu lệnh trên Telegram (chỉ chat của đại ca)

| Câu nhắn | Làm gì | Duyệt |
|---|---|---|
| «môi trường» | Liệt kê sổ môi trường, health gần nhất | — |
| «thêm môi trường staging: dir=~/stg compose="-f s.yml" branch=erp-v2 health=https://… db=stg kind=preview» | Thêm một dòng (khóa thêm: `host`, `port`, `user`, `heal`, `note`) | — |
| «gỡ môi trường staging» | Đóng dòng (dev, prod không gỡ bằng câu nhắn) | — |
| «trạng thái dev» · «log api dev 200» | `docker compose ps` · đuôi log một service | dev: không · prod: «đúng» |
| «chẩn đoán dev: sao api chậm?» | Gom container, log, commit, migration, tài nguyên → Claude chẩn đoán | dev: không · prod: «đúng» |
| «sql dev: SELECT …» | Chạy câu đọc (phiên MySQL chỉ đọc), in tối đa 50 dòng | dev: không · prod: «đúng» |
| «gán chức vụ Nhân viên (Demo) cho nhân sự có (CR-414) trong tên» (nói thường, ai-CR-073) | Máy sửa mã tự tra + soạn lệnh, thẻ tiếng Việt ghi số dòng + mẫu; xem [`09`](./09-quy-dinh-hoi-va-lam.md) §4 | «đúng» |
| «sql dev: UPDATE … WHERE …» (cho người biết SQL) | Sao lưu đúng các bảng bị đụng → chạy → ghi lệnh hoàn tác | «đúng» |
| «chạy dev: docker compose ps \| grep api» | Lệnh shell; nằm trong danh sách chỉ đọc thì là xem | đọc: như xem · sửa: «đúng» |
| «khởi động lại api celery-worker dev» · «dựng lại erp dev» · «dọn bộ đệm dev» | Thao tác có sẵn | «đúng» |
| «deploy prod a1b2c3d» · «deploy dev mới nhất api» | `deploy.sh`; prod sao lưu CẢ DB trước | «đúng» |
| «quay về bản trước dev» | Deploy lại commit trước lần deploy gần nhất của bot | «đúng» |
| «lịch sử thao tác [dev]» · «lịch sử deploy [prod]» · «thao tác #12» | Nhật ký, chi tiết một dòng | — |
| «hoàn tác thao tác #12» | Đẻ một thao tác MỚI theo cách hoàn tác đã ghi, cũng qua «đúng» | «đúng» |
| «chạy thao tác #12» · «bỏ thao tác #12» | Duyệt / bỏ một thẻ cũ (quá 15 phút không «đúng» suông được) | — |
| «tình hình máy» | RAM / CPU / đĩa từng máy, container ăn nhiều nhất, việc của bot 24 giờ | — |
| «sự cố [dev]» | Sổ sự cố | — |
| «bật tự chữa dev» · «tắt tự chữa dev» | Cờ tự chữa của một môi trường (prod không bao giờ bật được) | — |

«deploy dev AI-0007» vẫn là lệnh trên một VIỆC (đường gộp cũ), không đi vào sổ thao tác.
Thẻ «đúng» luôn hiện **nguyên văn** lệnh / câu SQL sẽ chạy, kèm cách sao lưu và cách hoàn tác.

## 3. Lan can

- **Lệnh shell.** Chỉ đọc khi MỌI đoạn (tách theo `|`, `&&`, `;`) bắt đầu bằng lệnh trong danh sách đọc (`docker compose ps/logs`,
  `df`, `free`, `cat`, `grep`, `git log`…) và không có `>`, `$(`, dấu huyền, `tee`, `sudo`. Từ chối thẳng, kể cả khi «đúng»:
  đụng `.env` / khóa / token / mật khẩu (kết quả sẽ lên Telegram), `rm -rf /`, `down -v`, `docker volume rm`, `mkfs`, tắt máy.
- **SQL.** Mỗi lần một câu, không chú thích. Đọc: `SELECT / SHOW / EXPLAIN / WITH`, cấm đọc cột mật khẩu / token / khóa và
  `SELECT *` trên bảng tài khoản. Sửa: `UPDATE / DELETE` phải có `WHERE` (muốn cả bảng thì ghi `WHERE 1=1`), `INSERT / REPLACE`.
  Cấm: `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT`, ghi tệp. Đổi cấu trúc bảng phải qua migration.
- **SQL chạy qua `python` trong container `api` của chính môi trường đó** (SQLAlchemy, câu SQL đi dạng base64) — không qua
  `mysql` CLI, đúng luật chống lỗi mã hóa tiếng Việt.
- **Kết quả** qua `mask_secrets` trước khi vào sổ hay lên Telegram.
- **Ba luật tự cải thiện (V-05)** thi hành bằng danh sách tệp cấm: bot code không sửa được `grants.py`, `runners.py` (sổ quyền,
  sổ máy), `ops.py`, `ops_runner.py`, `scripts/deploy/*` (cổng duyệt, lệnh prod), `guardrails.py` (chính danh sách cấm).

## 4. Sao lưu và hoàn tác

| Thao tác | Sao lưu trước | Hoàn tác |
|---|---|---|
| SQL sửa | `mysqldump` ĐÚNG các bảng bị đụng → `~/agent-backups/op<n>-<môi trường>-<giờ>.sql.gz`. Sao lưu hỏng thì KHÔNG chạy | Nạp lại tệp đó (trước khi nạp lại, sao lưu trạng thái hiện tại — hoàn tác được cả lượt hoàn tác) |
| Deploy prod | `mysqldump` cả DB prod | Deploy lại commit trước (`PREV`). DB không tự nạp lại — tệp sao lưu ghi trong thẻ |
| Deploy dev | — | Deploy lại commit trước |
| Khởi động lại / dựng lại / dọn bộ đệm | — | Không cần |
| Lệnh shell sửa | — | Không có cách tự động; thẻ nói rõ trước khi «đúng» |

`mysqldump` chạy TRONG container `procurement-mysql`; mật khẩu root nở ra bên trong container, không qua dòng lệnh VPS,
không lên output. Tệp sao lưu quá 14 ngày tự dọn (`AGENT_OPS_BACKUP_KEEP_DAYS`).

## 5. `deploy.sh`

```bash
ssh vps 'bash -s -- dev latest' < backend/scripts/deploy/deploy.sh
ssh vps 'bash -s -- prod a1b2c3d api erp' < backend/scripts/deploy/deploy.sh
```

Khóa lượt theo môi trường (`flock`) · ghi `PREV` · `git fetch` · commit phải NẰM TRÊN `origin/<nhánh của đích>` (dev = `erp-v2`,
prod = `main`) · `reset --hard` · `up -d --build` đúng service (bỏ trống = tự chọn theo thư mục đổi) · gõ health 2 phút · health hỏng
thì **tự quay về `PREV`**. In các dòng `PREV= HEAD= SERVICES= HEALTH= RESULT=ok|fail|rolled_back|busy`, ghi tệp nhật ký ở
`~/agent-deploy-logs`. Đường gộp + deploy dev của việc sửa mã (`coder.merge_and_deploy`) cũng đi qua tệp này từ ai-CR-067.

## 6. Tự vận hành (phase 7)

```
beat mỗi phút ── gõ health từng môi trường ── 200 ──> (có sự cố đang mở) đóng sự cố, báo thời gian gián đoạn
                        │
                        └─ hỏng 3 lượt liền ──> mở sự cố #n, báo đại ca ──> máy sửa mã:
                               gom container / log / commit / migration / tài nguyên (chỉ đọc)
                               → Claude chẩn đoán: nguyên nhân + MỘT thao tác an toàn
                               │
                               ├─ không có thao tác an toàn ─────────────> chờ người
                               ├─ prod, hoặc tự chữa tắt ────────────────> thẻ «đúng» (O-04)
                               ├─ dev, đã tự chữa 3 lần trong giờ ───────> DỪNG, chờ người
                               └─ dev ──> chạy thao tác (ghi sổ, tự chạy) → gõ health 2 phút → hết / chờ người
                        cùng nguyên nhân 3 lần / 7 ngày ──> mở việc «Sự cố lặp lại: …» đi đường thường (O-06)
```

Thao tác an toàn duy nhất bot được chọn: `up_services` · `restart_services` · `rollback_last_deploy` (chỉ khi bot deploy
trong 2 giờ qua) · `prune_build_cache` (bộ đệm build + ảnh treo quá 24 giờ; không volume) · `none`. Claude không trả lời được
thì dùng luật dự phòng: container dừng → bật lại; đĩa ≥ 92% → dọn bộ đệm; còn lại → chờ người.

Báo tài nguyên 07:35 mỗi sáng (cùng nội dung «tình hình máy»). Bản tin sáng Google (ai-CR-064) sửa giờ chạy về đúng 07:30.

## 7. Bật lên

1. Migration `e8a3c5f1d7b2` chạy khi deploy dev (Agent 1 gộp erp-v2).
2. `.env.dev` của bot: `AGENT_OPS_ENABLED=true` (tự chữa thêm `AGENT_HEAL_ENABLED=true`), rồi `up -d --force-recreate`
   `celery-worker celery-beat agent-poller`.
3. `.env.runner` của máy có cờ deploy: `AGENT_OPS_ENABLED=true` (+ `AGENT_HEAL_ENABLED=true`), dựng lại runner để có mã mới:
   `docker compose --env-file .env.runner -p agentrunner -f docker-compose.runner.yml up -d --build`.
4. **Cấp quyền DB cho tài khoản MySQL `agent_runner`** của máy sửa mã (nó chỉ được cấp theo TỪNG bảng). Thiếu bước này
   là máy nhận vé rồi hỏng lặng lẽ (05/10 đã dính: ba lệnh đầu tiên treo tới khi cấp). Đã cấp trên dev 05/10:
   ```sql
   GRANT SELECT, UPDATE ON procurement_dev.tab_agent_env TO agent_runner@'%';
   GRANT SELECT, INSERT, UPDATE ON procurement_dev.tab_agent_op TO agent_runner@'%';
   GRANT SELECT, UPDATE ON procurement_dev.tab_agent_incident TO agent_runner@'%';
   ```
   **Luật:** thêm bảng Agent Hub mới mà máy sửa mã đọc/ghi thì phải cấp thêm cho `agent_runner` cùng đợt deploy.
   Thao tác nằm «chờ máy» quá 5 phút thì bot tự báo một lần (`ops.remind_stuck_ops`).
5. Thử: «môi trường» → «trạng thái dev» → «tình hình máy» → «sql dev: SELECT COUNT(*) FROM tab_agent_task».

## 8. Chưa làm, nói thẳng

- **V-04 OTP** cho thay đổi prod: tạm bỏ qua theo lệnh đại ca. Lệnh prod hiện vẫn chạy từ máy sửa mã có cờ deploy (thiết kế
  gốc muốn phát từ VPS 1) — đổi khi có VPS 2 thật (V-08).
- **O-01 phần còn thiếu:** mỗi phút mới gõ health; container / đĩa / RAM chỉ xem lúc chẩn đoán và trong báo sáng; chưa đếm lỗi
  5xx tăng đột biến, chưa canh hàng đợi Celery.
- **O-03 «chạy lại migration dở»** không có thao tác riêng: khởi động lại `api` đã chạy lại `alembic upgrade head` trong
  `start.prod.sh`.
- Dev và prod chung một VPS: VPS chết hẳn thì bot (cũng ở trên đó) không báo được gì.
- **V-07 preview** chờ tên miền + token Cloudflare Tunnel; **V-08** chờ VPS 2 + tài khoản Claude công ty.
