/**
 * Hợp đồng `GET <gốc>/summary/rows` — «bấm số ra danh sách người» (duoc-CR-686,
 * khớp `backend/app/core/report_drilldown.py`). Backend là nguồn DUY NHẤT của cột
 * và nhãn cột; tầng này chỉ đọc `kind` để định dạng ô.
 */

/** Đơn vị của một cột danh sách — quyết định cách định dạng ô (`format-drilldown-cell.ts`). */
export type ReportDrilldownColumnKind = 'text' | 'date' | 'int' | 'days' | 'money'

export interface ReportDrilldownColumn {
  key: string
  label: string
  kind: ReportDrilldownColumnKind
}

/** Một dòng — khóa theo `columns[].key`; `link` (tùy chọn) là đường giao diện v2 mở khi bấm dòng. */
export type ReportDrilldownRow = Record<string, unknown> & { link?: string | null }

export interface ReportDrilldownResponse {
  metric: { key: string; label: string }
  columns: ReportDrilldownColumn[]
  rows: ReportDrilldownRow[]
  /** Số dòng THẬT trước khi cắt trần — lớn hơn `rows.length` khi `truncated`. */
  total: number
  /** Vượt trần 500 dòng của backend — chỉ `rows.length` dòng đầu được trả về. */
  truncated: boolean
}

/** Nhóm «Xem theo» đang mở danh sách; `null` ở `ReportDrilldownTarget.group` = cả dòng Tổng. */
export interface ReportDrilldownGroup {
  /** `group_by` gửi lên — chiều đang xem. */
  by: string
  /** `group_key` gửi lên — `""` là nhóm «(Chưa gắn)». */
  key: string
  /** Tên chiều ("Phòng ban") — để ghi phụ đề ngăn. */
  dimensionLabel: string
  /** Tên nhóm ("Kế toán") — để ghi phụ đề ngăn. */
  label: string
}

export interface ReportDrilldownTarget {
  metric: string
  group: ReportDrilldownGroup | null
}
