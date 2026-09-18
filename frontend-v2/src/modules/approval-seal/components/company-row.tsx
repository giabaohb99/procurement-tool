import { X } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'

interface CompanyRowProps {
  name: string
  logo?: string | null
  taxCode?: string | null
  onRemove?: () => void
  disabled?: boolean
}

/**
 * Một dòng pháp nhân: logo + tên + mã số thuế, khung viền nền mờ. Dùng chung cho
 * danh sách công ty ở chi tiết Duyệt dấu và ở phân công văn thư (sau khi chọn).
 */
export function CompanyRow({ name, logo, taxCode, onRemove, disabled }: CompanyRowProps) {
  const initial = (name.trim()[0] || '?').toUpperCase()
  return (
    <div className="group flex items-center justify-between gap-3 rounded-lg border border-border/60 bg-muted/20 px-3.5 py-2.5 transition-colors hover:bg-muted/40">
      <div className="flex min-w-0 items-center gap-3">
        <Avatar size="sm" className="size-8 shrink-0 rounded-md border border-border/50 bg-background">
          {logo && <AvatarImage src={logo} alt="" className="object-contain" />}
          <AvatarFallback className="rounded-md text-xs font-semibold text-primary">{initial}</AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-navy dark:text-foreground">{name}</p>
          <p className="text-xs text-muted-foreground">MST: {taxCode || '—'}</p>
        </div>
      </div>
      {onRemove && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-7 shrink-0 text-muted-foreground opacity-60 transition-opacity hover:bg-destructive/10 hover:text-destructive hover:opacity-100 group-hover:opacity-100"
          onClick={onRemove}
          disabled={disabled}
          title={`Gỡ ${name}`}
          aria-label={`Gỡ công ty ${name}`}
        >
          <X className="size-3.5" />
        </Button>
      )}
    </div>
  )
}

