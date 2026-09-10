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
        cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
      },
      { key: 'purpose', header: 'Mục đích', minWidth: 180, sortable: true, wrap: true, cell: (r) => r.purpose },
      {
        key: 'companies',
        header: 'Công ty đóng dấu',
        minWidth: 160,
        wrap: true,
        cell: (r) => r.companies.map((c) => c.name).join(', ') || '—',
      },
      { key: 'requester', header: 'Người tạo', width: 150, cell: (r) => r.requester },
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
