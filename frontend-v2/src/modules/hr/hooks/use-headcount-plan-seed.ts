import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import type { HeadcountPlanSeed } from '../utils/headcount-plan-draft'
import { buildSuggestedCostItems, pickSuggestedTemplateId } from '../utils/hr-cost-item-presets'
import { useActiveHrCostTemplates, useHrCostGroups, useHrCostTemplate } from './use-hr-cost-templates'

/**
 * NGUỒN CHI PHÍ ĐIỀN SẴN cho kế hoạch MỚI (duoc-CR-690 — trang không còn ô chọn mẫu): khoản của «Mẫu
 * gợi ý» (không có thì mẫu đang dùng đầu tiên); máy chủ không có mẫu nào → bộ gợi ý dựng ở giao diện.
 *
 * Trả `seed = null` khi còn đang tải (trang chặn nút Tạo tới lúc có). Nhóm chi phí cũng phải tải xong để
 * khoản tự dựng được xếp đúng nhóm. Kế hoạch đã lưu (`enabled = false`) không gọi gì cả.
 */
export function useHeadcountPlanSeed(enabled: boolean) {
  const { can } = usePermission()
  const allowed = enabled && can('headcount_plan', 'read')
  const groups = useHrCostGroups(allowed)
  const templates = useActiveHrCostTemplates(allowed)
  const templateId = templates.data ? pickSuggestedTemplateId(templates.data.items ?? []) : 0
  const template = useHrCostTemplate(allowed ? templateId : 0)
  const groupItems = groups.data?.items

  const seed = useMemo<HeadcountPlanSeed | null>(() => {
    if (!allowed || groups.isPending || templates.isPending) return null
    //  Đọc danh sách mẫu lỗi → coi như không có mẫu: người lập vẫn có bộ gợi ý để làm tiếp.
    if (templateId > 0 && template.isPending) return null
    if (templateId > 0 && template.data) {
      return { key: `t${templateId}`, templateId, items: template.data.items ?? [] }
    }
    return { key: 'ui', templateId: 0, items: buildSuggestedCostItems(groupItems ?? []) }
  }, [allowed, groups.isPending, templates.isPending, templateId, template.isPending, template.data, groupItems])

  return { seed, groups: groupItems ?? [] }
}
