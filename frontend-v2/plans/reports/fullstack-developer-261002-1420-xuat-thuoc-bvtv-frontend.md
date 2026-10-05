# Xuất Excel mục Thuốc BVTV — v1 + v2

## Status: DONE

## Việc đã làm

### v1 (`frontend/`, `/customs-prices/pesticides`)
- Mới `frontend/src/components/customs/CustomsPesticideExportMenu.tsx` — nút «Xuất Excel» +
  dropdown 2 lựa chọn, khuôn portal bám nút bê từ `TableToolbar.tsx` (`.col-menu` CSS có sẵn,
  không sửa `index.css`). Tải bằng `downloadBlob`/`blobErrorMessage` đã có sẵn ở
  `customs-shared.ts` (dùng chung với nút Xuất Excel của thẻ Danh sách) — không viết lại.
- Sửa `CustomsPesticideTab.tsx`: thêm `canExport = can('customs_price', 'export')`, gắn menu
  cạnh «Nạp danh mục», `disabled` khi `catalogTotal === 0`.
- scope=page gửi `buildPesticideParams(applied) + page + page_size` — ĐÚNG tham số `load()` đang
  dùng gọi `GET /pesticides`; scope=all chỉ gửi `{scope:'all'}`.
- Chặn bấm đúp bằng `useRef` (không chỉ `disabled`), theo đúng bẫy nêu trong
  `frontend-v2-ui-conventions.md` (áp dụng tinh thần cho v1 luôn, dù luật đó viết cho v2).

### v2 (`frontend-v2/`, phân hệ procurement)
- Mới `customs-pesticide-export-menu.tsx` — `DropdownMenu` shadcn, `useSingleFlight` (hook có
  sẵn) chặn bấm dồn, gọi `exportCustomsPesticides(params)`.
- Mới `customs-pesticide-filter-controls.tsx` — tách cụm ô tìm + 4 `Select` ra khỏi
  `customs-pesticide-tab.tsx` (tệp đó đã 236 dòng TRƯỚC khi tôi đụng, +nút export vượt hẳn 200 —
  tách để cả hai tệp dưới 200 dòng, theo luật modularization). `customs-pesticide-tab.tsx` còn
  196 dòng.
- Sửa `customs-pesticide-api.ts`: thêm `exportCustomsPesticides(params)` — tải `GET
  /pesticides/export`, lỗi blob đọc lại thành JSON qua `readBlobErrorMessage` (export MỚI từ
  `customs-api.ts`, tái dùng logic đã có cho `exportCustomsLines` — tránh viết trùng parser lỗi
  blob lần hai trong cùng module).
- Sửa `customs-api.ts`: đổi `readBlobErrorMessage` từ private → export (dùng chung).
- Sửa `use-customs-pesticides.ts`: `usePesticidePermissions` thêm `canExport:
  can('customs_price', 'export')`.
- Sửa `customs-pesticide-tab.tsx`: gắn nút export cạnh «Nạp danh mục», prop `filterParams =
  buildPesticideParams(filters)` (KHÔNG kèm page/page_size — hook export tự thêm khi scope=page),
  `pageRowCount`, `disabled={catalogTotal === 0}`.

## Hợp đồng gửi lên backend (cả hai bản khớp nhau)
- `GET /api/customs/pesticides/export?scope=page` → kèm `q · status · pest_group · sector ·
  banned_only · page · page_size` (đúng tên tham số `list_pesticides` đang nhận, đã đọc
  `pesticide_controller.py` để xác nhận — backend export chưa có lúc tôi làm, agent khác đang
  viết song song).
- `scope=all` → chỉ `{scope: 'all'}`, không kèm gì khác.

## Test
- v2: 2 test mới trong `customs-pesticide-tab.test.tsx` (ẩn nút khi thiếu `customs_price.export`,
  khóa nút khi danh mục rỗng — độc lập với quyền `customs_pesticide`) + 5 test mới ở
  `customs-pesticide-export-menu.test.tsx` (tham số scope=page đúng bộ lọc+trang, scope=all
  không kèm lọc, khóa nút lúc tải + bỏ qua bấm thứ hai, đọc đúng câu lỗi tiếng Việt từ blob JSON,
  khóa khi rỗng danh mục). Mock ở `@/core/api/download-file` (đúng submodule thật sự gọi mạng —
  barrel `@/core/api` không chặn được vì `downloadFile` import `httpClient` trực tiếp; đây là
  khuôn đã có sẵn ở `purchase-progress-page.test.tsx`).
- v1: không có hạ tầng test đơn vị (chỉ gác bằng `tsc --noEmit` theo luật đóng băng).

## Cổng chạy
- v2 `npm run typecheck`: 0 lỗi.
- v2 `npm run lint`: 0 lỗi, 29 cảnh báo — TOÀN BỘ ở tệp không đụng tới (đối chiếu từng dòng cảnh
  báo với tệp sửa, không trùng).
- v2 `npx vitest run src/modules/procurement`: 76 tệp / 786 bài, xanh hết (gồm 2 tệp mới).
- v1 `npm run typecheck` (service `web`): đúng 4 lỗi cũ (`AttachmentGallery.tsx`,
  `DocumentAttachmentSection.tsx`, `SurveyRequestDetail.tsx` ×2) — không thêm lỗi.

## Concerns / việc chưa chắc
- Backend `/pesticides/export` CHƯA tồn tại lúc tôi viết (agent backend làm song song) — tôi
  dựng đúng theo hợp đồng trong đề bài, chưa thử gọi thật E2E. Nếu backend đặt tên tham số khác
  (vd `pest_group` → khác tên) thì chỉ cần sửa `buildPesticideParams` (v1: `utils/customs-pesticide.ts`,
  v2: cùng tên tệp khác thư mục) — một chỗ, không rẽ nhánh.
- Comment đầu `CustomsPesticideExportMenu.tsx` (v1) không gắn số CR vì tôi không biết mã CR thật
  của việc này — nếu đại ca có số CR xin điền vào.
