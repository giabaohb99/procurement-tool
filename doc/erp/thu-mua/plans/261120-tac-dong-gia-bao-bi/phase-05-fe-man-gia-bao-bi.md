# Phase 05 — FE màn Giá bao bì (frontend-v2, phân hệ Thu mua)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P2 · 10 giờ · dựng khung theo hợp đồng phase 04, nối API thật sau khi 04 xong. Giao agent `giao-dien-v2`.

## Vì sao ở Thu mua, không ở phân hệ Báo cáo
Màn có **ghi** (báo giá, ngưỡng, định mức, nhập Excel) — phân hệ Báo cáo chỉ đọc và gác lớp thứ ba `require_report`.
Tiền lệ sát nhất là *Tra cứu thị trường* (`customs_price`): một khu trong Thu mua với khóa quyền riêng. Không thêm
`ReportKey` (đỡ một lớp gác không cần); nếu sau này muốn thẻ trong danh mục Báo cáo thì cấp khóa 31 ở đợt đó.

## Menu (trong `procurement/routes.tsx`, nhóm mới "Giá bao bì", mọi mục gác `entity: 'packaging_cost'`)
| Mục | Đường (`app-routes.ts`) | Màn |
|---|---|---|
| Tác động giá bao bì | `/procurement/packaging-cost` (`end: true`) | chọn mã, giá giả định, KPI, bảng SP bị ảnh hưởng, Xuất Excel |
| Bảng giá VTBB | `/procurement/packaging-cost/prices` | bảng phân trang máy chủ, chip nhóm, lọc "chỉ mã vượt ngưỡng", nút Báo giá / Ngưỡng từng dòng, Xuất Excel |
| Báo giá VTBB | `/procurement/packaging-cost/quotes` | danh sách + "+ Báo giá mới" (hộp thoại), sửa / xóa |
| Định mức bao bì | `/procurement/packaging-cost/boms` | danh sách + sửa (hộp thoại) + nút "Nhập từ Excel" (module 4) |
`V2_PREFIXES` đã có `/procurement` — không sửa. Khóa `packaging_cost` vào `permission-types.ts` + `permission-groups.ts`
**cùng commit với phase 01**.

## Màn Tác động (bám bản mẫu `renderImpact` / `drawImpact`)
- Ô chọn nhiều mã: dựa `shared/ui/multi-picker.tsx`; nguồn `GET /code-options` (nạp một lần, lọc tại trình duyệt). Gõ tên
  nhóm ("chai", "nắp", "nhãn, thùng") = lọc theo nhóm, còn lại tìm không dấu trong mã / tên; nút **Chọn tất cả (n)** chọn
  đúng các mã đang lọc; chip tối đa 8 + "+n mã"; trần 500 mã (báo khi vượt).
- Bảng mã đã chọn: giá cũ, mới (bảng giá), ô **giá giả định** (`shared/ui/number-input.tsx`, nhập kiểu vi-VN), chênh, %,
  số SP dùng, min / max, sàn / trần; ô ra ngoài ngưỡng tô đỏ + chú thích.
- Thẻ KPI: mã đã chọn (theo nhóm), SP bị ảnh hưởng, SP tăng (kèm số giảm), tăng nhiều nhất /thùng (kèm /chai).
- Bảng SP: STT, mã HH, tên, quy cách, 5 ô thành phần (mã + "cũ → mới"), CP/chai cũ, mới (hoặc giả định), tăng/giảm /chai,
  /thùng, ghi chú (ghép nhãn từ bộ mã `CostWarning` + `PackagingRole` sinh TS). Bảng nạp đủ dòng → tìm / xếp tại trình duyệt,
  phân trang trình duyệt. Mã đang chọn tô nổi trong ô thành phần.
- Gọi `POST /impact` bằng `useQuery` khóa `[procurement, packagingImpact, {codes, assumed, range}]`, trễ 400 ms khi gõ giá
  giả định, giữ dữ liệu cũ khi đang tải.

## Tệp (kebab-case, mỗi tệp < 200 dòng) — `frontend-v2/src/modules/procurement/`
- `api/packaging-cost-api.ts`, `types/packaging-cost-types.ts`
- `hooks/use-packaging-impact.ts`, `use-packaging-price-list.ts`, `use-packaging-quotes.ts`, `use-packaging-boms.ts`
- `pages/packaging-impact-page.tsx`, `packaging-price-list-page.tsx`, `packaging-quote-list-page.tsx`, `packaging-bom-list-page.tsx`
- `components/packaging-code-picker.tsx`, `packaging-impact-selected-table.tsx`, `packaging-impact-kpi-cards.tsx`,
  `packaging-impact-products-table.tsx`, `packaging-quote-dialog.tsx`, `packaging-price-limit-dialog.tsx`,
  `packaging-bom-dialog.tsx`, `packaging-bom-import-button.tsx` (theo nếp `hr/components/employee-import-button.tsx`)
- `utils/packaging-code-match.ts` (lọc theo nhóm / không dấu), `utils/packaging-warning-text.ts`
- Sửa: `routes.tsx`, `shared/constants/app-routes.ts`, `shared/constants/query-keys.ts`.

## Bài kiểm vitest (cạnh tệp; mock ở `@/core/api`)
- `routes.test.ts`: có / không có `packaging_cost.read` → thấy / không thấy 4 mục; gõ thẳng URL thiếu quyền bị chặn.
- `packaging-code-match.test.ts`: "chai" = lọc nhóm, "nhan, thung" = hai nhóm, "nắp 0085" = tìm thường, bỏ dấu.
- `packaging-code-picker.test.tsx`: Chọn tất cả chỉ chọn mã đang lọc; vượt 500 bị chặn.
- `packaging-impact-selected-table.test.tsx`: nhập "1.234,5" → gửi 1234.5; xóa ô → bỏ giả định; vượt trần tô đỏ.
- `packaging-quote-dialog.test.tsx`: thiếu mã / giá âm bị chặn; bấm đúp chỉ gửi một lần (`useRef`); nút trong form có `type="button"`.
- `packaging-impact-products-table.test.tsx`: CP rỗng hiện `<span>—</span>` (DataTable nuốt chuỗi gạch trần), ghi chú ghép đúng nhãn.

## Kiểm xong
`npm run typecheck` 0, `npm run lint` 0 lỗi (cảnh báo không tăng), `npx vitest run src/modules/procurement` +
`src/app/router src/shared/constants src/shared/notifications` (màn mới). Mở thử 1440 và khổ hẹp (emulate, không resize).

## Rủi ro
| Rủi ro | KN x AH | Giảm thiểu |
|---|---|---|
| Bảng SP hàng nghìn dòng giật | TB x TB | Phân trang trình duyệt 100 dòng; tính sẵn chuỗi tìm |
| Gõ giá giả định gọi API dồn dập | Cao x Thấp | Trễ 400 ms, khóa query ổn định |
| Lệch nhãn trạng thái tay | Thấp x TB | Chỉ dùng bộ mã sinh TS, không viết tay danh sách |
