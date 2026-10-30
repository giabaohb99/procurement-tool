import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useForm, FormProvider } from 'react-hook-form'
import { describe, expect, it } from 'vitest'

import type { ExtraPhone } from '../schemas/extra-phones-schema'
import { PhoneListEditor } from './phone-list-editor'

interface Shape {
  phone: string
  phone_label: string
  extra_phones: ExtraPhone[]
}

let latest: Shape = { phone: '', phone_label: '', extra_phones: [] }

function Harness({ initial, disabled }: { initial: Shape; disabled?: boolean }) {
  const form = useForm<Shape>({ defaultValues: initial })
  latest = form.watch()
  return (
    <FormProvider {...form}>
      <PhoneListEditor disabled={disabled} />
    </FormProvider>
  )
}

describe('PhoneListEditor (duoc-CR-694)', () => {
  it('thêm số cho tới khi đủ 4 số khác thì ẩn nút Thêm', async () => {
    render(<Harness initial={{ phone: '0911111111', phone_label: '', extra_phones: [] }} />)
    const add = () => screen.queryByRole('button', { name: /Thêm số/ })
    for (let i = 0; i < 4; i++) await userEvent.click(add()!)
    expect(add()).toBeNull()
    expect(screen.getAllByLabelText(/^Số điện thoại khác \d$/)).toHaveLength(4)
    expect(latest.extra_phones).toHaveLength(4)
  })

  it('đặt số phụ làm số chính thì hoán đổi trong form', async () => {
    render(<Harness initial={{ phone: '0911111111', phone_label: 'Cá nhân', extra_phones: [{ number: '0922222222', label: 'Zalo' }] }} />)
    await userEvent.click(screen.getByRole('button', { name: /Đặt số khác 1 làm số chính/ }))
    expect(latest.phone).toBe('0922222222')
    expect(latest.phone_label).toBe('Zalo')
    expect(latest.extra_phones).toEqual([{ number: '0911111111', label: 'Cá nhân' }])
    expect(screen.getByLabelText('Nhãn số chính')).toHaveValue('Zalo')
    expect(screen.getByLabelText('Số điện thoại')).toHaveValue('0922222222')
  })

  it('xóa một số phụ', async () => {
    render(<Harness initial={{ phone: '0911111111', phone_label: '', extra_phones: [{ number: '0922222222', label: '' }] }} />)
    await userEvent.click(screen.getByRole('button', { name: /Xóa số điện thoại khác 1/ }))
    expect(latest.extra_phones).toEqual([])
  })

  it('nhãn gõ tự do và báo lỗi số sai / trùng ngay tại dòng', async () => {
    render(<Harness initial={{ phone: '0911111111', phone_label: '', extra_phones: [{ number: '0911 111 111', label: '' }] }} />)
    expect(screen.getByText('Số này đã nhập ở trên')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Nhãn số điện thoại khác 1'), 'Vợ')
    expect(latest.extra_phones[0].label).toBe('Vợ')
    await userEvent.clear(screen.getByLabelText('Số điện thoại khác 1'))
    await userEvent.type(screen.getByLabelText('Số điện thoại khác 1'), 'abc')
    expect(screen.getByText(/Chỉ gồm chữ số/)).toBeInTheDocument()
  })

  it('chỉ xem: không có nút sửa', () => {
    render(<Harness disabled initial={{ phone: '0911111111', phone_label: '', extra_phones: [{ number: '0922222222', label: '' }] }} />)
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByLabelText('Số điện thoại khác 1')).toBeDisabled()
  })
})
