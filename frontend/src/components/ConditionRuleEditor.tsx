import { useEffect, useState } from 'react'
import { api } from '../api/client'
import MultiCheckSelect from './MultiCheckSelect'
import {
  buildCondition, conditionText, defaultConditionValue, fullRow, isMultiValueOp, isValueFreeOp,
  OP_LABELS, parseCondition, PR_DISPATCH_CONDITION_FIELDS,
  type ConditionChoice, type ConditionField, type ConditionOp, type ConditionRow,
} from '../utils/conditionRule'

/** Mã phòng thu mua mặc định khi ô cấu hình để trống — khớp `core/central_purchasing.py`. */
const DEFAULT_CENTRAL_DEPT_CODE = 'PBA017'

type Catalog = { id: number; code?: string; name?: string; full_name?: string; is_active?: boolean }

/**
 * BỘ CHỌN ĐIỀU KIỆN cho ô «Điều kiện bỏ qua điều phối» (bao-CR-528) — bản v1, cùng tính năng
 * với `frontend-v2` (`SettingConditionField`). Mỗi dòng «trường · phép so · giá trị», nối nhau
 * bằng VÀ, câu tiếng Việt tổng kết bên dưới. Giá trị gửi lên vẫn là chuỗi JSON cũ.
 *
 * Trước CR này ô là ô chữ bắt quản trị gõ `[{"field":"handler_dept_id","op":"not_empty"}]`.
 */
