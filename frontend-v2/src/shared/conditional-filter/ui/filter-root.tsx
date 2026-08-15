import { SlidersHorizontal } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { useFilterContext } from '../provider/filter-context'
import { FilterFooter } from './filter-footer'
import { FilterRowItem } from './filter-row'

/**
 * Nút "Bộ lọc" + popover chứa các dòng điều kiện.
 *
 * Vùng danh sách chỉ là div `overflow-y-auto` — bản gốc dùng `ScrollArea` của
 * shadcn, nhưng nó kéo theo một primitive nữa mà cái ta cần chỉ là thanh cuộn.
 */
export function ConditionalFilter() {
  const { state, config, activeCount } = useFilterContext()
  const locale = config.locale ?? {}

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">
          <SlidersHorizontal />
          {locale.filters}
          {activeCount > 0 && (
            <Badge variant="secondary" className="ml-1 rounded-full px-1.5">
              {activeCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent align="end" className="w-[min(46rem,95vw)] p-3">
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
