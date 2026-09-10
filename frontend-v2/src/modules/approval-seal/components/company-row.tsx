import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'

interface CompanyRowProps {
  name: string
  logo?: string | null
  taxCode?: string | null
}

/**
 * Một dòng pháp nhân: logo + tên + mã số thuế, khung viền nền mờ. Dùng chung cho
 * danh sách công ty ở chi tiết Duyệt dấu và ở phân công văn thư (sau khi chọn).
 */
export function CompanyRow({ name, logo, taxCode }: CompanyRowProps) {
  const initial = (name.trim()[0] || '?').toUpperCase()
  return (
    <div className="flex items-center gap-3 rounded-md border bg-muted/20 px-3 py-2">
      <Avatar size="sm" className="size-8">
        {logo && <AvatarImage src={logo} alt="" className="object-contain" />}
        <AvatarFallback>{initial}</AvatarFallback>
      </Avatar>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-navy dark:text-foreground">{name}</p>
        <p className="text-xs text-muted-foreground">MST: {taxCode || '—'}</p>
      </div>
    </div>
  )
}
