---
name: components
description: How to source, place, and build UI components in this project.
metadata:
  tags: components, shadcn, ui, base-ui, rsc
---

# Components

## Where components live

- Shared/reusable UI → `src/components/` (generic shadcn primitives in `src/components/ui/`).
- Feature-specific components → `src/features/<feature>/components/` (never in the shared dir).
- Import a feature's components ONLY through its barrel: `@/features/<feature>` — never reach into internal paths.

## Sourcing policy (in strict priority order)

When you need a UI component, decide in this order — do NOT hand-roll something shadcn already ships:

1. **shadcn/ui first.** If it exists in shadcn, install it:
   ```bash
   npx shadcn@latest add <component>   # e.g. dialog, input, card, table
   ```
   It lands in `src/components/ui/`. Config is `components.json` (style: `base-nova`, baseColor: neutral, icons: lucide, rsc: true). Primitives are built on **Base UI** (`@base-ui/react`), not Radix.
2. **Another library** only if shadcn does NOT have it (e.g. a data grid, date picker beyond shadcn). Prefer well-maintained, Tailwind-friendly libs. Add a one-line comment noting why the external lib was chosen.
3. **Custom** only when the component is trivial (a badge, a layout wrapper, a simple state display). Keep it small, colocate it, style with `cn` + Tailwind.

Rule of thumb: shadcn > library > custom. Reach for custom only when it's genuinely simpler than pulling a dependency.

## Building a component

- Never guess whether a shadcn component exists — check the registry (`npx shadcn@latest add <name>` will tell you) before writing it by hand.
- Do not edit `src/components/ui/**` by hand except to wire variants; treat them as generated.
- Compose shadcn primitives instead of duplicating their markup.
- Icons come from `lucide-react`.

## Server vs Client Components (App Router)

- Components are **Server Components by default**. Add `"use client"` only when the file needs state, effects, event handlers, or browser APIs.
- Push `"use client"` as far down the tree as possible — keep pages/layouts server-side and mark only the interactive leaf.
- Server Components must not import a client-only module's hooks; pass data down as props instead.
