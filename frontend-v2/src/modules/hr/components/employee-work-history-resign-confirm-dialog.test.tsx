import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { EmployeeWorkHistoryResignConfirmDialog } from './employee-work-history-resign-confirm-dialog'

function renderDialog(onConfirm = vi.fn(), onOpenChange = vi.fn()) {
  render(
    <EmployeeWorkHistoryResignConfirmDialog
      open
      onOpenChange={onOpenChange}
      resignDate="2026-09-30"
      onConfirm={onConfirm}
    />,
  )
  return { onConfirm, onOpenChange }
}

describe('EmployeeWorkHistoryResignConfirmDialog', () => {
  it('hiện ngày nghỉ việc lấy từ dòng, cảnh báo khóa và đăng xuất mọi thiết bị', () => {
    renderDialog()

    expect(screen.getByText('Chuyển hồ sơ sang nghỉ việc?')).toBeInTheDocument()
    expect(screen.getByText('30/09/2026')).toBeInTheDocument()
    expect(screen.getByText(/KHÓA/)).toBeInTheDocument()
    expect(screen.getByText(/ĐĂNG XUẤT/)).toBeInTheDocument()
    expect(screen.getByText(/khỏi mọi thiết bị/)).toBeInTheDocument()
  })

  it('«Chỉ lưu dòng» gọi onConfirm(false)', async () => {
    const { onConfirm } = renderDialog()

    await userEvent.click(screen.getByRole('button', { name: 'Chỉ lưu dòng' }))

    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(onConfirm).toHaveBeenCalledWith(false)
  })

  it('«Lưu và chuyển sang nghỉ việc» gọi onConfirm(true)', async () => {
    const { onConfirm } = renderDialog()

    await userEvent.click(screen.getByRole('button', { name: /Lưu và chuyển sang nghỉ việc/ }))

    expect(onConfirm).toHaveBeenCalledTimes(1)
    expect(onConfirm).toHaveBeenCalledWith(true)
  })

  it('Esc đóng hộp mà KHÔNG gọi onConfirm', async () => {
    const { onConfirm, onOpenChange } = renderDialog()

    await userEvent.keyboard('{Escape}')

    expect(onConfirm).not.toHaveBeenCalled()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})

describe('EmployeeWorkHistoryResignConfirmDialog — dùng lại ở nút ▶ «Áp vào hồ sơ» (H1)', () => {
  it('cancelLabel/confirmLabel truyền riêng thì HIỆN đúng nhãn đó, không phải nhãn mặc định', () => {
    render(
      <EmployeeWorkHistoryResignConfirmDialog
        open
        onOpenChange={vi.fn()}
        resignDate="2026-09-30"
        cancelLabel="Hủy"
        confirmLabel="Chuyển sang nghỉ việc"
        onConfirm={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chuyển sang nghỉ việc' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Chỉ lưu dòng' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Lưu và chuyển sang nghỉ việc/ })).not.toBeInTheDocument()
  })

  it('có onCancel riêng → bấm nút phụ CHỈ gọi onCancel, KHÔNG gọi onConfirm(false)', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    render(
      <EmployeeWorkHistoryResignConfirmDialog
        open
        onOpenChange={vi.fn()}
        resignDate="2026-09-30"
        cancelLabel="Hủy"
        confirmLabel="Chuyển sang nghỉ việc"
        onCancel={onCancel}
        onConfirm={onConfirm}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))

    expect(onCancel).toHaveBeenCalledTimes(1)
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('không có onCancel (hộp LƯU dòng cũ) → bấm nút phụ vẫn gọi onConfirm(false) như trước', async () => {
    const onConfirm = vi.fn()
    render(
      <EmployeeWorkHistoryResignConfirmDialog
        open
        onOpenChange={vi.fn()}
        resignDate="2026-09-30"
        onConfirm={onConfirm}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Chỉ lưu dòng' }))

    expect(onConfirm).toHaveBeenCalledWith(false)
  })
})
