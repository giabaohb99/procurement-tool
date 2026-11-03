import { useCallback, useMemo, useState } from 'react'
import { ArrowLeft, ListChecks, Loader2, Send } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { toDateInputValue } from '@/shared/utils/format-date'
import { LeavePolicyBulkPreviewTable } from '../components/leave-policy-bulk-preview-table'
import { LeavePolicyBulkResult } from '../components/leave-policy-bulk-result'
import { LeavePolicyBulkSettingsForm } from '../components/leave-policy-bulk-settings-form'
import { useLeaveTypes } from '../hooks/use-leave'
import { useBulkLeavePolicyAssignment, useLeavePolicyBulkPreview } from '../hooks/use-leave-policy'
import { useSingleFlight } from '../hooks/use-single-flight'
import type { PolicyBulkResult, PolicyPreviewResult } from '../types/leave-policy'
import {
  BULK_MAX,
  buildBulkPreviewPayload,
  bulkPreviewSignature,
  createBulkSettings,
  selectableEmployeeIds,
  validateBulkSettings,
} from '../utils/leave-policy-bulk'
import { buildLeaveTypeNameLookup } from '../utils/leave-policy-display'

/**
 * PHÂN BỔ HÀNG LOẠT — `/hr/leave-policy-assignments/bulk` (duoc-CR-717, kiểu Leave Control Panel của ERPNext).
 *
 * Ba bước: chọn chính sách + ngày → lọc nhân sự → "Xem danh sách" (`/preview`, tối đa 500 người) → tick →
 * "Phân bổ N người" (`/bulk`). Đổi bất kỳ ô nào ảnh hưởng xem trước (trừ "Tính lại") sau khi đã xem thì nút
 * Phân bổ khóa lại tới khi xem lại — không gán theo danh sách cũ. Gác `leave_balance.write` (mục menu ẩn).
 */
export function LeavePolicyBulkAssignPage() {
  const navigate = useNavigate()
  const [settings, setSettings] = useState(() => createBulkSettings(toDateInputValue(new Date())))
  const [preview, setPreview] = useState<{ signature: string; data: PolicyPreviewResult } | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [result, setResult] = useState<PolicyBulkResult | null>(null)

  const previewMutation = useLeavePolicyBulkPreview()
  const bulk = useBulkLeavePolicyAssignment()
  const runPreview = useSingleFlight()
  const runAssign = useSingleFlight()
  const { data: typeData } = useLeaveTypes(false)
  const typeName = useMemo(() => buildLeaveTypeNameLookup(typeData?.items), [typeData])

  const settingsError = validateBulkSettings(settings)
  const stale = preview !== null && preview.signature !== bulkPreviewSignature(settings)
  const items = useMemo(() => preview?.data.items ?? [], [preview])

  const loadPreview = () =>
    runPreview((release) => {
      if (settingsError) return release()
      const signature = bulkPreviewSignature(settings)
      previewMutation.mutate(buildBulkPreviewPayload(settings), {
        onSuccess: (data) => {
          setPreview({ signature, data })
          //  Mặc định chọn sẵn mọi người phân bổ được — đúng thói quen "lọc xong là gán cả nhóm".
          setSelected(new Set(selectableEmployeeIds(data.items)))
          setResult(null)
        },
        onSettled: release,
      })
    })

  const toggle = useCallback((id: number) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])
  const toggleAll = useCallback(() => {
    const ids = selectableEmployeeIds(items)
    setSelected((prev) => (ids.every((id) => prev.has(id)) ? new Set() : new Set(ids)))
  }, [items])

  //  Chỉ đếm id còn nằm trong danh sách hiện tại + không vướng — bộ chọn cũ không lọt sang lượt xem mới.
  const chosen = selectableEmployeeIds(items).filter((id) => selected.has(id))
  const canAssign = !stale && !settingsError && chosen.length > 0 && chosen.length <= BULK_MAX && !bulk.isPending

  const assign = () =>
    runAssign((release) => {
      if (!canAssign) return release()
      bulk.mutate(
        {
          policy_id: settings.policyId,
          effective_from: settings.from,
          effective_to: settings.to || null,
          close_previous: settings.closePrevious,
          recalc_current_year: settings.recalc,
          employee_ids: chosen,
        },
        {
          onSuccess: (data) => {
            setResult(data)
            //  Danh sách cũ đã lỗi thời (người vừa gán nay có chính sách) — bắt xem lại.
            setPreview(null)
            setSelected(new Set())
          },
          onSettled: release,
        },
      )
    })

  return (
    <PageContainer>
      <PageHeader
        leading={
          <Button
            type="button"
            variant="outline"
            size="icon"
            title="Về danh sách phân bổ"
            aria-label="Về danh sách phân bổ"
            onClick={() => navigate(appRoutes.hr.leavePolicyAssignments)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        title="Phân bổ chính sách hàng loạt"
        description="Lọc nhóm nhân sự, xem trước hạn mức năm nay thay đổi ra sao, rồi phân bổ một lần (tối đa 500 người)."
      />

      <div className="space-y-4">
        {result && <LeavePolicyBulkResult result={result} onDismiss={() => setResult(null)} />}

        <LeavePolicyBulkSettingsForm value={settings} onChange={setSettings} />

        <div className="flex flex-wrap items-center gap-3">
          <Button type="button" onClick={loadPreview} disabled={Boolean(settingsError) || previewMutation.isPending}>
            {previewMutation.isPending ? <Loader2 className="size-4 animate-spin" /> : <ListChecks className="size-4" />}
            Xem danh sách
          </Button>
          {settingsError && <span className="text-sm text-muted-foreground">{settingsError}</span>}
        </div>

        {preview && (
          <Card className="gap-3">
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
              <CardTitle className="text-base">
                3. Danh sách xem trước · {preview.data.total} người khớp
              </CardTitle>
              <Button type="button" onClick={assign} disabled={!canAssign}>
                <Send className="size-4" />
                Phân bổ {chosen.length} người
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {stale && (
                <p role="alert" className="text-sm text-warning">
                  Bạn vừa đổi chính sách, ngày hoặc bộ lọc — bấm <strong>Xem danh sách</strong> lại trước khi phân bổ.
                </p>
              )}
              {preview.data.truncated && (
                <p className="text-sm text-warning">
                  Chỉ hiện {BULK_MAX} người đầu (theo mã nhân viên) trên {preview.data.total} — thu hẹp bộ lọc để
                  phân bổ phần còn lại.
                </p>
              )}
              <LeavePolicyBulkPreviewTable
                items={items}
                selectedIds={selected}
                onToggle={toggle}
                onToggleAll={toggleAll}
                typeName={typeName}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </PageContainer>
  )
}
