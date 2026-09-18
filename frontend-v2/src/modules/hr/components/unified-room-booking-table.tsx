import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useMeetingRooms, useRoomBookings, useRoomHandled, useRoomToApprove } from '../hooks/use-room'
import { ROOM_BOOKING_STATUS, ROOM_BOOKING_STATUS_LABELS, type RoomBooking, type RoomInboxRow } from '../types/room'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import { RoomBookingCard } from './room-booking-card'
import {
  codeColumn,
  flowColumn,
  myTaskColumns,
  requesterColumn,
  roomColumn,
  timeColumns,
  titleColumn,
} from './room-booking-columns'
import { RoomStatusBadge } from './room-status-badge'

const ALL = 'all'

export const ROOM_SCOPE = {
  ALL: 'all',
  TO_APPROVE: 'to-approve',
  MINE: 'mine',
  HANDLED: 'handled',
} as const

export type RoomScope = (typeof ROOM_SCOPE)[keyof typeof ROOM_SCOPE]

/**
 * BẢNG PHIẾU ĐẶT PHÒNG DUY NHẤT — gom 3 tab (Cần tôi duyệt · Phiếu của tôi · Tôi đã duyệt)
 * thành 1 bảng với bộ lọc phạm vi, phòng và trạng thái; cùng khuôn với `UnifiedLeaveRequestTable`.
 */
