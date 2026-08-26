import { render, screen } from '@testing-library/react'
import { act } from 'react'
import { useForm, type UseFormReturn } from 'react-hook-form'
import { describe, expect, it, vi } from 'vitest'

import { Form } from '@/shared/ui/form'
import { emptyDocumentForm } from '../helpers/document-form-defaults'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { DocumentLeaveFields } from './document-leave-fields'

//  Ô «Người nghỉ» / «Người bàn giao» gọi API nhân sự — không phải thứ tệp này kiểm.
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { items: [], total: 0 } }),
}))

/** Dựng component kèm form thật, và trả `form` ra để test tự đặt giá trị. */
function dung() {
  let form!: UseFormReturn<DocumentRecordFormValues>

  function Khung() {
    form = useForm<DocumentRecordFormValues>({ defaultValues: emptyDocumentForm() })
    return (
      <Form {...form}>
        <DocumentLeaveFields form={form} />
      </Form>
    )
  }

  render(<Khung />)
  return () => form
}

/** Số ô «Buổi» đang hiện — đây là thứ phân biệt nghỉ một ngày với nghỉ nhiều ngày. */
function visibleCellCount() {
  return screen.getAllByText('Buổi').length
}

function setDate(form: UseFormReturn<DocumentRecordFormValues>, tu: string, den?: string) {
  act(() => {
    form.setValue('leave.from_date', tu)
    if (den !== undefined) form.setValue('leave.to_date', den)
  })
}

describe('DocumentLeaveFields', () => {
  it('chưa chọn ngày thì hiện HAI ô buổi như khoảng nhiều ngày', () => {
    dung()
    expect(visibleCellCount()).toBe(2)
  })

  it('chọn Từ ngày thì Đến ngày TỰ BÁM THEO', () => {
    //  «Nghỉ chiều thứ Sáu» là ca hay gặp nhất. Bắt khai đủ bốn ô cho một buổi
    //  nghỉ là bốn thao tác cho việc nhỏ nhất (khách góp ý 25/08/2026).
    const lay = dung()
    setDate(lay(), '2026-09-11')

    expect(lay().getValues('leave.to_date')).toBe('2026-09-11')
  })

  it('nghỉ trong MỘT ngày thì gộp còn một ô buổi', () => {
    //  Hai ô buổi lúc đó nói về CÙNG một buổi — để hai ô là mời người ta đặt
    //  lệch nhau rồi ra dữ liệu vô nghĩa («sáng → chiều» của cùng một ngày).
    const lay = dung()
    setDate(lay(), '2026-09-11', '2026-09-11')

    expect(visibleCellCount()).toBe(1)
  })

  it('nghỉ nhiều ngày thì vẫn đủ hai ô buổi', () => {
    const lay = dung()
    setDate(lay(), '2026-09-11', '2026-09-14')

    expect(visibleCellCount()).toBe(2)
  })

  it('Đến ngày đã có và SAU Từ ngày thì không bị ghi đè', () => {
    const lay = dung()
    setDate(lay(), '2026-09-11', '2026-09-14')
    setDate(lay(), '2026-09-12')

    expect(lay().getValues('leave.to_date')).toBe('2026-09-14')
  })

  it('đổi Từ ngày ra SAU Đến ngày thì kéo Đến ngày theo, không để khoảng ngược', () => {
    const lay = dung()
    setDate(lay(), '2026-09-11', '2026-09-14')
    setDate(lay(), '2026-09-20')

    expect(lay().getValues('leave.to_date')).toBe('2026-09-20')
  })

  it('tổng số ngày ĐIỀN SẴN theo khoảng đã chọn', () => {
    //  Bỏ trống KHÔNG làm con số biến mất — backend vẫn tự tính rồi lưu. Ô rỗng
    //  chỉ giấu đi một con số có thể sai (đếm cả cuối tuần).
    const lay = dung()
    setDate(lay(), '2026-09-11', '2026-09-14')

    expect(lay().getValues('leave.total_days')).toBe(4)
  })

  it('nửa ngày: cùng ngày + buổi sáng ra 0.5 công', () => {
    const lay = dung()
    setDate(lay(), '2026-09-11', '2026-09-11')
    act(() => {
      lay().setValue('leave.from_session', 'morning')
    })

    expect(lay().getValues('leave.total_days')).toBe(0.5)
  })
})
