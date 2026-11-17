import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { DEFAULT_LOCALE } from '../constants'
import { buildRestQuery } from '../helpers/query-builder'
import { FilterContext, type FilterContextValue } from '../provider/filter-context'
import type { FilterFieldDefinition, FilterValue, OperatorType, SelectOption } from '../types'
import { ValueInput } from './value-input'

/**
 * duoc-CR-778 — trường kiểu `select` chỉ khai `fetchOptions` (Loại văn bản, Pháp nhân ban
 * hành, Phòng chủ trì, Người chịu trách nhiệm, Sổ văn bản ở màn Văn bản; Vị trí / Chức vụ ở
 * màn Nhân sự) từng rơi xuống ô GÕ CHỮ: gõ "Hành chính" thành `department_id__eq=Hành chính`,
 * backend lặng lẽ bỏ qua và bảng ra đủ mọi dòng. Còn operator "thuộc danh sách" thì ra hộp
 * rỗng. Bộ bài này giữ cho hai lỗi đó không quay lại.
 */

const DEPARTMENTS: SelectOption[] = [
  { value: '7', label: 'Hành chính' },
  { value: '9', label: 'Kế toán' },
  //  id 0 là GIÁ TRỊ THẬT (nhóm chưa gắn phòng) — không được nuốt mất khi chọn.
  { value: '0', label: '(Chưa gắn phòng)' },
]

function makeFetch(rows: SelectOption[] = DEPARTMENTS) {
  return vi.fn(async (search: string) =>
    rows.filter((row) => row.label.toLowerCase().includes(search.toLowerCase())),
  )
}

function renderValueInput(
  field: FilterFieldDefinition,
  operator: OperatorType,
  value: FilterValue,
) {
  const updateValue = vi.fn()
  const context: FilterContextValue = {
    config: { fields: [field], locale: DEFAULT_LOCALE },
    state: { rows: [], conjunction: 'and' },
    appliedState: { rows: [], conjunction: 'and' },
    addRow: vi.fn(),
    removeRow: vi.fn(),
    updateField: vi.fn(),
    updateOperator: vi.fn(),
    updateValue,
    setConjunction: vi.fn(),
    reset: vi.fn(),
    apply: vi.fn(),
    activeCount: 0,
  }
  const utils = render(
    <FilterContext.Provider value={context}>
      <ValueInput rowId="row-1" field={field} operator={operator} value={value} />
    </FilterContext.Provider>,
  )
  return { ...utils, updateValue }
}

function departmentField(fetchOptions = makeFetch()): FilterFieldDefinition {
  return { name: 'department_id', label: 'Phòng chủ trì', type: 'select', fetchOptions }
}

describe('ValueInput — select field that only declares fetchOptions, single value', () => {
  it('renders a searchable picker instead of a free-text box', async () => {
    const fetchOptions = makeFetch()
    renderValueInput(departmentField(fetchOptions), 'is', '')

    expect(screen.queryByPlaceholderText('Nhập giá trị…')).toBeNull()
    expect(screen.getByRole('combobox')).toHaveTextContent('Chọn giá trị…')
    await waitFor(() => expect(fetchOptions).toHaveBeenCalledWith(''))
  })

  it('sends the picked ID as a string, exactly like the old combobox fields', async () => {
    const user = userEvent.setup()
    const fetchOptions = makeFetch()
    const { updateValue } = renderValueInput(departmentField(fetchOptions), 'is', '')

    await user.click(screen.getByRole('combobox'))
    await user.click(await screen.findByRole('button', { name: 'Kế toán' }))

    expect(updateValue).toHaveBeenCalledWith('row-1', '9')
  })

  it('keeps id 0 pickable — it is the real "chưa gắn" group, not an "all" sentinel', async () => {
    const user = userEvent.setup()
    const { updateValue } = renderValueInput(departmentField(), 'is_not', '')

    await user.click(screen.getByRole('combobox'))
    await user.click(await screen.findByRole('button', { name: '(Chưa gắn phòng)' }))

    expect(updateValue).toHaveBeenCalledWith('row-1', '0')
  })

  it('searches on the server with the typed keyword', async () => {
    const user = userEvent.setup()
    const fetchOptions = makeFetch()
    renderValueInput(departmentField(fetchOptions), 'is', '')

    await user.click(screen.getByRole('combobox'))
    await user.type(screen.getByPlaceholderText('Gõ để tìm…'), 'hành')

    await waitFor(() => expect(fetchOptions).toHaveBeenLastCalledWith('hành'))
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Kế toán' })).toBeNull())
    expect(screen.getByRole('button', { name: 'Hành chính' })).toBeInTheDocument()
  })

  it('shows the label of a value restored from the URL once the list has loaded', async () => {
    renderValueInput(departmentField(), 'is', '7')
    await waitFor(() => expect(screen.getByRole('combobox')).toHaveTextContent('Hành chính'))
  })

  it('still opens (empty, no crash) when the option request fails', async () => {
    const user = userEvent.setup()
    const failing = vi.fn(async () => {
      throw new Error('500')
    })
    renderValueInput(departmentField(failing), 'is', '')

    await user.click(screen.getByRole('combobox'))
    expect(await screen.findByText('Không tìm thấy kết quả.')).toBeInTheDocument()
  })
})

