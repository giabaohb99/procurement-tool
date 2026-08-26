/** Nhãn định dạng file xuất. */
export type ExportFormat = 'csv' | 'xlsx'

export const EXPORT_FORMAT_LABELS: Record<string, string> = {
  csv: 'CSV',
  xlsx: 'Excel (XLSX)',
}

export const EXPORT_FORMAT_OPTIONS: { value: ExportFormat; label: string }[] = [
  { value: 'xlsx', label: 'Excel (XLSX)' },
  { value: 'csv', label: 'CSV' },
]
