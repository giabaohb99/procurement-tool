/**
 * duoc-CR-784 — danh mục Định mức bao bì theo mã hàng hóa (`/api/packaging-boms`, khóa `packaging_cost`).
 *
 * Mỗi mã HH một dòng: chai + nắp + nhãn (tính theo chai) và nhãn thùng + thùng (tính theo thùng, chia quy
 * cách). Nạp hàng loạt bằng nút "Nhập từ Excel" (`PackagingExcelImportButton`); ở đây sửa từng dòng.
 * Mã thành phần chưa có trong danh mục sản phẩm thì ô tô đỏ (máy chủ gắn `parts[].in_catalog`).
 */
import type { CrudConfig, CrudFormField } from '@/shared/crud'
import type { DataTableColumn } from '@/shared/data-table'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

import { PACKAGING_BOM_API } from '../api/packaging-cost-api'
import { PackagingExcelImportButton } from '../components/packaging-excel-import-button'
import { PACKAGING_BOM_IMPORT } from './packaging-excel-imports'
import type { PackagingBom } from '../types/packaging-cost-types'
import { packagingRoleLabel } from '../utils/packaging-warning-text'
import { packagingCostKeys } from './packaging-cost-query-keys'
import { PACKAGING_PART_COLUMNS } from './packaging-part-columns'

function partColumn(role: number, field: string): DataTableColumn<PackagingBom> {
  return {
    key: field,
    header: packagingRoleLabel(role),
    width: 150,
    sortable: true,
    cell: (row) => {
      const code = String(row[field] ?? '')
      if (!code) return <span className="text-muted-foreground">—</span>
      const part = row.parts?.find((item) => item.role === role)
      const missing = part ? !part.in_catalog : false
      return (
        <div
          className="leading-tight"
          title={missing ? 'Mã chưa có trong danh mục sản phẩm' : part?.name}
        >
          <div className={cn('text-xs font-medium tabular-nums', missing && 'text-destructive')}>
            {code}
          </div>
          <div className="truncate text-xs text-muted-foreground">
            {missing ? 'chưa có trong danh mục' : part?.name}
          </div>
        </div>
      )
    },
  }
}

const PART_FORM_FIELDS: CrudFormField[] = PACKAGING_PART_COLUMNS.map((part) => ({
  name: part.field,
  label: `Mã ${packagingRoleLabel(part.role).toLowerCase()}`,
  type: 'text' as const,
  required: part.role === 1,
  section: 'Thành phần bao bì',
  hint: part.perCarton
    ? 'Giá tính cho cả thùng, chia quy cách thùng khi cộng vào chi phí /chai.'
    : undefined,
}))

export const PACKAGING_BOM_CRUD_CONFIG: CrudConfig<PackagingBom> = {
  entity: 'packaging_cost',
  auditEntity: 'packaging_bom',
  title: 'Định mức bao bì',
  description:
    'Mỗi mã hàng hóa dùng chai, nắp, nhãn, nhãn thùng, thùng nào và bao nhiêu chai một thùng. CP bao bì/chai = chai + nắp + nhãn + (nhãn thùng + thùng) / quy cách thùng.',
  unitLabel: 'định mức',
  apiPath: PACKAGING_BOM_API,
  storageKey: 'procurement.packaging-boms',
  searchParam: 'hh_code',
  searchPlaceholder: 'Tìm theo mã HH…',
  defaultSort: { by: 'hh_code', dir: 'asc' },
  getItemName: (row) => `định mức ${row.hh_code}`,
  openFormOnRowClick: true,
  deleteInForm: true,
  dialogMaxWidth: 'sm:max-w-2xl',
  alsoInvalidate: [packagingCostKeys.all],
  renderToolbarExtra: () => <PackagingExcelImportButton kind={PACKAGING_BOM_IMPORT} />,
  columns: [
    {
      key: 'hh_code',
      header: 'Mã HH',
      width: 110,
      sortable: true,
      hideable: false,
      defaultPinned: true,
      cell: (row) => <span className="font-semibold tabular-nums">{row.hh_code}</span>,
    },
    {
      key: 'hh_name',
      header: 'Tên hàng hóa',
      width: 240,
      wrap: true,
      sortable: true,
      cell: (row) => row.hh_name,
    },
    {
      key: 'legal_name',
      header: 'Tên pháp lý',
      width: 200,
      wrap: true,
      defaultHidden: true,
      cell: (row) => row.legal_name,
    },
    {
      key: 'carton_qty',
      header: 'Quy cách thùng',
      width: 100,
      align: 'right',
      sortable: true,
      cell: (row) =>
        row.carton_qty ? (
          row.carton_qty.toLocaleString('vi-VN')
        ) : (
          <span className="text-destructive">chưa có</span>
        ),
    },
    ...PACKAGING_PART_COLUMNS.map((part) => partColumn(part.role, part.field)),
    {
      key: 'updated_at',
      header: 'Cập nhật',
      width: 150,
      sortable: true,
      sortDescFirst: true,
      defaultHidden: true,
      cell: (row) => formatDateTime(row.updated_at),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'hh_code', label: 'Mã HH', type: 'text' },
      { name: 'hh_name', label: 'Tên hàng hóa', type: 'text' },
      ...PACKAGING_PART_COLUMNS.map((part) => ({
        name: part.field,
        label: `Mã ${packagingRoleLabel(part.role).toLowerCase()}`,
        type: 'text' as const,
      })),
    ],
  },
  formFields: [
    { name: 'hh_code', label: 'Mã HH', type: 'text', required: true, readonlyOnEdit: true },
    {
      name: 'carton_qty',
      label: 'Quy cách thùng (chai / thùng)',
      type: 'number',
      defaultValue: 0,
      hint: '0 = chưa có — phần nhãn thùng / thùng sẽ không tính được.',
    },
    { name: 'hh_name', label: 'Tên hàng hóa', type: 'text', fullWidth: true },
    { name: 'legal_name', label: 'Tên pháp lý', type: 'text', fullWidth: true },
    ...PART_FORM_FIELDS,
  ],
}
