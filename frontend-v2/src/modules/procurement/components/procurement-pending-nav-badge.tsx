import type { MenuBadgeCounts } from '../api/procurement-dashboard-api'
import { useProcurementMenuBadges } from '../hooks/use-procurement-menu-badges'

type PendingEntity = keyof MenuBadgeCounts

/**
 * Viên số trên mục menu Thu mua — số phiếu đang CHỜ DUYỆT của mục đó (duoc-CR-723, phiếu hỗ trợ TK06112601).
 *
 * Cùng khuôn `ModuleNavItem.badge` của các viên số có sẵn (`ProfileChangeRequestNavBadge`,
 * `DocumentApprovalNavBadge`): đứng cuối dòng (`ml-auto`), không có việc thì không hiện. Khác ở MÀU — nền đỏ
 * chữ trắng theo đúng phiếu yêu cầu, cùng màu với bóng đỏ trên menu giao diện cũ (thumua) để người dùng hai
 * bản đọc ra cùng một tín hiệu.
 */
function PendingNavBadge({ entity }: { entity: PendingEntity }) {
  const { data } = useProcurementMenuBadges()
  const count = data?.[entity] ?? 0
  if (count <= 0) return null
  return (
    <span
      className="ml-auto rounded-full bg-destructive px-1.5 py-0.5 text-[0.6875rem] leading-none font-semibold text-white tabular-nums"
      aria-label={`${count} phiếu đang chờ duyệt`}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

//  `ModuleNavItem.badge` nhận một component KHÔNG prop, nên mỗi mục menu một component bọc.
export function SurveyRequestPendingNavBadge() {
  return <PendingNavBadge entity="survey_request" />
}

export function PurchaseRequestPendingNavBadge() {
  return <PendingNavBadge entity="purchase_request" />
}

export function PurchaseOrderPendingNavBadge() {
  return <PendingNavBadge entity="purchase_order" />
}

export function SurveyPendingNavBadge() {
  return <PendingNavBadge entity="survey" />
}