export function UnifiedRoomBookingTable() {
  const navigate = useNavigate()

  const [scopeParam, setScopeParam] = useUrlParamState('scope', ROOM_SCOPE.ALL)
  const currentScope: RoomScope = Object.values(ROOM_SCOPE).includes(scopeParam as RoomScope)
    ? (scopeParam as RoomScope)
    : ROOM_SCOPE.ALL

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [roomId, setRoomId] = useUrlParamState('room_id', ALL)

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  // Đổi phạm vi hay điều kiện lọc → về trang 1
  const querySignature = `${currentScope}-${status}-${roomId}-${debouncedValue}`
  const [lastSignature, setLastSignature] = useState(querySignature)
  if (lastSignature !== querySignature) {
    setLastSignature(querySignature)
    setPage(1)
  }

  // Danh sách phòng cho ô chọn
  const { data: roomData } = useMeetingRooms()

  // Hàng đợi Cần tôi duyệt — luôn nạp để hiện số huy hiệu
  const toApproveQuery = useRoomToApprove()
  const toApproveItems = useMemo(() => toApproveQuery.data?.items ?? [], [toApproveQuery.data])
  const waitingCount = toApproveItems.length
  const toApproveIds = useMemo(() => new Set(toApproveItems.map((r) => r.id)), [toApproveItems])

  // Tôi đã duyệt — chỉ nạp khi đang ở phạm vi HANDLED
  const handledQuery = useRoomHandled(30, currentScope === ROOM_SCOPE.HANDLED)
  const handledItems = useMemo(() => handledQuery.data?.items ?? [], [handledQuery.data])

  // Danh sách phiếu phân trang (cho ALL và MINE)
  const serverParams = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (roomId !== ALL) p.room_id = roomId
    //  Phạm vi MINE: backend trả phiếu của chính người đang đăng nhập khi
    //  `scope=mine` — giả định backend hỗ trợ; nếu chưa thì lọc phía client
    //  bằng employee_id giống UnifiedLeaveRequestTable.
    if (currentScope === ROOM_SCOPE.MINE) p.scope = 'mine'
    return p
  }, [page, pageSize, debouncedValue, status, roomId, currentScope])

  const bookingsQuery = useRoomBookings(
    serverParams,
    currentScope === ROOM_SCOPE.ALL || currentScope === ROOM_SCOPE.MINE,
  )

  // ── Dữ liệu hiển thị theo phạm vi ──────────────────────────────────────────
  const { displayRows, totalCount, isLoading, isError } = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()

    if (currentScope === ROOM_SCOPE.TO_APPROVE) {
      let list: RoomInboxRow[] = toApproveItems
      if (needle) {
        list = list.filter(
          (r) =>
            r.code?.toLowerCase().includes(needle) ||
            r.title?.toLowerCase().includes(needle) ||
            r.room_name?.toLowerCase().includes(needle) ||
            r.requester_name?.toLowerCase().includes(needle),
        )
      }
      if (roomId !== ALL) list = list.filter((r) => String(r.room_id) === roomId)
      const total = list.length
      const paged = list.slice((page - 1) * pageSize, page * pageSize)
      return {
        displayRows: paged,
        totalCount: total,
        isLoading: toApproveQuery.isLoading,
        isError: toApproveQuery.isError,
      }
    }

    if (currentScope === ROOM_SCOPE.HANDLED) {
      let list: RoomInboxRow[] = handledItems
      if (needle) {
        list = list.filter(
          (r) =>
            r.code?.toLowerCase().includes(needle) ||
            r.title?.toLowerCase().includes(needle) ||
            r.room_name?.toLowerCase().includes(needle) ||
            r.requester_name?.toLowerCase().includes(needle),
        )
      }
      if (status !== ALL) list = list.filter((r) => String(r.status) === status)
      if (roomId !== ALL) list = list.filter((r) => String(r.room_id) === roomId)
      const total = list.length
      const paged = list.slice((page - 1) * pageSize, page * pageSize)
      return {
        displayRows: paged,
        totalCount: total,
        isLoading: handledQuery.isLoading,
        isError: handledQuery.isError,
      }
    }

    // ALL | MINE — dữ liệu từ server, đẩy Cần tôi duyệt lên đầu khi xem ALL
    const rawItems = bookingsQuery.data?.items ?? []
    const sorted =
      currentScope === ROOM_SCOPE.ALL
        ? [...rawItems].sort((a, b) => {
            const aMine = toApproveIds.has(a.id) ? 0 : 1
            const bMine = toApproveIds.has(b.id) ? 0 : 1
            if (aMine !== bMine) return aMine - bMine
            return b.id - a.id
          })
        : rawItems

    return {
      displayRows: sorted,
      totalCount: bookingsQuery.data?.total ?? 0,
      isLoading: bookingsQuery.isLoading,
      isError: bookingsQuery.isError,
    }
  }, [
    currentScope,
    debouncedValue,
    toApproveItems,
    roomId,
    page,
    pageSize,
    toApproveQuery.isLoading,
    toApproveQuery.isError,
    handledItems,
    status,
    handledQuery.isLoading,
    handledQuery.isError,
    bookingsQuery.data,
    bookingsQuery.isLoading,
    bookingsQuery.isError,
    toApproveIds,
  ])

  // ── Cột theo phạm vi ───────────────────────────────────────────────────────
  //  «Cần tôi duyệt»: thêm cột Luồng duyệt + Việc của tôi + Hạn xử lý.
  //  «Tôi đã duyệt»: thêm Luồng duyệt, bỏ Việc/Hạn (không còn tác dụng).
  //  Còn lại: cột chuẩn + huy hiệu «Cần bạn duyệt» trên trạng thái.
  const columns = useMemo<DataTableColumn<RoomBooking>[]>(() => {
    const base: DataTableColumn<RoomBooking>[] = [
      codeColumn<RoomBooking>(),
      {
        key: 'status',
        header: 'Trạng thái',
        width: currentScope === ROOM_SCOPE.TO_APPROVE ? 140 : 230,
        cell: (b) => {
          const isMyTask = toApproveIds.has(b.id)
          return (
            <div className="flex min-w-0 items-center gap-1.5">
              <RoomStatusBadge status={b.status} label={b.status_label} />
              {isMyTask && currentScope === ROOM_SCOPE.ALL && (
                <Badge
                  variant="outline"
                  className="shrink-0 border-sky-300 bg-sky-50 text-[11px] font-medium text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200"
                >
                  Cần bạn duyệt
                </Badge>
              )}
            </div>
          )
        },
      },
      titleColumn<RoomBooking>(),
      roomColumn<RoomBooking>(),
      ...timeColumns<RoomBooking>(),
      requesterColumn<RoomBooking>(),
      {
        key: 'attendee_count',
        header: 'Số người',
        width: 100,
        align: 'right',
        cell: (b) =>
          b.attendee_count ? (
            <span className="tabular-nums">{b.attendee_count}</span>
          ) : (
            <span className="text-muted-foreground/50">—</span>
          ),
      },
    ]

    if (currentScope === ROOM_SCOPE.TO_APPROVE) {
      return [
        ...base,
        flowColumn() as DataTableColumn<RoomBooking>,
        ...(myTaskColumns() as DataTableColumn<RoomBooking>[]),
      ]
    }

    if (currentScope === ROOM_SCOPE.HANDLED) {
      return [...base, flowColumn() as DataTableColumn<RoomBooking>]
    }

    return base
  }, [currentScope, toApproveIds])

  // ── Ô chọn lọc ─────────────────────────────────────────────────────────────
  const scopeSelect = (
    <Select value={currentScope} onValueChange={(val) => setScopeParam(val as RoomScope)}>
      <SelectTrigger className="w-full md:w-44">
        <SelectValue placeholder="Phạm vi" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ROOM_SCOPE.ALL}>Tất cả</SelectItem>
        <SelectItem value={ROOM_SCOPE.TO_APPROVE}>
          Cần tôi duyệt{waitingCount > 0 ? ` (${waitingCount})` : ''}
        </SelectItem>
        <SelectItem value={ROOM_SCOPE.MINE}>Phiếu của tôi</SelectItem>
        <SelectItem value={ROOM_SCOPE.HANDLED}>Tôi đã duyệt</SelectItem>
      </SelectContent>
    </Select>
  )

  const roomSelect = (
    <Select value={roomId} onValueChange={setRoomId}>
      <SelectTrigger className="w-full md:w-48" aria-label="Lọc theo phòng">
        <SelectValue placeholder="Phòng" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả phòng</SelectItem>
        {(roomData?.items ?? []).map((room) => (
          <SelectItem key={room.id} value={String(room.id)}>
            {room.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select
      value={status}
      onValueChange={setStatus}
      disabled={currentScope === ROOM_SCOPE.TO_APPROVE}
    >
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo trạng thái">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
        {Object.values(ROOM_BOOKING_STATUS).map((value) => (
          <SelectItem key={value} value={String(value)}>
            {ROOM_BOOKING_STATUS_LABELS[value]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const isFiltered =
    Boolean(debouncedValue) ||
    (currentScope !== ROOM_SCOPE.TO_APPROVE && status !== ALL) ||
    roomId !== ALL

  const emptyMessage = isFiltered
    ? 'Không có phiếu nào khớp bộ lọc.'
    : currentScope === ROOM_SCOPE.TO_APPROVE
      ? 'Không có phiếu nào đang chờ bạn duyệt.'
      : currentScope === ROOM_SCOPE.HANDLED
        ? 'Bạn chưa duyệt phiếu đặt phòng nào trong 30 ngày qua.'
        : currentScope === ROOM_SCOPE.MINE
          ? 'Bạn chưa có phiếu đặt phòng nào.'
          : 'Chưa có phiếu đặt phòng nào. Bấm «Đặt phòng» để tạo.'

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={displayRows}
      getRowId={(b) => b.id}
      isLoading={isLoading}
      isError={isError}
      emptyMessage={emptyMessage}
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
      storageKey="hr.unified-room-bookings"
      onRowClick={(b) => navigate(appRoutes.hr.roomBookingDetail(b.id))}
      mobileCard={(b) => {
        const dueAt =
          currentScope === ROOM_SCOPE.TO_APPROVE && 'task' in b
            ? (b as RoomInboxRow).task?.due_at
            : undefined
        return (
          <RoomBookingCard
            booking={b}
            showStatus={currentScope !== ROOM_SCOPE.TO_APPROVE}
            dueAt={dueAt}
          />
        )
      }}
      pagination={{
        page,
        pageSize,
        total: totalCount,
        onPageChange: setPage,
        onPageSizeChange: setPageSize,
        unitLabel: 'phiếu',
      }}
      toolbar={
        <>
          <SearchField
            value={keyword}
            onChange={setKeyword}
            placeholder="Tìm phiếu, nội dung…"
            className="md:min-w-56 md:max-w-xs"
          />

          <QuickFilterSheet
            activeCount={
              (currentScope !== ROOM_SCOPE.ALL ? 1 : 0) +
              (roomId !== ALL ? 1 : 0) +
              (status !== ALL && currentScope !== ROOM_SCOPE.TO_APPROVE ? 1 : 0)
            }
            onClearAll={() => {
              setScopeParam(ROOM_SCOPE.ALL)
              setRoomId(ALL)
              setStatus(ALL)
            }}
          >
            <QuickFilterField label="Phạm vi">{scopeSelect}</QuickFilterField>
            <QuickFilterField label="Phòng">{roomSelect}</QuickFilterField>
            {currentScope !== ROOM_SCOPE.TO_APPROVE && (
              <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
            )}
          </QuickFilterSheet>

          <div className="hidden items-center gap-3 md:flex md:flex-wrap">
            {scopeSelect}
            {roomSelect}
            {currentScope !== ROOM_SCOPE.TO_APPROVE && statusSelect}
          </div>
        </>
      }
    />
  )
}
