import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'
import { CompanyAvatarGroup } from './company-avatar-group'
import { SealStatusBadge } from './status-pill'
import { SEAL_STATUS_LABELS, type SealRequest } from '../types/seal-request'

const ALL = 'all'

function formatDate(value: string | null): string {
  if (!value) return ''
  const [date] = value.split('T')
  if (!date) return value
  const [y, m, d] = date.split('-')
  return `${d}/${m}/${y}`
}

function fieldValue(row: SealRequest, key: string): string | number {
  if (key === 'status') return row.status
  if (key === 'created_at') return row.created_at || ''
  if (key === 'code') return row.code || ''
  if (key === 'purpose') return row.purpose || ''
  return ''
}

interface SealQueueTableProps {
  rows: SealRequest[]
  emptyMessage?: string
  hideStatusFilter?: boolean
  /** Tiêu đề bảng — hiển thị CHUNG 1 HÀNG với ô lọc + nút Tải lại + nút Cột. */
  title?: string
  description?: string
  isLoading?: boolean
}

/**
 * Bảng gọn cho các khối "việc cần xử lý" trên Tổng quan Duyệt dấu: sắp xếp cột +
 * lọc nhanh trạng thái tại chỗ. Tiêu đề + ô lọc + nút Tải lại/Cột (do `DataTable`
 * dựng) nằm CHUNG một hàng công cụ.
 */
export function SealQueueTable({
  rows,
  emptyMessage,
  hideStatusFilter,
  title,
  description,
  isLoading,
}: SealQueueTableProps) {
  const navigate = useNavigate()
  const [status, setStatus] = useState(ALL)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const view = useMemo(() => {
    const filtered = status === ALL ? rows : rows.filter((r) => String(r.status) === status)
    if (!sortBy) return filtered
    const sorted = [...filtered].sort((a, b) => {
      const va = fieldValue(a, sortBy)
      const vb = fieldValue(b, sortBy)
      if (va < vb) return -1
      if (va > vb) return 1
      return 0
    })
    return sortDir === 'asc' ? sorted : sorted.reverse()
  }, [rows, status, sortBy, sortDir])

  const columns = useMemo<DataTableColumn<SealRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 110,
        sortable: true,
        cell: (r) => (
          <span className="font-semibold text-primary tabular-nums" title={r.code}>
            {r.code}
          </span>
        ),
      },
      {
        key: 'purpose',
        header: 'Văn bản / Mục đích',
        minWidth: 200,
        sortable: true,
        wrap: true,
        cell: (r) => (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="min-w-0 py-0.5 cursor-default">
                {r.title && (
                  <div className="truncate font-medium text-foreground">{r.title}</div>
                )}
                <div className="line-clamp-2 text-xs text-muted-foreground">{r.purpose}</div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-md p-3 text-left space-y-1.5 shadow-lg">
              {r.title && (
                <div className="font-semibold text-xs text-background border-b border-background/20 pb-1">
                  {r.title}
                </div>
              )}
              <div className="text-xs text-background/90 whitespace-pre-wrap leading-relaxed">
                {r.purpose}
              </div>
            </TooltipContent>
          </Tooltip>
        ),
      },
      {
        key: 'companies',
        header: 'Công ty đóng dấu',
        minWidth: 160,
        cell: (r) => <CompanyAvatarGroup companies={r.companies} />,
      },
      {
        key: 'requester',
        header: 'Người tạo',
        width: 150,
        cell: (r) => (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="min-w-0 cursor-default">
                <div className="truncate text-xs font-medium text-foreground">{r.requester || '—'}</div>
                {r.requester_role && (
                  <div className="truncate text-[11px] text-muted-foreground">{r.requester_role}</div>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs p-2.5 text-left space-y-1 shadow-lg">
              <div className="font-semibold text-xs text-background">{r.requester || '—'}</div>
              {r.requester_role && (
                <div className="text-[11px] text-background/80">{r.requester_role}</div>
              )}
              {r.requester_email && (
                <div className="text-[11px] text-background/70 font-mono">{r.requester_email}</div>
              )}
            </TooltipContent>
          </Tooltip>
        ),
      },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 120,
        sortable: true,
        cell: (r) => <span className="tabular-nums">{formatDate(r.created_at)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        sortable: true,
        cell: (r) => <SealStatusBadge status={r.status} label={r.status_label} />,
      },
    ],
    [],
  )

  return (
    <DataTable
      columns={columns}
      rows={view}
      getRowId={(r) => r.id}
      isLoading={isLoading}
      onRowClick={(r) => navigate(appRoutes.approvalSeal.detail(r.id))}
      emptyMessage={emptyMessage ?? 'Không có phiếu nào.'}
      sortBy={sortBy}
      sortDir={sortDir}
      onSortChange={(by, dir) => {
        setSortBy(by)
        setSortDir(dir)
      }}
      toolbar={
        //  Tiêu đề + ô lọc bên TRÁI; nút Tải lại/Cột do DataTable dựng bên phải —
        //  tất cả trên CÙNG một hàng.
        <div className="flex flex-1 flex-wrap items-center gap-3">
          {title && (
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">{title}</div>
              {description && (
                <div className="truncate text-xs text-muted-foreground">{description}</div>
              )}
            </div>
          )}
          {!hideStatusFilter && (
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="h-8 w-40 text-xs">
                <SelectValue placeholder="Lọc trạng thái" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
                {Object.entries(SEAL_STATUS_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      }
    />
  )
}
