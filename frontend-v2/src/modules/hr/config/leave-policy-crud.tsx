import { CircleCheck, CircleX, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { LeavePolicyAssignmentsTab } from '../components/leave-policy-assignments-tab'
import { LeavePolicyLinesCard } from '../components/leave-policy-lines-card'
import type { LeavePolicy } from '../types/leave-policy'
import { buildLeavePolicyHubHref, LEAVE_POLICY_HUB_TAB_PARAM, LEAVE_POLICY_HUB_TITLE } from '../utils/leave-policy-hub-tabs'

/**
 * CHÍNH SÁCH NGHỈ PHÉP (duoc-CR-717) — gói "loại nghỉ → số ngày mỗi năm", chép ý Leave Policy của ERPNext.
 *
 * Danh sách gói là tab "Chính sách" của màn Nghỉ phép › Chính sách nghỉ phép, gán gói cho người ở tab "Phân bổ" cùng
 * màn (duoc-CR-750, trước đó là tab thứ tư của Thiết lập + màn riêng "Phân bổ chính sách"). Lúc cấp quỹ, hạn mức lấy theo thứ tự: phân bổ chính sách
 * của người → hạn mức theo nhóm (hình thức NV, cấp bậc) → "Hạn mức mỗi năm" của loại nghỉ (D1a).
 * Khóa quyền dùng chung `leave_type` — cùng "Thiết lập" nghỉ phép (D4a, không thêm khóa).
 *
 * ⚠️ "Mã" KHÔNG đổi được sau khi tạo (`readonlyOnEdit`) — backend cũng không nhận `code` ở lệnh sửa.
 */
const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng' },
  { value: 'false', label: 'Ngừng' },
]

const policyChips = (p: LeavePolicy) => [
  { icon: Hash, text: p.code, tone: 'code' as const },
  {
    icon: p.is_active ? CircleCheck : CircleX,
    text: p.is_active ? 'Đang dùng' : 'Ngừng',
    tone: p.is_active ? ('ok' as const) : ('muted' as const),
  },
]

export const LEAVE_POLICY_CRUD_CONFIG: CrudConfig<LeavePolicy> = {
  entity: 'leave_type',
  auditEntity: 'leave_policy',
  title: LEAVE_POLICY_HUB_TITLE,
  description: 'Gói số ngày phép mỗi năm theo loại nghỉ, gán cho từng nhân sự ở tab Phân bổ chính sách.',
  unitLabel: 'chính sách',
  apiPath: '/api/leave-policies',
  storageKey: 'hr.leave-policies',
  //  duoc-CR-750: nút quay lại / xóa xong ở trang chi tiết về đúng tab Chính sách của màn gộp. Đường cũ
  //  `/hr/leave-policies` vẫn chạy (chuyển hướng sang đây) nhưng đi thẳng thì khỏi một nhịp chuyển.
  listRoute: buildLeavePolicyHubHref('policies'),
  detailRoute: (id) => appRoutes.hr.leavePolicyDetail(id),
  createRoute: appRoutes.hr.leavePolicyNew,
  detailLayout: 'flat',
  //  Đổi tên / ngừng dùng / xóa gói thì danh sách phân bổ (cột "Chính sách", ô gợi ý trên chi tiết quỹ)
  //  đang giữ tên cũ trong cache `hr` — dọn gốc phân bổ cùng lúc (review L7).
  alsoInvalidate: [queryKeys.hr.leavePolicyAssignmentsRoot],
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên chính sách…',
  quickFilters: [{ key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS }],
  getItemName: (p) => `${p.name} (${p.code})`,
  deleteWarning:
    'Chính sách đang được phân bổ cho nhân sự thì không xóa được — kết thúc hoặc xóa phân bổ trước. ' +
    'Muốn ẩn khỏi ô chọn mà vẫn giữ phân bổ cũ thì tắt "Đang dùng".',
  chips: policyChips,
  mobileCard: (p) => (
    <CrudRecordCard title={p.name} subtitle={p.note || 'Không ghi chú'} chips={policyChips(p)} />
  ),
  columns: [
    {
      key: 'code',
      header: 'Mã',
      width: 140,
      sortable: true,
      hideable: false,
      cell: (p) => <span className="font-semibold text-primary">{p.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên chính sách',
      width: 260,
      sortable: true,
      hideable: false,
      cell: (p) => <span className="font-medium">{p.name}</span>,
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (p) => (
        <Badge variant={p.is_active ? 'default' : 'secondary'}>{p.is_active ? 'Đang dùng' : 'Ngừng'}</Badge>
      ),
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 320,
      //  Cột thật; dòng không ghi chú là ô trống, xuống cuối cả hai chiều (duoc-CR-748).
      sortable: true,
      cell: (p) => (p.note ? p.note : <span className="text-muted-foreground">Không ghi chú</span>),
    },
  ],
  filterConfig: {
    //  ⚠️ Bấm "Áp dụng" bộ lọc nâng cao VIẾT LẠI cả chuỗi truy vấn, chỉ chừa tham số khai ở đây — thiếu `tab` thì
    //  người có cả hai quyền lọc xong bị đá về tab Phân bổ (tab mặc định), duoc-CR-750.
    preserveParams: [LEAVE_POLICY_HUB_TAB_PARAM],
    fields: [
      { name: 'code', label: 'Mã chính sách', type: 'text' },
      { name: 'name', label: 'Tên chính sách', type: 'text' },
      { name: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
  },
  formFields: [
    {
      name: 'code',
      label: 'Mã chính sách',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: CS-QUANLY',
      hint: 'Tối đa 30 ký tự, không trùng. KHÔNG đổi được sau khi tạo.',
    },
    {
      name: 'name',
      label: 'Tên chính sách',
      type: 'text',
      required: true,
      placeholder: 'VD: Chính sách cấp quản lý',
      hint: 'Tối đa 150 ký tự. Hiện trong ô chọn khi phân bổ và trên chi tiết quỹ phép của từng người.',
    },
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
      fullWidth: true,
      hint: 'Tối đa 500 ký tự.',
    },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng thì không phân bổ mới được; phân bổ đã có vẫn giữ nguyên.',
    },
  ],
  //  Tab chỉ dựng khi đã có bản ghi (khung CRUD tự lo) — gói chưa lưu thì chưa có id để gắn dòng.
  tabs: [
    {
      key: 'lines',
      label: 'Loại nghỉ & số ngày',
      render: (p) => <LeavePolicyLinesCard policyId={p.id} />,
    },
    {
      key: 'assignments',
      label: 'Đang phân bổ',
      render: (p) => <LeavePolicyAssignmentsTab policyId={p.id} />,
    },
  ],
}
