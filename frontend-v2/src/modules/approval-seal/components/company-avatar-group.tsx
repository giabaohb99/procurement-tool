import { Building2 } from 'lucide-react'

import { Avatar, AvatarFallback, AvatarGroup, AvatarImage } from '@/shared/ui/avatar'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import type { SealCompanyRef } from '../types/seal-request'

interface CompanyAvatarGroupProps {
  companies: SealCompanyRef[]
  maxVisible?: number
  showNameWhenSingle?: boolean
}

export function CompanyAvatarGroup({
  companies,
  maxVisible = 4,
  showNameWhenSingle = true,
}: CompanyAvatarGroupProps) {
  if (!companies || companies.length === 0) {
    return <span className="text-muted-foreground">—</span>
  }

  // Trường hợp chỉ có 1 công ty: Hiển thị Avatar + Tên công ty kèm Tooltip
  if (companies.length === 1) {
    const c = companies[0]
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="inline-flex max-w-full cursor-pointer items-center gap-2 rounded-md py-0.5 transition-colors hover:text-primary">
            <Avatar size="sm" className="size-6 shrink-0 border border-border/60 bg-white shadow-2xs">
              <AvatarImage src={c.logo} alt={c.name} className="object-contain p-0.5" />
              <AvatarFallback className="bg-primary/10 text-[10px] font-bold text-primary">
                {(c.name || '?').trim().charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            {showNameWhenSingle && (
              <span className="truncate text-xs font-medium text-foreground">
                {c.name}
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-sm space-y-1 p-2.5 text-left shadow-lg">
          <div className="flex items-start gap-1.5 font-semibold text-xs text-background">
            <Building2 className="size-3.5 shrink-0 mt-0.5 text-primary-foreground/70" />
            <span className="break-words leading-tight">{c.name}</span>
          </div>
          {c.tax_code && (
            <div className="font-mono text-[11px] text-background/80 pl-5">
              MST: {c.tax_code}
            </div>
          )}
        </TooltipContent>
      </Tooltip>
    )
  }

  // Trường hợp từ 2 công ty trở lên: Hiển thị Avatar Group xếp đè nhau
  const visibleCompanies = companies.slice(0, maxVisible)
  const remainingCount = companies.length - maxVisible

  return (
    <div className="flex items-center gap-2">
      <AvatarGroup className="-space-x-2">
        {visibleCompanies.map((c) => (
          <Tooltip key={c.id}>
            <TooltipTrigger asChild>
              <Avatar
                size="sm"
                className="size-7 cursor-pointer border-2 border-background bg-white shadow-2xs transition-all hover:z-20 hover:scale-115 hover:border-primary"
              >
                <AvatarImage src={c.logo} alt={c.name} className="object-contain p-0.5" />
                <AvatarFallback className="bg-primary/10 text-[10px] font-bold text-primary">
                  {(c.name || '?').trim().charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-sm space-y-1 p-2.5 text-left shadow-lg">
              <div className="flex items-start gap-1.5 font-semibold text-xs text-background">
                <Building2 className="size-3.5 shrink-0 mt-0.5 text-primary-foreground/70" />
                <span className="break-words leading-tight">{c.name}</span>
              </div>
              {c.tax_code && (
                <div className="font-mono text-[11px] text-background/80 pl-5">
                  MST: {c.tax_code}
                </div>
              )}
            </TooltipContent>
          </Tooltip>
        ))}

        {remainingCount > 0 && (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="relative flex size-7 shrink-0 cursor-pointer items-center justify-center rounded-full border-2 border-background bg-muted text-[11px] font-bold text-muted-foreground shadow-2xs transition-transform hover:z-20 hover:scale-110">
                +{remainingCount}
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-sm p-2.5 text-left shadow-lg space-y-1.5">
              <div className="font-semibold text-xs text-background border-b border-background/20 pb-1">
                Các công ty khác ({remainingCount}):
              </div>
              <ul className="space-y-1.5 text-xs text-background/90 max-h-48 overflow-y-auto">
                {companies.slice(maxVisible).map((c) => (
                  <li key={c.id} className="space-y-0.5">
                    <div className="break-words leading-tight">• {c.name}</div>
                    {c.tax_code && (
                      <div className="text-[10px] text-background/70 pl-2 font-mono">
                        MST: {c.tax_code}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </TooltipContent>
          </Tooltip>
        )}
      </AvatarGroup>

      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-pointer text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground hover:underline underline-offset-2">
            ({companies.length} công ty)
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-sm p-2.5 text-left shadow-lg space-y-1.5">
          <div className="font-semibold text-xs text-background border-b border-background/20 pb-1">
            Danh sách công ty ({companies.length})
          </div>
          <ul className="space-y-1.5 text-xs text-background/90 max-h-48 overflow-y-auto">
            {companies.map((c) => (
              <li key={c.id} className="space-y-0.5">
                <div className="break-words leading-tight">• {c.name}</div>
                {c.tax_code && (
                  <div className="text-[10px] text-background/70 pl-2 font-mono">
                    MST: {c.tax_code}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </TooltipContent>
      </Tooltip>
    </div>
  )
}
