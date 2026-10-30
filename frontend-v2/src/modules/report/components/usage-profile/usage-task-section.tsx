import { useMemo } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'

import { USAGE_DOC_ENTITY_LABELS } from '../../config/usage-metric-labels'
import type { UsageDocCounts, UsageSnapshot } from '../../types/usage-profile'
import { UsageMetricGrid } from './usage-metric-grid'
import { UsageSectionCard } from './usage-section-card'

interface DocRow extends UsageDocCounts {
  entity: string
  name: string
}

const KEYS = [
  'drafts_before_submit_p50',
  'edits_after_submit_share',
  'returned_rate',
  'form_submit_p50_ms',
  'form_abandon_rate',
  'approval_wait_p50_h',
  'approval_wait_p90_h',
  'pending_now',
  'batch_approval_share',
  'month_end_create_share',
]

/** Cách làm phiếu: bảng theo loại phiếu + các chỉ số lưu nháp / sửa sau gửi / thời gian lập / duyệt. */
export function UsageTaskSection({ snapshot }: { snapshot: UsageSnapshot }) {
  const rows = useMemo<DocRow[]>(
    () =>
      Object.entries(snapshot.lists?.docs ?? {}).map(([entity, counts]) => ({
        entity,
        name: USAGE_DOC_ENTITY_LABELS[entity] ?? entity,
        ...counts,
      })),
    [snapshot.lists?.docs],
  )
  const columns = useMemo<DataTableColumn<DocRow>[]>(
    () => [
      { key: 'name', header: 'Loại phiếu', width: 220, hideable: false, cell: (r) => r.name },
      { key: 'c', header: 'Lập', width: 90, align: 'right', cell: (r) => r.c ?? 0 },
      { key: 's', header: 'Gửi', width: 90, align: 'right', cell: (r) => r.s ?? 0 },
      { key: 'a', header: 'Duyệt', width: 90, align: 'right', cell: (r) => r.a ?? 0 },
      { key: 'r', header: 'Từ chối', width: 90, align: 'right', cell: (r) => r.r ?? 0 },
      { key: 'u', header: 'Sửa', width: 90, align: 'right', cell: (r) => r.u ?? 0 },
      { key: 't', header: 'Bị trả về', width: 100, align: 'right', cell: (r) => r.t ?? 0 },
      { key: 'd', header: 'Xóa', width: 90, align: 'right', cell: (r) => r.d ?? 0 },
    ],
    [],
  )
  return (
    <UsageSectionCard title="Cách làm phiếu" description='Theo loại phiếu: số liệu trong cửa sổ của hồ sơ. Cột "nhóm" nằm cạnh từng chỉ số bên dưới.'>
      {rows.length > 0 ? (
        <DataTable columns={columns} rows={rows} getRowId={(r) => r.entity} storageKey="report.usage-docs" emptyMessage="Chưa có phiếu nào." />
      ) : (
        <p className="text-sm text-muted-foreground">Không có phiếu nào được lập hoặc duyệt trong kỳ.</p>
      )}
      <UsageMetricGrid snapshot={snapshot} keys={KEYS} />
    </UsageSectionCard>
  )
}