export default function ConditionRuleEditor({
  value, onChange, disabled, centralDeptCode,
}: {
  value: string
  onChange: (next: string) => void
  disabled?: boolean
  centralDeptCode?: string
}) {
  const fields = PR_DISPATCH_CONDITION_FIELDS
  const { advanced } = parseCondition(value, fields)
  //  Dòng giữ ở state riêng: dòng khai dở chưa vào chuỗi gửi đi, suy ngược từ chuỗi thì nó
  //  biến mất ngay dưới tay người dùng.
  const [rows, setRows] = useState<ConditionRow[]>(() => parseCondition(value, fields).rows)
  const [departments, setDepartments] = useState<Catalog[]>([])
  const [companies, setCompanies] = useState<Catalog[]>([])
  const [employees, setEmployees] = useState<Catalog[]>([])

  useEffect(() => {
    //  `_silent`: thiếu quyền đọc danh mục thì ô chọn trống, không bắn toast lỗi lúc mở màn.
    const load = (url: string, params: Record<string, unknown>, set: (items: Catalog[]) => void) =>
      api.get(url, { params, _silent: true } as any)
        .then((r) => set(r.data.data.items || r.data.data || []))
        .catch(() => set([]))
    load('/api/departments', { page_size: 500 }, setDepartments)
    load('/api/companies', { page_size: 200, is_active: true }, setCompanies)
    load('/api/employees', { page_size: 500 }, setEmployees)
  }, [])

  const centralCode = (centralDeptCode || '').trim() || DEFAULT_CENTRAL_DEPT_CODE
  const getOptions = (f: ConditionField): ConditionChoice[] => {
    if (f.source === 'handler_department' || f.source === 'department') {
      return departments
        .filter((d) => d.is_active !== false)
        //  Phòng thu mua mặc định = «để trống» trong bối cảnh phiếu; chọn nó ở «thuộc» thì
        //  không phiếu nào khớp, nên gỡ khỏi ô «Phòng xử lý».
        .filter((d) => f.source === 'department' || d.code !== centralCode)
        .map((d) => ({ id: d.id, label: d.name || String(d.id) }))
    }
    if (f.source === 'company') return companies.map((c) => ({ id: c.id, label: c.name || String(c.id) }))
    if (f.source === 'employee') return employees.map((e) => ({ id: e.id, label: e.full_name || String(e.id) }))
    return []
  }

  const write = (next: ConditionRow[]) => { setRows(next); onChange(buildCondition(next, fields)) }
  const changeRow = (i: number, patch: Partial<ConditionRow>) =>
    write(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)))
  const addRow = () => {
    const f = fields[0]
    write([...rows, { field: f.name, op: f.ops[0], value: defaultConditionValue(f.ops[0], f.kind) }])
  }

  const box: React.CSSProperties = { border: '1px solid var(--border)', borderRadius: 8, padding: 10, background: '#fff' }

  if (advanced) {
    //  Điều kiện khai tay từ trước: giữ nguyên, không lặng lẽ ghi đè.
    return (
      <div style={{ ...box, background: '#fffbeb', borderColor: '#fcd34d', color: '#92400e', fontSize: 13 }}>
        <div><i className="ti ti-alert-triangle" /> Ô này đang giữ điều kiện <b>khai tay</b> từ trước, bộ chọn không diễn tả được. Hệ thống vẫn đọc nó như cũ; muốn sửa thì bỏ đi rồi chọn lại.</div>
        <div style={{ fontFamily: 'monospace', fontSize: 12, wordBreak: 'break-all', margin: '6px 0' }}>{value}</div>
        {!disabled && (
          <button type="button" className="btn ghost" onClick={() => { setRows([]); onChange('') }}>
            Bỏ điều kiện này và chọn lại
          </button>
        )}
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {rows.length === 0 && (
        <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>
          Chưa đặt điều kiện — <b>không phiếu nào</b> được bỏ qua bước thu mua duyệt lần 2.
        </div>
      )}

      {rows.map((row, i) => {
        const f = fields.find((x) => x.name === row.field)
        return (
          <div key={i} style={box}>
            {/* Các dòng nối bằng VÀ — nói ra để không ai tưởng là HOẶC. */}
            {i > 0 && <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>VÀ</div>}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <select value={row.field} disabled={disabled} style={{ flex: '1 1 180px' }}
                onChange={(e) => {
                  const next = fields.find((x) => x.name === e.target.value)
                  if (!next) return
                  //  Đổi ô thì reset phép và giá trị: id của ô trước đọc sang ô sau là sai nghĩa.
                  changeRow(i, { field: next.name, op: next.ops[0], value: defaultConditionValue(next.ops[0], next.kind) })
                }}>
                {fields.map((x) => <option key={x.name} value={x.name}>{x.label}</option>)}
              </select>
              {f && (
                <select value={row.op} disabled={disabled} style={{ flex: '0 0 160px' }}
                  onChange={(e) => {
                    const op = e.target.value as ConditionOp
                    changeRow(i, { op, value: defaultConditionValue(op, f.kind) })
                  }}>
                  {f.ops.map((op) => <option key={op} value={op}>{OP_LABELS[op]}</option>)}
                </select>
              )}
              {f && !isValueFreeOp(row.op) && (
                <div style={{ flex: '1 1 220px', minWidth: 0 }}>
                  {isMultiValueOp(row.op) ? (
                    <MultiCheckSelect
                      value={(Array.isArray(row.value) ? row.value : []).map(String)}
                      options={getOptions(f).map((o) => ({ value: String(o.id), label: o.label }))}
                      onChange={(ids) => changeRow(i, { value: ids.map(Number) })}
                      disabled={disabled}
                      placeholder="Chọn giá trị…"
                    />
                  ) : f.kind === 'bool' ? (
                    <select value={row.value === false ? 'false' : 'true'} disabled={disabled} style={{ width: '100%' }}
                      onChange={(e) => changeRow(i, { value: e.target.value === 'true' })}>
                      <option value="true">Có</option>
                      <option value="false">Không</option>
                    </select>
                  ) : f.kind === 'number' ? (
                    <input type="number" min={0} disabled={disabled} placeholder="Nhập số…" style={{ width: '100%' }}
                      value={typeof row.value === 'number' ? row.value : ''}
                      //  Ô trống = «chưa nhập» (null), không phải 0: «số dòng từ 0 trở xuống» là điều kiện thật.
                      onChange={(e) => changeRow(i, { value: e.target.value === '' ? null : Number(e.target.value) })} />
                  ) : (
                    <select value={String(row.value || '')} disabled={disabled} style={{ width: '100%' }}
                      onChange={(e) => changeRow(i, { value: Number(e.target.value) })}>
                      <option value="">Chọn…</option>
                      {getOptions(f).map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
                    </select>
                  )}
                </div>
              )}
              {!disabled && (
                <button type="button" className="btn ghost" title="Bỏ điều kiện này"
                  onClick={() => write(rows.filter((_, idx) => idx !== i))}>
                  <i className="ti ti-x" />
                </button>
              )}
            </div>
          </div>
        )
      })}

      {!disabled && (
        <div>
          <button type="button" className="btn ghost" onClick={addRow}><i className="ti ti-plus" />Thêm điều kiện</button>
        </div>
      )}

      {rows.some((r) => !fullRow(r, fields.find((x) => x.name === r.field)?.kind)) && (
        <div style={{ fontSize: 12.5, color: '#b45309' }}>Điều kiện chưa chọn giá trị sẽ không được lưu.</div>
      )}

      {rows.length > 0 && (
        <div style={{ fontSize: 12.5, background: '#f1f5f9', borderRadius: 6, padding: '8px 10px' }}>
          <span style={{ color: 'var(--muted)' }}>Bỏ qua bước thu mua duyệt lần 2 khi: </span>
          <b>{conditionText(rows, fields, getOptions)}</b>
        </div>
      )}
    </div>
  )
}
