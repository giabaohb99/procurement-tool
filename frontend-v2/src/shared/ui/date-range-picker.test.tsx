import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DateRangePicker } from './date-range-picker'

const change = vi.fn()

function build(props: Partial<Parameters<typeof DateRangePicker>[0]> = {}) {
  return render(<DateRangePicker onChange={change} {...props} />)
}

/** Lịch để ở tháng 8/2026 cho mọi test — `defaultMonth` bám đầu khoảng đang chọn. */
const THANG_8 = { from: '2026-08-10', to: '2026-08-20' }

/** Nút mở lịch. Bám `aria-haspopup` của Radix chứ không bám tên: tên dễ đọc của
 *  nút này gộp cả nhãn nút ✕ nằm bên trong, khớp theo tên là dính hai phần tử. */
function trigger(): HTMLElement {
  const el = document.querySelector('[aria-haspopup="dialog"]')
  if (!el) throw new Error('Không thấy nút mở lịch')
  return el as HTMLElement
}

const apDung = () => screen.getByRole('button', { name: 'Áp dụng' })

/** Ô ngày trong lịch — `data-day` là `yyyy-mm-dd`, khỏi lo trùng số giữa hai tháng. */
function ngay(value: string) {
  const cell = document.querySelector(`[data-day="${value}"]`)
  if (!cell) throw new Error(`Lịch không có ngày ${value}`)
  return within(cell as HTMLElement).getByRole('button')
}

async function moLich(props: Partial<Parameters<typeof DateRangePicker>[0]> = {}) {
  const nguoi = userEvent.setup()
  build(props)
  await nguoi.click(trigger())
  return nguoi
}

beforeEach(() => change.mockClear())

