import SearchSelect from '../../SearchSelect'
import { DEFAULT_OPERATORS, operatorLabel } from '../constants'
import { useFilterContext } from '../provider/filter-context'
import type { FilterRow as Row, OperatorType } from '../types'
import ValueInput from './value-input'

/** Một dòng điều kiện: [Trường] [Phép so sánh] [Giá trị] [Xóa] */
export default function FilterRow({ row, index }: { row: Row; index: number }) {
  const { config, updateField, updateOperator, removeRow, state } = useFilterContext()

  const fieldOptions = config.fields.map((f) => ({ value: f.name, label: f.label }))
  const operators: OperatorType[] = row.field
    ? (row.field.operators || DEFAULT_OPERATORS[row.field.type] || ['eq'])
    : []
  const operatorOptions = operators.map((op) => ({
    value: op, label: operatorLabel(op, row.field?.type),
  }))

  return (
    <div className="cf-row">
      <div className="cf-conj">
        {index === 0
          ? 'Lọc theo'
          : <span className="cf-conj-word">{state.conjunction === 'or' ? 'HOẶC' : 'VÀ'}</span>}
      </div>

      <div className="cf-field">
        <SearchSelect
          value={row.field?.name || ''} options={fieldOptions} placeholder="Chọn trường…"
          onChange={(name) => {
            const f = config.fields.find((x) => x.name === name)
            if (f) updateField(row.id, f)
          }}
        />
      </div>

      <div className="cf-operator">
        <SearchSelect
          value={row.operator || ''} options={operatorOptions}
          placeholder={row.field ? 'Phép so sánh…' : '—'} disabled={!row.field}
          onChange={(op) => updateOperator(row.id, op as OperatorType)}
        />
      </div>

      <ValueInput row={row} />

      <button type="button" className="btn ghost cf-remove" title="Xóa điều kiện"
        onClick={() => removeRow(row.id)}>
        <i className="ti ti-x" />
      </button>
    </div>
  )
}
