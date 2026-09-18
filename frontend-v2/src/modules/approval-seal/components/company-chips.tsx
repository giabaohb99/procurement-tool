import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import type { SealClerkCompany } from '../types/seal-clerk'

/**
 * Cột "Công ty phụ trách": mỗi công ty một chip ĐỦ ảnh tròn + tên (DEGO HOLDING đã
 * được backend xếp đầu). Kèm tooltip hiển thị đầy đủ tên công ty khi hover.
 */
export function CompanyChips({ companies }: { companies: SealClerkCompany[] }) {
  if (companies.length === 0) return <span className="text-muted-foreground">—</span>

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {companies.map((company) => (
        <Tooltip key={company.id} disableHoverableContent>
          <TooltipTrigger asChild>
            <span className="inline-flex max-w-56 cursor-default items-center gap-1.5 rounded-full border border-border/60 bg-muted/40 py-0.5 pr-2.5 pl-0.5 transition-colors hover:bg-muted/80">
              <Avatar size="sm" className="size-5 shrink-0 border border-border/40 bg-white shadow-2xs [&>*]:pointer-events-none">
                {company.logo && (
                  <AvatarImage src={company.logo} alt={company.name} className="object-contain p-0.5" />
                )}
                <AvatarFallback className="bg-primary/10 text-[9px] font-bold text-primary">
                  {(company.name || '?').trim().charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="truncate text-xs font-medium text-foreground/90">{company.name}</span>
            </span>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs p-2 text-left text-xs shadow-lg">
            {company.name}
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}
