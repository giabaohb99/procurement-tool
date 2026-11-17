import {
  BriefcaseBusiness,
  Building,
  Building2,
  CalendarDays,
  DoorOpen,
  FileSignature,
  ScrollText,
  Settings2,
  SlidersHorizontal,
} from 'lucide-react'

import type { ModuleNavItem } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { workScheduleSetupNavItems } from './work-schedule-module-entries'

/**
 * Mục **Thiết lập** của menu Nhân sự (duoc-CR-754): gom mọi màn cấu hình nền vào MỘT dòng menu (không sổ xuống, mục
 * con thành dải tab phẳng) thay vì rải ở Master, Nghỉ phép, Lịch làm việc và Đặt phòng họp như trước.
 *
 * ⚠️ Mỗi mục con GIỮ NGUYÊN `entity` / `entities` / `action` / `manage` / `matchPaths` như lúc còn ở cụm cũ: bộ gác
 * route (`canAccessRoute`) duyệt cả mục con và khớp theo đường dẫn dài nhất, nên dời cụm không đổi quyền của màn nào.
 * Mục cha có con thì chỉ hiện khi có ÍT NHẤT MỘT con được phép; bấm vào mục cha mở mục con đầu tiên được phép.
 * Mục con KHÔNG hiện trên menu (`childrenAsTabs`) mà thành dải tab ở đầu từng màn — `components/hr-setup-tabs.tsx`.
 *
 * duoc-CR-773 (anh Được chốt 17/11/2026): cụm **Danh mục** (Phòng ban, Công ty, Chức vụ, Mẫu hợp đồng) gom vào đây thành
 * bốn tab ĐẦU — menu Nhân sự không còn hai dòng na ná nhau. Bốn mục giữ nguyên khóa quyền như lúc ở cụm Danh mục:
 * Phòng ban / Công ty / Mẫu hợp đồng chỉ cần ĐỌC (`entity`), Chức vụ cần QUẢN LÝ (`manage`).
 */
export const hrSetupNavItem: ModuleNavItem = {
  label: 'Thiết lập',
  path: appRoutes.hr.settings,
  icon: SlidersHorizontal,
  entities: [
    'department',
    'company',
    'job_position',
    'labor_contract_template',
    'setting',
    'leave_balance',
    'leave_type',
    'holiday',
    'work_schedule',
    'meeting_room',
  ],
  //  Anh Được chốt 12/11/2026: MỘT mục menu, vào trong chia tab (`components/hr-setup-tabs.tsx`) — không sổ xuống.
  childrenAsTabs: true,
  children: [
    { label: 'Phòng ban', path: appRoutes.hr.departments, icon: Building, entity: 'department' },
    { label: 'Công ty', path: appRoutes.hr.companies, icon: Building2, entity: 'company' },
    {
      //  Mọi vai trò ĐỌC được danh mục chức vụ (ô chọn cần thế), nhưng màn quản lý chỉ cho người SỬA được.
      label: 'Chức vụ',
      path: appRoutes.hr.jobPositions,
      icon: BriefcaseBusiness,
      entity: 'job_position',
      manage: true,
    },
    {
      //  Hàng rào cho cả `/hr/labor-contract-templates/*` (trình soạn, danh sách biến) vì gác khớp theo ranh giới `/`.
      label: 'Mẫu hợp đồng',
      path: appRoutes.hr.laborContractTemplates,
      icon: FileSignature,
      entity: 'labor_contract_template',
    },
    {
      //  duoc-CR-713: Cài đặt nhân sự (kiểu HR Settings của ERPNext). ⚠️ `entity` ở đây LÀ hàng rào của route
      //  (gác điều hướng mặc định MỞ); backend `/api/settings` gác `setting.read` / `setting.write`.
      label: 'Cài đặt nhân sự',
      path: appRoutes.hr.settings,
      icon: Settings2,
      entity: 'setting',
    },
    {
      //  duoc-CR-750: màn gộp HAI TAB — Phân bổ (`leave_balance.write`) · Chính sách (`leave_type.write`). ⚠️ Mục này
      //  LÀ hàng rào của route, nên phải hiện khi có ÍT NHẤT một trong hai quyền và tắt khi thiếu cả hai: `entities` =
      //  "bất kỳ khóa nào", `action: 'write'` áp cho TỪNG khóa (`module-visibility.entityAllowed`) — ra đúng
      //  `leave_balance.write || leave_type.write`, cùng luật hiện tab ở `utils/leave-policy-hub-tabs.ts` (bài kiểm
      //  canh hai luật bằng nhau). KHÔNG gác `read`: seed cấp `leave_balance.read` phạm vi "của tôi" cho MỌI nhân viên.
      //  Không dùng `manage` vì nó mở cả người chỉ có `create`/`delete` trên quỹ phép. Trang hàng loạt và chi tiết gói
      //  có mục ẩn riêng ở `routes.tsx`.
      label: 'Chính sách nghỉ phép',
      path: appRoutes.hr.leavePolicyAssignments,
      icon: ScrollText,
      entities: ['leave_balance', 'leave_type'],
      action: 'write',
      matchPaths: [appRoutes.hr.leavePolicyBulkAssign, appRoutes.hr.leavePolicies],
    },
    {
      //  Ba tab Loại nghỉ · Lịch ngày lễ · Ngày cấm nghỉ (`components/leave-section-tabs.tsx`).
      label: 'Loại nghỉ và ngày lễ',
      path: appRoutes.hr.leaveTypes,
      icon: CalendarDays,
      entities: ['leave_type', 'holiday'],
      manage: true,
      matchPaths: [appRoutes.hr.holidays, appRoutes.hr.leaveBlocks],
    },
    ...workScheduleSetupNavItems,
    {
      //  Chỉ quản trị viên phòng họp: mọi vai trò đọc được danh mục (ô chọn phòng cần) nhưng vào màn quản lý phải sửa được.
      label: 'Danh mục phòng họp',
      path: appRoutes.hr.meetingRooms,
      icon: DoorOpen,
      entity: 'meeting_room',
      manage: true,
    },
  ],
}
