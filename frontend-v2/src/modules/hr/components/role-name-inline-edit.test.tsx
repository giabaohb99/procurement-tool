import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RoleNameInlineEdit } from './role-name-inline-edit'
import type { Role } from '../types/role'

const VAI_TRO: Role = {
  id: 2,
  code: 'employee',
  name: 'Nhân sự',
  description: '',
  sort_order: 2,
}

const doiTen = vi.fn()

function dung(props: Partial<Parameters<typeof RoleNameInlineEdit>[0]> = {}) {
  return render(
    <RoleNameInlineEdit
      role={VAI_TRO}
      canWrite
      pending={false}
      onRename={doiTen}
      {...props}
    />,
  )
}

async function moOSua() {
  const nguoi = userEvent.setup()
  dung()
  await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))
  return { nguoi, o: screen.getByLabelText('Tên vai trò employee') }
}

beforeEach(() => doiTen.mockClear())

describe('RoleNameInlineEdit', () => {
  it('bình thường hiện tên + mã, có nút đổi tên', () => {
    dung()
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
    expect(screen.getByText('employee')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' })).toBeInTheDocument()
  })

  it('MÃ vai trò vẫn hiện trong lúc đang sửa', async () => {
    //  Đây là thứ bản sửa-tại-dòng ở cột trái làm mất: đang gõ thì mã biến mất
    //  nên không còn biết mình sửa vai trò nào (khách báo 26/08/2026).
    await moOSua()
    expect(screen.getByText('employee')).toBeInTheDocument()
  })

  it('sửa rồi Enter thì lưu đúng một lần với tên mới', async () => {
    const { nguoi, o } = await moOSua()
    await nguoi.clear(o)
    await nguoi.type(o, 'Nhân sự & Hành chính{Enter}')

    expect(doiTen).toHaveBeenCalledTimes(1)
    expect(doiTen).toHaveBeenCalledWith(2, 'Nhân sự & Hành chính')
  })

  it('Esc thì bỏ qua, KHÔNG lưu và trả lại tên cũ', async () => {
    const { nguoi, o } = await moOSua()
    await nguoi.clear(o)
    await nguoi.type(o, 'gõ nhầm{Escape}')

    expect(doiTen).not.toHaveBeenCalled()
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
  })

  it('bấm ✕ cũng bỏ qua và trả lại tên cũ', async () => {
    const { nguoi, o } = await moOSua()
    await nguoi.clear(o)
    await nguoi.type(o, 'gõ nhầm')
    await nguoi.click(screen.getByRole('button', { name: 'Bỏ qua' }))

    expect(doiTen).not.toHaveBeenCalled()
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
  })

  it('tên rỗng thì khóa nút lưu và nói rõ vì sao', async () => {
    //  Backend chặn từ CR-173, nhưng để bấm được rồi mới ăn 422 thì người dùng
    //  tưởng hệ hỏng.
    const { nguoi, o } = await moOSua()
    await nguoi.clear(o)

    expect(screen.getByRole('button', { name: 'Lưu tên' })).toBeDisabled()
    expect(screen.getByText(/không được để trống/i)).toBeInTheDocument()
  })

  it('tên không đổi thì khóa nút lưu, không gọi máy chủ', async () => {
    await moOSua()
    expect(screen.getByRole('button', { name: 'Lưu tên' })).toBeDisabled()
    expect(doiTen).not.toHaveBeenCalled()
  })

  it('cắt khoảng trắng thừa trước khi lưu', async () => {
    const { nguoi, o } = await moOSua()
    await nguoi.clear(o)
    await nguoi.type(o, '   Nhân sự mới   {Enter}')

    expect(doiTen).toHaveBeenCalledWith(2, 'Nhân sự mới')
  })

  it('thiếu quyền ghi thì không có nút đổi tên', () => {
    dung({ canWrite: false })
    expect(screen.queryByRole('button', { name: /^Đổi tên vai trò/ })).not.toBeInTheDocument()
    expect(screen.getByText('Nhân sự')).toBeInTheDocument()
  })

  it('đổi sang vai trò KHÁC thì bỏ dở việc sửa, không mang tên cũ sang', async () => {
    //  Đang sửa dở rồi bấm sang vai trò khác ở cột trái: giữ nguyên ô nhập là
    //  người dùng lưu nhầm tên của vai trò trước vào vai trò mới.
    const nguoi = userEvent.setup()
    const { rerender } = dung()
    await nguoi.click(screen.getByRole('button', { name: 'Đổi tên vai trò Nhân sự' }))
    await nguoi.type(screen.getByLabelText('Tên vai trò employee'), ' đang gõ dở')

    rerender(
      <RoleNameInlineEdit
        role={{ id: 1, code: 'admin', name: 'Quản trị hệ thống', description: '', sort_order: 1 }}
        canWrite
        pending={false}
        onRename={doiTen}
      />,
    )

    expect(screen.queryByLabelText(/^Tên vai trò/)).not.toBeInTheDocument()
    expect(screen.getByText('Quản trị hệ thống')).toBeInTheDocument()
  })
})
