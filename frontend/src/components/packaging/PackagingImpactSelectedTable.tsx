import { useMemo } from 'react'
import type { ReactNode } from 'react'
import NumberInput from '../NumberInput'
import TableHead, { TableCells, TableColGroup } from '../TableHead'
import TableToolbar from '../TableToolbar'
import { useTableColumns, TableColumn } from '../../hooks/useTableColumns'
import type { PackagingSelectedCode } from '../../api/packaging-cost-types'
import { PRICE_DECIMALS } from '../../utils/money'
import {
  COST_WARNING_KIND, isNum, isOutsideLimit, joinWarnings, normalizeWarnings, warningText,
} from '../../utils/packaging-price'
import { CodeLink, DiffText, OneLine, PctText, PriceText, RangeText } from './PackagingCells'
import { PACKAGING_LIMITS_ENABLED } from '../../utils/packaging-flags'

/** Câu ghi chú một mã: cảnh báo máy chủ gửi + câu ngoài ngưỡng tính tại chỗ (giá giả định chưa kịp gửi, trễ 400 ms). */
function buildNote(row: PackagingSelectedCode, applied: number | null): string {
  //  Bỏ cảnh báo ngưỡng của máy chủ rồi tự tính lại theo giá đang gõ: vừa gõ về trong ngưỡng mà ô vẫn báo "vượt trần" thêm một nhịp là sai.
  const limitKinds: number[] = [COST_WARNING_KIND.BELOW_FLOOR, COST_WARNING_KIND.ABOVE_CEILING]
  const notes = [joinWarnings(normalizeWarnings(row.warnings).filter((w) => !limitKinds.includes(w.kind)))]
  if (isNum(applied) && isNum(row.floor) && applied < row.floor) notes.push(warningText({ kind: COST_WARNING_KIND.BELOW_FLOOR }))
  if (isNum(applied) && isNum(row.ceiling) && applied > row.ceiling) notes.push(warningText({ kind: COST_WARNING_KIND.ABOVE_CEILING }))
  return notes.filter(Boolean).join('; ')
}

/**
 * Bảng MÃ ĐÃ CHỌN của màn Tác động giá: giá cũ / mới, ô giá giả định (nền vàng), chênh lệch, số SP dùng, min / max
 * theo sổ giá, ngưỡng sàn–trần. Giá đang dùng ra ngoài ngưỡng thì ô ngưỡng tô đỏ và ghi chú nói rõ.
 */
export default function PackagingImpactSelectedTable({
  rows, loading, failed, assumed, onAssumedChange, onRemove, summary,
}: {
  rows: PackagingSelectedCode[] | undefined
  loading: boolean
  failed: boolean
  /** Giá giả định đang gõ (chưa qua trễ) — ô nhập đọc từ đây, không đọc `row.assumed` của máy chủ. */
  assumed: Record<string, number>
  /** `null` = bỏ giả định, quay về giá bảng giá. */
  onAssumedChange: (code: string, price: number | null) => void
  onRemove: (code: string) => void
  /** Dòng tóm tắt bên trái thanh công cụ. */
  summary: ReactNode
}) {
  const columns = useMemo<TableColumn<PackagingSelectedCode>[]>(() => {
    const appliedOf = (r: PackagingSelectedCode) => assumed[r.code] ?? r.new
    return [
      { key: 'code', label: 'Mã', width: 110, fixed: true, cell: (r) => <CodeLink code={r.code} /> },
      { key: 'name', label: 'Tên vật tư', width: 240, cell: (r) => <OneLine>{r.name}</OneLine> },
      { key: 'group', label: 'Nhóm', width: 80, cell: (r) => r.group },
      { key: 'old', label: 'Giá cũ', width: 100, align: 'right', cell: (r) => <PriceText value={r.old} /> },
      { key: 'new', label: 'Giá mới', width: 100, align: 'right', cell: (r) => <PriceText value={r.new} /> },
      {
        key: 'assumed', label: 'Giá giả định', width: 140, fixed: true,
        cell: (r) => (
          <NumberInput className="pkg-assumed" placeholder="Nhập giá" maxDecimals={PRICE_DECIMALS}
            value={assumed[r.code] ?? 0}
            //  Ô xóa trắng trả 0 — coi là BỎ giả định (giá bao bì 0 đồng không có nghĩa mô phỏng).
            onChange={(p) => onAssumedChange(r.code, p > 0 ? p : null)} />
        ),
      },
      { key: 'diff', label: 'Chênh lệch', width: 110, align: 'right', cell: (r) => <DiffText value={r.diff} bold /> },
      { key: 'pct', label: '%', width: 80, align: 'right', cell: (r) => <PctText value={r.pct} /> },
      { key: 'usage', label: 'Số SP', width: 70, align: 'right', cell: (r) => r.usage },
      //  Min và Max tách hai cột — giá thấp / cao nhất trong sổ giá của mã.
      { key: 'min', label: 'Min', width: 100, align: 'right', cell: (r) => <PriceText value={r.min} /> },
      { key: 'max', label: 'Max', width: 100, align: 'right', cell: (r) => <PriceText value={r.max} /> },
      ...(PACKAGING_LIMITS_ENABLED ? [{
        key: 'limit', label: 'Sàn – Trần', width: 140, align: 'right' as const,
        cell: (r: PackagingSelectedCode) => <RangeText low={r.floor} high={r.ceiling} danger={isOutsideLimit(appliedOf(r), r.floor, r.ceiling)} />,
      }] : []),
      {
        key: 'note', label: 'Ghi chú', width: 170,
        cell: (r) => <span className="pkg-err" title={buildNote(r, appliedOf(r))}>{buildNote(r, appliedOf(r))}</span>,
      },
      {
        key: 'remove', label: '', width: 44, align: 'center', fixed: true,
        cell: (r) => <button className="pkg-x" aria-label={`Bỏ ${r.code}`} title="Bỏ mã này" onClick={() => onRemove(r.code)}><i className="ti ti-x" /></button>,
      },
    ]
  }, [assumed, onAssumedChange, onRemove])

  const table = useTableColumns('packaging-impact-selected', columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)
  const list = rows ?? []

  return (
    <div>
      <TableToolbar {...table}>
        <div className="pkg-summary" style={{ flex: 1, textAlign: 'left' }}>{summary}</div>
      </TableToolbar>
      {/*  Chọn cả nhóm là vài chục mã — chặn chiều cao, cuộn trong khung để bảng sản phẩm không bị đẩy xuống tận cuối trang. */}
      <div className="table-scroll pkg-scroll-y">
          <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
            <TableColGroup columns={table.columns} colW={table.colW} />
            <TableHead columns={table.columns} startResize={table.startResize} />
            <tbody>
              {list.map((r, i) => <tr key={r.code}><TableCells columns={table.columns} row={r} index={i} /></tr>)}
              {list.length === 0 && (
                <tr><td colSpan={table.columns.length} className="table-empty">
                  {failed ? 'Không tính được tác động — thử lại sau.' : loading ? 'Đang tính…' : 'Các mã đã chọn chưa có trong định mức nào.'}
                </td></tr>
              )}
            </tbody>
          </table>
      </div>
    </div>
  )
}
