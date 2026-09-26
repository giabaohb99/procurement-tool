import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { Company } from '@/modules/hr/types/company'
import type { Department } from '@/modules/hr/types/department'
import type { Employee } from '@/modules/hr/types/employee'
import type {
  DeptHeadCandidate,
  PurchaseRequestDetail,
} from '../types/purchase-request-detail'
import { resolveShownDeptHead } from '../utils/dept-head-display'
import {
  ASSIGN_OTHER_DEPT_LABEL,
  HANDLING_DEPT_HINT,
  SHARED_PURCHASING_LABEL,
  handlingDeptLabel,
  handlingDeptOptions,
  isHandlingDeptAssigned,
} from '../utils/handling-dept-display'
import { ApproverSelect } from './approver-select'

interface InfoCardProps {
  /** bao-CR-499 — người duyệt được chứng từ này (nguồn ô «Trưởng phòng phê duyệt»). */
  approverCandidates?: DeptHeadCandidate[]
  data: PurchaseRequestDetail
  editing: boolean
  /** bao-CR-488 — đang LẬP phiếu mới: ô Phòng xử lý ẩn sau ô tick «Nhờ phòng khác xử lý». */
  isNew?: boolean
  /** Sau khi phiếu duyệt, quản lý vẫn được đổi cờ Gấp và backend đồng bộ sang ĐMH. */
  urgentEditable?: boolean
  onUrgentChange?: (checked: boolean) => void
  companies?: Company[]
  employees?: Employee[]
  /** bao-CR-414 — danh mục phòng ban cho ô «Nhờ phòng xử lý»; rỗng thì ô chỉ hiện chữ. */
  departments?: Department[]
  /** CR-071 — ứng viên đứng tên TBP trên phiếu; rỗng thì ô về dạng chữ như cũ. */
  deptHeadCandidates?: DeptHeadCandidate[]
  /** bao-CR-474 — trưởng phòng mặc định của phòng, hiện khi phiếu chưa chọn TBP. */
  defaultDeptHead?: { head_of_dept: string; head_of_dept_id: number }
  onChange: (changes: Partial<PurchaseRequestDetail>) => void
}

/**
 * Thẻ "Thông tin chung" — GIỮ NGUYÊN thứ tự và tên nhãn của bản `frontend` cũ
 * (`PurchaseRequestDetail.tsx`) để người dùng không phải học lại màn hình.
 *
 * Bộ phận YC luôn khóa: backend tự điền theo hồ sơ nhân sự của người yêu cầu,
 * sửa tay ở đây là sai nguồn dữ liệu.
 *
 * Trưởng bộ phận thì KHÁC (CR-071): chọn được trong số những người duyệt được
 * phiếu này — nhưng CHỈ để lưu + in, không khóa quyền duyệt của ai.
 */
