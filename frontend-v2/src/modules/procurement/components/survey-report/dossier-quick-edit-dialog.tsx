import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Loader2, Lock, Save } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { apiPatch } from '@/core/api'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useDossier } from '@/modules/dossier/hooks/use-dossier'
import { useDossierTypesForForm } from '@/modules/dossier/hooks/use-dossier-types'
import {
  DOSSIER_STATUS,
  DOSSIER_STATUS_LABEL,
  type Dossier,
  type DossierStatus,
} from '@/modules/dossier/types/dossier'
import { useSetDossierProgress } from '@/modules/dossier/hooks/use-dossier-progress'
import {
  DOSSIER_PROGRESS_LABEL,
  DOSSIER_PROGRESS_ORDER,
  type ApplicableDossier,
  type DocKind,
  type DossierProgressStatus,
} from '@/modules/dossier/types/dossier-applicability'
import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'

interface DossierQuickEditDialogProps {
  /** Hồ sơ đang sửa; `null` = đóng hộp thoại. */
  doc: ApplicableDossier | null
  onClose: () => void
  /** Chứng từ đang mở — đích của phần TIẾN ĐỘ. */
  docKind: DocKind
  docId: number
  /** Mọi hồ sơ áp dụng cho phiếu — ứng viên tiên quyết. Backend chặn lại lần nữa. */
  candidates: ApplicableDossier[]
  /** Sửa được chính TỜ HỒ SƠ không (`dossier.write`). Không thì phần đó chỉ đọc. */
  canEditDossier: boolean
  /** Ghi được TIẾN ĐỘ của phiếu không (quyền ghi trên chứng từ). */
  canTrack: boolean
}

/**
 * Bộ ô của hộp — gộp HAI bảng, và phải biết ô nào đi về đâu:
 *
 * · Nhóm `dossier_*` → `PATCH /api/dossiers/{id}` → sửa TỜ GIẤY, đụng mọi phiếu.
 * · Nhóm `progress_*` → `PATCH /api/dossiers/applicable/…/progress` → chỉ đụng
 *   PHIẾU ĐANG MỞ.
 *
 * ⚠️ Tiền tố không phải cho đẹp: hai bảng có hai cột `note` và hai cột `status`
 * mang nghĩa ngược nhau. Trộn chung không tiền tố là lưu ghi chú của phiếu đè
 * lên mô tả dùng chung của tờ giấy, và không có gì báo.
 */
interface QuickEditDraft {
  dossier_name: string
  dossier_note: string
  dossier_status: DossierStatus
  dossier_type_id: number
  issued_date: string
  expiry_date: string
  owner_employee_id: number
  storage_location: string

  progress_status: DossierProgressStatus
  progress_required: boolean
  progress_assignee_id: number
  progress_planned_date: string
  progress_note: string
  progress_file_note: string
}

function buildDraft(full: Dossier, doc: ApplicableDossier): QuickEditDraft {
  return {
    dossier_name: full.name,
    dossier_note: full.note,
    dossier_status: full.status,
    dossier_type_id: full.dossier_type_id,
    //  Backend khai `date | None`; ô ngày của giao diện làm việc bằng chuỗi.
    issued_date: full.issued_date ?? '',
    expiry_date: full.expiry_date ?? '',
    owner_employee_id: full.owner_employee_id,
    storage_location: full.storage_location,

    //  Tiến độ lấy từ `doc` (danh sách `applicable`), KHÔNG từ `full`: tờ hồ sơ
    //  không biết gì về phiếu đang mở.
    progress_status: doc.progress_status,
    progress_required: doc.required,
    progress_assignee_id: doc.assignee_id,
    progress_planned_date: doc.planned_date ?? '',
    progress_note: doc.progress_note,
    progress_file_note: doc.file_note,
  }
}

