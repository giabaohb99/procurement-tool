---
name: naming
description: File and symbol naming conventions optimized for fast discovery.
metadata:
  tags: naming, files, conventions
---

# Naming

Goal: a name should tell you what's inside before you open the file. Long-but-descriptive beats short-but-cryptic.

## Files & folders → kebab-case

Every `.ts` / `.tsx` file is kebab-case, named after its main export's role:

| File                    | Contains                    |
| ----------------------- | --------------------------- |
| `todo-list.tsx`         | `TodoList` component        |
| `use-todos.ts`          | `useTodos` hook             |
| `query-client.ts`       | the query client            |
| `user-profile-form.tsx` | `UserProfileForm` component |

- One primary export per file; name the file after it.
- Hooks files start with `use-` (`use-auth.ts`). Component files are the kebab-case of the component name.
- Feature folders: `src/features/<feature>/` with `api/`, `components/`, `hooks/`, `types.ts`, `index.ts`.
- Tests sit next to the file they cover: `utils.ts` → `utils.test.ts`.

## Symbols

- Components & types/interfaces → `PascalCase` (`TodoList`, `interface Todo`).
- Hooks, functions, variables → `camelCase` (`useTodos`, `fetchTodos`).
- Constants that are true constants → `SCREAMING_SNAKE_CASE` only when global/config; otherwise `camelCase`.
- Query-key factories → `<feature>Keys` (e.g. `exampleKeys`), colocated with the feature's API.

## Barrels

- Each feature exposes a public API via `index.ts`. Export the component, hooks, and types other code is allowed to use — nothing else.
