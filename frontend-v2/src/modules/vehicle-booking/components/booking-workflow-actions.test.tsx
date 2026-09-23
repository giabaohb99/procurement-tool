import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'
import type { VehicleBooking } from '../types/vehicle-booking'
import { BOOKING_STATUS, DRIVER_STATUS } from '../types/vehicle-booking'
import { BookingWorkflowActions } from './booking-workflow-actions'

//  Mock ở tầng `@/core/api` (luật của repo): mọi hook thật — TanStack Query, bộ
//  máy duyệt, hook đặt xe — vẫn chạy, chỉ đường ra mạng là giả.
const apiGet = vi.fn()
const apiPost = vi.fn()
vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<typeof CoreApi>()),
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
}))

let canApprove = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (_entity: string, action: string) => (action === 'approve' ? canApprove : true),
    canAny: () => true,
  }),
}))

const BOOKING_ID = 740
const INSTANCE_ID = 9

function booking(over: Partial<VehicleBooking> = {}): VehicleBooking {
  return {
    id: BOOKING_ID,
    code: 'DX392',
    purpose: 'Thử luồng duyệt',
    status: BOOKING_STATUS.pending,
    driver_status: 0,
    is_assigned_driver: false,
    approval_running: false,
    ...over,
  } as VehicleBooking
}

/** Bộ máy trả lời: phiên đang chạy + (tùy bài) một việc đang chờ tôi. */
function serveFlow({ myTurn }: { myTurn: boolean }) {
  apiGet.mockImplementation((url: string) => {
    if (url === `/api/approvals/of/vehicle_booking/${BOOKING_ID}`)
      return Promise.resolve({ id: INSTANCE_ID, status: 1 })
    if (url === '/api/approvals/my-tasks')
      return Promise.resolve({
        items: myTurn
          ? [{ entity: 'vehicle_booking', entity_id: BOOKING_ID, instance_id: INSTANCE_ID }]
          : [],
        total: myTurn ? 1 : 0,
      })
    return Promise.reject(new Error(`GET chưa khai trong bài kiểm: ${url}`))
  })
}

function renderActions(b: VehicleBooking, scope: 'all' | 'driver' = 'all') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <BookingWorkflowActions booking={b} layout="menu" scope={scope} onDispatch={() => undefined} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  canApprove = true
  apiGet.mockReset()
  apiPost.mockReset()
  apiPost.mockResolvedValue({})
})

