import {
  Calendar,
  FileCheck,
  FileText,
  Hash,
  UserCheck,
} from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import {
  CONTRACT_PARTY_TYPE,
  CONTRACT_STATUS,
  type StatusOption,
} from '@/shared/constants/statuses'
import type { CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS, type StatusTone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { CONTRACT_FILTER_FIELDS } from './contract-filter-fields'
import { contractTypeLabel } from './contract-type-options'
import { ContractFilesTab } from '../components/contract-files-tab'
import { ContractPartnerTab } from '../components/contract-partner-tab'
import type { Contract } from '../types/contract'

/**
 * Tô màu theo MÃ tình trạng hạn (B-02), không theo nhãn tiếng Việt nữa.
 *
 * Trước đây khóa là chuỗi hiển thị, nên sửa một chữ trong nhãn là mất màu mà không ai
 * biết — hỏng lặng lẽ, chỉ lộ ra khi có người nhìn kỹ cột đó.
 */
const EXPIRY_TONE: Record<string, StatusTone> = {
  expired: 'danger',
  expiring_soon: 'pending',
  valid: 'done',
}

/**
 * Màu viền của trạng thái hợp đồng. `expired`/`cancelled` rơi vào nhánh xám mặc định.
 */
const STATUS_CLASS: Record<string, string> = {
  active: 'border-emerald-500 text-emerald-600 bg-emerald-50',
  liquidated: 'border-blue-500 text-blue-600 bg-blue-50',
}

// Ô chọn dựng từ bộ mã sinh tự động (`@/shared/constants/statuses`) — không khai lại tay.
const toOptions = (set: readonly StatusOption[]) =>
  set.map(({ value, label }) => ({ value, label }))

const PARTY_TYPE_OPTIONS = toOptions(CONTRACT_PARTY_TYPE)
const STATUS_OPTIONS = toOptions(CONTRACT_STATUS)

export const CONTRACT_CRUD_CONFIG: CrudConfig<Contract> = {
  entity: 'contract',
  title: 'Hợp đồng',
  unitLabel: 'hợp đồng',
  apiPath: '/api/contracts',
  storageKey: 'production.contracts',
  listRoute: appRoutes.production.contracts,
  detailRoute: (id) => appRoutes.production.contractDetail(id),
  searchParam: 'title',
  searchPlaceholder: 'Tìm theo tên, mã hợp đồng...',
  quickFilters: [
    {
      key: 'party_type',
      label: 'Bên ký kết',
      type: 'select',
      options: PARTY_TYPE_OPTIONS,
    },
    {
      key: 'status',
      label: 'Trạng thái',
      type: 'select',
      options: STATUS_OPTIONS,
    },
  ],
  filterConfig: {
    fields: CONTRACT_FILTER_FIELDS,
  },
  getItemName: (c) => `${c.title} (${c.code})`,
  deleteWarning:
    'Xóa hợp đồng sẽ giải phóng các tệp đính kèm văn bản hợp đồng này. Bạn có chắc chắn muốn xóa không?',
  chips: (c) => [
    ...(c.code ? [{ icon: Hash, text: c.code, tone: 'code' as const }] : []),
    {
      icon: UserCheck,
      text: `${c.party_type_label || c.party_type}: ${c.party_name || c.party_code || 'Chưa chọn'}`,
    },
    { icon: FileText, text: contractTypeLabel(c.contract_type) || 'Chưa phân loại' },
    { icon: Calendar, text: c.end_date ? `Hết hạn: ${formatDate(c.end_date)}` : 'Không thời hạn' },
    { icon: FileCheck, text: c.signed ? 'Đã ký kết' : 'Chưa ký' },
  ],
  columns: [
    {
      key: 'code',
      header: 'Số hợp đồng',
      width: 150,
      sortable: true,
      hideable: false,
      defaultPinned: true,
      cell: (c) => <span className="font-semibold text-navy dark:text-foreground">{c.code}</span>,
    },
    {
      key: 'title',
      header: 'Tên / Trích yếu hợp đồng',
      width: 280,
      sortable: true,
      wrap: true,
      hideable: false,
      cell: (c) => c.title || '(Không có tiêu đề)',
    },
    {
      key: 'party_type',
      header: 'Bên ký kết',
      width: 220,
      wrap: true,
      cell: (c) => (
        <div>
          <div className="font-medium text-foreground">{c.party_name || '—'}</div>
          <div className="text-xs text-muted-foreground">
            {c.party_type_label || c.party_type} {c.party_code ? `(${c.party_code})` : ''}
          </div>
        </div>
      ),
    },
    {
      key: 'contract_type',
      header: 'Loại hợp đồng',
      width: 140,
      cell: (c) => contractTypeLabel(c.contract_type) || '—',
    },
    {
      key: 'start_date',
      header: 'Ngày ký',
      width: 110,
      sortable: true,
      cell: (c) => formatDate(c.start_date) || '—',
    },
    {
      key: 'end_date',
      header: 'Ngày hết hạn',
      width: 120,
      sortable: true,
      cell: (c) => formatDate(c.end_date) || 'Không thời hạn',
    },
    {
      key: 'expiry',
      header: 'Hiệu lực',
      width: 120,
      cell: (c) =>
        c.expiry ? (
          <Badge
            variant="secondary"
            className={cn('border-0', TONE_CLASS[EXPIRY_TONE[c.expiry] ?? 'neutral'])}
          >
            {c.expiry_label || c.expiry}
          </Badge>
        ) : (
          <span className="text-xs text-muted-foreground">Không thời hạn</span>
        ),
    },
    {
      key: 'signed',
      header: 'Trạng thái ký',
      width: 110,
      cell: (c) => (
        <Badge variant={c.signed ? 'default' : 'secondary'}>
          {c.signed ? 'Đã ký' : 'Chưa ký'}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 120,
      sortable: true,
      cell: (c) => (
        <Badge
          variant="outline"
          className={cn(STATUS_CLASS[c.status] ?? 'border-slate-300 text-slate-600 bg-slate-50')}
        >
          {c.status_label || c.status || '—'}
        </Badge>
      ),
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 200,
      wrap: true,
      defaultHidden: true,
      cell: (c) => c.note || '—',
    },
  ],
  formFields: [
    {
      name: 'code',
      label: 'Số / Mã hợp đồng',
      type: 'text',
      // `ContractUpdate` ở backend KHÔNG có trường `code`: gửi lên thì bị bỏ im
      // lặng, người dùng sửa xong thấy "Đã lưu" mà số hợp đồng vẫn y nguyên.
      readonlyOnEdit: true,
      placeholder: 'VD: HD00001 (để trống tự sinh mã)',
      hint: 'Mã độc nhất nhận diện hợp đồng; đặt xong không đổi được.',
    },
    {
      name: 'title',
      label: 'Tên / Trích yếu hợp đồng',
      type: 'text',
      required: true,
      placeholder: 'VD: Hợp đồng nguyên tắc cung ứng bao bì carton 2026',
    },
    {
      name: 'party_type',
      label: 'Loại đối tác ký kết',
      type: 'select',
      options: PARTY_TYPE_OPTIONS,
      defaultValue: 'supplier',
    },
    {
      name: 'party_code',
      label: 'Mã đối tác (VD mã NCC)',
      type: 'text',
      placeholder: 'VD: NCC00001',
      hint: 'Điền mã nhà cung cấp hoặc đối tác liên quan.',
    },
    {
      name: 'party_name',
      label: 'Tên đối tác',
      type: 'text',
      placeholder: 'VD: Công ty TNHH Bao Bì Dego',
      hint: 'Tự động điền theo mã NCC nếu có.',
    },
    {
      name: 'contract_type',
      label: 'Loại hợp đồng',
      type: 'select',
      // Nạp từ backend chứ không khai tĩnh (CR-118): backend chặn mã lạ bằng 422, nên
      // danh sách chọn phải là ĐÚNG bộ backend đang nhận, không phải bản chép tay dễ lệch.
      source: { url: '/api/contracts/meta/types', valueKey: 'value', labelKey: 'label' },
      defaultValue: 'purchase',
    },
    {
      name: 'company_id',
      label: 'Công ty pháp nhân ký hợp đồng',
      type: 'select',
      source: { url: '/api/companies', valueKey: 'id', labelKey: 'name' },
      // Khai theo DẠNG LƯU: `company_id` là số, 0 = chưa gắn pháp nhân. Để trống
      // thì form gửi chuỗi rỗng và `ContractCreate.company_id: int` trả 422.
      defaultValue: 0,
      placeholder: 'Chọn pháp nhân đứng tên',
      hint: 'Cần quyền đọc danh mục Công ty mới thấy danh sách.',
    },
    {
      name: 'start_date',
      label: 'Ngày ký / Bắt đầu',
      type: 'date',
    },
    {
      name: 'end_date',
      label: 'Ngày hết hạn',
      type: 'date',
    },
    {
      name: 'signed',
      label: 'Đã hoàn tất ký kết',
      type: 'switch',
      defaultValue: true,
    },
    {
      name: 'status',
      label: 'Trạng thái hợp đồng',
      type: 'select',
      options: STATUS_OPTIONS,
      defaultValue: 'active',
    },
    {
      name: 'note',
      label: 'Ghi chú / Điều khoản phụ',
      type: 'textarea',
      placeholder: 'Nhập ghi chú thêm về hợp đồng...',
      fullWidth: true,
    },
  ],
  tabs: [
    {
      key: 'files',
      label: 'Tệp đính kèm',
      render: (contract) => <ContractFilesTab contractId={contract.id} />,
    },
    {
      key: 'partner',
      label: 'Đối tác liên quan',
      render: (contract) => <ContractPartnerTab contract={contract} />,
    },
  ],
}
