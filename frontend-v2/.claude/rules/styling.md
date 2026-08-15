---
name: styling
description: Tailwind + cn() styling conventions. No string-concatenated class names.
metadata:
  tags: styling, tailwind, cn, classnames
---

# Styling

Tailwind CSS v4. Theme tokens live in `src/app/globals.css` (`:root` / `.dark` CSS variables in `oklch()` + `@theme inline`). There is no `tailwind.config.*` — v4 is configured entirely from CSS. Use semantic tokens (`bg-background`, `text-muted-foreground`, `border-input`, …), not raw hex.

## Always merge classes with `cn()`

`cn` (`@/lib/utils`) = `clsx` + `tailwind-merge`. It composes conditional classes AND resolves Tailwind conflicts (last wins).

```tsx
import { cn } from "@/lib/utils";

<div className={cn("rounded-md border p-4", isActive && "bg-accent", className)} />;
```

## NEVER build class strings by concatenation

Template strings and `+` skip conflict resolution and read poorly.

```tsx
// ❌ FORBIDDEN
<div className={`p-4 ${isActive ? 'bg-accent' : ''} ${className}`} />
<div className={'p-4 ' + (isActive ? 'bg-accent' : '')} />

// ✅ REQUIRED
<div className={cn('p-4', isActive && 'bg-accent', className)} />
```

- Conditional classes → pass as separate `cn` args (`condition && 'class'`), not ternaries inside a template.
- Variant-heavy components → use `class-variance-authority` (`cva`), the shadcn pattern.
- A component that accepts styling overrides takes a `className?: string` prop and merges it LAST inside `cn`.
- Prefer Tailwind utilities over inline `style={{}}`; use `style` only for truly dynamic values (computed positions, colors from data).