export function PurchaseRequestInfoCard({
  data,
  editing,
  isNew = false,
  urgentEditable,
  onUrgentChange,
  companies = [],
  employees = [],
  approverCandidates = [],
  departments = [],
  deptHeadCandidates = [],
  defaultDeptHead,
  onChange,
}: InfoCardProps) {
  const { can } = usePermission()
  // bao-CR-474 — ô TBP LUÔN hiện một người, xem `resolveShownDeptHead`.
  const { head_of_dept_id: shownHeadId, head_of_dept: shownHeadName } = resolveShownDeptHead(
    data,
    editing,
    defaultDeptHead,
  )
  // bao-CR-480: một ô «Phòng xử lý» cho cả ba chứng từ — luật nhãn/mục chọn ở util dùng chung.
  const handlingDeptOptionList = handlingDeptOptions(departments, data.handler_dept_id)
  const handlingDeptText = handlingDeptLabel(data.handler_dept_id, data.handler_dept_name, departments)
  const handlingDeptAssigned = isHandlingDeptAssigned(data)
  // bao-CR-318: đường về YCBG nguồn — chỉ thành link khi người xem đọc được YCBG,
  // không thì hiện mã dạng chữ (bấm vào chỉ ăn 403).
  const surveyRequestLinkable = Boolean(data.survey_request_id) && can('survey_request', 'read')
  // bao-CR-422: một phiếu có thể gom nhiều YCBG. Ô này chỉ đủ chỗ cho phiếu đầu, nên khi
  // còn phiếu khác phải nói ra — im lặng là người đọc tưởng phiếu chỉ có một nguồn. Danh
  // sách đủ nằm ở thẻ "Chứng từ liên quan" (`purchase-request-linked-documents-card.tsx`).
  const otherSurveyRequestCount = Math.max((data.survey_requests?.length ?? 0) - 1, 0)
  return (
    <Card className="gap-4 py-4">
      {/* Cùng một khuôn với các thẻ khác trên trang — xem ghi chú `pb-3!` ở
          `purchase-request-attachments-card.tsx`. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Thông tin chung
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-x-4 gap-y-3 px-4 md:grid-cols-2">
        <Field label="Mã phiếu yêu cầu">{data.code || '— (phiếu nháp)'}</Field>
        <Field label="Ngày tạo">{formatDateTime(data.created_at) || '—'}</Field>

        {data.survey_request_code && (
          <Field label="Từ yêu cầu báo giá">
            {surveyRequestLinkable && data.survey_request_id ? (
              <Link
                className="inline-flex items-center gap-1 text-primary hover:underline"
                to={appRoutes.procurement.surveyRequestDetail(data.survey_request_id)}
              >
                {data.survey_request_code}
                <ExternalLink className="size-3.5" />
              </Link>
            ) : (
              data.survey_request_code
            )}
            {otherSurveyRequestCount > 0 && (
              <span className="text-muted-foreground ml-1 text-xs">
                và {otherSurveyRequestCount} phiếu nữa
              </span>
            )}
          </Field>
        )}

        <div className="space-y-1.5">
          <Label>
            Ngày tiếp nhận
            {/* bao-CR-293/298 (ticket 20): backend TỰ ĐIỀN khi thu mua duyệt điều
                phối — khóa ô nhập, trước lúc đó giá trị chỉ là tạm (ngày lập phiếu) */}
            <span className="text-xs font-normal text-muted-foreground">
              (tự điền khi thu mua duyệt điều phối)
            </span>
          </Label>
          {/* bao-CR-316: đọc cột RIÊNG `received_date` — `request_date` nay chỉ còn nghĩa
              ngày LẬP phiếu. Rỗng = thu mua chưa tiếp nhận (bao-CR-315: bày ngày lập ra
              dưới nhãn này thì người lập tưởng thu mua đã nhận việc rồi). */}
          <ReadOnlyValue>{formatDate(data.received_date) || 'Chưa tiếp nhận'}</ReadOnlyValue>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="pr-company">
            Công ty nhận hóa đơn
            <RequiredMark />
          </Label>
          {editing && companies.length ? (
            <SearchSelect
              id="pr-company"
              searchInTrigger
              value={data.company_id ? String(data.company_id) : ''}
              placeholder="Chọn công ty"
              searchPlaceholder="Gõ để tìm công ty…"
              options={companies.map((company) => ({
                value: String(company.id),
                label: company.name,
              }))}
              onChange={(value) => {
                //  Chọn lại đúng mục đang chọn thì thôi — Radix Select cũ không bắn sự kiện.
                if (value === String(data.company_id)) return
                const company = companies.find((option) => option.id === Number(value))
                onChange({ company_id: Number(value), company_name: company?.name ?? '' })
              }}
            />
          ) : (
            <ReadOnlyValue>{data.company_name || 'Chưa chọn công ty'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="pr-requester">
            Nhân sự YC
            <RequiredMark />
          </Label>
          {editing && employees.length ? (
            <SearchSelect
              id="pr-requester"
              searchInTrigger
              value={data.requester_id ? String(data.requester_id) : ''}
              placeholder="Chọn nhân sự yêu cầu"
              searchPlaceholder="Tìm theo mã hoặc tên nhân sự…"
              options={employees.map((employee) => ({
                value: String(employee.id),
                label: `${employee.code} - ${employee.full_name}`,
              }))}
              onChange={(value) => {
                //  Chọn lại đúng người đang chọn thì thôi: Radix Select cũ không bắn sự kiện,
                //  còn chạy tiếp là ô TBP bị đè về trưởng phòng mặc định.
                if (value === String(data.requester_id)) return
                const employee = employees.find((option) => option.id === Number(value))
                if (!employee) return
                const nextDepartment = employee.department_name || ''
                onChange({
                  requester_id: employee.id,
                  requester: employee.full_name,
                  requester_position: employee.position || '',
                  department: nextDepartment,
                  head_of_dept: employee.manager_name || '',
                  // Đổi sang phòng khác thì TBP đã chọn không còn đúng phòng nữa
                  // -> bỏ đi, người lập chọn lại (CR-071).
                  ...(nextDepartment !== data.department ? { head_of_dept_id: 0 } : {}),
                  company_id: employee.company_id || data.company_id,
                  company_name:
                    companies.find((company) => company.id === employee.company_id)?.name ||
                    data.company_name,
                })
              }}
            />
          ) : editing ? (
            <Input
              value={data.requester}
              placeholder="Nhập nhân sự yêu cầu"
              onChange={(event) => onChange({ requester: event.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.requester || 'Chưa chọn nhân sự'}</ReadOnlyValue>
          )}
        </div>
        <Field label="Bộ phận YC" required>
          {data.department}
        </Field>

        {/*
          bao-CR-414 / bao-CR-480 — «Phòng xử lý»: phòng nào sẽ đi mua cho phiếu này. `0` là
          Thu mua chung; nhà máy tự mua thì backend tự điền phòng nhà máy lúc lập phiếu.
          Chọn phòng thì quản lý thu mua của phòng đó thấy + điều phối được phiếu, còn bộ
          thu mua chung «trừ nhà máy» thì KHÔNG thấy (loại trừ so đúng ô này). Mục «Thu mua
          chung» là MỘT MỤC CHỌN ĐƯỢC mang giá trị `0`, đúng cách backend lưu.
        */}
        {editing && isNew && departments.length ? (
          /* bao-CR-488: lúc LẬP phiếu ô Phòng xử lý ẩn — hệ thống tự chọn mặc định (nhà máy → chính
             phòng mình, còn lại → Thu mua chung). Tick «Nhờ phòng khác xử lý» mới bung ô chọn; đã
             tick thì gửi đúng phòng đã chọn, kể cả Thu mua chung. Màn chi tiết bên dưới giữ như cũ. */
          <div className="space-y-1.5">
            <Label htmlFor="pr-handler-dept">Phòng xử lý</Label>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <Checkbox
                checked={handlingDeptAssigned}
                onCheckedChange={(checked) =>
                  onChange({
                    handler_dept_assigned: checked === true,
                    handler_dept_id: checked === true ? data.handler_dept_id : 0,
                  })
                }
              />
              {ASSIGN_OTHER_DEPT_LABEL}
            </label>
            {handlingDeptAssigned ? (
              <SearchSelect
                id="pr-handler-dept"
                searchInTrigger
                value={String(data.handler_dept_id || 0)}
                placeholder={SHARED_PURCHASING_LABEL}
                searchPlaceholder="Gõ để tìm phòng ban…"
                options={handlingDeptOptionList}
                onChange={(value) => onChange({ handler_dept_id: Number(value) || 0 })}
              />
            ) : (
              <p className="text-xs text-muted-foreground">{HANDLING_DEPT_HINT}</p>
            )}
          </div>
        ) : (
          <div className="space-y-1.5">
            <Label htmlFor="pr-handler-dept">Phòng xử lý</Label>
            {editing && departments.length ? (
              <>
                <SearchSelect
                  id="pr-handler-dept"
                  searchInTrigger
                  value={String(data.handler_dept_id || 0)}
                  placeholder={SHARED_PURCHASING_LABEL}
                  searchPlaceholder="Gõ để tìm phòng ban…"
                  options={handlingDeptOptionList}
                  onChange={(value) => onChange({ handler_dept_id: Number(value) || 0 })}
                />
                <p className="text-xs text-muted-foreground">{HANDLING_DEPT_HINT}</p>
              </>
            ) : (
              <ReadOnlyValue>{handlingDeptText}</ReadOnlyValue>
            )}
          </div>
        )}

        <div className="space-y-1.5">
          <Label>Chức vụ (Nếu có)</Label>
          {editing ? (
            <Input
              value={data.requester_position}
              placeholder="Tự động theo Nhân sự"
              onChange={(e) => onChange({ requester_position: e.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.requester_position || '—'}</ReadOnlyValue>
          )}
        </div>

        {/*
          CR-071 — phòng có nhiều người ký được (phó phòng, quyền trưởng phòng),
          trước đây ô này khóa cứng theo `Department.manager_id` nên in ra sai tên.
          Người được chọn CHỈ để lưu + in — luật duyệt giữ nguyên, ai có quyền trên
          phiếu vẫn bấm Duyệt được. Danh sách do backend lọc theo đúng luật phạm vi,
          rỗng thì để dạng chữ như cũ.
        */}
        <div className="space-y-1.5">
          <Label
            htmlFor="pr-dept-head"
            className={editing && deptHeadCandidates.length ? '' : 'text-muted-foreground'}
          >
            Trưởng bộ phận (TBP) / Người liên hệ
          </Label>
          {editing && deptHeadCandidates.length ? (
            //  Người đang hiện KHÔNG nằm trong danh sách ứng viên thì để ô rỗng và bày tên đó ở
            //  placeholder (chữ mờ) — y như bản Radix cũ. Đưa id vào `value` thì SearchSelect
            //  hiện nguyên văn con số id, vì nó không tìm thấy nhãn trong `options`.
            //  Phòng chưa gán trưởng ở danh mục Phòng ban thì không có «mặc định» nào để
            //  hiện — nói rõ lý do và mời chọn, KHÔNG tự đoán một người: đoán mà không lưu
            //  xuống thì lúc gửi duyệt vẫn bị chặn «thiếu Trưởng bộ phận» (CR-466).
            <SearchSelect
              id="pr-dept-head"
              searchInTrigger
              value={
                deptHeadCandidates.some((candidate) => candidate.employee_id === shownHeadId)
                  ? String(shownHeadId)
                  : ''
              }
              placeholder={shownHeadName || 'Phòng chưa gán trưởng — chọn người đứng tên'}
              searchPlaceholder="Gõ để tìm người đứng tên…"
              options={deptHeadCandidates.map((candidate) => ({
                value: String(candidate.employee_id),
                label: candidate.position
                  ? `${candidate.name} - ${candidate.position}`
                  : candidate.name,
              }))}
              onChange={(value) => {
                //  Chọn lại đúng người đang hiện thì thôi — kể cả khi người đó chỉ là TBP
                //  MẶC ĐỊNH chưa lưu: ghi xuống lúc này là tự lưu thay người dùng.
                if (value === String(shownHeadId)) return
                const candidate = deptHeadCandidates.find(
                  (option) => option.employee_id === Number(value),
                )
                if (!candidate) return
                onChange({ head_of_dept_id: candidate.employee_id, head_of_dept: candidate.name })
              }}
            />
          ) : (
            <ReadOnlyValue>
              {shownHeadName || (editing ? 'Phòng chưa gán Trưởng bộ phận ở màn Phòng ban' : '—')}
            </ReadOnlyValue>
          )}
        </div>

        {/* bao-CR-490: ai THỰC bấm Duyệt ở chặng trưởng phòng — chỉ xem, hệ thống ghi lúc duyệt. */}
        {/* bao-CR-499: CHỌN được trước khi duyệt (hệ báo người này lúc gửi duyệt); Duyệt xong hệ ghi
            đè người THỰC duyệt và khóa. Phiếu duyệt trước 25/09/2026 trống — scripts/backfill_approver_employee.py. */}
        <ApproverSelect
          id="pr-approver"
          value={data.approver_employee_id ?? 0}
          name={data.approver_employee_name ?? ''}
          candidates={approverCandidates}
          editable={editing}
          onChange={onChange}
        />

        {/*
          Ô "Đơn gấp" chiếm trọn một hàng để hai ô chữ dài bên dưới đứng CẠNH
          NHAU: xếp một ô ngắn cạnh một textarea cao sẽ hở một mảng trống lớn.
        */}
        <div className="space-y-1.5 md:col-span-2">
          <Label>Tùy chọn phiếu</Label>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-destructive">
            <Checkbox
              checked={data.is_urgent}
              disabled={!editing && !urgentEditable}
              onCheckedChange={(checked) => {
                const next = checked === true
                onChange({ is_urgent: next })
                if (!editing) onUrgentChange?.(next)
              }}
            />
            Đơn gấp
          </label>
        </div>

        <div className="space-y-1.5">
          <Label>
            Mục đích mua hàng
            <RequiredMark />
          </Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập mục đích mua hàng/dịch vụ..."
              value={data.purpose}
              onChange={(e) => onChange({ purpose: e.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.purpose || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Nội dung mua hàng</Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập nội dung chi tiết..."
              value={data.note}
              onChange={(e) => onChange({ note: e.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.note || '—'}</ReadOnlyValue>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/** Ô chỉ đọc: dữ liệu do backend gán, màn này không cho sửa. */
function Field({
  label,
  required,
  children,
}: {
  label: string
  /**
   * Ô bắt buộc. Nhãn ở đây là chữ mờ nhưng dấu sao vẫn đỏ — `RequiredMark` mang
   * màu riêng nên không bị `text-muted-foreground` nuốt thành xám.
   */
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground">
        {label}
        {required && <RequiredMark />}
      </Label>
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}
