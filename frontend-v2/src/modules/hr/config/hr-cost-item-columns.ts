import type { LinesTableColumn } from '@/shared/data-table/types'

/**
 * Cột của BẢNG KHOẢN CHI PHÍ (màn Mẫu + khối 2 trang Kế hoạch, duoc-CR-690). Đuôi `" *"` = cột bắt
 * buộc (`required-header.ts`).
 */
/** Hai cột TIỀN — gỡ hẳn khỏi bảng khi người xem không được xem lương. */
const MONEY_COLUMN_KEYS = new Set(['cap_amount', 'amount'])

const COLUMNS: LinesTableColumn[] = [
  { key: 'code', header: 'Mã *', width: 130, hideable: false, defaultPinned: true },
  { key: 'name', header: 'Tên khoản *', width: 220, hideable: false, defaultPinned: true },
  { key: 'group_id', header: 'Nhóm', width: 160 },
  { key: 'calc_method', header: 'Cách tính', width: 230, hideable: false },
  { key: 'rate', header: 'Tỷ lệ %', width: 100, align: 'right' },
  { key: 'factor', header: 'Hệ số', width: 90, align: 'right', compactHidden: true },
  { key: 'cap_amount', header: 'Trần / người', width: 140, align: 'right' },
  { key: 'amount', header: 'Số tiền', width: 140, align: 'right' },
  { key: 'base_codes', header: 'Khoản gốc', width: 200 },
  { key: 'months', header: 'Rơi vào tháng', width: 170 },
  { key: 'applies_to', header: 'Áp cho', width: 210 },
  { key: 'actual_source', header: 'Lấy thực tế từ', width: 200, compactHidden: true },
  { key: 'actions', header: 'Thao tác', width: 110, hideable: false },
]

/** Cột nào bảng dựng — bỏ cột tiền khi bị che, bỏ cột thao tác khi chỉ xem. Tách ra để bài kiểm canh. */
export function buildCostItemColumns(showMoney: boolean, readOnly: boolean): LinesTableColumn[] {
  return COLUMNS.filter(
    (c) => (showMoney || !MONEY_COLUMN_KEYS.has(c.key)) && (!readOnly || c.key !== 'actions'),
  )
}

