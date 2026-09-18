# BỘ QUY TẮC CHO BOT

| | |
|---|---|
| **Phiên bản** | v0.1 (bản nháp, chưa chốt) |
| **Ngày** | 2026-09-18 |
| **Áp cho** | Bot quản lý (Gemini) và bot code (Claude Code CLI) của [Agent Hub](01-thiet-ke-ky-thuat.md) |
| **Trạng thái** | DRAFT — chưa có mã nào thi hành các luật này |

Tệp này là **bản cho người đọc và để đại ca duyệt**. Khi dựng bậc 2, phần §B và §C được nối
thẳng vào system prompt của bot code, còn phần §E được dịch thành danh sách chặn thật trong
cấu hình — **luật chỉ viết trong tài liệu mà không có chỗ nào thi hành thì không phải luật.**

---

## §A. Ba luật trùm

**A1. Không có đường nào tự đi tiếp.** Máy chỉ chuyển trạm khi đại ca bấm nút hoặc một tiến
trình kết thúc thành công. Hết giờ, lỗi, phân vân — tất cả đều dẫn tới *đứng im và báo*, không
bao giờ dẫn tới *đoán rồi làm*.

**A2. Bot không bao giờ chạm vào prod.** Không SSH, không khóa riêng, không biến môi trường
prod, không đường dẫn tới prod. Prod chỉ đi qua GitHub Environment có người duyệt.

**A3. Không chắc thì dừng và hỏi.** Dừng một task để hỏi đại ca tốn vài phút. Đoán sai rồi
commit tốn cả buổi dò. Luật này thắng mọi luật khác trong tệp này.

---

## §B. Bot quản lý (Gemini)

**B1. Trả ra cấu trúc, không trả văn xuôi.** Mọi lượt gọi phải ra JSON đúng khuôn ở §6 của bản
thiết kế. Không parse văn xuôi tự do.

**B2. Không viết nổi `plan_files` cụ thể thì không được sang CODE.** Phải đặt
`needs_clarification = true` kèm câu hỏi và nhắn đại ca. Ticket mơ hồ là nguồn gốc của mọi
thảm họa trong loại hệ thống này.

**B3. Chỉ gom ticket thật sự cùng loại.** Cùng phân hệ, cùng kiểu sửa. Gom cho đủ số là tạo ra
một task không ai review nổi. Nghi ngờ thì tách.

**B4. Trích dẫn phải có thật.** Khi viện dẫn tài liệu hay CR cũ, phải kèm đường dẫn tệp và mã
CR lấy từ Qdrant. Cấm bịa mã CR — sổ CR là thứ cả đội tra, một mã bịa là một dấu vết giả.

**B5. Ở REVIEW phải đọc diff.** Không được tổng hợp chỉ dựa trên "bài kiểm xanh". Bài kiểm do
chính bot code viết ra thì việc nó xanh chưa chứng minh được điều gì.

**B6. Đánh `risk_level = 3` cho mọi thứ đụng tiền, phân quyền, migration, hoặc `main`.** Rủi ro
cao thì bản tin Telegram phải nói rõ *rủi ro ở đâu*, không được chỉ dán nhãn.

---

## §C. Bot code (Claude Code CLI)

### Phạm vi

**C1. Bám `plan_files`.** Đụng tệp ngoài danh sách thì phải nói rõ lý do trong bản tổng kết.
Lệch quá **30%** số tệp, hoặc quá `AGENT_MAX_FILES_TOUCHED` tệp, thì **dừng, không commit,
leo thang**.

**C2. Một task một nhánh.** `bot/ai-CR-<số>-<slug>`, cắt từ `erp-v2`. Không làm hai task trên
một nhánh, không cắt nhánh từ nhánh của task khác.

**C3. Không tự sinh migration.** Cần đổi cấu trúc DB thì **dừng và leo thang cho người**.
Migration hỏng trên một cơ sở dữ liệu 141 bảng đang chạy thật là loại lỗi không cứu bằng cách
revert commit. Đây là luật cứng nhất trong §C.

**C4. Không đổi phân quyền, không đổi `seed_prod.py`, không đổi `.github/workflows/`, không
đổi `docker-compose.production.yml`.** Bốn thứ này chạm vào là chạm vào chính bộ máy đang canh
gác nó.

### Chất lượng

**C5. Bắt buộc có bài kiểm, và bắt buộc có bài canh chiều ngược lại.** Không chỉ kiểm "làm
đúng thì chạy", phải có ít nhất một bài canh "cái đáng lẽ không được xảy ra thì không xảy ra" —
đúng khuôn bài canh nút khỏi bị dựng lại ở `bao-CR-419`.

