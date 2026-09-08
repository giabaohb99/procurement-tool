import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LabelMultiCell } from './label-multi-cell'
import type { WorkLabelField } from '../types/work'
import { WORK_FIELD_TYPE } from '../types/work'

/**
 * Ô chọn NHIỀU của trường tùy biến ở khung nhìn Danh sách (cột Tag).
 *
 * Chỗ hỏng âm thầm nhất là **tick liên tiếp**: menu cố ý đứng yên để chọn được
 * mấy giá trị một lượt, mà mỗi lần tick là một lượt gọi máy chủ. Nếu mỗi lượt
 * đều đọc bộ giá trị CŨ từ props thì lượt sau ghi đè lượt trước — tick ba nhãn
 * chỉ dính nhãn cuối, và không có lỗi nào báo ra.
 */

const OPTIONS = [
  { id: 10, field_id: 3, name: 'Nội dung', color: 'violet', sort_order: 1 },
  { id: 11, field_id: 3, name: 'Sự kiện', color: 'pink', sort_order: 2 },
  { id: 12, field_id: 3, name: 'Quảng cáo', color: 'sky', sort_order: 3 },
]

function truong(over: Partial<WorkLabelField> = {}): WorkLabelField {
  return {
    id: 3,
    list_id: 1,
    name: 'Tag',
    sort_order: 1,
    field_type: WORK_FIELD_TYPE.MULTI,
    system_key: '',
    value_count: 0,
    options: OPTIONS,
    ...over,
  }
}

/**
 * Mở menu rồi trả về hàm lấy một mục theo tên.
 *
 * `userEvent` chứ không `fireEvent.click`: Radix mở menu bằng `pointerdown`,
 * mà `fireEvent.click` không bắn sự kiện con trỏ nào nên menu không mở.
 */
async function moMenu(nguoi: ReturnType<typeof userEvent.setup>) {
  await nguoi.click(screen.getByRole('button', { name: 'Tag' }))
  return (name: string) => screen.getByRole('menuitemcheckbox', { name: new RegExp(name) })
}