/**
 * SỬA một tờ hồ sơ ngay trong thẻ — khỏi rời trang YCBG đang làm dở.
 *
 * Bố cục chép **`SurveyReportDocDialog`** của khối *Báo cáo thực hiện* để đặt
 * cạnh nhau là so được từng ô (đại ca yêu cầu 21/09/2026). Tám ô có chỗ lưu
 * thật thì sửa được; bốn ô bên kia có mà kho Hồ sơ KHÔNG có cột nào tương ứng
 * thì dựng dạng CHỈ ĐỌC kèm câu nói rõ vì sao:
 *
 * | Báo cáo thực hiện       | Kho Hồ sơ                                  |
 * | ----------------------- | ------------------------------------------ |
 * | Tiêu đề hồ sơ           | `name`                                     |
 * | Mô tả chi tiết          | `note`                                     |
 * | Trạng thái (4 mức)      | `status` (2 mức)                           |
 * | Giai đoạn               | `dossier_type_id` (Loại hồ sơ)             |
 * | Ngày bắt đầu thực hiện  | `issued_date` (Ngày cấp)                   |
 * | Ngày hết hiệu lực       | `expiry_date`                              |
 * | Nhân sự thực hiện       | `owner_employee_id` (Người phụ trách)      |
 * | Tệp đính kèm            | `storage_location` (Nơi lưu bản giấy)      |
 * | Dòng hàng               | *(suy ra từ điều kiện áp dụng — chỉ đọc)*  |
 * | Bắt buộc?               | **không có cột**                           |
 * | Dự định hoàn tất        | **không có cột**                           |
 * | Tiên quyết              | **không có cột**                           |
 *
 * ⚠️ **Bốn ô chỉ-đọc dùng `ReadOnlyValue`, KHÔNG dùng `<Select disabled>`.**
 * Dựng ô nhập rồi khóa là mời người dùng bấm vào một thứ không bao giờ phản hồi,
 * và `disabled` còn gỡ luôn khả năng bôi đen / copy (luật chung của dự án).
 *
 * ⚠️ **Mọi thay đổi ở đây áp cho MỌI phiếu** dùng tờ hồ sơ này — phân hệ Hồ sơ
 * chưa có trạng thái theo từng phiếu. Hộp phải nói thành lời, kẻo người dùng
 * tick «đã có giấy» cho phiếu này rồi vô tình đánh dấu xong cho hai chục phiếu
 * khác. Đây là khác biệt lớn nhất so với khối Báo cáo thực hiện, nơi mỗi phiếu
 * giữ bản ghi riêng.
 *
 * ⚠️ **Cố ý KHÔNG có nút Xóa** (bản gốc có). Xóa ở đây là xóa tờ giấy khỏi kho
 * của cả công ty, không phải gỡ nó khỏi phiếu đang mở — hai việc khác hẳn nhau,
 * mà nút đứng cùng chỗ thì người dùng đọc ra nghĩa thứ hai. Muốn xóa thì mở kho
 * hồ sơ.
 */
