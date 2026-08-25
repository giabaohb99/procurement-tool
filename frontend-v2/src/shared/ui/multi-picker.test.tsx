import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { MultiPicker, type MultiPickerOption } from './multi-picker'

const OPTIONS: MultiPickerOption[] = [
  { id: 1, label: 'CÔNG TY TNHH DEGO HOLDING', hint: 'DEGO' },
  { id: 2, label: 'CÔNG TY TNHH N2SBIO VIỆT NAM', hint: 'N2SBIO' },
  { id: 3, label: 'NHÀ PHÂN PHỐI DR XANH', hint: 'NPP DR.XANH' },
]

async function openPicker(value: number[] = [], onChange = vi.fn()) {
  const user = userEvent.setup()
  render(
    <MultiPicker
      value={value}
      onChange={onChange}
      options={OPTIONS}
      placeholder="Chọn pháp nhân…"
    />,
  )
  //  Nút mở đổi CHỮ khi đã chọn gì đó: rỗng thì là câu mời, có rồi thì là
  //  «Đã chọn N» (CR-172). Tìm theo cả hai kiểu để không phải sửa mỗi bài test.
  await user.click(
    screen.getByRole('button', {
      name: value.length ? new RegExp(`Đã chọn ${value.length}`) : /Chọn pháp nhân/,
    }),
  )
  return { user, onChange }
}

describe('MultiPicker', () => {
  it('chọn tất cả thì tick hết danh sách trong một lần bấm', async () => {
    const { user, onChange } = await openPicker()
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    expect(onChange).toHaveBeenCalledWith([1, 2, 3])
  })

  it('đang tìm thì chỉ chọn phần khớp từ khóa, không đụng mục đã chọn trước đó', async () => {
    const { user, onChange } = await openPicker([3])
    await user.type(screen.getByPlaceholderText('Tìm…'), 'n2sbio')
    await user.click(screen.getByRole('button', { name: /Chọn tất cả/ }))
    expect(onChange).toHaveBeenCalledWith([3, 2])
  })

  it('tick hết rồi thì nút đổi thành bỏ chọn tất cả', async () => {
    const { user, onChange } = await openPicker([1, 2, 3])
    await user.click(screen.getByRole('button', { name: /Bỏ chọn tất cả/ }))
    expect(onChange).toHaveBeenCalledWith([])
  })
})

/** 40 mục để vượt ngưỡng gập chip (10). Ghim `id: number` để `value` khớp kiểu. */
const NHIEU: (MultiPickerOption & { id: number })[] = Array.from({ length: 40 }, (_, i) => ({
  id: i + 1,
  label: `Nhân sự ${i + 1}`,
}))

function dungNhieuChip(value: number[], onChange = vi.fn()) {
  render(
    <MultiPicker
      value={value}
      onChange={onChange}
      options={NHIEU}
      placeholder="Chọn người được xem…"
    />,
  )
  return onChange
}

