import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { EmployeeKeepOldDepartmentDialog } from './employee-keep-old-department-dialog'

function renderDialog(overrides: Partial<Parameters<typeof EmployeeKeepOldDepartmentDialog>[0]> = {}) {
  const onChoose = vi.fn()
  const onOpenChange = vi.fn()
  render(
    <EmployeeKeepOldDepartmentDialog
      open
      onOpenChange={onOpenChange}
      oldDepartmentName="Sản xuất - Thu mua"
      newDepartmentName="Dego Organic"
      onChoose={onChoose}
      {...overrides}
    />,
  )
  return { onChoose, onOpenChange }
}

//  bao-CR-709: ca NSU012 (31/10/2026) — đổi phòng chính mà phòng cũ âm thầm thành kiêm nhiệm, người đó
//  vẫn thấy phiếu của phòng cũ. Hộp này phải nói rõ hệ quả và mặc định là GỠ.
describe('EmployeeKeepOldDepartmentDialog', () => {
  it('names both departments and warns that keeping the old one keeps its data visible', () => {
    renderDialog()
    expect(screen.getAllByText('Sản xuất - Thu mua').length).toBeGreaterThan(0)
    expect(screen.getByText('Dego Organic')).toBeInTheDocument()
    expect(screen.getByText('vẫn thấy')).toBeInTheDocument()
  })

  it('focuses the remove button by default so Enter removes the old department', () => {
    renderDialog()
    expect(screen.getByRole('button', { name: 'Không, gỡ phòng cũ' })).toHaveFocus()
  })

  it('reports false when removing and true when keeping', () => {
    const { onChoose } = renderDialog()
    fireEvent.click(screen.getByRole('button', { name: 'Không, gỡ phòng cũ' }))
    fireEvent.click(screen.getByRole('button', { name: 'Giữ làm kiêm nhiệm' }))
    expect(onChoose.mock.calls).toEqual([[false], [true]])
  })

  it('disables every choice while saving so a double click cannot send twice', () => {
    const { onChoose } = renderDialog({ pending: true })
    for (const name of ['Hủy', 'Giữ làm kiêm nhiệm', 'Không, gỡ phòng cũ']) {
      expect(screen.getByRole('button', { name })).toBeDisabled()
    }
    fireEvent.click(screen.getByRole('button', { name: 'Giữ làm kiêm nhiệm' }))
    expect(onChoose).not.toHaveBeenCalled()
  })
})