export function DossierQuickEditDialog({
  doc,
  onClose,
  docKind,
  docId,
  candidates,
  canEditDossier,
  canTrack,
}: DossierQuickEditDialogProps) {
  const queryClient = useQueryClient()
  //  ⚠️ `key` theo id để React DỰNG LẠI phần thân mỗi khi đổi tờ hồ sơ. Không
  //  có nó thì `useState` bên trong giữ giá trị của tờ mở lần trước — mở tờ
  //  thứ hai ra thấy nội dung của tờ thứ nhất, và bấm Lưu là chép đè.
  return (
    <Dialog open={Boolean(doc)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="sm:max-w-xl"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        {doc && (
          <QuickEditBody
            key={doc.id}
            doc={doc}
            onClose={onClose}
            docKind={docKind}
            docId={docId}
            candidates={candidates}
            canEditDossier={canEditDossier}
            canTrack={canTrack}
            queryClient={queryClient}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

function QuickEditBody({
  doc,
  onClose,
  docKind,
  docId,
  candidates,
  canEditDossier,
  canTrack,
  queryClient,
}: {
  doc: ApplicableDossier
  onClose: () => void
  docKind: DocKind
  docId: number
  candidates: ApplicableDossier[]
  canEditDossier: boolean
  canTrack: boolean
  queryClient: ReturnType<typeof useQueryClient>
}) {
  //  Danh sách `applicable` không mang ngày cấp / người phụ trách / nơi lưu —
  //  phải đọc tờ hồ sơ đầy đủ. Mở hộp mới gọi, xem `useDossier`.
  const { data: full, isLoading } = useDossier(doc.id)
  const { data: typePage } = useDossierTypesForForm()
  const { data: employeePage } = useEmployees({ page_size: 1000, is_active: true })

  const [draft, setDraft] = useState<QuickEditDraft | null>(null)
  const [initial, setInitial] = useState<QuickEditDraft | null>(null)
  //  Chặn bấm trùng trong cùng một nhịp — `disabled={isPending}` chỉ đúng ở lần
  //  render SAU, nên bấm năm lần liền tay ra năm request và năm dòng nhật ký
  //  cho một lần lưu (bẫy thứ tư của duoc-CR-317).
  const once = useSingleFlight()

  //  Nạp nháp ngay trong lúc render khi dữ liệu về, không qua effect — đỡ một
  //  khung hình biểu mẫu rỗng, và ESLint chặn `setState` trong effect.
  if (full && draft === null) {
    const next = buildDraft(full, doc)
    setDraft(next)
    setInitial(next)
  }

  const setProgress = useSetDossierProgress(docKind, docId)

  const save = useMutation({
    mutationFn: async (payload: QuickEditDraft) => {
      //  ⚠️ HAI đường ghi, và thứ tự có ý nghĩa: ghi TIẾN ĐỘ trước. Nếu quyền
      //  chỉ đủ một bên thì bên còn lại phải im lặng bỏ qua chứ không nổ 403 —
      //  người dùng đang sửa thứ họ được sửa.
      if (canTrack) {
        await setProgress.mutateAsync({
          dossierId: doc.id,
          payload: {
            status: payload.progress_status,
            required: payload.progress_required,
            assignee_id: payload.progress_assignee_id,
            //  Ô ngày trống gửi `null` tường minh = XÓA ngày. Gửi chuỗi rỗng
            //  thì backend khai `date | None` kiểu THẬT nên trả 422.
            planned_date: payload.progress_planned_date || null,
            note: payload.progress_note,
            file_note: payload.progress_file_note,
          },
        })
      }
      if (canEditDossier) {
        await apiPatch(`/api/dossiers/${doc.id}`, {
          name: payload.dossier_name,
          note: payload.dossier_note,
          status: payload.dossier_status,
          dossier_type_id: payload.dossier_type_id,
          issued_date: payload.issued_date || null,
          expiry_date: payload.expiry_date || null,
          owner_employee_id: payload.owner_employee_id,
          storage_location: payload.storage_location,
        })
      }
    },
    onSuccess: () => {
      //  ⚠️ MỘT lần dọn là đủ. `queryKeys.dossier.all` = `['dossier']`, mà khóa
      //  của `applicable` và `detail` đều bắt đầu bằng đúng chuỗi đó — TanStack
      //  khớp theo TIỀN TỐ, nên dọn thêm hai khóa con chỉ tổ gọi lại mỗi đường
      //  API hai lượt cho một lần lưu (thấy rõ trong log mạng).
      queryClient.invalidateQueries({ queryKey: queryKeys.dossier.all })
      toast.success(`Đã cập nhật ${doc.code}`)
      onClose()
    },
  })

  const isDirty = JSON.stringify(draft) !== JSON.stringify(initial)

  const attemptClose = async () => {
    if (save.isPending) return
    if (
      isDirty &&
      !(await confirm({ message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?' }))
    )
      return
    onClose()
  }

  const patch = (changes: Partial<QuickEditDraft>) =>
    setDraft((current) => (current ? { ...current, ...changes } : current))

  const handleSave = () =>
    once(async () => {
      if (!draft) return
      if (!draft.dossier_name.trim()) {
        toast.error('Nhập tiêu đề hồ sơ')
        return
      }
      await save.mutateAsync({ ...draft, dossier_name: draft.dossier_name.trim() })
    })

  const typeOptions = typePage?.items ?? []
  const employeeOptions = (employeePage?.items ?? []).map((employee) => ({
    value: String(employee.id),
    label: employee.code ? `${employee.full_name} · ${employee.code}` : employee.full_name,
  }))

  return (
    <>
      <DialogHeader>
        <DialogTitle>Chỉnh sửa hồ sơ</DialogTitle>
        <DialogDescription>
          {doc.code} — phần lớn các ô chỉ tính cho <strong>phiếu đang mở</strong>. Cụm
          cuối hộp (tình trạng trong kho · người phụ trách · nơi lưu) đụng tới tờ giấy
          dùng chung cho mọi phiếu.
        </DialogDescription>
      </DialogHeader>

      {!draft || isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-9 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-9 w-full" />
        </div>
      ) : (
        <div className="max-h-[65dvh] space-y-4 overflow-y-auto pr-1">
          <div className="space-y-1.5">
            <Label>
              Tiêu đề hồ sơ
              <RequiredMark />
            </Label>
            <Input
              value={draft.dossier_name}
              placeholder="VD: Giấy phép nhập khẩu tiền chất"
              onChange={(e) => patch({ dossier_name: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Mô tả chi tiết</Label>
            <Textarea
              rows={2}
              value={draft.dossier_note}
              placeholder="Cơ quan cấp, căn cứ pháp lý, thời gian xử lý, lưu ý…"
              onChange={(e) => patch({ dossier_note: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">
              Mô tả dùng chung của tờ hồ sơ. Ghi chú riêng cho phiếu này nằm ở ô bên dưới.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Dòng hàng</Label>
              {/*  CHỈ ĐỌC: bên kho Hồ sơ, «dòng hàng nào» không phải một ô người
                   dùng chọn mà là KẾT QUẢ của điều kiện áp dụng — sửa nó là sửa
                   luật khớp cho mọi phiếu, việc đó nằm ở chính tờ hồ sơ. */}
              <ReadOnlyValue>
                {doc.matched_lines.length === 0
                  ? 'Chung (mọi dòng hàng)'
                  : `${doc.matched_lines.length} dòng hàng`}
              </ReadOnlyValue>
              <p className="text-xs text-muted-foreground">{doc.reason}</p>
            </div>
            <div className="space-y-1.5">
              <Label>Trạng thái</Label>
              {/*  ⚠️ Đây là TIẾN ĐỘ của phiếu đang mở (4 mức), KHÔNG phải tình
                   trạng tờ giấy trong kho — ô đó nằm riêng ở cụm dưới. Hai thứ
                   cùng tên «trạng thái» nên phải đứng cách xa nhau trên màn. */}
              <Select
                value={String(draft.progress_status)}
                onValueChange={(v) =>
                  patch({ progress_status: Number(v) as DossierProgressStatus })
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DOSSIER_PROGRESS_ORDER.map((code) => (
                    <SelectItem key={code} value={String(code)}>
                      {DOSSIER_PROGRESS_LABEL[code]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Giai đoạn (Loại hồ sơ)</Label>
              <Select
                value={String(draft.dossier_type_id)}
                onValueChange={(v) => patch({ dossier_type_id: Number(v) })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {typeOptions.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Bắt buộc?</Label>
              {/*  Cờ này thuộc về PHIẾU, không thuộc tờ giấy: cùng một tờ có thể
                   bắt buộc ở đơn nhập khẩu mà không bắt buộc ở đơn trong nước. */}
              <Select
                value={draft.progress_required ? '1' : '0'}
                onValueChange={(v) => patch({ progress_required: v === '1' })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Bắt buộc</SelectItem>
                  <SelectItem value="0">Không bắt buộc</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label>Ngày cấp</Label>
              <DatePicker
                value={draft.issued_date}
                onChange={(value) => patch({ issued_date: value })}
                placeholder="Chọn ngày cấp"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Dự định hoàn tất</Label>
              <DatePicker
                value={draft.progress_planned_date}
                onChange={(value) => patch({ progress_planned_date: value })}
                placeholder="Chọn ngày dự định"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Ngày hết hiệu lực</Label>
              <DatePicker
                value={draft.expiry_date}
                onChange={(value) => patch({ expiry_date: value })}
                placeholder="Chọn ngày hết hiệu lực"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Người thực hiện</Label>
            <SearchSelect
              value={draft.progress_assignee_id ? String(draft.progress_assignee_id) : ''}
              onChange={(value) => patch({ progress_assignee_id: Number(value) || 0 })}
              options={employeeOptions}
              placeholder="Chọn người thực hiện"
              searchPlaceholder="Tìm theo tên hoặc mã…"
              emptyMessage="Không tìm thấy nhân sự nào."
              clearable
            />
          </div>

          <div className="space-y-1.5">
            <Label>Tệp đính kèm (tên tệp hoặc link)</Label>
            <Input
              value={draft.progress_file_note}
              placeholder="VD: GP-tienchat.pdf · hoặc dán link Drive"
              onChange={(e) => patch({ progress_file_note: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Ghi chú cho phiếu này</Label>
            <Textarea
              rows={2}
              value={draft.progress_note}
              placeholder="Đang chờ NCC gửi bản scan, hẹn thứ Sáu…"
              onChange={(e) => patch({ progress_note: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Tiên quyết — hồ sơ phải xong trước</Label>
            {/*  ⚠️ CHỈ ĐỌC, và cố ý (đại ca chốt 21/09/2026). Trình tự giấy tờ
                 của công ty là MỘT, nên ràng buộc khai ở chính tờ hồ sơ bên
                 phân hệ Hồ sơ — khai lại trong từng tờ phiếu thì mỗi phiếu một
                 chuỗi, và không ai biết bản nào đúng. Ở đây chỉ bày ra để người
                 đang làm phiếu hiểu vì sao tờ này đang khóa. */}
            {doc.depends.length === 0 ? (
              <ReadOnlyValue>Không có — tờ này làm được ngay</ReadOnlyValue>
            ) : (
              <div className="space-y-1 rounded-md border bg-muted/30 p-2.5">
                {doc.depends.map((id) => {
                  const cho = doc.waiting.find((w) => w.id === id)
                  const other = candidates.find((c) => c.id === id)
                  return (
                    <div key={id} className="flex items-center gap-2 text-sm">
                      {cho ? (
                        <Lock className="size-3.5 shrink-0 text-destructive" />
                      ) : (
                        <Check className="size-3.5 shrink-0 text-success" />
                      )}
                      <span className="truncate">{other?.name ?? cho?.name ?? `#${id}`}</span>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {cho ? 'chưa xong' : 'đã xong'}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Khai ở chính tờ hồ sơ trong{' '}
              <Link
                to={appRoutes.dossier.detail(doc.id)}
                target="_blank"
                rel="noreferrer"
                className="text-primary underline-offset-2 hover:underline"
              >
                kho hồ sơ
              </Link>
              . Dùng chung cả công ty; riêng «đã xong hay chưa» thì tính theo từng chứng từ.
            </p>
          </div>

          {/*  ⚠️ Cụm dưới đây đụng tới TỜ GIẤY DÙNG CHUNG. Tách hẳn xuống cuối
               và nói thành lời: mọi ô ở trên (trừ tiêu đề / mô tả / loại / hai
               ngày của tờ giấy) chỉ ảnh hưởng phiếu đang mở, còn ô này đổi là
               mọi phiếu thấy theo. Trộn lẫn hai nhóm thì không ai phân biệt nổi
               thao tác nào lan ra ngoài. */}
          <div className="space-y-1.5 rounded-lg border border-dashed p-3">
            <Label>Tình trạng tờ hồ sơ trong kho</Label>
            <Select
              value={String(draft.dossier_status)}
              onValueChange={(v) => patch({ dossier_status: Number(v) as DossierStatus })}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {/*  «Đã lưu trữ» có trong bộ mã nhưng KHÔNG bày ở đây: API
                     `applicable` đã lọc nó ra, nên chọn xong là tờ hồ sơ biến
                     mất khỏi chính cái thẻ vừa thao tác — trông như vừa xóa nhầm. */}
                {[DOSSIER_STATUS.DRAFT, DOSSIER_STATUS.ACTIVE].map((code) => (
                  <SelectItem key={code} value={String(code)}>
                    {DOSSIER_STATUS_LABEL[code]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Công ty đã có tờ giấy này chưa — <strong>dùng chung cho mọi phiếu</strong>.
              Khác với ô «Trạng thái» ở trên, thứ chỉ tính cho phiếu đang mở.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label>Người phụ trách hồ sơ (trong kho)</Label>
            <SearchSelect
              value={draft.owner_employee_id ? String(draft.owner_employee_id) : ''}
              onChange={(value) => patch({ owner_employee_id: Number(value) || 0 })}
              options={employeeOptions}
              placeholder="Chọn người phụ trách"
              searchPlaceholder="Tìm theo tên hoặc mã…"
              emptyMessage="Không tìm thấy nhân sự nào."
              clearable
            />
          </div>

          <div className="space-y-1.5">
            <Label>Nơi lưu bản giấy</Label>
            <Input
              value={draft.storage_location}
              placeholder="VD: Tủ A2 · P. Hành chính — hoặc dán link Drive"
              onChange={(e) => patch({ storage_location: e.target.value })}
            />
          </div>
        </div>
      )}

      <DialogFooter>
        <Button variant="outline" onClick={attemptClose} disabled={save.isPending}>
          Hủy
        </Button>
        <Button onClick={handleSave} disabled={save.isPending || !draft}>
          {save.isPending ? <Loader2 className="animate-spin" /> : <Save />}
          Lưu
        </Button>
      </DialogFooter>
    </>
  )
}
