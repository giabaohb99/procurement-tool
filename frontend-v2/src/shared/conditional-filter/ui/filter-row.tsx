import { Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { useFilterContext } from '../provider/filter-context'
import { FieldSelect } from './field-select'
import { OperatorSelect } from './operator-select'
import { ValueInput } from './value-input'

/** Một dòng: [trường] [phép so sánh] [giá trị] [xóa]. */
export function FilterRowItem({ rowId }: { rowId: string }) {
  const { state, removeRow } = useFilterContext()
  const row = state.rows.find((item) => item.id === rowId)

  if (!row) return null

  return (
    <div className="flex w-full items-center gap-2 py-1">
      <FieldSelect rowId={row.id} selectedField={row.field} />

      {row.field && (
        <OperatorSelect
          rowId={row.id}
          field={row.field}
          selectedOperator={row.operator}
        />
      )}

      {row.field && row.operator && (
        <div className="flex min-w-0 flex-1">
          <ValueInput
            rowId={row.id}
            field={row.field}
            operator={row.operator}
            value={row.value}
          />
        </div>
      )}

      <Button
        variant="ghost"
        size="icon-sm"
        className="ml-auto shrink-0 text-muted-foreground"
        aria-label="Xóa điều kiện"
        onClick={() => removeRow(row.id)}
      >
        <Trash2 />
      </Button>
    </div>
  )
}
