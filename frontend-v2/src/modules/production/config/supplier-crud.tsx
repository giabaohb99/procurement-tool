import { Building2, CircleCheck, CircleX, Hash, Percent, Receipt, Truck } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { ratioToPercentInput } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { formatPercent } from '@/shared/utils/format-money'
import { PurchaseHistoryTable } from '../components/purchase-history-table'
import { SupplierContractsTable } from '../components/supplier-contracts-table'
import { SupplierFilesTab } from '../components/supplier-files-tab'
import { SupplierPayablesPanel } from '../components/supplier-payables-panel'
import { SupplierSurveysPanel } from '../components/supplier-surveys-panel'
import { SUPPLIER_TYPE_LABELS, type Supplier } from '../types/supplier'

/** Tư cách pháp lý của bên bán — khớp bộ giá trị bản đang chạy thật. */
const LEGAL_TYPE_OPTIONS = ['Công ty', 'Cá nhân', 'Hợp danh', 'Hộ kinh doanh'].map((value) => ({
  value,
  label: value,
}))

/**
 * Hình thức thanh toán — danh sách CỐ ĐỊNH, không phải danh mục trong CSDL.
 * Giá trị lưu chính là chuỗi hiển thị, nên sửa chữ ở đây là lệch dữ liệu cũ.
 */
const PAYMENT_TERMS_OPTIONS = [
  'Công nợ 60 ngày',
  'Công nợ 30 ngày',
  'Công nợ 20 ngày',
  'Thanh toán 100% khi nhận hàng',
  'Thanh toán trước khi giao hàng',
  'Thanh toán 7 ngày sau khi nhận hàng',
].map((value) => ({ value, label: value }))

const SUPPLIER_TYPE_OPTIONS = (Object.keys(SUPPLIER_TYPE_LABELS) as Supplier['supplier_type'][]).map(
  (value) => ({ value, label: SUPPLIER_TYPE_LABELS[value] }),
)

