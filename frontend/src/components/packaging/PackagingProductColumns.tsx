import type { ReactNode } from 'react'
import type { TableColumn } from '../../hooks/useTableColumns'
import type { PackagingImpactProduct, PackagingPart } from '../../api/packaging-cost-types'
import { diffColor, joinWarnings, priceText, roleLabel } from '../../utils/packaging-price'
import { CodeLink, DiffText, OneLine, PriceText } from './PackagingCells'

/** Năm cột thành phần của định mức: vai trò (`PackagingRole`) + `perCarton` = giá tính cho cả thùng, chia quy cách thùng + `sort` = khóa `sort_by` máy chủ nhận (xếp theo giá đang áp của thành phần). */
const PART_COLUMNS = [
  { role: 1, perCarton: false, sort: 'part_bottle' }, { role: 2, perCarton: false, sort: 'part_cap' },
  { role: 3, perCarton: false, sort: 'part_label' }, { role: 4, perCarton: true, sort: 'part_carton_label' },
  { role: 5, perCarton: true, sort: 'part_carton' },
] as const

/** Ô THÀNH PHẦN: mã trên, giá dưới — giá đổi thì "cũ → mới" với số mới tô theo chiều tăng / giảm; mã đang chọn tô nổi. */
function PartCell({ part, linkCode }: { part: PackagingPart | undefined; linkCode?: boolean }) {
  if (!part?.code) return <span className="pkg-muted">—</span>
  const current = part.applied ?? part.new
  const changed = part.old != null && current != null && Math.abs(current - part.old) > 1e-9
  return (
    <div className={'pkg-part' + (part.selected ? ' sel' : '')}>
      <div className="code">{linkCode ? <CodeLink code={part.code} /> : part.code}</div>
      <div className="price">
        {current == null ? <span className="pkg-muted">chưa có giá</span> : changed ? (
          <>
            <span className="pkg-muted">{priceText(part.old)} →</span>{' '}
            <b style={{ color: diffColor(current - (part.old ?? 0)) }}>{priceText(current)}</b>
          </>
        ) : priceText(current)}
      </div>
    </div>
  )
}

/**
 * Cột của bảng SẢN PHẨM dùng chung cho hai màn: Tác động giá (bảng sản phẩm bị ảnh hưởng) và Tổng hợp theo sản phẩm.
 * Cùng hình dòng (`PackagingImpactProduct`) nên cùng ô: STT, mã HH, tên, quy cách thùng, năm ô thành phần, chi phí / chai
 * cũ và mới, tăng / giảm theo chai và thùng, ghi chú.
 *
 * Tác động giá đo "mới" bằng giá ĐANG ÁP (`cost_applied_bottle`, có giá giả định); Tổng hợp theo sản phẩm đo bằng giá mới
 * (`cost_new_bottle`), cho mã HH + mã thành phần bấm được sang Lịch sử (`compact`), ghi chú một dòng, đặt cột chi phí + xu
 * hướng TRƯỚC năm ô thành phần, và chèn thêm cột (% chênh, xu hướng) sau chi phí (`extraAfterCosts`).
 */
export function buildProductColumns({ offset, newKey, compact, extraAfterCosts = [] }: {
  offset: number
  newKey: 'cost_applied_bottle' | 'cost_new_bottle'
  compact?: boolean
  extraAfterCosts?: TableColumn<PackagingImpactProduct>[]
}): TableColumn<PackagingImpactProduct>[] {
  const note = (r: PackagingImpactProduct): ReactNode => {
    const text = joinWarnings(r.warnings)
    return compact ? <OneLine title={text}><span className="pkg-hint">{text}</span></OneLine> : <span className="pkg-hint">{text}</span>
  }
  const lead: TableColumn<PackagingImpactProduct>[] = [
    { key: 'stt', label: 'STT', width: 56, align: 'center', fixed: true, cell: (_r, i) => offset + i + 1 },
    { key: 'fg_code', label: 'Mã HH', width: 110, sort: 'fg_code', fixed: true,
      cell: (r) => (compact ? <CodeLink code={r.fg_code} product /> : <b className="pkg-num">{r.fg_code}</b>) },
    { key: 'fg_name', label: 'Tên hàng hóa', width: compact ? 220 : 250, sort: 'fg_name', cell: (r) => <OneLine>{r.fg_name}</OneLine> },
    { key: 'carton_qty', label: 'Quy cách thùng', width: compact ? 112 : 100, align: 'right', sort: 'carton_qty',
      cell: (r) => (r.carton_qty ? r.carton_qty.toLocaleString('vi-VN') : <span className="pkg-muted">—</span>) },
  ]
  const parts = PART_COLUMNS.map<TableColumn<PackagingImpactProduct>>((p) => ({
    key: `part_${p.role}`,
    label: p.perCarton ? `${roleLabel(p.role)} (giá /thùng)` : roleLabel(p.role),
    width: 140,
    sort: p.sort,
    sortTitle: 'Xếp theo giá mới của thành phần',
    cell: (r) => <PartCell part={r.parts.find((x) => x.role === p.role)} linkCode={compact} />,
  }))
  const costs: TableColumn<PackagingImpactProduct>[] = [
    { key: 'cost_old_bottle', label: 'CP bao bì/chai cũ', width: 110, align: 'right', sort: 'cost_old_bottle', cell: (r) => <PriceText value={r.cost_old_bottle} /> },
    { key: newKey, label: 'CP bao bì/chai mới', width: 110, align: 'right', sort: newKey, cell: (r) => <PriceText value={r[newKey]} bold /> },
    { key: 'diff_bottle', label: 'Tăng/giảm /chai', width: 110, align: 'right', sort: 'diff_bottle', cell: (r) => <DiffText value={r.diff_bottle} bold /> },
    { key: 'diff_carton', label: 'Tăng/giảm /thùng', width: 120, align: 'right', sort: 'diff_carton', cell: (r) => <DiffText value={r.diff_carton} bold /> },
  ]
  const noteCol: TableColumn<PackagingImpactProduct> = { key: 'note', label: 'Ghi chú', width: 220, cell: note }
  //  Tổng hợp (compact): con số cần đọc (chi phí cũ / mới, chênh lệch, xu hướng) đứng TRƯỚC năm ô thành phần để thấy ngay
  //  không phải cuộn ngang; Tác động giá giữ thứ tự bản mẫu (thành phần rồi tới chi phí).
  return compact ? [...lead, ...costs, ...extraAfterCosts, ...parts, noteCol] : [...lead, ...parts, ...costs, ...extraAfterCosts, noteCol]
}
