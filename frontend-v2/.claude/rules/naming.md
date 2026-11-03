---
name: naming
description: File and symbol naming conventions optimized for fast discovery.
metadata:
  tags: naming, files, conventions
---

# Naming (riêng frontend-v2)

Goal: a name should tell you what's inside before you open the file. Long-but-descriptive beats short-but-cryptic.

## Files & folders → kebab-case

Every `.ts` / `.tsx` file is kebab-case, named after its main export's role:

| File                     | Contains                     |
| ------------------------ | ---------------------------- |
| `employee-list-page.tsx` | `EmployeeListPage` component |
| `use-employees.ts`       | `useEmployees` hook          |
| `employee-api.ts`        | the employee API functions   |
| `query-client.ts`        | the query client             |

- One primary export per file; name the file after it.
- Hooks files start with `use-` (`use-permission.ts`). Component files are the
  kebab-case of the component name. API files end with `-api.ts`. Page components
  end with `-page.tsx` and live in `pages/`.
- Module folders: `src/modules/<module>/` with `api/`, `components/`, `config/`,
  `hooks/`, `pages/`, `types/`, `utils/`, `routes.tsx`. Not every module needs every
  folder — create one when there is something to put in it.
- Tests sit next to the file they cover: `format-money.ts` → `format-money.test.ts`.

## Symbols

- Components & types/interfaces → `PascalCase` (`EmployeeListPage`, `interface Employee`).
- Hooks, functions, variables → `camelCase` (`useEmployees`, `fetchEmployees`).
- Constants that are true constants → `SCREAMING_SNAKE_CASE` only when global/config; otherwise `camelCase`.
- A module's route definition is exported as `<module>Module` from
  `modules/<module>/routes.tsx` and registered in `src/app/router/module-registry.ts`.

## Query keys

There are **no per-feature `<feature>Keys` factories**. All query keys live in one
place: `src/shared/constants/query-keys.ts`, shaped `[<module>, <entity>, <params>]`
so invalidation can work by level. Add new keys there; never inline a raw key string.
The one deliberate exception is a key used by exactly one hook and never invalidated
from outside it — keep it as a local `const …Keys` at the top of that hook file and
say why in a comment.

## Barrels

**Modules do NOT have barrels.** Import the exact file
(`@/modules/hr/components/employee-form-dialog`). Only self-contained shared kits
expose an `index.ts` (`@/shared/conditional-filter`, `@/core/api`); don't add more.

## Luật chung

Định danh tiếng Anh, hàm là động từ, chuỗi / chú thích tiếng Việt, không emoji, commit, bài kiểm: xem
`.claude/rules/chung-dat-ten-va-quy-uoc.md` ở gốc repo (luôn nạp, gom 03/11/2026 — bao-CR-712). Tệp này chỉ giữ phần
RIÊNG của frontend-v2.
