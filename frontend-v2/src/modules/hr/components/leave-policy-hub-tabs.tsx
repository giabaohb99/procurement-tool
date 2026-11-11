import { cn } from '@/shared/utils/cn'
import { buildLeavePolicyHubHref, type LeavePolicyHubTab, type LeavePolicyHubTabDef } from '../utils/leave-policy-hub-tabs'
import { LIST_SECTION_TABS_STICKY } from '../utils/list-sticky'
import { SubTabLink } from './leave-section-tabs'

interface LeavePolicyHubTabsProps {
  tabs: readonly LeavePolicyHubTabDef[]
  active: LeavePolicyHubTab
}

/**
 * Thanh hai tab Phân bổ · Chính sách của màn Chính sách nghỉ phép (duoc-CR-750). Cùng kiểu gạch chân với thanh
 * Thiết lập nghỉ phép (`SubTabLink`) và cùng mốc ghim ở khổ điện thoại (`LIST_SECTION_TABS_STICKY` đi cặp với
 * `LIST_SECTION_TOOLBAR_STICKY` của thanh công cụ bên dưới).
 *
 * Tab là LINK (đổi `?tab=`), không phải `<Tabs>` của Radix: mỗi tab là một màn danh sách riêng với bộ lọc riêng
 * trên URL, bấm sang tab kia thì bỏ bộ lọc của tab cũ — dùng chung một chuỗi truy vấn là lọc `is_active` của gói
 * dính sang bảng phân bổ.
 *
 * Chỉ một tab được phép thì vẫn dựng (khác thanh Thiết lập): tab là chữ duy nhất nói bảng đang bày là gói hay là
 * phân bổ, vì tiêu đề màn giống nhau.
 *
 * ⚠️ KHÔNG gắn `overflow-x-auto` cho hàng tab: `SubTabLink` dùng `-mb-px` để gạch chân đè lên viền dưới của hàng,
 * mà khung cuộn cắt phần tràn đó (và đẻ thanh cuộn dọc 1px). Hai nhãn ngắn vừa cả màn 360px nên không cần cuộn.
 */
export function LeavePolicyHubTabs({ tabs, active }: LeavePolicyHubTabsProps) {
  return (
    <div className={cn('shrink-0 pb-3', LIST_SECTION_TABS_STICKY)}>
      <nav className="flex flex-wrap items-center gap-4 border-b" aria-label="Chính sách nghỉ phép">
        {tabs.map((tab) => (
          <SubTabLink key={tab.key} to={buildLeavePolicyHubHref(tab.key)} active={tab.key === active}>
            {tab.label}
          </SubTabLink>
        ))}
      </nav>
    </div>
  )
}
