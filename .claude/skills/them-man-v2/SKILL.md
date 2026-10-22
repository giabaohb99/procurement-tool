---
name: them-man-v2
description: Thêm một màn hoặc một phân hệ mới vào ERP v2 (procurement-tool/frontend-v2) — sáu nơi phải khai, bài kiểm đồng bộ, bẫy biểu mẫu, cổng kiểm, và cách commit an toàn ở cây git dùng chung. Dùng mỗi khi tạo route / trang / phân hệ / entity quyền mới ở frontend-v2.
---

# Thêm màn / phân hệ ở frontend-v2

## Khi nào dùng
Tạo trang mới, phân hệ mới, route công khai, hoặc màn cần một khóa quyền (entity) mới. Sửa màn có sẵn thì chỉ cần
phần **Bẫy** + **Kiểm xong**.

## Các bước

1. **Hợp đồng API trước.** Đọc tài liệu của khu backend (vd `doc/agent-hub/06-cong-mcp.md` §7). Thiếu đường thì nhắn
   `ai-mcp` / `nghiep-vu-erp`, đừng tự sửa backend. Backend LOCAL có thể chậm hơn origin (cây chung chưa kéo về): soát
   trường bằng `git fetch -q origin && git grep -n <tên_trường> origin/erp-v2 -- backend/`, không chỉ đọc tệp local.
   Trường mới khai **tùy chọn** (`field?:`) và có nhánh dự phòng khi máy chủ cũ chưa trả.
2. **Thư mục phân hệ** `src/modules/<tên>/`: `api/` · `hooks/` · `types/` · `config/` · `components/` · `pages/` ·
   `utils/` · `routes.tsx`. Không barrel. Gọi API qua `@/core/api` (`apiGet/apiPost/...` đã bóc phong bì).
3. **Khai đủ SÁU nơi** (thiếu một nơi là có bài kiểm đỏ hoặc lỗi âm thầm):

   | # | Tệp | Khai gì |
   |---|---|---|
   | 1 | `src/app/router/module-registry.ts` | import `<tên>Module`, đặt vào mảng (thứ tự = thứ tự màn chọn phân hệ) |
   | 2 | `src/shared/constants/app-routes.ts` | đường của từng màn; route công khai đặt ở gốc |
   | 3 | `src/shared/constants/query-keys.ts` | khối khóa `[<phân hệ>, <thực thể>, <tham số>]`, không gõ chuỗi khóa tại chỗ |
   | 4 | `src/shared/notifications/notification-link.ts` | thêm tiền tố `/<tên>` vào `V2_PREFIXES` (xếp chữ cái) |
   | 5 | `src/core/authorization/permission-types.ts` | entity mới vào `ENTITIES` — phải khớp `ENTITIES` backend |
   | 6 | `src/modules/system/config/permission-groups.ts` | entity mới vào đúng nhóm ở màn phân quyền (quên thì nó rơi vào nhóm Khác, không báo lỗi) |

   Route ngoài khung (trang in, đồng ý OAuth, trang công khai) khai ở `src/app/router/app-router.tsx`: cần đăng nhập
   thì trong `ProtectedRoute`, công khai thì ở mảng con gốc, kèm `errorElement`.
4. **Menu phân hệ** (`routes.tsx`): mỗi mục tự gác bằng `entity` / `entities` / `manage`. Phân hệ mở cho nhiều khóa thì
   KHÔNG khai `entity` cấp phân hệ — `canOpenModule` đếm mục còn hiện. Mục trùng tiền tố đặt `end: true` + `matchPaths`;
   trang con không lên menu thì thêm mục `hidden: true` để giữ chốt quyền khi gõ thẳng URL.
5. **Màn**: bảng dùng `DataTable` (`docs/ui/table.md`), ô chỉ xem dùng `readOnly` / `read-only-value.tsx`, class qua
   `cn()`, icon `lucide-react`, chữ trên giao diện tiếng Việt, tên hàm tiếng Anh.
6. **Bài kiểm đặt cạnh tệp**: `routes.test.ts` (ai thấy mục nào), hàm thuần (`config/`, `utils/`), màn có hành vi dễ
   sai. Mock ở `@/core/api`, đừng mock axios. Viết để làm nó SAI: rỗng, 0, âm, quá dài, thiếu quyền, bấm đúp.
7. **Ghi sổ** (dòng change-log-bao + mục nhật ký, câu tiếng Việt trọn ý, dòng cuối `Mã nguồn:` / `Commit:`).

## Bẫy đã gặp

