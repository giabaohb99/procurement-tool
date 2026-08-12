---
name: typescript
description: TypeScript conventions — component props and avoiding `any`.
metadata:
  tags: typescript, props, types, any
---

# TypeScript

Strict mode is on (`tsconfig.json`). Write code the next reader (human or AI) understands without running it.

## Component props

- Define props inline for tiny components, or as a named `interface` when reused/exported:
  ```tsx
  interface TodoListProps {
    items: Todo[]
    onSelect?: (id: number) => void
    className?: string
  }

  export function TodoList({ items, onSelect, className }: TodoListProps) { … }
  ```
- Name the props type `<Component>Props`.
- Destructure props in the signature — don't reach into a `props` object.
- Components that render children type them as `React.ReactNode`.
- Reuse domain types from the feature's `types.ts` (e.g. `Todo`); don't redefine shapes inline.

## Avoid `any`

- `any` is a last resort, not a default. Prefer:
  - a concrete type or `interface`,
  - `unknown` + a narrowing check when the shape is truly unknown (e.g. caught errors, external JSON),
  - generics for reusable helpers.
- Type API responses explicitly: `apiClient.get<Todo[]>('/todos')`.
- If `any` is genuinely unavoidable, isolate it behind a typed boundary and leave a `// why:` comment. Never let `any` leak into a public/exported signature.

## General

- Let TypeScript infer local variables; annotate function boundaries (params + return when non-obvious) and exported APIs.
- Use `import type { … }` for type-only imports.
- No non-null `!` assertions — narrow instead.

## Next.js generated types

`next build` / `next dev` generate route types into `.next/types`. Prefer them over hand-written shapes:

- Layouts: `{ children }: LayoutProps<"/">` (see `src/app/layout.tsx`).
- Pages with params/searchParams: `PageProps<"/route/[id]">`.
- In Next 16 `params` and `searchParams` are **Promises** — `await` them inside async Server Components.