describe('DateRangePicker', () => {
  it('chưa chọn thì hiện chữ gợi ý', () => {
    build({ placeholder: 'Ngày tạo…' })
    expect(trigger()).toHaveTextContent('Ngày tạo…')
  })

  it('hiện dd/mm/yyyy CÓ số 0 ở đầu, không phải d/m/yyyy hay chuỗi ISO', () => {
    //  Lỗi cũ: `toLocaleDateString('vi-VN')` trần ra `10/8/2026`, lệch hẳn với
    //  `formatDate` mà cả hệ đang dùng (`10/08/2026`). Bản trước đó nữa còn hiện
    //  thẳng `2026-08-10 -> 2026-08-20`.
    build(THANG_8)
    expect(trigger()).toHaveTextContent('10/08/2026 – 20/08/2026')
  })

  // ── Lỗi chính: bấm MỘT ngày là chốt luôn khoảng một ngày ───────────────────
  it('bấm ngày ĐẦU thôi thì CHƯA báo ra ngoài và CHƯA đóng lịch', async () => {
    //  Đây là lỗi khách báo 26/08/2026 ("range date khó xài"): react-day-picker
    //  trả `{from: X, to: X}` ngay cú bấm đầu, bản cũ thấy đủ hai đầu là bắn
    //  `onChange` rồi đóng popover — không tài nào chọn nổi một khoảng thật.
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-05'))

    expect(change).not.toHaveBeenCalled()
    const lich = within(screen.getByRole('dialog'))
    expect(lich.getByText('05/08/2026')).toBeInTheDocument()
    expect(lich.getByText('chọn tiếp ngày kết thúc')).toBeInTheDocument()
  })

  it('bấm đủ hai đầu rồi Áp dụng mới ra khoảng thật', async () => {
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-05'))
    await nguoi.click(ngay('2026-08-19'))
    await nguoi.click(apDung())

    expect(change).toHaveBeenCalledTimes(1)
    expect(change).toHaveBeenCalledWith('2026-08-05', '2026-08-19')
  })

  it('Áp dụng bị khóa khi chưa có đủ hai đầu', async () => {
    await moLich()
    expect(apDung()).toBeDisabled()
  })

  it('chọn NGƯỢC (kết thúc trước bắt đầu) vẫn ra khoảng đúng chiều', async () => {
    //  react-day-picker tự đảo lại; nếu lỡ tự nối `from`/`to` theo thứ tự bấm
    //  thì backend nhận `from > to` và trả về rỗng, người dùng tưởng không có
    //  dữ liệu.
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-19'))
    await nguoi.click(ngay('2026-08-05'))
    await nguoi.click(apDung())

    expect(change).toHaveBeenCalledWith('2026-08-05', '2026-08-19')
  })

  it('bấm hai lần vào CÙNG một ngày = khoảng một ngày', async () => {
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-07'))
    await nguoi.click(ngay('2026-08-07'))
    await nguoi.click(apDung())

    expect(change).toHaveBeenCalledWith('2026-08-07', '2026-08-07')
  })

  it('đang có khoảng cũ mà bấm tiếp thì chọn LẠI TỪ ĐẦU, không nong khoảng cũ ra', async () => {
    //  react-day-picker để nguyên sẽ NONG khoảng đang có: đang 10/08–20/08 mà
    //  bấm 28/08 thì ra 10/08–28/08, muốn chọn khoảng mới phải bấm ✕ xóa trước.
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-28'))

    expect(apDung()).toBeDisabled()   // mới có một đầu -> chưa chốt được

    await nguoi.click(ngay('2026-08-30'))
    await nguoi.click(apDung())
    expect(change).toHaveBeenCalledWith('2026-08-28', '2026-08-30')
  })

  // ── Hủy giữa chừng ─────────────────────────────────────────────────────────
  it('đóng lịch giữa chừng là HỦY, khoảng cũ còn nguyên', async () => {
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-03'))
    await nguoi.keyboard('{Escape}')

    expect(change).not.toHaveBeenCalled()
    expect(trigger()).toHaveTextContent('10/08/2026 – 20/08/2026')
  })

  it('mở lại sau khi hủy thì thấy khoảng ĐANG áp dụng, không phải bản nháp dở', async () => {
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-03'))
    await nguoi.keyboard('{Escape}')
    await nguoi.click(trigger())

    const lich = within(screen.getByRole('dialog'))
    expect(lich.getByText('10/08/2026')).toBeInTheDocument()
    expect(lich.getByText('20/08/2026')).toBeInTheDocument()
  })

  // ── Chọn nhanh ─────────────────────────────────────────────────────────────
  it('chọn nhanh áp NGAY một cú bấm, không bắt bấm thêm Áp dụng', async () => {
    const nguoi = await moLich()
    await nguoi.click(screen.getByRole('button', { name: 'Hôm nay' }))

    expect(change).toHaveBeenCalledTimes(1)
    const [from, to] = change.mock.calls[0]
    expect(from).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(from).toBe(to)
  })

  it('tắt được hàng chọn nhanh', async () => {
    await moLich({ showPresets: false })
    expect(screen.queryByRole('button', { name: 'Hôm nay' })).not.toBeInTheDocument()
  })

  // ── Xóa ────────────────────────────────────────────────────────────────────
  it('nút ✕ trên ô chọn trả về hai chuỗi rỗng', async () => {
    const nguoi = userEvent.setup()
    build(THANG_8)
    await nguoi.click(screen.getByRole('button', { name: 'Xóa khoảng ngày' }))

    expect(change).toHaveBeenCalledWith('', '')
  })

  it('nút ✕ KHÔNG mở lịch kèm theo', async () => {
    //  Trigger của popover mở lịch ngay từ `pointerdown`, nên nút ✕ phải chặn ở
    //  đúng nhịp đó — chặn ở `click` là xóa xong lịch vẫn bung ra.
    const nguoi = userEvent.setup()
    build(THANG_8)
    await nguoi.click(screen.getByRole('button', { name: 'Xóa khoảng ngày' }))

    expect(screen.queryByRole('button', { name: 'Áp dụng' })).not.toBeInTheDocument()
  })

  it('nút Xóa trong lịch cũng trả rỗng và đóng lịch', async () => {
    const nguoi = await moLich(THANG_8)
    await nguoi.click(screen.getByRole('button', { name: 'Xóa' }))

    expect(change).toHaveBeenCalledWith('', '')
    expect(screen.queryByRole('button', { name: 'Áp dụng' })).not.toBeInTheDocument()
  })

  it('chưa chọn gì thì không có nút Xóa nào cả', async () => {
    await moLich()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa khoảng ngày' })).not.toBeInTheDocument()
  })

  // ── Giá trị vào bị lỗi ─────────────────────────────────────────────────────
  it('chỉ có ĐẦU mà thiếu CUỐI thì coi như chưa chọn, không hiện nửa vời', async () => {
    build({ from: '2026-08-10' })
    expect(trigger()).toHaveTextContent('Chọn khoảng ngày')
    expect(screen.queryByRole('button', { name: 'Xóa khoảng ngày' })).not.toBeInTheDocument()
  })

  it('chuỗi ngày rác không làm vỡ trang', async () => {
    //  Người dùng sửa tay URL là chuyện thường; hai đầu này đi thẳng từ query string vào đây.
    build({ from: 'khong-phai-ngay', to: '2026-13-45' })
    expect(trigger()).toBeInTheDocument()
  })

  it('khóa ô thì không mở được lịch', async () => {
    const nguoi = userEvent.setup()
    build({ ...THANG_8, disabled: true })
    await nguoi.click(trigger())
    expect(screen.queryByRole('button', { name: 'Áp dụng' })).not.toBeInTheDocument()
  })

  // ── Lịch ───────────────────────────────────────────────────────────────────
  it('mở đúng THÁNG của đầu khoảng đang chọn, không phải tháng hiện tại', async () => {
    //  Không thì mỗi lần mở lại phải bấm mũi tên lùi về mới thấy khoảng cũ.
    await moLich({ from: '2024-02-05', to: '2024-02-09' })
    expect(document.querySelector('[data-day="2024-02-05"]')).not.toBeNull()
  })

  it('bày HAI tháng cạnh nhau — khoảng ngày hay vắt qua đầu tháng', async () => {
    await moLich({ from: '2026-08-10', to: '2026-09-02' })
    expect(document.querySelector('[data-day="2026-08-10"]')).not.toBeNull()
    expect(document.querySelector('[data-day="2026-09-02"]')).not.toBeNull()
  })

  it('chọn được khoảng VẮT QUA hai tháng', async () => {
    const nguoi = await moLich(THANG_8)
    await nguoi.click(ngay('2026-08-28'))
    await nguoi.click(ngay('2026-09-03'))
    await nguoi.click(apDung())

    expect(change).toHaveBeenCalledWith('2026-08-28', '2026-09-03')
  })
})