**C6. Chỉ chạy bài kiểm của phần vừa sửa.** Không `npm run check`, không `npm run test`, không
`pytest test/backend` cả cây. Luật này đại ca chốt 17/09/2026 và nó bảo vệ cái máy đang chạy
11 container.

**C7. Viết theo lối của mã xung quanh.** Theo `CLAUDE.md` và `backend/.claude/rules/`. Tên hàm
tiếng Anh, là động từ. Cột trạng thái mới theo luật R2 (`SMALLINT` + `IntEnum`), không lưu chữ
tiếng Việt.

**C8. Không dọn dẹp ngoài phạm vi.** Thấy mã xấu ở chỗ khác thì ghi vào bản tổng kết, đừng sửa.
Một PR tự động mà lẫn mười chỗ "tiện tay dọn" là một PR không ai review.

### Báo cáo

**C9. Bản tổng kết phải nói thật.** Bài kiểm đỏ thì nói đỏ kèm nguyên văn lỗi. Bỏ qua bước nào
thì nói bỏ. Cấm báo "xong" khi chưa chạy cổng kiểm. Một con bot báo cáo đẹp hơn sự thật thì
nguy hiểm hơn một con bot dở.

**C10. Không tự merge, không `--force`, không `git push` lên `main`.**

---

## §D. Khi nào phải dừng và leo thang

Gặp một trong các trường hợp sau thì **dừng ngay, ghi `FAILED` hoặc `NEEDS_INPUT`, nhắn
Telegram**, không tự xoay xở:

1. Cần đổi cấu trúc cơ sở dữ liệu.
2. Cần đổi phân quyền hoặc luật nghiệp vụ mà `plan` không nói tới.
3. Bài kiểm có sẵn (không phải bài mới viết) chuyển từ xanh sang đỏ.
4. Phải sửa quá `AGENT_MAX_FILES_TOUCHED` tệp.
5. Cần đọc hoặc ghi bất kỳ tệp nào trong danh sách cấm ở §E.
6. Hai lần sửa liên tiếp không làm cổng kiểm xanh lên.
7. Hết `AGENT_RUN_TIMEOUT_SEC`.
8. Yêu cầu trong ticket mâu thuẫn với tài liệu chức năng hiện có.

Trường hợp 8 đáng nói riêng: mâu thuẫn ấy **có thể là ticket sai, mà cũng có thể là tài liệu
cũ**. Bot không đủ tư cách phân xử, người mới đủ.

---

## §E. Danh sách cấm cứng

Phải thi hành bằng **cấu hình quyền và biên container**, không phải bằng lời dặn trong prompt.
Một con bot được yêu cầu "đừng đọc `.env`" vẫn đọc được `.env`.

### Cấm đọc và cấm ghi

```
.env  .env.*  *.pem  *.key  *.p12
~/.claude/.credentials.json
backend/app/seed_prod.py
backend/migrations/versions/*
.github/workflows/*
docker-compose.production.yml
mọi thứ ngoài git worktree của task đang làm
```

### Cấm chạy

```
ssh · scp · rsync · sftp
docker · docker compose   (chạy trên máy chủ — cổng kiểm phải gọi qua hub)
wsl --shutdown
git push --force · git push ... main · git merge
curl/wget tới địa chỉ ngoài danh sách cho phép
mọi lệnh xóa ngoài worktree
```

### Biên container

- Chỉ mount **đúng git worktree** của task đó.
- **Không** mount `D:\`, không mount thư mục home, **không** đưa Docker socket vào.
- Chỉ cho ra mạng tới GitHub và API của Claude. Còn lại chặn.

---

## §F. Ghi sổ

**F1. Mỗi task một dòng trong [`change-log-ai.md`](../tai-lieu-ky-thuat/change-log-ai.md)**,
mã `ai-CR-<số>`. Đặt chỗ ngay khi bắt đầu, điền đủ khi xong — đúng nếp của `change-log-bao.md`.

**F2. Dải số `ai-CR-*` là dải riêng**, không chung với `CR-*` và `bao-CR-*`. Cấp số mới thì
grep đúng một tệp.

**F3. Mọi lượt Telegram đều lưu xuống `tab_agent_message`.** Sáu tháng sau còn truy được vì sao
hồi đó chốt vậy — đó chính là thứ `nhat-ky-task.md` đang làm cho việc tay.

**F4. Mọi lượt gọi model đều lưu xuống `tab_agent_run`** kèm token và chi phí. Không đo thì
không biết nó đốt bao nhiêu.

---

## §G. Luật cho chính bộ quy tắc này

Bot **không được sửa tệp này**, không được sửa `CLAUDE.md`, không được sửa
`backend/.claude/rules/`. Sửa luật là việc của đại ca.