describe('BookingWorkflowActions — hai đường duyệt, một bộ nút', () => {
  it('đường một bước cũ: nút Duyệt gọi API của đặt xe', async () => {
    renderActions(booking())

    await userEvent.click(screen.getByRole('button', { name: 'Duyệt' }))

    expect(apiPost).toHaveBeenCalledWith(`/api/vehicle-bookings/${BOOKING_ID}/approve`, {})
    //  Không bật luồng thì không có lý do gì hỏi bộ máy duyệt.
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('luồng nhiều bước, tới lượt tôi: CÙNG nút Duyệt, nhưng ký trên phiên của bộ máy', async () => {
    serveFlow({ myTurn: true })
    renderActions(booking({ approval_running: true }))

    await userEvent.click(await screen.findByRole('button', { name: 'Duyệt' }))

    expect(apiPost).toHaveBeenCalledWith(
      `/api/approvals/${INSTANCE_ID}/approve`,
      expect.objectContaining({ comment: '' }),
    )
    //  Gọi API cũ ở đây là đi vòng qua cả luồng — backend chặn bằng
    //  `block_legacy_path`, nhưng giao diện không được phép thử.
    expect(apiPost).not.toHaveBeenCalledWith(
      `/api/vehicle-bookings/${BOOKING_ID}/approve`,
      expect.anything(),
    )
  })

  it('luồng nhiều bước, tới lượt tôi: có nút dù KHÔNG có quyền approve', async () => {
    //  Trưởng phòng được giao chặng 1 thường không có `vehicle_booking.approve`.
    //  Gác bằng quyền thì bộ máy giao việc rồi giao diện giấu nút khỏi chính họ.
    canApprove = false
    serveFlow({ myTurn: true })
    renderActions(booking({ approval_running: true }))

    expect(await screen.findByRole('button', { name: 'Duyệt' })).toBeInTheDocument()
  })

  it('luồng nhiều bước, CHƯA tới lượt tôi: không có nút Duyệt dù có quyền approve', async () => {
    serveFlow({ myTurn: false })
    renderActions(booking({ approval_running: true }))

    await waitFor(() => expect(apiGet).toHaveBeenCalledWith('/api/approvals/my-tasks', expect.anything()))
    expect(screen.queryByRole('button', { name: 'Duyệt' })).not.toBeInTheDocument()
  })

  it('luồng nhiều bước: Từ chối trong menu mở CÙNG hộp lý do, gửi lý do sang bộ máy', async () => {
    const user = userEvent.setup()
    serveFlow({ myTurn: true })
    renderActions(booking({ approval_running: true }))

    await user.click(await screen.findByRole('button', { name: 'Thao tác khác' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Từ chối' }))
    await user.type(screen.getByLabelText(/Lý do từ chối/), 'Không phải việc công')
    await user.click(screen.getByRole('button', { name: 'Từ chối yêu cầu' }))

    expect(apiPost).toHaveBeenCalledWith(`/api/approvals/${INSTANCE_ID}/reject`, {
      reason: 'Không phải việc công',
    })
  })

  it('luồng nhiều bước: Yêu cầu chỉnh sửa trả về NGƯỜI NỘP (không truyền chặng nào)', async () => {
    const user = userEvent.setup()
    serveFlow({ myTurn: true })
    renderActions(booking({ approval_running: true }))

    await user.click(await screen.findByRole('button', { name: 'Thao tác khác' }))
    await user.click(await screen.findByRole('menuitem', { name: 'Yêu cầu chỉnh sửa' }))
    await user.type(screen.getByLabelText(/Lý do cần chỉnh sửa/), 'Thiếu giờ về')
    await user.click(screen.getByRole('button', { name: 'Trả lại chỉnh sửa' }))

    const call = apiPost.mock.calls.find(([url]) => url === `/api/approvals/${INSTANCE_ID}/return`)
    expect(call?.[1]).toEqual(expect.objectContaining({ reason: 'Thiếu giờ về' }))
    //  Có chặng đích là "lùi một bước" — nghĩa khác hẳn nút cũ.
    expect(call?.[1]?.to_seq ?? null).toBeNull()
  })

  it('màn chỉ-tài-xế không hỏi bộ máy duyệt, kể cả phiếu đang chạy luồng', () => {
    renderActions(booking({ approval_running: true }), 'driver')

    expect(apiGet).not.toHaveBeenCalled()
  })

  it('chuyến đã điều phối: người KHÔNG phải tài xế được phân không thấy «Chấp nhận», kể cả có quyền write', () => {
    //  Lỗi thấy ngày 23/09/2026: gác bằng `is_assigned_driver || write` nên tài
    //  xế có `write` mở chuyến của đồng nghiệp thấy nút, bấm vào backend trả 403
    //  "Bạn không phải tài xế được phân cho chuyến này".
    renderActions(
      booking({ status: BOOKING_STATUS.dispatched, driver_status: DRIVER_STATUS.waiting, is_assigned_driver: false }),
    )

    expect(screen.queryByRole('button', { name: 'Chấp nhận' })).not.toBeInTheDocument()
  })

  it('chuyến đã điều phối: đúng tài xế được phân thấy «Chấp nhận»', () => {
    renderActions(
      booking({ status: BOOKING_STATUS.dispatched, driver_status: DRIVER_STATUS.waiting, is_assigned_driver: true }),
      'driver',
    )

    expect(screen.getByRole('button', { name: 'Chấp nhận' })).toBeInTheDocument()
  })

  it('approval_running VẮNG MẶT không được hiểu là "bật" để đi hỏi bộ máy', () => {
    //  Lỗi bắt được lúc viết (23/09/2026): `undefined && x` ra `undefined`, mà
    //  `undefined` vào tham số `enabled = true` là BẬT — mỗi thẻ «Chuyến của
    //  tôi» (danh sách không gửi ô này) lại bắn hai lượt gọi bộ máy duyệt.
    renderActions(booking({ approval_running: undefined }))

    expect(apiGet).not.toHaveBeenCalled()
  })
})
