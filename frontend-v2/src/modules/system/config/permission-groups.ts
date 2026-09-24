import { matchesVietnamese } from '@/shared/utils/vn-text'

/**
 * Gom các entity phân quyền thành CÂY hai cấp cho màn /system/permissions.
 *
 * Cấp 1 = phân hệ (Đặt xe, Văn thư, Thu mua…). Cấp 2 = các entity con của phân hệ
 * đó (Yêu cầu đặt xe, Tài xế, Phương tiện…). Backend trả danh sách entity PHẲNG
 * (`/api/roles/meta`) không kèm nhóm, nên nhóm khai ở đây.
 *
 * ⚠️ Entity nào KHÔNG khai trong bảng dưới sẽ tự rơi vào nhóm cuối "Khác" — không
 * bao giờ biến mất khỏi màn. Thêm phân hệ/entity mới thì bổ sung một dòng ở đây.
 */

export interface PermissionGroupDef {
  /** Mã nhóm (ổn định) — dùng làm khóa mở/gập. */
  id: string
  /** Nhãn phân hệ hiện ở cấp 1. */
  title: string
  /** Mã entity con, theo thứ tự muốn hiển thị. */
  entities: string[]
}

// Thứ tự khai = thứ tự hiển thị trên màn.
export const PERMISSION_GROUPS: PermissionGroupDef[] = [
  { id: 'vehicle-booking', title: 'Đặt xe', entities: ['vehicle_booking', 'vehicle', 'driver'] },
  {
    id: 'procurement',
    title: 'Thu mua',
    entities: [
      'purchase_request',
      'survey_request',
      'survey',
      'purchase_order',
      'goods_receipt',
      'category_assignee',
    ],
  },
  {
    id: 'production',
    title: 'Sản xuất & Danh mục',
    entities: ['supplier', 'product', 'unit', 'item_group', 'brand', 'contract'],
  },
  { id: 'inventory', title: 'Kho', entities: ['warehouse', 'inventory'] },
  { id: 'finance', title: 'Tài chính', entities: ['payable', 'payment', 'payment_request'] },
  {
    id: 'document',
    title: 'Văn thư',
    entities: [
      'document',
      'document_book',
      'doc_type',
      'doc_template',
      'doc_numbering_rule',
      'doc_link_rule',
      'external_party',
      'security_level',
    ],
  },
  { id: 'approval', title: 'Phê duyệt', entities: ['approval_flow'] },
  { id: 'approval-seal', title: 'Duyệt dấu', entities: ['seal_request', 'seal_type'] },
  { id: 'work', title: 'Dự án / Công việc', entities: ['work_task'] },
  { id: 'forum', title: 'Diễn đàn', entities: ['forum_post', 'forum_board'] },
  {
    id: 'hr',
    title: 'Nhân sự',
    //  `employee_sensitive` (15 trường che) và `job_position` (danh mục chức vụ)
    //  từng rơi vào «Khác» — chúng là khóa của phân hệ Nhân sự (bao-CR-428).
    entities: ['company', 'department', 'employee', 'employee_sensitive',
      'job_position', 'user', 'role'],
  },
  {
    id: 'leave',
    title: 'Nghỉ phép',
    entities: ['leave_request', 'leave_balance', 'leave_type', 'holiday'],
  },
  { id: 'dossier', title: 'Hồ sơ', entities: ['dossier', 'dossier_type'] },
  { id: 'room-booking', title: 'Đặt phòng họp', entities: ['room_booking', 'meeting_room'] },
  {
    id: 'coffee',
    title: 'Điểm cà phê',
    entities: ['coffee_policy', 'coffee_member', 'coffee_ledger', 'pos_order'],
  },
  { id: 'report', title: 'Báo cáo', entities: ['report'] },
  { id: 'support', title: 'Hỗ trợ & Trợ giúp', entities: ['ticket', 'help_article'] },
  { id: 'assistant', title: 'Trợ lý AI', entities: ['assistant'] },
  {
    id: 'system',
    title: 'Hệ thống',
    entities: ['setting', 'backup', 'mailbox', 'import',
      //  Nhật ký & phiên đăng nhập (CR-312). `login_session` trước nay rơi vào
      //  nhóm «Khác» — cùng một mối quan tâm với hai khóa nhật ký, xếp chung.
      //  `sync_log` là sổ đồng bộ với hệ ngoài, cùng họ nhật ký.
      'login_session', 'audit', 'change_log', 'sync_log',
      //  Việc của bot Agent Hub (ai-CR-036).
      'agent_task'],
  },
]

export interface MetaEntity {
  key: string
  label: string
}

export interface PermissionGroup {
  id: string
  title: string
  entities: MetaEntity[]
}

/**
 * Dựng cây từ danh sách entity phẳng của backend.
 *
 * - Chỉ giữ entity CÓ THẬT trong `metaEntities` (backend là nguồn sự thật; nhóm
 *   khai dư một mã cũng không sao — bỏ qua).
 * - Bỏ nhóm rỗng (không entity nào của nhóm đó tồn tại).
 * - Entity không thuộc nhóm nào → dồn vào nhóm cuối "Khác", giữ nguyên nhãn.
 */
export function buildPermissionTree(metaEntities: MetaEntity[]): PermissionGroup[] {
  const byKey = new Map(metaEntities.map((e) => [e.key, e]))
  const used = new Set<string>()
  const groups: PermissionGroup[] = []

  for (const def of PERMISSION_GROUPS) {
    const entities: MetaEntity[] = []
    for (const key of def.entities) {
      const found = byKey.get(key)
      if (found && !used.has(key)) {
        entities.push(found)
        used.add(key)
      }
    }
    if (entities.length > 0) {
      groups.push({ id: def.id, title: def.title, entities })
    }
  }

  const leftovers = metaEntities.filter((e) => !used.has(e.key))
  if (leftovers.length > 0) {
    groups.push({ id: '__other__', title: 'Khác', entities: leftovers })
  }

  return groups
}

/**
 * Lọc cây theo từ khóa — ô tìm của ma trận phân quyền.
 *
 * Luật:
 * - Từ khóa rỗng → trả NGUYÊN cây (cùng tham chiếu, không dựng lại).
 * - Khớp TÊN PHÂN HỆ → giữ cả nhóm với đủ mục con. Gõ "thu mua" là muốn xem cả
 *   phân hệ Thu mua, chứ không phải chỉ những mục có chữ "thu mua" trong tên.
 * - Không khớp tên nhóm → chỉ giữ mục con khớp; hết mục thì bỏ nhóm.
 *
 * So khớp bỏ qua DẤU và hoa thường (`matchesVietnamese`): người Việt gõ ô tìm
 * thường không bỏ dấu, so thô thì "don mua hang" không ra "Đơn mua hàng" và
 * người dùng kết luận là màn không có mục đó.
 *
 * Tìm cả theo **mã entity** (`purchase_order`) chứ không chỉ nhãn: mã là thứ
 * nằm trong tài liệu phân quyền và trong thông báo lỗi 403, nên người đi tra
 * một khóa quyền có mã trong tay chứ chưa chắc biết nhãn tiếng Việt của nó.
 */
export function filterPermissionTree(
  groups: PermissionGroup[],
  keyword: string,
): PermissionGroup[] {
  if (!keyword.trim()) return groups

  const result: PermissionGroup[] = []
  for (const group of groups) {
    if (matchesVietnamese(group.title, keyword)) {
      result.push(group)
      continue
    }
    const entities = group.entities.filter((entity) =>
      matchesVietnamese([entity.label, entity.key], keyword),
    )
    if (entities.length > 0) result.push({ ...group, entities })
  }
  return result
}
