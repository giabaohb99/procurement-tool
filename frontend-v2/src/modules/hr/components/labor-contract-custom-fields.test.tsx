import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useForm } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

import { Form } from '@/shared/ui/form'
import type { LaborContractFormValues } from '../schemas/labor-contract-schema'
import type { LaborContractInputField } from '../types/labor-contract-variable'
import { LaborContractCustomFields } from './labor-contract-custom-fields'

const f = (code: string, value_type: number, over: Partial<LaborContractInputField> = {}): LaborContractInputField => ({
  code, label: `Nhãn ${code}`, description: '', value_type, default_value: '', is_required: false, is_active: true, sort_order: 0, ...over,
})

function Harness({ fields, stored = {}, onOuterSubmit }: { fields: LaborContractInputField[]; stored?: Record<string, string>; onOuterSubmit?: () => void }) {
  const form = useForm<LaborContractFormValues>({ defaultValues: { custom_values: stored } as LaborContractFormValues })
  return (
    <form onSubmit={(e) => { e.preventDefault(); onOuterSubmit?.() }}>
      <Form {...form}>
        <LaborContractCustomFields form={form} fields={fields} />
      </Form>
      <output data-testid="dump">{JSON.stringify(form.watch('custom_values'))}</output>
    </form>
  )
}

describe('LaborContractCustomFields', () => {
  it('không có biến nào -> không vẽ khối', () => {
    const { container } = render(<Harness fields={[]} />)
    expect(container.querySelector('section')).toBeNull()
  })

  it('mỗi kiểu ra đúng loại ô', () => {
    render(<Harness fields={[f('a_chu', 1), f('b_nhieu', 2), f('c_so', 3), f('d_ngay', 4, { default_value: '' }), f('e_tien', 5)]} />)
    expect(screen.getByRole('textbox', { name: 'Nhãn a_chu' }).tagName).toBe('INPUT')
    expect(screen.getByRole('textbox', { name: 'Nhãn b_nhieu' }).tagName).toBe('TEXTAREA')
    expect(screen.getByRole('textbox', { name: 'Nhãn c_so' })).toHaveAttribute('inputmode', 'decimal')
    expect(screen.getByRole('textbox', { name: 'Nhãn e_tien' })).toBeInTheDocument()
    expect(screen.getByText('Thông tin bổ sung cho mẫu')).toBeInTheDocument()
  })

  it('biến bắt buộc có dấu sao + chú "bắt buộc khi sinh tệp"; mô tả hiện dưới ô', () => {
    render(<Harness fields={[f('a_chu', 1, { is_required: true, description: 'Điền số ngày phép' })]} />)
    expect(screen.getByTitle('Bắt buộc khi sinh tệp và khi chuyển sang Đã ký')).toBeInTheDocument()
    expect(screen.getByText(/Bắt buộc khi sinh tệp \(lưu nháp/)).toBeInTheDocument()
    expect(screen.getByText('Điền số ngày phép')).toBeInTheDocument()
  })

  it('nhập giá trị cập nhật đúng khóa trong form', async () => {
    render(<Harness fields={[f('a_chu', 1)]} />)
    await userEvent.type(screen.getByRole('textbox', { name: 'Nhãn a_chu' }), 'xin')
    expect(screen.getByTestId('dump')).toHaveTextContent('{"a_chu":"xin"}')
  })

  it('biến ngừng dùng còn giá trị -> hiện CHỈ ĐỌC (không ô nhập); không có giá trị -> ẩn hẳn', () => {
    render(<Harness fields={[f('cu', 5, { is_active: false }), f('cu_trong', 1, { is_active: false }), f('moi', 1)]} stored={{ cu: '15000000' }} />)
    expect(screen.getByText('15.000.000')).toBeInTheDocument()
    expect(screen.getByText(/đã ngừng dùng/)).toBeInTheDocument()
    expect(screen.queryByRole('textbox', { name: 'Nhãn cu' })).toBeNull()
    expect(screen.queryByText('Nhãn cu_trong')).toBeNull()
    expect(screen.getByRole('textbox', { name: 'Nhãn moi' })).toBeInTheDocument()
  })

  it('Enter trong ô chữ không submit form cha', async () => {
    const outer = vi.fn()
    render(<Harness fields={[f('a_chu', 1)]} onOuterSubmit={outer} />)
    await userEvent.type(screen.getByRole('textbox', { name: 'Nhãn a_chu' }), 'abc{Enter}')
    expect(outer).not.toHaveBeenCalled()
  })
})
