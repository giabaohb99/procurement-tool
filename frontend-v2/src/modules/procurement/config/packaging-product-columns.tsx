/**
 * duoc-CR-784 — cột của bảng SẢN PHẨM dùng chung cho hai màn: Tác động giá (bảng sản phẩm bị ảnh hưởng) và Tổng hợp theo
 * sản phẩm. Cùng hình dòng (`PackagingImpactProduct`) nên cùng ô: STT, mã HH, tên, quy cách thùng, năm ô thành phần,
 * chi phí / chai cũ và mới, tăng / giảm theo chai và thùng, ghi chú.
 *
 * Khác nhau gói trong `options`: Tác động giá đo "mới" bằng giá ĐANG ÁP (có giá giả định) và cho tên / ghi chú xuống dòng,
 * Tổng hợp theo sản phẩm (`compact`: bỏ cột STT, tiêu đề cột rút gọn — cho vừa màn 1440px) đo bằng giá mới, một dòng cắt `…`, mã bấm được sang Lịch sử, đặt các cột chi phí + xu
 * hướng TRƯỚC năm ô thành phần (con số cần đọc không bị đẩy ra ngoài màn), và chèn thêm cột (% chênh, xu hướng) sau chi phí.
 */
import type { DataTableColumn } from '@/shared/data-table'

import { PackagingCodeLink } from '../components/packaging-code-link'
import { PackagingPartCell } from '../components/packaging-part-cell'
import { DiffText, PriceText } from '../components/packaging-price-cells'
import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { joinPackagingWarnings, packagingRoleLabel } from '../utils/packaging-warning-text'
import { PACKAGING_PART_COLUMNS } from './packaging-part-columns'

export type PackagingProductColumn = DataTableColumn<PackagingImpactProduct>

export interface PackagingProductColumnOptions {
  /** Số dòng đứng trước trang hiện tại — để STT chạy tiếp qua các trang (bản `compact` không có cột STT). */
  offset?: number
  rows?: PackagingImpactProduct[]
  /** Khóa của cột "CP bao bì/chai mới" (cũng là khóa xếp gửi máy chủ). */
  newCostKey: 'cost_applied_bottle' | 'cost_new_bottle'
  /** Mã HH và mã thành phần bấm được sang Lịch sử mua hàng; tên + ghi chú cắt một dòng thay vì xuống dòng. */
  compact?: boolean
  /** Cột chèn thêm ngay sau các cột chi phí (Tổng hợp: % chênh, xu hướng). */
  extraAfterCosts?: PackagingProductColumn[]
}

export function buildPackagingProductColumns({
  offset = 0,
  rows,
  newCostKey,
  compact = false,
  extraAfterCosts = [],
}: PackagingProductColumnOptions): PackagingProductColumn[] {
  const stt: PackagingProductColumn = {
    key: 'stt',
    header: 'STT',
    width: 56,
    align: 'center',
    hideable: false,
    defaultPinned: true,
    cell: (row) => offset + (rows?.indexOf(row) ?? 0) + 1,
  }
  const lead: PackagingProductColumn[] = [
    ...(compact ? [] : [stt]),
    {
      key: 'fg_code',
      header: 'Mã HH',
      width: compact ? 104 : 110,
      hideable: false,
      defaultPinned: true,
      sortable: true,
      cell: (row) =>
        compact ? (
          <PackagingCodeLink code={row.fg_code} product />
        ) : (
          <span className="font-medium tabular-nums">{row.fg_code}</span>
        ),
    },
    {
      key: 'fg_name',
      header: 'Tên hàng hóa',
      width: compact ? 190 : 240,
      wrap: !compact,
      sortable: true,
      cell: (row) => (compact ? <span title={row.fg_name}>{row.fg_name}</span> : row.fg_name),
    },
    {
      key: 'carton_qty',
      header: compact ? 'Quy cách' : 'Quy cách thùng',
      width: compact ? 104 : 90,
      align: 'right',
      sortable: true,
      cell: (row) => (row.carton_qty ? row.carton_qty.toLocaleString('vi-VN') : <span>—</span>),
    },
  ]
  const parts = PACKAGING_PART_COLUMNS.map<PackagingProductColumn>((part) => {
    const header = part.perCarton
      ? `${packagingRoleLabel(part.role)} (giá /thùng)`
      : packagingRoleLabel(part.role)
    return {
      key: `part_${part.role}`,
      header,
      //  Xếp theo GIÁ MỚI (đang áp) của thành phần — con số kéo chi phí; ô không có mã / chưa có giá xuống cuối.
      sortable: true,
      sortKey: part.sortKey,
      headerTitle: 'Xếp theo giá mới của thành phần',
      width: 140,
      cell: (row: PackagingImpactProduct) => (
        <PackagingPartCell
          part={row.parts.find((item) => item.role === part.role)}
          linkCode={compact}
        />
      ),
    }
  })
  const costs: PackagingProductColumn[] = [
    {
      key: 'cost_old_bottle',
      header: compact ? 'CP cũ /chai' : 'CP bao bì/chai cũ',
      width: compact ? 116 : 110,
      align: 'right',
      sortable: true,
      cell: (row) => <PriceText value={row.cost_old_bottle} />,
    },
    {
      key: newCostKey,
      header: compact ? 'CP mới /chai' : 'CP bao bì/chai mới',
      width: compact ? 124 : 110,
      align: 'right',
      sortable: true,
      cell: (row) => <PriceText value={row[newCostKey]} className="font-medium" />,
    },
    {
      key: 'diff_bottle',
      header: 'Tăng/giảm /chai',
      width: compact ? 140 : 100,
      align: 'right',
      sortable: true,
      sortDescFirst: true,
      cell: (row) => <DiffText value={row.diff_bottle} bold />,
    },
    {
      key: 'diff_carton',
      header: 'Tăng/giảm /thùng',
      width: compact ? 152 : 110,
      align: 'right',
      sortable: true,
      sortDescFirst: true,
      cell: (row) => <DiffText value={row.diff_carton} bold />,
    },
  ]
  const note: PackagingProductColumn = {
    key: 'note',
    header: 'Ghi chú',
    width: 220,
    wrap: !compact,
    cell: (row) => {
      const text = joinPackagingWarnings(row.warnings)
      return (
        <span className="text-xs text-muted-foreground" title={compact ? text : undefined}>
          {text}
        </span>
      )
    },
  }
  //  Tổng hợp (compact): con số cần đọc (chi phí cũ / mới, chênh lệch, xu hướng) đứng TRƯỚC năm ô thành phần để thấy ngay
  //  không phải cuộn ngang; Tác động giá giữ thứ tự bản mẫu (thành phần rồi tới chi phí).
  return compact
    ? [...lead, ...costs, ...extraAfterCosts, ...parts, note]
    : [...lead, ...parts, ...costs, ...extraAfterCosts, note]
}
