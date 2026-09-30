import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ConditionBuilder } from './condition-builder'
import type { ConditionField } from './condition-rule'

const FIELDS: ConditionField[] = [
  { name: 'handler_dept_id', label: 'Phòng xử lý', ops: ['not_empty', 'empty', 'in', 'not_in'] },
  { name: 'line_count', label: 'Số dòng hàng', kind: 'number', ops: ['lte', 'gte'] },
]

function renderBuilder(value: string, onChange = vi.fn(), disabled = false) {
  render(
    <ConditionBuilder
      value={value}
      onChange={onChange}
      fields={FIELDS}
      getOptions={() => [{ id: 5, label: 'Nhà máy' }]}
      emptyText="Chưa đặt điều kiện"
      sentencePrefix="Bỏ qua khi: "
      advancedText="Điều kiện khai tay"
      disabled={disabled}
    />,
  )
  return onChange
}

describe('ConditionBuilder', () => {
  it('says what "no condition" means instead of showing an empty box', () => {
    renderBuilder('')
    expect(screen.getByText('Chưa đặt điều kiện')).toBeInTheDocument()
  })

  it('adding a row with a value-free first op saves a complete rule at once', async () => {
    const onChange = renderBuilder('')
    await userEvent.setup().click(screen.getByRole('button', { name: /Thêm điều kiện/ }))

    expect(onChange).toHaveBeenLastCalledWith('[{"field":"handler_dept_id","op":"not_empty"}]')
    expect(screen.getByText('Phòng xử lý có giá trị')).toBeInTheDocument()
  })

  it('reads the stored rule back as a sentence under the builder', () => {
    renderBuilder('[{"field":"handler_dept_id","op":"not_empty"}]')
    expect(screen.getByText('Bỏ qua khi:')).toBeInTheDocument()
    expect(screen.getByText('Phòng xử lý có giá trị')).toBeInTheDocument()
  })

  it('removing the last row clears the stored rule', async () => {
    const onChange = renderBuilder('[{"field":"handler_dept_id","op":"not_empty"}]')
    await userEvent.setup().click(screen.getByRole('button', { name: 'Bỏ điều kiện này' }))
    expect(onChange).toHaveBeenLastCalledWith('')
  })

  it('an empty number box is flagged as unsaved and left out of the rule', async () => {
    const onChange = renderBuilder('[{"field":"line_count","op":"lte","value":2}]')
    await userEvent.setup().clear(screen.getByRole('spinbutton', { name: 'Giá trị' }))

    expect(onChange).toHaveBeenLastCalledWith('')
    expect(screen.getByText('Điều kiện chưa chọn giá trị sẽ không được lưu.')).toBeInTheDocument()
  })

  it('typing 0 in a number box is a real value, not "not filled in"', async () => {
    const onChange = renderBuilder('[{"field":"line_count","op":"lte","value":2}]')
    const box = screen.getByRole('spinbutton', { name: 'Giá trị' })
    const user = userEvent.setup()
    await user.clear(box)
    await user.type(box, '0')

    expect(onChange).toHaveBeenLastCalledWith('[{"field":"line_count","op":"lte","value":0}]')
  })

  it('keeps a hand-written rule verbatim and never overwrites it silently', async () => {
    const onChange = renderBuilder('[{"field":"total","op":"gte","value":1}]')
    expect(screen.getByText('Điều kiện khai tay')).toBeInTheDocument()
    expect(screen.getByText('[{"field":"total","op":"gte","value":1}]')).toBeInTheDocument()
    expect(onChange).not.toHaveBeenCalled()

    await userEvent.setup().click(screen.getByRole('button', { name: /Bỏ điều kiện này và chọn lại/ }))
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('read-only users see the rule but get no add, remove or clear buttons', () => {
    renderBuilder('[{"field":"handler_dept_id","op":"not_empty"}]', vi.fn(), true)
    expect(screen.queryByRole('button', { name: /Thêm điều kiện/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Bỏ điều kiện này' })).not.toBeInTheDocument()
    for (const box of screen.getAllByRole('combobox')) expect(box).toBeDisabled()
  })
})