describe('ValueInput — fetchOptions field with operator in / not_in', () => {
  function multiField(fetchOptions = makeFetch()): FilterFieldDefinition {
    return { ...departmentField(fetchOptions), operators: ['is', 'in', 'not_in'] }
  }

  it('lists the fetched options instead of the empty box it used to show', async () => {
    const user = userEvent.setup()
    renderValueInput(multiField(), 'in', [])

    await user.click(screen.getByRole('combobox'))
    expect(await screen.findByRole('checkbox', { name: 'Hành chính' })).toBeInTheDocument()
    expect(screen.queryByText('Không có giá trị nào.')).toBeNull()
  })

  it('adds the ticked ID to the selection as strings', async () => {
    const user = userEvent.setup()
    const { updateValue } = renderValueInput(multiField(), 'not_in', ['7'])

    await user.click(screen.getByRole('combobox'))
    await user.click(await screen.findByRole('checkbox', { name: 'Kế toán' }))

    expect(updateValue).toHaveBeenCalledWith('row-1', ['7', '9'])
  })

  it('keeps the label of a selected item after a search pushes it out of the list', async () => {
    const user = userEvent.setup()
    const fetchOptions = makeFetch()
    renderValueInput(multiField(fetchOptions), 'in', ['7'])

    await waitFor(() => expect(screen.getByRole('combobox')).toHaveTextContent('Hành chính'))
    await user.click(screen.getByRole('combobox'))
    await user.type(screen.getByPlaceholderText('Gõ để tìm…'), 'kế')
    await waitFor(() => expect(fetchOptions).toHaveBeenLastCalledWith('kế'))
    await waitFor(() => expect(screen.queryByRole('checkbox', { name: 'Hành chính' })).toBeNull())

    expect(screen.getByRole('combobox')).toHaveTextContent('Hành chính')
  })

  it('summarises several picks as a count', () => {
    renderValueInput(multiField(), 'in', ['7', '9'])
    expect(screen.getByRole('combobox')).toHaveTextContent('Đã chọn 2')
  })

  it('produces the same URL params as before: comma-joined IDs', () => {
    const field = multiField()
    expect(
      buildRestQuery({
        rows: [
          { id: 'a', field, operator: 'in', value: ['7', '0'] },
          { id: 'b', field: departmentField(), operator: 'is', value: '9' },
        ],
        conjunction: 'and',
      }),
    ).toEqual({ department_id__in: '7,0', department_id__eq: '9' })
  })
})

describe('ValueInput — fields that were already fine stay unchanged', () => {
  it('a select with static options keeps the plain list and never fetches', () => {
    const fetchOptions = makeFetch()
    renderValueInput(
      {
        name: 'status',
        label: 'Trạng thái',
        type: 'select',
        options: [{ value: '1', label: 'Nháp' }],
        fetchOptions,
      },
      'is',
      '',
    )
    expect(screen.getByRole('combobox')).toHaveTextContent('Chọn giá trị…')
    expect(fetchOptions).not.toHaveBeenCalled()
  })

  it('a static multi-select shows no search box', async () => {
    const user = userEvent.setup()
    renderValueInput(
      {
        name: 'status',
        label: 'Trạng thái',
        type: 'select',
        operators: ['in'],
        options: [{ value: '1', label: 'Nháp' }],
      },
      'in',
      [],
    )
    await user.click(screen.getByRole('combobox'))
    expect(screen.getByRole('checkbox', { name: 'Nháp' })).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Gõ để tìm…')).toBeNull()
  })

  it('a text field is still a free-text box', () => {
    renderValueInput({ name: 'title', label: 'Trích yếu', type: 'text' }, 'contains', '')
    expect(screen.getByPlaceholderText('Nhập giá trị…')).toBeInTheDocument()
  })
})
