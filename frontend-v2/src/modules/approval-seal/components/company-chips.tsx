import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import type { SealClerkCompany } from '../types/seal-clerk'

/**
 * Cột "Công ty phụ trách": mỗi công ty một chip ĐỦ ảnh tròn + tên (DEGO HOLDING đã
 * được backend xếp đầu). Chip tự xuống dòng khi nhiều công ty.
 */
export function CompanyChips({ companies }: { companies: SealClerkCompany[] }) {
  if (companies.length === 0) return <span className="text-muted-foreground">—</span>

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {companies.map((company) => (
        <span
          key={company.id}
          title={company.name}
          className="inline-flex max-w-full items-center gap-1.5 rounded-full border bg-muted/30 py-0.5 pr-2 pl-0.5"
        >
          <Avatar size="sm" className="size-5">
            <AvatarImage src={company.logo} alt={company.name} className="object-contain" />
            <AvatarFallback>{(company.name || '?').trim().charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>
          <span className="truncate text-xs">{company.name}</span>
        </span>
      ))}
    </div>
  )
}
