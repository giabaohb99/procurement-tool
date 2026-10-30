import { zodResolver } from '@hookform/resolvers/zod'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useForm } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

import { Form } from '@/shared/ui/form'
import {
  EMPTY_EMPLOYEE_PROFILE_FORM,
  employeeProfileFormValues,
  employeeProfileSchema,
  pickWritableProfile,
  type EmployeeProfileFormValues,
} from '../schemas/employee-schema'
import type { EmployeeDetail } from '../types/employee'
import { EmployeeSalarySection } from './employee-salary-section'

const BASE = {
  id: 9,
  user_id: 3,
  code: 'NSU009',
  full_name: 'Nguyễn Văn A',
  status: 'official',
} as EmployeeDetail

interface HarnessProps {
  employee: EmployeeDetail
  isSelf?: boolean
  canWrite?: boolean
  onSave?: (payload: Partial<EmployeeProfileFormValues>) => void
}

/** Dựng đúng đường của màn chi tiết: nạp form từ API → zod → `pickWritableProfile` → PATCH. */
function Harness({ employee, isSelf = false, canWrite = true, onSave = () => {} }: HarnessProps) {
  const form = useForm<EmployeeProfileFormValues>({
    resolver: zodResolver(employeeProfileSchema),
    defaultValues: { ...EMPTY_EMPLOYEE_PROFILE_FORM, ...employeeProfileFormValues(employee) },
  })
  return (
    <Form {...form}>
      <form onSubmit={(e) => void form.handleSubmit((v) => onSave(pickWritableProfile(v, true)))(e)}>
        <EmployeeSalarySection employee={employee} isSelf={isSelf} canWrite={canWrite} />
        <button type="submit">Lưu</button>
      </form>
    </Form>
  )
}

async function save(onSave: ReturnType<typeof vi.fn>) {
  await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
  expect(onSave).toHaveBeenCalledTimes(1)
  return onSave.mock.calls[0][0] as Partial<EmployeeProfileFormValues>
}

describe('EmployeeSalarySection — người khác có quyền sửa', () => {
  it('sends neither salary key when the user never touched the fields — the hidden real number is kept', async () => {
    //  Bẫy mất dữ liệu: người lưu không thấy số; gửi 0/null cho ô trống là đè lên lương thật.
    const onSave = vi.fn()
    render(<Harness employee={{ ...BASE, salary_set: true }} onSave={onSave} />)
    const payload = await save(onSave)
    expect(payload).not.toHaveProperty('salary_monthly')
    expect(payload).not.toHaveProperty('allowance_monthly')
  })

  it('shows empty inputs with the "Đã nhập (ẩn)" hint when a salary exists, "Chưa nhập" when not', () => {
    const { unmount } = render(<Harness employee={{ ...BASE, salary_set: true }} />)
    const boxes = screen.getAllByRole('textbox')
    expect(boxes).toHaveLength(2)
    for (const box of boxes) {
      expect(box).toHaveValue('')
      expect(box).toHaveAttribute('placeholder', 'Đã nhập (ẩn)')
    }
    unmount()
    render(<Harness employee={{ ...BASE, salary_set: false }} />)
    for (const box of screen.getAllByRole('textbox')) expect(box).toHaveAttribute('placeholder', 'Chưa nhập')
    expect(screen.queryByRole('button', { name: 'Xóa số đã nhập' })).not.toBeInTheDocument()
  })

  it('sends only the field the user typed into', async () => {
    const onSave = vi.fn()
    render(<Harness employee={{ ...BASE, salary_set: true }} onSave={onSave} />)
    await userEvent.type(screen.getByRole('textbox', { name: 'Lương (đ/tháng)' }), '15.000.000')
    const payload = await save(onSave)
    expect(payload.salary_monthly).toBe(15_000_000)
    expect(payload).not.toHaveProperty('allowance_monthly')
  })

  it('typing then clearing the field goes back to "keep", never to 0', async () => {
    const onSave = vi.fn()
    render(<Harness employee={{ ...BASE, salary_set: true }} onSave={onSave} />)
    const box = screen.getByRole('textbox', { name: 'Phụ cấp (đ/tháng)' })
    await userEvent.type(box, '500000')
    await userEvent.clear(box)
    await userEvent.tab()
    const payload = await save(onSave)
    expect(payload).not.toHaveProperty('allowance_monthly')
  })

  it('"Xóa số đã nhập" sends 0 for both fields, does not submit by itself, and can be undone', async () => {
    const onSave = vi.fn()
    render(<Harness employee={{ ...BASE, salary_set: true }} onSave={onSave} />)
    await userEvent.click(screen.getByRole('button', { name: 'Xóa số đã nhập' }))
    //  Nút nằm trong form hồ sơ: thiếu `type="button"` là bấm vào đã LƯU luôn.
    expect(onSave).not.toHaveBeenCalled()
    expect(screen.getByText('Lương và phụ cấp đã nhập sẽ bị xóa khi bấm Lưu.')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Không xóa nữa' }))
    await userEvent.click(screen.getByRole('button', { name: 'Xóa số đã nhập' }))
    const payload = await save(onSave)
    expect(payload).toMatchObject({ salary_monthly: 0, allowance_monthly: 0 })
  })

  it('keeps the "clear" intent when the user focuses and leaves an empty field', async () => {
    const onSave = vi.fn()
    render(<Harness employee={{ ...BASE, salary_set: true }} onSave={onSave} />)
    await userEvent.click(screen.getByRole('button', { name: 'Xóa số đã nhập' }))
    await userEvent.click(screen.getByRole('textbox', { name: 'Lương (đ/tháng)' }))
    await userEvent.tab()
    const payload = await save(onSave)
    expect(payload).toMatchObject({ salary_monthly: 0, allowance_monthly: 0 })
  })
})

describe('EmployeeSalarySection — chính chủ và người chỉ xem', () => {
  it('the employee sees their own numbers read-only and can never send them (backend would 403)', async () => {
    const onSave = vi.fn()
    render(
      <Harness
        employee={{ ...BASE, salary_monthly: 12_500_000, allowance_monthly: 0 }}
        isSelf
        canWrite
        onSave={onSave}
      />,
    )
    expect(screen.getByText('12.500.000 đ')).toBeInTheDocument()
    expect(screen.getByText('Chưa nhập')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    //  Số đã có trong API nhưng KHÔNG được nạp vào form — lần Lưu nào cũng không mang lương theo.
    const payload = await save(onSave)
    expect(payload).not.toHaveProperty('salary_monthly')
    expect(payload).not.toHaveProperty('allowance_monthly')
  })

  it('a read-only viewer sees only whether a salary exists, never an input', () => {
    const { unmount } = render(<Harness employee={{ ...BASE, salary_set: true }} canWrite={false} />)
    expect(screen.getAllByText('Đã nhập (ẩn)')).toHaveLength(2)
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    unmount()
    render(<Harness employee={{ ...BASE, salary_set: false }} canWrite={false} />)
    expect(screen.getAllByText('Chưa nhập')).toHaveLength(2)
  })

  it('falls back to the numbers when an older server sends no salary_set flag', () => {
    render(<Harness employee={{ ...BASE, allowance_monthly: 300_000 }} canWrite={false} />)
    expect(screen.getAllByText('Đã nhập (ẩn)')).toHaveLength(2)
  })
})