describe('LabelMultiCell', () => {
  it('tick liên tiếp thì CỘNG DỒN, không để lượt sau nuốt lượt trước', async () => {
    //  Đúng ca gây lỗi: bảng chỉ mới lại sau khi máy chủ trả lời, nên hai lượt
    //  tick nhanh hơn một vòng gọi đều thấy `chosen` cũ là rỗng.
    const nguoi = userEvent.setup()
    const onChange = vi.fn()
    render(<LabelMultiCell field={truong()} chosen={[]} onChange={onChange} />)

    const muc = await moMenu(nguoi)
    await nguoi.click(muc('Nội dung'))
    await nguoi.click(muc('Quảng cáo'))

    expect(onChange).toHaveBeenNthCalledWith(1, [10])
    expect(onChange).toHaveBeenNthCalledWith(2, [10, 12])
  })

  it('bỏ tick một giá trị thì chỉ rụng đúng nó', async () => {
    const nguoi = userEvent.setup()
    const onChange = vi.fn()
    render(<LabelMultiCell field={truong()} chosen={[10, 11, 12]} onChange={onChange} />)

    await nguoi.click((await moMenu(nguoi))('Sự kiện'))
    expect(onChange).toHaveBeenCalledWith([10, 12])
  })

  it('bỏ tick giá trị CUỐI CÙNG thì gửi null, không phải mảng rỗng', async () => {
    //  Cùng một nghĩa "bỏ chọn" với năm kiểu trường kia; gửi `[]` là để máy chủ
    //  tự đoán.
    const nguoi = userEvent.setup()
    const onChange = vi.fn()
    render(<LabelMultiCell field={truong()} chosen={[10]} onChange={onChange} />)

    await nguoi.click((await moMenu(nguoi))('Nội dung'))
    expect(onChange).toHaveBeenCalledWith(null)
  })

  it('«Bỏ chọn hết» gửi null và chỉ hiện khi đang có giá trị', async () => {
    const nguoi = userEvent.setup()
    const onChange = vi.fn()
    const { rerender } = render(<LabelMultiCell field={truong()} chosen={[]} onChange={onChange} />)
    await moMenu(nguoi)
    expect(screen.queryByText('Bỏ chọn hết')).not.toBeInTheDocument()
    await nguoi.keyboard('{Escape}')

    rerender(<LabelMultiCell field={truong()} chosen={[10, 11]} onChange={onChange} />)
    await moMenu(nguoi)
    await nguoi.click(screen.getByText('Bỏ chọn hết'))
    expect(onChange).toHaveBeenCalledWith(null)
  })

  it('dữ liệu máy chủ đổi thì ô bám theo, không giữ bản nháp cũ', () => {
    //  Người khác sửa cùng việc, hoặc lượt lưu bị máy chủ từ chối và bảng nạp
    //  lại giá trị cũ — ô phải theo máy chủ chứ không khăng khăng bản của mình.
    const { rerender } = render(
      <LabelMultiCell field={truong()} chosen={[10]} onChange={vi.fn()} />,
    )
    expect(screen.getByText('Nội dung')).toBeInTheDocument()

    rerender(<LabelMultiCell field={truong()} chosen={[11]} onChange={vi.fn()} />)
    expect(screen.getByText('Sự kiện')).toBeInTheDocument()
    expect(screen.queryByText('Nội dung')).not.toBeInTheDocument()
  })

  it('mảng props dựng mới mỗi lần render KHÔNG làm ô đặt lại vô tận', async () => {
    //  Tầng trên dựng `chosen` bằng `.map().filter()` nên mỗi lần render là một
    //  tham chiếu khác. So theo tham chiếu là vòng lặp đặt-lại vô tận.
    const nguoi = userEvent.setup()
    const onChange = vi.fn()
    const { rerender } = render(
      <LabelMultiCell field={truong()} chosen={[10]} onChange={onChange} />,
    )
    const muc = await moMenu(nguoi)
    await nguoi.click(muc('Sự kiện'))
    expect(onChange).toHaveBeenCalledWith([10, 11])

    //  Cùng NỘI DUNG nhưng mảng mới: bản nháp vừa tick không được đặt lại.
    rerender(<LabelMultiCell field={truong()} chosen={[10]} onChange={onChange} />)
    expect(screen.getByRole('menuitemcheckbox', { name: /Sự kiện/ })).toHaveAttribute(
      'aria-checked',
      'true',
    )
  })

  it('chỉ xem thì KHÔNG dựng nút — nút bấm không ăn gì là lừa người dùng', () => {
    render(<LabelMultiCell field={truong()} chosen={[10]} disabled onChange={vi.fn()} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByText('Nội dung')).toBeInTheDocument()
  })

  it('chỉ xem mà chưa chọn gì thì hiện gạch ngang, không để ô trống trơn', () => {
    render(<LabelMultiCell field={truong()} chosen={[]} disabled onChange={vi.fn()} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('nhiều giá trị thì gom lại thành «+N», tên đầy đủ nằm ở tooltip', () => {
    //  Ô rộng 150px: hai chip tiếng Việt là đã tràn.
    render(<LabelMultiCell field={truong()} chosen={[10, 11, 12]} onChange={vi.fn()} />)
    expect(screen.getByText('+2')).toHaveAttribute('title', 'Sự kiện, Quảng cáo')
  })

  it('trường CHƯA KHAI giá trị nào thì nói ra, không mở menu rỗng', async () => {
    const nguoi = userEvent.setup()
    render(<LabelMultiCell field={truong({ options: [] })} chosen={[]} onChange={vi.fn()} />)
    await nguoi.click(screen.getByRole('button', { name: 'Tag' }))
    expect(screen.getByText('Trường chưa khai giá trị')).toBeInTheDocument()
  })

  it('giá trị đã bị XÓA khỏi trường thì không vẽ chip ma', () => {
    //  Quản trị xóa một giá trị khỏi bộ chọn nhưng việc cũ còn trỏ vào nó.
    render(<LabelMultiCell field={truong()} chosen={[999]} onChange={vi.fn()} />)
    expect(screen.getByText('Chưa chọn')).toBeInTheDocument()
  })
})