describe('MultiPicker — dải chip khi chọn nhiều', () => {
  it('chọn nhiều thì GẬP dải chip lại, không đổ hết ra màn hình', () => {
    //  Khách báo 25/08/2026: sổ văn bản chọn ~200 người xem, mỗi người một chip
    //  nên dải chip cao hơn cả màn hình và đẩy ô «Người quản lý» ngay dưới đi
    //  mất — người dùng tưởng form hỏng.
    dungNhieuChip(NHIEU.map((item) => item.id))

    expect(screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })).toHaveLength(10)
    expect(screen.getByRole('button', { name: /Xem thêm 30/ })).toBeInTheDocument()
  })

  it('nút mở nói SỐ LƯỢNG đã chọn thay cho câu mời chọn', () => {
    dungNhieuChip([1, 2, 3])
    expect(screen.getByRole('button', { name: /Đã chọn 3/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Chọn người được xem/ })).not.toBeInTheDocument()
  })

  it('bung ra thì thấy đủ, và thu gọn lại được', async () => {
    //  Gập chứ KHÔNG giấu hẳn: bỏ đúng một người trong số đã chọn vẫn phải làm
    //  được, chỉ là không bày sẵn cả trăm chip.
    const nguoi = userEvent.setup()
    dungNhieuChip(NHIEU.map((item) => item.id))

    await nguoi.click(screen.getByRole('button', { name: /Xem thêm 30/ }))
    expect(screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })).toHaveLength(40)

    await nguoi.click(screen.getByRole('button', { name: /Thu gọn/ }))
    expect(screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })).toHaveLength(10)
  })

  it('bung ra thì dải chip ĐÓNG KHUNG và cuộn, không dựng lại bức tường vừa dỡ', async () => {
    //  Bung mà thả trôi thì 200 chip lại đẩy phần dưới của form đi mất — đúng
    //  cái lỗi ban đầu, chỉ khác là phải bấm một nút mới thấy.
    const nguoi = userEvent.setup()
    dungNhieuChip(NHIEU.map((item) => item.id))
    await nguoi.click(screen.getByRole('button', { name: /Xem thêm 30/ }))

    const chip = screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })[0]
    const khung = chip.closest('div')
    expect(khung?.className).toMatch(/overflow-y-auto/)
    expect(khung?.className).toMatch(/max-h-/)
  })

  it('gập lại thì bỏ khung cuộn, không để lại ô trống lửng', async () => {
    const nguoi = userEvent.setup()
    dungNhieuChip(NHIEU.map((item) => item.id))
    await nguoi.click(screen.getByRole('button', { name: /Xem thêm 30/ }))
    await nguoi.click(screen.getByRole('button', { name: /Thu gọn/ }))

    const chip = screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })[0]
    expect(chip.closest('div')?.className).not.toMatch(/overflow-y-auto/)
  })

  it('nút thao tác KHÔNG nằm lẫn trong dải chip', () => {
    //  «Xem thêm» / «Bỏ hết» không phải là "một người đã chọn"; để lẫn giữa các
    //  chip thì người dùng đọc nhầm thành một mục nữa trong danh sách.
    dungNhieuChip(NHIEU.map((item) => item.id))
    const chip = screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })[0]
    const daiChip = chip.closest('div')

    expect(daiChip?.contains(screen.getByRole('button', { name: /Xem thêm/ }))).toBe(false)
    expect(daiChip?.contains(screen.getByRole('button', { name: 'Bỏ hết' }))).toBe(false)
  })

  it('ít hơn ngưỡng thì không hiện nút bung', () => {
    dungNhieuChip([1, 2])
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thu gọn/ })).not.toBeInTheDocument()
  })

  it('ĐÚNG 10 (bằng ngưỡng) thì hiện hết, không bày nút bung thừa', () => {
    //  Ca biên: `slice(0, 10)` của đúng 10 phần tử vẫn là 10, phần dư = 0. Sai
    //  dấu so sánh một chút là hiện «Xem thêm 0».
    dungNhieuChip(NHIEU.slice(0, 10).map((item) => item.id))
    expect(screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })).toHaveLength(10)
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
  })

  it('11 mục thì gập còn 10 và báo đúng «Xem thêm 1»', () => {
    dungNhieuChip(NHIEU.slice(0, 11).map((item) => item.id))
    expect(screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })).toHaveLength(10)
    expect(screen.getByRole('button', { name: /Xem thêm 1$/ })).toBeInTheDocument()
  })

  it('id đã chọn nhưng KHÔNG còn trong danh mục thì không đếm, không vẽ chip ma', () => {
    //  `selected` lọc theo `options`, nên id mồ côi (nhân sự đã nghỉ, bị gỡ khỏi
    //  danh sách `is_active`) phải rụng khỏi cả số đếm lẫn dải chip — nếu không,
    //  nút mở nói «Đã chọn 3» trong khi chỉ vẽ ra 2 chip.
    dungNhieuChip([1, 2, 999_999])
    expect(screen.getByRole('button', { name: /Đã chọn 2/ })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /^Bỏ Nhân sự/ })).toHaveLength(2)
  })

  it('chưa chọn gì thì nút mở vẫn là câu mời', () => {
    dungNhieuChip([])
    expect(screen.getByRole('button', { name: /Chọn người được xem/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Đã chọn/ })).not.toBeInTheDocument()
  })

  it('«Bỏ hết» xóa sạch lựa chọn trong một lần bấm', async () => {
    const nguoi = userEvent.setup()
    const onChange = dungNhieuChip([1, 2, 3])
    await nguoi.click(screen.getByRole('button', { name: 'Bỏ hết' }))
    expect(onChange).toHaveBeenCalledWith([])
  })
})
