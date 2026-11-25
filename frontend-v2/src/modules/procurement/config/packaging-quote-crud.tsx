/**
 * duoc-CR-784 — danh sách Báo giá VTBB (`/api/product-price-quotes`, khóa `packaging_cost`).
 *
 * Sửa / thêm bằng hộp thoại riêng `PackagingQuoteDialog` (ô đơn giá kiểu vi-VN) gắn qua `FormDialog`;
 * `formFields` vẫn khai để khung CRUD biết bộ ô (giá trị mặc định, nhãn) dù không dựng form chung.
 */
import type { CrudConfig } from '@/shared/crud'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'

import { PACKAGING_QUOTE_API } from '../api/packaging-cost-api'
import { PackagingQuoteDialog } from '../components/packaging-quote-dialog'
import { PackagingQuoteSourceCell } from '../components/packaging-quote-source-cell'
import { PriceText } from '../components/packaging-price-cells'
import { packagingCostKeys } from './packaging-cost-query-keys'
import type { PackagingQuote } from '../types/packaging-cost-types'

export const PACKAGING_QUOTE_CRUD_CONFIG: CrudConfig<PackagingQuote> = {
  entity: 'packaging_cost',
  auditEntity: 'packaging_cost_quote',
  title: 'Báo giá VTBB',
  description:
    'Giá nhà cung cấp báo cho vật tư bao bì (VNĐ chưa VAT). Báo giá mới nhất của một mã là giá mới ở màn Tác động giá — kể cả báo giá có ngày hiệu lực ở tương lai.',
  unitLabel: 'báo giá',
  apiPath: PACKAGING_QUOTE_API,
  storageKey: 'procurement.packaging-quotes',
  searchParam: 'product_code',
  searchPlaceholder: 'Tìm theo mã VTBB…',
  defaultSort: { by: 'valid_from', dir: 'desc' },
  getItemName: (row) => `báo giá ${row.product_code}`,
  openFormOnRowClick: true,
  FormDialog: PackagingQuoteDialog,
  alsoInvalidate: [packagingCostKeys.all],
  columns: [
    {
      key: 'product_code',
      header: 'Mã VTBB',
      width: 120,
      sortable: true,
      hideable: false,
      cell: (row) => <span className="font-semibold tabular-nums">{row.product_code}</span>,
    },
    {
      key: 'product_name',
      header: 'Tên vật tư',
      width: 240,
      wrap: true,
      cell: (row) => row.product_name,
    },
    {
      key: 'supplier_code',
      header: 'Mã NCC',
      width: 110,
      sortable: true,
      cell: (row) => row.supplier_code,
    },
    {
      key: 'supplier_name',
      header: 'Nhà cung cấp',
      width: 220,
      wrap: true,
      cell: (row) => row.supplier_name,
    },
    {
      key: 'price',
      header: 'Đơn giá',
      width: 110,
      align: 'right',
      sortable: true,
      cell: (row) => <PriceText value={Number(row.price)} className="font-medium" />,
    },
    {
      key: 'vat',
      header: 'VAT %',
      width: 70,
      align: 'right',
      sortable: true,
      cell: (row) => Number(row.vat),
    },
    {
      key: 'valid_from',
      header: 'Ngày hiệu lực',
      width: 120,
      sortable: true,
      sortDescFirst: true,
      cell: (row) => formatDate(row.valid_from),
    },
    { key: 'note', header: 'Ghi chú', width: 220, wrap: true, cell: (row) => row.note },
    {
      // Chỉ xem, không xếp: máy chủ ghi, không phải ô người dùng gõ; chữ "(lô #N)" ghép ở giao diện nên không có khóa xếp khớp.
      key: 'source',
      header: 'Nguồn',
      width: 150,
      cell: (row) => <PackagingQuoteSourceCell row={row} />,
    },
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
      { name: 'product_code', label: 'Mã VTBB', type: 'text' },
      { name: 'supplier_code', label: 'Mã NCC', type: 'text' },
      { name: 'note', label: 'Ghi chú', type: 'text' },
    ],
  },
  formFields: [
    { name: 'product_code', label: 'Mã VTBB', type: 'text', required: true },
    { name: 'supplier_code', label: 'Mã NCC', type: 'text' },
    { name: 'price', label: 'Đơn giá', type: 'number', required: true },
    { name: 'vat', label: 'VAT (%)', type: 'number' },
    { name: 'valid_from', label: 'Ngày hiệu lực', type: 'date', required: true },
    { name: 'note', label: 'Ghi chú', type: 'textarea' },
  ],
}
