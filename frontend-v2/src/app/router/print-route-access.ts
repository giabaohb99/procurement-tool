import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Quyền để MỞ một trang in (NF-20). Trang in đứng NGOÀI `ModuleLayout` nên không
 * đi qua gác menu — không khai ở đây thì ai đăng nhập cũng gõ link vào được.
 *
 *  - `{ entity, action }` — đối chiếu đúng `require(...)` của endpoint mà trang gọi.
 *  - `{ flow }` — backend cố ý KHÔNG đòi quyền vai trò mà gác theo "đang có việc
 *    duyệt trên phiếu" / quyền trên chính văn bản; chặn ở giao diện sẽ cấm nhầm
 *    người duyệt. Phải ghi lý do; backend vẫn là chốt chặn.
 */
export type PrintRouteAccess =
  | { entity: PermissionEntity; action: PermissionAction }
  | { flow: string }

/** Khóa là đường dẫn route y như khai trong `appRoutes` (tham số là `:id`). */
export const PRINT_ROUTE_ACCESS: Readonly<Record<string, PrintRouteAccess>> = {
  [appRoutes.procurement.purchaseRequestPrint(':id')]: {
    entity: 'purchase_request',
    action: 'read', // GET /api/purchase-requests/{id}
  },
  [appRoutes.procurement.purchaseRequestSupplierPrint(':id')]: {
    entity: 'purchase_request',
    action: 'read', // trang còn tự gác thêm supplier:read (N-17)
  },
  [appRoutes.procurement.purchaseRequestPrintFromPo(':id')]: {
    entity: 'purchase_order',
    action: 'print', // GET /api/purchase-orders/{id}/purchase-request
  },
  [appRoutes.procurement.purchaseOrderPrint(':id')]: {
    entity: 'purchase_order',
    action: 'print', // GET /api/purchase-orders/{id}/print
  },
  [appRoutes.procurement.purchaseOrderGoodsPrint(':id')]: {
    entity: 'purchase_order',
    action: 'print',
  },
  [appRoutes.procurement.purchaseOrderImportPrint(':id')]: {
    entity: 'purchase_order',
    action: 'print',
  },
  [appRoutes.procurement.importLandedCostPrint]: {
    entity: 'report',
    action: 'read', // GET /api/reports/import-landed-cost
  },
  [appRoutes.finance.paymentRequestPrint(':id')]: {
    entity: 'payment_request',
    action: 'print', // GET /api/payment-requests/{id}/print
  },
  [appRoutes.document.documentPrint(':id')]: {
    flow: 'Backend gác lớp văn bản (doc_reader + ensure_can): người duyệt trong luồng không có vai trò Văn bản vẫn phải mở được.',
  },
  [appRoutes.vehicleBooking.print(':id')]: {
    flow: 'GET /api/vehicle-bookings/{id} chỉ đòi đăng nhập: người đang giữ việc duyệt trên phiếu đọc được dù không có vehicle_booking.read (bao-CR-584, booking_for_approver).',
  },
  [appRoutes.approvalSeal.print(':id')]: {
    flow: 'Backend cho người đang giữ việc duyệt trên phiếu đọc dù không có seal_request.read (bao-CR-584).',
  },
  [appRoutes.hr.employeeInfoPrint(':id')]: {
    entity: 'employee',
    action: 'read', // GET /api/employees/{id} (+ hai bảng con khi có employee_sensitive.read)
  },
  [appRoutes.hr.myEmployeeInfoPrint]: {
    flow: 'Phiếu của CHÍNH MÌNH: GET /api/employees/me, /me/contacts, /me/families chỉ đòi đăng nhập, hồ sơ lấy từ phiên — 9/19 vai trò không có employee.read nhưng vẫn phải in được phiếu của mình.',
  },
  [appRoutes.hr.leaveRequestPrint(':id')]: {
    entity: 'leave_request',
    action: 'read', // GET /api/leave/requests/{id}
  },
}
