---
name: testing
description: Vitest + Testing Library setup, what to test, and the three gates that must stay green.
metadata:
  tags: testing, vitest, testing-library, lint
---

# Testing

Runner: **Vitest 4** (`vitest.config.ts`), DOM: **jsdom**, component queries:
**@testing-library/react**. Linter: **ESLint 10** flat config (`eslint.config.js`) —
`@eslint/js` + `typescript-eslint` + `react-hooks` v7 + `react-refresh`, với
`eslint-config-prettier` đặt cuối. Định dạng: **Prettier** (`.prettierrc.json`,
kèm `prettier-plugin-tailwindcss` tự sắp xếp class Tailwind).

`typescript` đang ghim ở **5.9.3** (không phải 7.x) vì `typescript-eslint@8` chưa
chạy được trên TS 7. Đừng nâng lên 7 nếu chưa kiểm tra ESLint còn dựng được.

Mọi thứ chạy trong Docker service `erp`:

```bash
docker compose exec erp npm run check        # typecheck + lint + test (chạy hết trước khi báo xong việc)
docker compose exec erp npm run test         # vitest run
docker compose exec erp npm run test:watch   # vitest ở chế độ theo dõi
docker compose exec erp npm run lint         # eslint .
docker compose exec erp npm run lint:fix     # eslint . --fix
docker compose exec erp npm run typecheck    # tsc --noEmit
docker compose exec erp npm run format       # prettier --write . (đọc ghi chú bên dưới)
```

Ba cổng, cả ba phải xanh:

| Cổng        | Ngưỡng                                                 |
| ----------- | ------------------------------------------------------ |
| `typecheck` | **0 lỗi**                                              |
| `lint`      | **0 lỗi**. Cảnh báo còn vài chỗ cũ — đừng thêm mới      |
| `test`      | **toàn bộ xanh**                                       |

**`format:check` CHƯA nằm trong `check`** và hiện đỏ ở ~381 tệp: Prettier mới được
thêm vào, chưa ai chạy `format --write` cho toàn bộ mã. Đừng tự ý chạy
`npm run format` trên cả cây trong lúc đang làm việc khác — nó đẻ ra một diff khổng
lồ đè lên việc đang làm dở của người khác. Chạy riêng, thành một commit độc lập,
lúc không ai sửa dở.

## Where tests go

Next to the file they cover: `format-money.ts` → `format-money.test.ts`.
No `__tests__/` folder, no separate mirror tree. The only file outside that rule is
`src/test/setup.ts` (dọn DOM sau mỗi test + nạp matcher của jest-dom).

## What to test

Đi từ chỗ dễ sai nhất, không chạy theo phần trăm bao phủ:

1. **Hàm thuần có quy tắc nghiệp vụ** — tiền, ngày, đọc số thành chữ, dịch bộ lọc
   thành query param. Rẻ, chạy nhanh, và chính là chỗ lỗi âm thầm hay nằm.
2. **Ràng buộc dữ liệu** — bảng đăng ký module, hằng số phải khớp nhau
   (xem `src/app/router/module-registry.test.ts`).
3. **Hành vi component mà người dùng thấy được** — bấm được / không bấm được,
   hiện gì khi rỗng, gọi callback với đối số nào. Khẳng định theo VAI TRÒ và
   NỘI DUNG (`getByRole`, `getByText`), **không** theo class Tailwind hay
   `data-testid` bịa ra.

Không viết test cho: dựng bố cục thuần túy, đầu ra của thư viện ngoài, hay
"gọi hàm này rồi kiểm tra chính hàm này được gọi".

## Conventions

- Không bật `globals` — `import { describe, expect, it, vi } from 'vitest'` rõ ràng.
- Tên `it(...)` viết bằng **tiếng Việt**, mô tả HÀNH VI chứ không mô tả hàm:
  "làm tròn tới đồng, không để lẻ rò ra cột danh sách", không phải "test formatMoney".
- Test nào nhắc lại một lỗi đã từng xảy ra thì ghi rõ lỗi đó trong comment —
  người sau đọc mới biết tại sao không được xóa.
- Múi giờ khi chạy test cố định `Asia/Ho_Chi_Minh` (đặt trong `vitest.config.ts`).
  Đừng viết khẳng định phụ thuộc "hôm nay"; truyền ngày cụ thể vào.
- Gọi API thật thì mock ở tầng `@/core/api` (`vi.mock`), không mock `axios`.
