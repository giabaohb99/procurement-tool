import { cn } from '@/shared/utils/cn'

interface ScopeChipProps {
  label: string
  active: boolean
  onToggle: () => void
  /** Chip loại trừ tô đỏ để không nhầm với chip "được xem". */
  danger?: boolean
}

/** Chip bật/tắt một giá trị trong phạm vi dữ liệu (công ty, phòng ban, nhân sự). */
export function ScopeChip({ label, active, onToggle, danger }: ScopeChipProps) {
  return (
    <button
      type="button"
      title={label}
      onClick={onToggle}
      aria-pressed={active}
      className={cn(
        'max-w-56 truncate rounded-md border px-2.5 py-1 text-xs transition-colors',
        active
          ? danger
            ? 'border-destructive bg-destructive/10 text-destructive'
            : 'border-primary bg-primary/10 text-primary'
          : 'border-input bg-background text-foreground hover:bg-accent',
      )}
    >
      {label}
    </button>
  )
}
