import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { AccessSubjectPicker } from './access-subject-picker'
import { SUBJECT_KIND } from './subject-kind'
import type { MixedSubject, SubjectOption } from './subject-kind'

//  Chuyển từ `document/components/folder-share-subject-picker*.test.tsx`
//  (phase 04, kế hoạch `plans/261002-0836-phan-quyen-tung-bao-cao`) — bản THUẦN
//  UI nhận `options` cố định qua prop, không còn mock 4 hook của `hr` (component
//  không tự gọi hook nào nữa).
const FIXED_OPTIONS: SubjectOption[] = [
  { subject_kind: SUBJECT_KIND.company, subject_id: 1, label: 'DEGO Holding' },
  { subject_kind: SUBJECT_KIND.department, subject_id: 7, label: 'Kế toán · DEGO Holding' },
  { subject_kind: SUBJECT_KIND.department, subject_id: 8, label: 'Kế toán · CÔNG TY TNHH ABA' },
  { subject_kind: SUBJECT_KIND.role, subject_id: 3, label: 'Văn thư' },
  { subject_kind: SUBJECT_KIND.employee, subject_id: 1, label: 'Người Một' },
  { subject_kind: SUBJECT_KIND.employee, subject_id: 2, label: 'Người Hai' },
]

function Picker({
  value = [],
  onChange = vi.fn(),
  options = FIXED_OPTIONS,
  loading,
}: {
  value?: MixedSubject[]
  onChange?: (v: MixedSubject[]) => void
  options?: SubjectOption[]
  loading?: boolean
}) {
  return <AccessSubjectPicker value={value} onChange={onChange} options={options} loading={loading} />
}

async function openPicker(props: Parameters<typeof Picker>[0] = {}) {
  const user = userEvent.setup()
  render(<Picker {...props} />)
  await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
  return user
}

describe('AccessSubjectPicker', () => {
  //  Bug lead bắt 23/09/2026: dòng tùy chọn từng là `<button>` bọc `Checkbox`
  //  (cũng là một `<button>`) — React cảnh báo "cannot contain a nested
  //  <button>". Rà lại bằng cách theo dõi `console.error` thật (jsdom/React
  //  in cảnh báo này qua đó) trong lúc mở popup và bấm chọn.
  it('không phát cảnh báo lồng <button> khi mở popup và chọn một dòng', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const user = await openPicker()
    await user.click(await screen.findByText('Người Một'))

    const nestedButtonWarning = errorSpy.mock.calls.some((args) =>
      args.some((arg) => typeof arg === 'string' && arg.includes('cannot contain a nested')),
    )
    expect(nestedButtonWarning).toBe(false)
    errorSpy.mockRestore()
  })

  it('bấm CHUỘT vào một dòng → gọi onChange kèm đúng subject vừa chọn', async () => {
    const onChange = vi.fn()
    const user = await openPicker({ onChange })
    await user.click(await screen.findByText('Người Một'))

    expect(onChange).toHaveBeenCalledWith([{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }])
  })

  it('điều hướng bằng BÀN PHÍM (Tab tới dòng rồi Enter) vẫn chọn được — không phụ thuộc chuột', async () => {
    const onChange = vi.fn()
    const user = await openPicker({ onChange })
    const option = await screen.findByRole('option', { name: /Người Một/ })
    option.focus()
    await user.keyboard('{Enter}')

    expect(onChange).toHaveBeenCalledWith([{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }])
  })

  it('phím Space trên dòng đã chọn → bỏ chọn lại (khớp aria-selected)', async () => {
    const onChange = vi.fn()
    const user = await openPicker({
      value: [{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }],
      onChange,
    })
    const option = await screen.findByRole('option', { name: /Người Một/ })
    expect(option).toHaveAttribute('aria-selected', 'true')

    option.focus()
    await user.keyboard(' ')

    expect(onChange).toHaveBeenCalledWith([])
  })

  it('lọc theo loại hiện đúng số đếm và thu hẹp danh sách khi bấm', async () => {
    const user = await openPicker()
    const filters = screen.getByRole('group', { name: 'Lọc theo loại' })
    expect(within(filters).getByRole('button', { name: 'Phòng ban (2)' })).toBeInTheDocument()
    expect(within(filters).getByRole('button', { name: 'Người (2)' })).toBeInTheDocument()

    await user.click(within(filters).getByRole('button', { name: 'Phòng ban (2)' }))
    expect(screen.getAllByRole('option')).toHaveLength(2)
  })

  it('số đếm đi theo từ khóa đang gõ, không phải tổng cố định', async () => {
    const user = await openPicker()
    await user.type(screen.getByPlaceholderText('Gõ để tìm…'), 'ke toan')

    expect(screen.getByRole('button', { name: 'Tất cả (2)' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Người (0)' })).toBeInTheDocument()
  })

  it('gõ không dấu vẫn khớp nhãn có dấu', async () => {
    await openPicker()
    await userEvent.type(screen.getByPlaceholderText('Gõ để tìm…'), 'ke toan')

    expect(screen.getByRole('option', { name: /Kế toán · DEGO Holding/ })).toBeInTheDocument()
  })

  it('đang tải (`loading`) + chưa có mục nào khớp → báo "Đang tải…", không phải "Không có ai khớp."', async () => {
    await openPicker({ options: [], loading: true })

    expect(screen.getByText('Đang tải…')).toBeInTheDocument()
    expect(screen.queryByText('Không có ai khớp.')).not.toBeInTheDocument()
  })

  it('đã tải xong mà không khớp gì → báo "Không có ai khớp."', async () => {
    const user = await openPicker({ options: [] })
    await user.type(screen.getByPlaceholderText('Gõ để tìm…'), 'khong ai ten vay')

    expect(screen.getByText('Không có ai khớp.')).toBeInTheDocument()
  })

  it('chọn rồi bấm nút X trên chip → gọi onChange bỏ đúng subject đó', async () => {
    const onChange = vi.fn()
    render(
      <Picker
        value={[{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }]}
        onChange={onChange}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: /Bỏ Người Một/ }))

    expect(onChange).toHaveBeenCalledWith([])
  })
})
