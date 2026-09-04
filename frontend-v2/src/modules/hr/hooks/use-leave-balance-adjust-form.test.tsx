import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useLeaveBalanceAdjustForm } from './use-leave-balance-adjust-form'
import { balanceFixture } from '../components/leave-balance-fixture'

//  Giả lập ĐÚNG hợp đồng của TanStack: `mutate` luôn gọi `onSettled` khi xong,
//  dù thành hay bại. Bỏ nhịp đó thì khóa chống-bấm-trùng không bao giờ nhả và
//  bài kiểm xanh nhầm.
const mutate = vi.fn((_vars, options?: { onSettled?: () => void }) => options?.onSettled?.())
let isPending = false

vi.mock('./use-leave', () => ({
  useAdjustLeaveBalance: () => ({ mutate, isPending }),
}))

beforeEach(() => {
  vi.clearAllMocks()
  isPending = false
})

/**
 * Trạng thái dùng chung giữa NÚT LƯU (đầu trang) và Ô NHẬP (trong thẻ) — hai
 * component cách nhau cả màn hình.
 */
describe('useLeaveBalanceAdjustForm', () => {
  it('xem trước «còn lại» = gỡ lần chỉnh cũ rồi cộng lần mới', () => {
    //  Ô này GHI ĐÈ chứ không cộng dồn: đang +3 mà gõ 5 thì còn lại tăng 2, chứ
    //  không tăng 5. Cộng thẳng vào là con số xem trước sai ngay từ đầu.
    const { result } = renderHook(() =>
      useLeaveBalanceAdjustForm(balanceFixture({ adjusted_days: 3, remaining_days: 10 })),
    )
    act(() => result.current.setDays(5))
    expect(result.current.preview).toBe(12)
  })

  it('nhận số ÂM — cột duy nhất trừ được, dùng khi cấp nhầm', () => {
    const { result } = renderHook(() =>
      useLeaveBalanceAdjustForm(balanceFixture({ adjusted_days: 0, remaining_days: 12 })),
    )
    act(() => result.current.setDays(-2))
    expect(result.current.preview).toBe(10)
  })

  it('nửa ngày không đẻ ra số lẻ vô tận', () => {
    //  0.1 + 0.2 của JavaScript ra 0.30000000000000004; in thẳng ra màn là con
    //  số đọc như dữ liệu hỏng.
    const { result } = renderHook(() =>
      useLeaveBalanceAdjustForm(balanceFixture({ adjusted_days: 0.1, remaining_days: 12.2 })),
    )
    act(() => result.current.setDays(0.3))
    expect(result.current.preview).toBe(12.4)
  })

  it('ĐỔI sang dòng quỹ khác thì nạp lại số và lý do của dòng đó', () => {
    //  Không nạp lại thì màn hình mang số của người TRƯỚC, và bấm Lưu là ghi số
    //  đó lên quỹ của người ĐANG mở.
    const { result, rerender } = renderHook(
      ({ id }: { id: number }) =>
        useLeaveBalanceAdjustForm(
          balanceFixture({ id, adjusted_days: id, note: `ghi chú ${id}` }),
        ),
      { initialProps: { id: 1 } },
    )
    expect(result.current.days).toBe(1)

    rerender({ id: 2 })
    expect(result.current.days).toBe(2)
    expect(result.current.note).toBe('ghi chú 2')
  })

  it('ĐANG GỬI thì khóa nút — chặn bấm hai lần thành hai lệnh ghi đè', () => {
    isPending = true
    const { result } = renderHook(() =>
      useLeaveBalanceAdjustForm(balanceFixture({ note: 'Có lý do rồi' })),
    )
    expect(result.current.canSave).toBe(false)
  })

  it('gửi lý do đã CẮT khoảng trắng hai đầu', () => {
    const { result } = renderHook(() => useLeaveBalanceAdjustForm(balanceFixture({ id: 7 })))
    act(() => result.current.setNote('   Bù phép   '))
    act(() => result.current.submit())

    expect(mutate).toHaveBeenCalledWith(
      { id: 7, values: { adjusted_days: expect.any(Number), note: 'Bù phép' } },
      expect.anything(),
    )
  })

  it('bấm Lưu BA LẦN liên tiếp chỉ gửi MỘT lệnh', async () => {
    //  PATCH ghi đè nên không đẻ bản ghi trùng, nhưng đẻ ba dòng dấu vết giống
    //  hệt nhau — sổ điều chỉnh quỹ phép đọc ra như có ba lần chỉnh tay.
    const { result } = renderHook(() =>
      useLeaveBalanceAdjustForm(balanceFixture({ note: 'Có lý do' })),
    )
    act(() => {
      result.current.submit()
      result.current.submit()
      result.current.submit()
    })
    expect(mutate).toHaveBeenCalledTimes(1)
  })

  it('lý do CHỈ có khoảng trắng thì không lưu được', () => {
    const { result } = renderHook(() => useLeaveBalanceAdjustForm(balanceFixture({ note: '' })))
    act(() => result.current.setNote('\n\t   '))
    expect(result.current.canSave).toBe(false)
  })
})