- **Quên `V2_PREFIXES`** (bao-CR-623/624, 19/10/2026): thêm phân hệ `/ai-skill` mà không khai → link thông báo bị coi
  là đường cũ, chết. Chỉ `notification-link.test.ts` ở bộ kiểm FULL bắt được — chạy thêm `src/shared/notifications`.
- **`ENTITIES` hai đầu lệch** (05/09/2026): FE 51 khóa, BE 53 → `can('khoa_moi')` không biên dịch, người viết ép kiểu
  hoặc bỏ cổng quyền. `test/backend/test_dong_bo_giao_dien_v2.py` canh, kèm mục `manage: true` phải có đủ
  create / write / delete ở backend.
- **NavLink không `end`** (bao-CR-623, 17/10/2026): mục gốc `/ai-skill` sáng ở mọi trang con.
- **Cột phải đè mất bảng ở màn hẹp** (bao-CR-638, 19/10/2026): `flex-col` + bảng `fillHeight` co về 0 khi có thêm cột
  phụ. Cột phụ `hidden xl:block` + nút mở hộp thoại dưới xl; bảng cần `min-w-0` kẻo cột phải bị đẩy ra ngoài màn rộng.
- **Bốn bẫy biểu mẫu** (duoc-CR-317): ô sai ở tab ẩn → bấm Lưu im lặng (cần `onInvalid` nhảy tab); Enter trong ô con
  submit form cha; nút mở hộp trong `<form>` thiếu `type="button"` là submit; `disabled={isPending}` KHÔNG chặn bấm
  đúp — chặn bằng `useRef`.
- **Gọi API "tốn" lúc mở màn** (bao-CR-638): đường có ghi nhật ký / không cache (vd xem lại khóa `reveal`) phải là
  `useMutation` gọi khi bấm, KHÔNG `useQuery`. Có bài kiểm "mở màn không gọi".
- **`getBy` trước khi dữ liệu về** → bài kiểm chập chờn; dùng `findBy`.
- **`DataTable` nuốt ô `'—'` / `'-'`** (CR-132, 24/08/2026): ô trả đúng chuỗi đó bị đổi thành ô trống
  (`shared/data-table/data-table.tsx`, vòng vẽ hàng) — bài kiểm tìm `—` trong bảng sẽ không thấy. Cần gạch thật thì trả
  `<span>—</span>`. Ghi ở `frontend-v2/docs/ui/table.md` §1.
- **Cây git dùng chung bị agent khác rebase dở** (19/10/2026): commit của mình dính dấu `<<<<<<<` vào tệp backend, sau
  đó họ `rebase --abort` làm cây lùi về ảnh cũ, mất tệp mới. Xem bước commit bên dưới.

## Commit an toàn ở cây chung (chỉ sau khi đại ca gật trong phiên)

Không add từ cây làm việc khi cây có sửa dở của người khác. Dựng commit bằng **index tạm** trên đầu origin:
```bash
git fetch -q origin
export GIT_INDEX_FILE=/tmp/idx-<cr>   # index riêng, KHÔNG đụng index chung
git read-tree origin/erp-v2
for f in <danh sách tệp của mình>; do git update-index --add --cacheinfo 100644,$(git hash-object -w "$f"),"$f"; done
# hai sổ: lấy bản origin + chèn đúng khối của mình rồi hash-object -w --stdin
git write-tree                                 # -> <tree>
git commit-tree <tree> -p origin/erp-v2 -F msg.txt   # -> <sha>
unset GIT_INDEX_FILE
git push origin <sha>:refs/heads/erp-v2
```
Trước đó: `git status` không có "rebase in progress"; `grep '^<<<<<<<'` các tệp sạch; tệp frontend của mình không bị
thay đổi trên origin từ lúc chạy cổng (`git diff --stat <gốc> origin/erp-v2 -- frontend-v2`).

## Kiểm xong
- typecheck 0, lint 0 lỗi (cảnh báo không tăng — 19/10/2026 là 29; CLAUDE.md còn ghi 23, chờ đợt dọn tài liệu sửa).
- vitest: thư mục phân hệ đã sửa (+ khu dùng chung đã đụng). CHỈ KHI THÊM MÀN / PHÂN HỆ / ROUTE MỚI mới chạy thêm
  `src/app/router` + `src/shared/constants` + `src/shared/notifications` (bắt sót khai ở sáu nơi). Sửa màn có sẵn thì thôi.
- Mở thử trên trình duyệt local ở 1440 và màn hẹp; route công khai mở được khi chưa đăng nhập.
- Báo `dieu-phoi`: số CR, mã commit, tệp, cổng kiểm.
