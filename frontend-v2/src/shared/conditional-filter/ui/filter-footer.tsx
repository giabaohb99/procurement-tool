import { Button } from '@/shared/ui/button'
import { PopoverClose } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { isValidFilterRow } from '../helpers/validators'
import { useFilterContext } from '../provider/filter-context'

/** Chân popover: thêm dòng, đổi VÀ/HOẶC, xóa hết, áp dụng. */
export function FilterFooter() {
  const { config, state, addRow, reset, apply, setConjunction } = useFilterContext()
  const locale = config.locale ?? {}

  const canAddMore = state.rows.length < (config.maxRows ?? 10)
  // Cho phép Áp dụng cả khi không còn dòng nào hợp lệ — đó chính là thao tác gỡ lọc.
  const hasDraftRows = state.rows.length > 0
  const hasValidRow = state.rows.some(isValidFilterRow)

  return (
    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t pt-3">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={addRow} disabled={!canAddMore}>
          {locale.addFilter}
        </Button>

        {config.allowConjunctionToggle && state.rows.length > 1 && (
          <div className="flex items-center gap-0.5 rounded-md bg-muted p-0.5">
            {(['and', 'or'] as const).map((conjunction) => (
              <button
                key={conjunction}
                type="button"
                onClick={() => setConjunction(conjunction)}
                className={cn(
                  'rounded px-2.5 py-1 text-xs font-medium transition-colors',
                  state.conjunction === conjunction
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                {conjunction === 'and' ? locale.and : locale.or}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <PopoverClose asChild>
          <Button variant="outline" size="sm" onClick={reset}>
            {locale.reset}
          </Button>
        </PopoverClose>

        <PopoverClose asChild>
          <Button size="sm" onClick={apply} disabled={hasDraftRows && !hasValidRow}>
            {locale.apply}
          </Button>
        </PopoverClose>
      </div>
    </div>
  )
}
