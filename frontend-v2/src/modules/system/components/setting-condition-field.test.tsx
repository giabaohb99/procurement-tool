import { render, renderHook, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PR_DISPATCH_CONDITION_FIELDS } from '../config/pr-dispatch-condition-fields'
import { usePrDispatchConditionChoices } from '../hooks/use-pr-dispatch-condition-choices'
import type { SettingField } from '../types/setting'

import { SettingFieldRow } from './setting-field-row'

/**
 * bao-CR-528 — ô «Điều kiện bỏ qua điều phối» vẽ BỘ CHỌN, không còn là ô gõ JSON.
 *
 * Đại ca chê ô cũ «cấu hình là gõ code vào à». Hàng cấu hình đọc cờ
 * `type: 'condition'` + `condition_entity` backend khai để quyết định vẽ gì.
 */

let centralCode = ''
let canRead = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => canRead }),
}))

vi.mock('../hooks/use-settings', () => ({
  useSettings: () => ({
    data: {
      fields: [{ key: 'central_purchasing_dept_code', value: centralCode }],
      secrets: [],
    },
  }),
}))

const departmentsQuery = vi.fn()
const companiesQuery = vi.fn()
const employeesQuery = vi.fn()

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: (_params: unknown, options: { enabled?: boolean }) => {
    departmentsQuery(options)
    return {
      data: {
        items: [
          { id: 17, code: 'PBA017', name: 'Sản xuất -Thu mua', is_active: true },
          { id: 5, code: 'NM01', name: 'Nhà máy Bắc Ninh', is_active: true },
          { id: 6, code: 'NM02', name: 'Nhà máy đã đóng', is_active: false },
          { id: 9, code: 'KT', name: 'Kế toán', is_active: true },
        ],
      },
    }
  },
}))

vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: (_params: unknown, options: { enabled?: boolean }) => {
    companiesQuery(options)
    return { data: { items: [{ id: 1, code: 'DEGO', name: 'DEGO Holding' }] } }
  },
}))

vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: (_params: unknown, options: { enabled?: boolean }) => {
    employeesQuery(options)
    return { data: { items: [{ id: 42, code: 'NSU042', full_name: 'Nguyễn Văn A' }] } }
  },
}))

const field: SettingField = {
  key: 'pr_dispatch_skip_rules',
  group: 'workflow',
  label: 'Yêu cầu mua hàng: BỎ QUA bước thu mua duyệt lần 2 cho phiếu thỏa điều kiện',
  type: 'condition',
  condition_entity: 'pr_dispatch',
  value: '[{"field":"handler_dept_id","op":"not_empty"}]',
  hint: 'Chỉ có tác dụng khi công tắc ở trên đang BẬT.',
}

beforeEach(() => {
  centralCode = ''
  canRead = true
  departmentsQuery.mockClear()
  companiesQuery.mockClear()
  employeesQuery.mockClear()
})

describe('SettingFieldRow — condition field', () => {
  it('renders the builder and the sentence instead of a JSON text box', () => {
    render(<SettingFieldRow field={field} disabled={false} onChange={vi.fn()} />)

    expect(screen.getByText('Bỏ qua bước thu mua duyệt lần 2 khi:')).toBeInTheDocument()
    expect(screen.getByText('Phòng xử lý có giá trị')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByText(/Chỉ có tác dụng khi công tắc/)).toBeInTheDocument()
  })

  it('explains that an empty rule skips nothing', () => {
    render(<SettingFieldRow field={{ ...field, value: '' }} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByText(/không phiếu nào/)).toBeInTheDocument()
  })

  it('treats a null value from the backend as no rule, not as a crash', () => {
    render(<SettingFieldRow field={{ ...field, value: null }} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: /Thêm điều kiện/ })).toBeInTheDocument()
  })

  it('shows a legacy hand-typed rule verbatim instead of rewriting it', () => {
    const raw = '[{"field":"handler_dept","op":"not_empty"}]'
    const onChange = vi.fn()
    render(<SettingFieldRow field={{ ...field, value: raw }} disabled={false} onChange={onChange} />)

    expect(screen.getByText(raw)).toBeInTheDocument()
    expect(onChange).not.toHaveBeenCalled()
  })

  it('locks the builder for users who may only read settings', () => {
    render(<SettingFieldRow field={field} disabled onChange={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /Thêm điều kiện/ })).not.toBeInTheDocument()
  })

  it('falls back to a plain text box for a condition set this screen does not know', () => {
    render(
      <SettingFieldRow
        field={{ ...field, condition_entity: 'unknown_set' }}
        disabled={false}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('textbox')).toHaveValue(String(field.value))
  })
})

describe('usePrDispatchConditionChoices', () => {
  const handler = PR_DISPATCH_CONDITION_FIELDS.find((item) => item.name === 'handler_dept_id')
  const department = PR_DISPATCH_CONDITION_FIELDS.find((item) => item.name === 'department_id')

  it('drops the default purchasing department from «Phòng xử lý» because it counts as empty', () => {
    //  Bối cảnh phiếu đưa phòng thu mua mặc định vào dưới dạng 0; chọn nó ở phép
    //  «thuộc» là một điều kiện không phiếu nào khớp.
    const { result } = renderHook(() => usePrDispatchConditionChoices(''))
    if (!handler || !department) throw new Error('thiếu ô trong cấu hình')

    expect(result.current(handler).map((item) => item.id)).toEqual([5, 9])
    expect(result.current(department).map((item) => item.id)).toEqual([17, 5, 9])
  })

  it('follows the configured purchasing department code, not a hard-coded one', () => {
    centralCode = 'KT'
    const { result } = renderHook(() => usePrDispatchConditionChoices('  KT  '))
    if (!handler) throw new Error('thiếu ô trong cấu hình')

    expect(result.current(handler).map((item) => item.id)).toEqual([17, 5])
  })

  it('does not call the HR catalogues when the user cannot read them', () => {
    canRead = false
    renderHook(() => usePrDispatchConditionChoices(''))
    expect(departmentsQuery).toHaveBeenCalledWith({ enabled: false })
    expect(companiesQuery).toHaveBeenCalledWith({ enabled: false })
    expect(employeesQuery).toHaveBeenCalledWith({ enabled: false })
  })

  it('declares exactly the keys the backend dispatch context sends', () => {
    //  Khớp `DISPATCH_CONTEXT_FIELDS` ở `purchase_request/service.py`; lệch là cửa
    //  lưu trả 400 cho mọi điều kiện dùng ô thừa.
    expect(PR_DISPATCH_CONDITION_FIELDS.map((item) => item.name).sort()).toEqual(
      ['company_id', 'department_id', 'handler_dept_id', 'is_urgent', 'line_count', 'requester_id'],
    )
  })
})
