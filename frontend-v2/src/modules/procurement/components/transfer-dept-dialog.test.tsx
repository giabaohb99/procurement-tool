import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { Department } from '@/modules/hr/types/department'

import { TransferDeptDialog, type TransferDeptMode } from './transfer-dept-dialog'

function makeDepartment(id: number, name: string, isActive = true): Department {
  return {
    id,
    code: `P${id}`,
    name,
    issue_code: '',
    kind: 1,
    company_id: 1,
    parent: 0,
    manager_id: 0,
    is_active: isActive,
  }
}

const DEPARTMENTS = [
  makeDepartment(1, 'Phòng Thu mua'),
  makeDepartment(2, 'Nhà máy'),
  makeDepartment(3, 'Phòng Kế toán'),
  makeDepartment(4, 'Phòng đã giải thể', false),
]

function renderDialog(mode: TransferDeptMode, currentDeptId = 2, requestingDeptId = 3) {
  const onConfirm = vi.fn()
  render(
    <TransferDeptDialog
      open
      mode={mode}
      docLabel="yêu cầu mua hàng"
      departments={DEPARTMENTS}
      currentDeptId={currentDeptId}
      requestingDeptId={requestingDeptId}
      onOpenChange={vi.fn()}
      onConfirm={onConfirm}
    />,
  )
  return onConfirm
}

async function openDeptPicker(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('combobox'))
}

describe('TransferDeptDialog', () => {
  it('keeps confirm disabled until both department and reason are filled in transfer mode', async () => {
    const user = userEvent.setup()
    renderDialog('transfer')
    const confirm = screen.getByRole('button', { name: /Chuyển phòng/ })
    expect(confirm).toBeDisabled()

    await user.type(screen.getByLabelText(/Lý do/), 'Nhà máy quá tải')
    expect(confirm).toBeDisabled()

    await openDeptPicker(user)
    await user.click(screen.getByText('Phòng Thu mua'))
    expect(confirm).toBeEnabled()
  })

  it('excludes the department currently handling the ticket and inactive ones from the picker', async () => {
    const user = userEvent.setup()
    renderDialog('transfer')
    await openDeptPicker(user)

    expect(screen.getByText('Phòng Thu mua')).toBeInTheDocument()
    expect(screen.getByText('Phòng Kế toán')).toBeInTheDocument()
    expect(screen.queryByText('Nhà máy')).not.toBeInTheDocument()
    expect(screen.queryByText('Phòng đã giải thể')).not.toBeInTheDocument()
  })

  it('falls back to the requesting department as the excluded one when nobody is asked yet', async () => {
    //  `handler_dept_id` = 0 nghĩa là phòng lập tự xử lý — không được đề nghị
    //  "chuyển" phiếu sang chính phòng đó.
    const user = userEvent.setup()
    renderDialog('transfer', 0, 3)
    await openDeptPicker(user)

    expect(screen.getByText('Nhà máy')).toBeInTheDocument()
    expect(screen.queryByText('Phòng Kế toán')).not.toBeInTheDocument()
  })

  it('calls onConfirm with the chosen department id and the trimmed reason', async () => {
    const user = userEvent.setup()
    const onConfirm = renderDialog('transfer')

    await openDeptPicker(user)
    await user.click(screen.getByText('Phòng Kế toán'))
    await user.type(screen.getByLabelText(/Lý do/), '  Kế toán tự mua  ')
    await user.click(screen.getByRole('button', { name: /Chuyển phòng/ }))

    expect(onConfirm).toHaveBeenCalledWith(3, 'Kế toán tự mua')
  })

  it('hides the department picker in return mode and sends department 0', async () => {
    const user = userEvent.setup()
    const onConfirm = renderDialog('return')

    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    const confirm = screen.getByRole('button', { name: /Trả về/ })
    expect(confirm).toBeDisabled()

    await user.type(screen.getByLabelText(/Lý do/), 'Phòng lập tự xử lý')
    await user.click(confirm)

    expect(onConfirm).toHaveBeenCalledWith(0, 'Phòng lập tự xử lý')
  })
})
