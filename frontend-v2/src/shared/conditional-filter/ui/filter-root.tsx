import { SlidersHorizontal, type LucideIcon } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { useFilterContext } from '../provider/filter-context'
import { FilterFooter } from './filter-footer'
import { FilterRowItem } from './filter-row'

export interface ConditionalFilterProps {
  align?: 'start' | 'center' | 'end'
  /** Dáng nút mở bộ lọc — `ghost` cho thanh công cụ phẳng kiểu Lark. */
  variant?: 'outline' | 'ghost'
  className?: string
  /**
   * Biểu tượng trên nút. Đổi được vì có màn để nút này CẠNH một nút khác cũng
   * dùng `SlidersHorizontal` (menu «Tùy chỉnh» của bảng Công việc) — hai biểu
   * tượng giống hệt nhau cạnh nhau thì không ai phân biệt được nút nào.
   */
  icon?: LucideIcon
}

/**
 * Nút "Bộ lọc" + popover chứa các dòng điều kiện.
 *
 * Mặc định `align="start"` để khi nút nằm phía bên trái thanh công cụ (sau ô tìm kiếm),
 * khung popover mở rộng sang bên phải, không bị lệch/tràn ra khỏi mép trái màn hình.
 */
export function ConditionalFilter({
  align = 'start',
  variant = 'outline',
  className,
  icon: Icon = SlidersHorizontal,
}: ConditionalFilterProps = {}) {
  const { state, config, activeCount } = useFilterContext()
  const locale = config.locale ?? {}

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant={variant} size={variant === 'ghost' ? 'sm' : 'default'} className={className}>
          <Icon />
          {locale.filters}
          {activeCount > 0 && (
            <Badge variant="secondary" className="ml-1 rounded-full px-1.5">
              {activeCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent align={align} className="w-[min(46rem,95vw)] p-3">
        <div className="max-h-[24rem] overflow-y-auto pr-1">
          {state.rows.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              {locale.noFilters}
            </p>
          ) : (
            <div className="flex flex-col gap-1">
              {state.rows.map((row) => (
                <FilterRowItem key={row.id} rowId={row.id} />
              ))}
            </div>
          )}
        </div>

        <FilterFooter />
      </PopoverContent>
    </Popover>
  )
}
