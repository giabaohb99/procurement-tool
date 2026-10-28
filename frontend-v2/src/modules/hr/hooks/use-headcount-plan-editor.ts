import { useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { getCrudDetailKey } from '@/shared/crud'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { HR_COST_TEMPLATE_API_PATH, hrCostApi } from '../api/hr-cost-template-api'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import {
  addDraftLine,
  applyTemplateToDraft,
  changeDraftPeriod,
  createEmptyDraft,
  draftFromDetail,
  type HeadcountPlanDraft,
} from '../utils/headcount-plan-draft'
import { describeActualNotes } from '../utils/headcount-plan-actual-notes'
import { resolveCanSeeMoney } from '../utils/headcount-plan-money'
import { buildCreatePayload, buildDraftPayload, buildPlanPayload } from '../utils/headcount-plan-payload'
import { buildSubPeriods, listPeriodMonths } from '../utils/headcount-plan-periods'
import {
  useHeadcountPlan,
  useHeadcountPlanCompute,
  useHeadcountPlanPositionStats,
  useSaveHeadcountPlan,
} from './use-headcount-plans'

/**
 * TOÀN BỘ trạng thái của trang kế hoạch nhân sự (duoc-CR-690): bản nháp, xem trước bằng `/compute`,
 * số «Đang có», chép khoản từ mẫu, lưu. Tách khỏi trang để trang chỉ còn việc bày bốn khối.
 */
export function useHeadcountPlanEditor(planId: number, currentYear: number) {
  const { can } = usePermission()
  const queryClient = useQueryClient()
  const detailQuery = useHeadcountPlan(planId)
  const detail = detailQuery.data
  const isNew = planId <= 0

  //  Vào lại trang mà kế hoạch đã có trong bộ đệm thì lấy luôn ở lượt render đầu — lượt đầu
  //  `useHasChanged` luôn trả `false` nên nhịp đổ bên dưới không chạy (bẫy bao-CR-492).
  const [draft, setDraft] = useState<HeadcountPlanDraft>(() =>
    detail && !isNew ? draftFromDetail(detail) : createEmptyDraft(currentYear),
  )
  //  Đổ lại khi chuyển sang MỘT KẾ HOẠCH KHÁC — theo id, không theo tham chiếu: nạp lại bộ đệm
  //  (quay lại tab trình duyệt) không được xóa thứ người dùng đang gõ dở.
  if (useHasChanged(detail?.id ?? 0) && detail && !isNew) setDraft(draftFromDetail(detail))

  const readOnly = !can('headcount_plan', isNew ? 'create' : 'write')
  const canReadContracts = can('labor_contract', 'read')

  //  Bản xem trước dựng theo cờ tiền của lượt trước: cờ đổi thì payload đổi đúng một lần, không vòng.
  const [moneyHint, setMoneyHint] = useState(canReadContracts)
  //  Ô căn cứ / ghi chú không đổi con số → để trống trong bản xem trước, gõ số căn cứ không gọi lại bộ tính.
  const draftPayload = useMemo(
    () => ({ ...buildDraftPayload(draft, moneyHint), basis_no: '', basis_date: null, approver_employee_id: 0, note: '' }),
    [draft, moneyHint],
  )
  const compute = useHeadcountPlanCompute(draftPayload, draft.company_id > 0)
  const canSeeMoney = resolveCanSeeMoney(canReadContracts, detail, compute.data)
  if (canSeeMoney !== moneyHint) setMoneyHint(canSeeMoney)

  const stats = useHeadcountPlanPositionStats(draft.company_id, draft.department_id)
  const periods = useMemo(() => buildSubPeriods(draft.period_type, draft.period_no), [draft.period_type, draft.period_no])
  const periodMonths = useMemo(
    () => listPeriodMonths(draft.period_type, draft.period_no),
    [draft.period_type, draft.period_no],
  )

  //  Thực tế chỉ có ở kế hoạch ĐÃ LƯU (GET chi tiết, không có ở `/compute`) và tính theo bản đã lưu.
  const actual = isNew ? null : (detail?.computed?.actual ?? null)
  const actualNotes = useMemo(() => {
    if (!actual) return []
    const names = new Map((detail?.cost_items ?? []).map((i) => [i.code, i.name]))
    return describeActualNotes(actual, detail?.computed?.periods ?? periods, names)
  }, [actual, detail, periods])

  const save = useSaveHeadcountPlan()
  const once = useSingleFlight()

  const patch = (p: Partial<HeadcountPlanDraft>) => setDraft((d) => ({ ...d, ...p }))
  const changePeriod = (c: { period_type?: number; period_no?: number }) => setDraft((d) => changeDraftPeriod(d, c))
  const addLine = (positionId: number, name: string) => setDraft((d) => addDraftLine(d, positionId, name))
  /** Sửa bảng khoản = thôi chép lại theo mẫu khi đổi kỳ, và lúc tạo phải gửi bộ khoản đã sửa lên. */
  const changeCostItems = (items: HrCostItem[], lines: HeadcountPlanLine[]) =>
    setDraft((d) => ({ ...d, cost_items: items, lines, cost_items_edited: true, skipped_items: [] }))

  /** Chọn mẫu lúc tạo: CHÉP bộ khoản theo kỳ đang chọn để người dùng thấy, sửa và xem trước ngay. */
  const chooseTemplate = async (templateId: number) => {
    patch({ template_id: templateId })
    try {
      const tpl = await queryClient.fetchQuery({
        queryKey: getCrudDetailKey(HR_COST_TEMPLATE_API_PATH, templateId),
        queryFn: () => hrCostApi.getTemplate(templateId),
      })
      setDraft((d) => (d.template_id === templateId ? applyTemplateToDraft(d, templateId, tpl.items ?? []) : d))
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  /** Nạp lại bản nháp từ máy chủ (sau khi nhập CSV dòng vị trí) — bỏ phần đang sửa dở. */
  const reload = async () => {
    const fresh = await detailQuery.refetch()
    if (fresh.data) setDraft(draftFromDetail(fresh.data))
  }

  /** Lưu rồi gọi `onSaved(id)` — trang tạo mới dùng id đó để chuyển sang trang của kế hoạch. */
  const submit = (onSaved: (id: number) => void) =>
    once(async () => {
      if (!draft.company_id) return void toast.error('Chọn pháp nhân trước khi lưu.')
      if (isNew && !draft.template_id) return void toast.error('Chọn mẫu khoản chi phí trước khi lưu.')
      try {
        const saved = await save.mutateAsync({
          id: planId,
          create: buildCreatePayload(draft, canSeeMoney),
          payload: buildPlanPayload(draft, canSeeMoney),
        })
        //  Đổ lại đúng thứ máy chủ đã lưu (id dòng, tiền giữ nguyên của người không thấy tiền…).
        if (!isNew) setDraft(draftFromDetail(saved))
        onSaved(saved.id)
      } catch {
        //  `httpClient` đã bật toast câu lỗi của máy chủ (422 luật tính, 403 tiền, 409 trùng kỳ).
      }
    })

  return {
    detail,
    isLoading: !isNew && detailQuery.isLoading,
    notFound: !isNew && !detailQuery.isLoading && !detail,
    isNew,
    draft,
    patch,
    changePeriod,
    changeCostItems,
    addLine,
    chooseTemplate,
    submit,
    reload,
    saving: save.isPending,
    readOnly,
    canSeeMoney,
    compute,
    computeError: compute.error ? extractErrorMessage(compute.error) : undefined,
    stats: stats.data ?? [],
    periods,
    periodMonths,
    actual,
    actualNotes,
  }
}