export const SUPPLIER_CRUD_CONFIG: CrudConfig<Supplier> = {
  entity: 'supplier',
  title: 'Nhà cung cấp',
  unitLabel: 'nhà cung cấp',
  apiPath: '/api/suppliers',
  storageKey: 'production.suppliers',
  listRoute: appRoutes.production.suppliers,
  detailRoute: (id) => appRoutes.production.supplierDetail(id),
  // Backend không có tham số `search` cho NCC; whitelist FILTERABLE có `name` nên
  // ô tìm nhanh chạy thẳng vào bộ lọc LIKE của tên pháp lý.
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên pháp lý…',
  getItemName: (s) => `${s.name} (${s.code})`,
  deleteWarning:
    'Đơn mua hàng, hợp đồng, công nợ và phiếu khảo sát cũ tham chiếu tới mã nhà cung cấp này. Xóa sẽ làm mất liên kết; muốn ngừng giao dịch thì tắt "Đang giao dịch" thay vì xóa.',
  chips: (s) => [
    ...(s.code ? [{ icon: Hash, text: s.code, tone: 'code' as const }] : []),
    {
      icon: s.supplier_type === 'transport' ? Truck : Building2,
      text: SUPPLIER_TYPE_LABELS[s.supplier_type] ?? s.supplier_type,
    },
    ...(s.tax_code ? [{ icon: Receipt, text: `MST: ${s.tax_code}` }] : []),
    { icon: Percent, text: `VAT ${formatPercent(ratioToPercentInput(s.vat))}` },
    {
      icon: s.is_active ? CircleCheck : CircleX,
      text: s.is_active ? 'Đang giao dịch' : 'Ngừng giao dịch',
      tone: s.is_active ? ('ok' as const) : ('muted' as const),
    },
  ],
  columns: [
    {
      key: 'code',
      header: 'Tên viết tắt',
      width: 150,
      hideable: false,
      defaultPinned: true,
      cell: (s) => <span className="font-semibold text-primary">{s.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên pháp lý',
      width: 300,
      wrap: true,
      hideable: false,
      cell: (s) => <span className="font-medium">{s.name}</span>,
    },
    {
      key: 'supplier_type',
      header: 'Vai trò',
      width: 180,
      cell: (s) => SUPPLIER_TYPE_LABELS[s.supplier_type] ?? s.supplier_type,
    },
    { key: 'tax_code', header: 'Mã số thuế', width: 140, cell: (s) => s.tax_code },
    { key: 'contact_person', header: 'Người liên hệ', width: 180, cell: (s) => s.contact_person },
    { key: 'phone', header: 'Điện thoại', width: 140, cell: (s) => s.phone },
    {
      key: 'payment_terms',
      header: 'Hình thức thanh toán',
      width: 220,
      wrap: true,
      cell: (s) => s.payment_terms,
    },
    {
      key: 'vat',
      header: 'VAT',
      width: 100,
      align: 'right',
      // `vat` lưu dạng TỈ LỆ (0.08) — nhân 100 rồi mới định dạng, đừng đọc thẳng.
      cell: (s) => <span className="tabular-nums">{formatPercent(ratioToPercentInput(s.vat))}</span>,
    },
    {
      key: 'address',
      header: 'Địa chỉ',
      width: 300,
      wrap: true,
      defaultHidden: true,
      cell: (s) => s.address,
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 140,
      cell: (s) => (
        <Badge variant={s.is_active ? 'default' : 'secondary'}>
          {s.is_active ? 'Đang giao dịch' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    // Chỉ khai được đúng những cột nằm trong FILTERABLE của backend
    // (`supplier/service.py`); thêm cột ngoài danh sách đó thì tham số bị bỏ qua
    // im lặng và người dùng tưởng bộ lọc hỏng.
    fields: [
      { name: 'code', label: 'Tên viết tắt', type: 'text' },
      { name: 'name', label: 'Tên pháp lý', type: 'text' },
      { name: 'tax_code', label: 'Mã số thuế', type: 'text' },
      {
        name: 'supplier_type',
        label: 'Vai trò cung cấp',
        type: 'select',
        options: SUPPLIER_TYPE_OPTIONS,
      },
      {
        name: 'is_active',
        label: 'Trạng thái',
        type: 'select',
        options: [
          { value: 'true', label: 'Đang giao dịch' },
          { value: 'false', label: 'Ngừng giao dịch' },
        ],
      },
    ],
  },
  formFields: [
    {
      name: 'code',
      label: 'Tên viết tắt',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: ABC, TANTIEN…',
      hint: 'Mã định danh duy nhất của nhà cung cấp. Không sửa được sau khi tạo vì hợp đồng, công nợ và khảo sát đều nối theo mã này.',
    },
    {
      name: 'supplier_type',
      label: 'Vai trò cung cấp',
      type: 'select',
      required: true,
      options: SUPPLIER_TYPE_OPTIONS,
      defaultValue: 'goods',
      placeholder: 'Chọn vai trò',
    },
    {
      name: 'name',
      label: 'Tên pháp lý',
      type: 'text',
      required: true,
      fullWidth: true,
      placeholder: 'Tên công ty / cá nhân theo giấy tờ…',
    },
    {
      name: 'legal_type',
      label: 'Tư cách pháp lý',
      type: 'select',
      options: LEGAL_TYPE_OPTIONS,
      placeholder: 'Chọn tư cách pháp lý',
    },
    {
      name: 'tax_code',
      label: 'Mã số thuế',
      type: 'text',
      placeholder: 'VD: 0312345678',
    },
    {
      name: 'contact_person',
      label: 'Người liên hệ',
      type: 'text',
      placeholder: 'Tên người đại diện liên hệ…',
    },
    {
      name: 'phone',
      label: 'Điện thoại',
      type: 'text',
      placeholder: 'Số điện thoại liên hệ…',
    },
    {
      name: 'address',
      label: 'Địa chỉ',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'Địa chỉ trụ sở / kho bãi…',
    },
    {
      name: 'vat',
      label: 'VAT mặc định',
      type: 'percent',
      // Khai theo DẠNG LƯU: 0.08 = 8%. Form tự đổi sang phần trăm khi hiển thị.
      defaultValue: 0.08,
      hint: 'Thuế suất tự điền vào dòng hàng khi chọn nhà cung cấp này trong Đơn mua hàng. Nhập theo phần trăm, từ 0 đến dưới 100.',
    },
    {
      name: 'payment_terms',
      label: 'Hình thức thanh toán',
      type: 'select',
      fullWidth: true,
      options: PAYMENT_TERMS_OPTIONS,
      placeholder: 'Chọn hình thức thanh toán',
    },
    {
      name: 'bank_account_name',
      label: 'Tên tài khoản thụ hưởng',
      type: 'text',
      placeholder: 'Tên chủ tài khoản trên sao kê…',
    },
    {
      name: 'bank_account',
      label: 'Số tài khoản',
      type: 'text',
      placeholder: 'Số tài khoản giao dịch…',
    },
    {
      name: 'bank_name',
      label: 'Ngân hàng & chi nhánh',
      type: 'text',
      fullWidth: true,
      placeholder: 'VD: Vietcombank - CN Tân Bình',
    },
    {
      name: 'is_active',
      label: 'Đang giao dịch',
      type: 'switch',
      defaultValue: true,
      hint: 'Tắt sẽ ẩn khỏi ô chọn nhà cung cấp khi lập chứng từ mới; chứng từ cũ giữ nguyên.',
    },
  ],
  tabs: [
    {
      key: 'contracts',
      label: 'Hợp đồng',
      render: (supplier) => <SupplierContractsTable supplierCode={supplier.code} />,
    },
    {
      key: 'payables',
      label: 'Công nợ & Đánh giá',
      render: (supplier) => <SupplierPayablesPanel supplier={supplier} />,
    },
    {
      key: 'purchase-history',
      label: 'Lịch sử mua hàng',
      render: (supplier) => <PurchaseHistoryTable supplierCode={supplier.code} />,
    },
    {
      key: 'surveys',
      label: 'Khảo sát của NCC',
      render: (supplier) => <SupplierSurveysPanel supplier={supplier} />,
    },
    {
      key: 'files',
      label: 'Tệp đính kèm',
      render: (supplier) => <SupplierFilesTab supplierId={supplier.id} />,
    },
  ],
}
