import {
  CalendarCheck,
  CalendarClock,
  Check,
  ChevronDown,
  ExternalLink,
  Lock,
  Pencil,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import {
  DOSSIER_PROGRESS,
  type ApplicableDossier,
} from '@/modules/dossier/types/dossier-applicability'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { nameInitials } from '@/shared/utils/name-initials'
import {
  EXPIRY_TONE_CLASS,
  donePercent,
  expiryTone,
  isDossierDone,
  type ChecklistGroup,
} from '../../utils/dossier-checklist-helpers'

interface DossierChecklistGroupsProps {
  groups: ChecklistGroup[]
  /** Khóa của nhóm đang GẬP. Gập là ngoại lệ nên nhớ cái gập, không nhớ cái mở. */
  collapsed: ReadonlySet<string>
  onToggle: (key: string) => void
  /** Mở hộp thoại sửa nhanh. Bỏ trống = người xem không sửa được. */
  onEdit?: (doc: ApplicableDossier) => void
  /** Bấm ô tick — gạt giữa «Hoàn thành» và «Đang làm». Bỏ trống = chỉ xem. */
  onToggleDone?: (doc: ApplicableDossier) => void
  /** Đang có lệnh ghi chạy dở — khóa ô tick để khỏi bắn chồng request. */
  busy?: boolean
  /**
   * Nhãn dòng hàng của một tờ hồ sơ (`CHUNG` khi không gắn dòng nào).
   *
   * ⚠️ Chỉ bày ở dạng **Xem tổng**. Dạng *Theo dòng hàng* thì tiêu đề nhóm đã
   * nói rồi — lặp lại ở từng dòng là chiếm chỗ của cột mô tả, đúng lý lẽ đã ghi
   * trong `ReportDocRow` của bản gốc.
   */
  itemTagOf?: (doc: ApplicableDossier) => string
}

/**
 * Danh sách hồ sơ xếp theo NHÓM — **chép markup thân khối *Báo cáo thực hiện***
 * (`ReportPhaseList` + `ReportDocRow`) để hai thẻ nhìn không phân biệt được.
 *
 * Bản đầu tiên tôi vẽ lại theo ảnh chụp nên ra một thứ na ná mà lạ mắt (đại ca
 * bắt 21/09/2026). Giờ chép đúng từng lớp: hàng giai đoạn có ô số nền đậm ·
 * phụ đề · thanh tiến độ dồn phải; dòng hồ sơ là THẺ RỜI có viền, ô tick vuông
 * bo góc, nhãn nút dòng hàng, tên đậm cắt 45%, mô tả co giãn, huy hiệu trạng
 * thái dạng viên.
 *
 * ⚠️ **Nhớ nhóm ĐANG GẬP, không nhớ nhóm đang mở.** Danh sách nhóm đổi theo chế
 * độ xem và theo bộ lọc, nên nhớ cái mở thì nhóm mới xuất hiện sẽ mặc định
 * ĐÓNG — người dùng đổi bộ lọc xong thấy một trang toàn tiêu đề rỗng.
 */
export function DossierChecklistGroups({
  groups,
  collapsed,
  onToggle,
  onEdit,
  onToggleDone,
  busy,
  itemTagOf,
}: DossierChecklistGroupsProps) {
  if (!groups.length) {
    return (
      <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
        Không có hồ sơ nào khớp bộ lọc đang đặt.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {groups.map((group, index) => {
        const open = !collapsed.has(group.key)
        return (
          <div key={group.key} className="space-y-2">
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                aria-expanded={open}
                aria-label={open ? 'Thu gọn nhóm' : 'Hiện hồ sơ của nhóm'}
                className="-mr-1 cursor-pointer rounded-md p-0.5 text-muted-foreground hover:text-foreground"
                onClick={() => onToggle(group.key)}
              >
                <ChevronDown className={cn('size-4 transition-transform', !open && '-rotate-90')} />
              </button>
              <span className="grid size-6 place-items-center rounded-md bg-navy text-xs font-semibold text-white dark:bg-muted dark:text-foreground">
                {index + 1}
              </span>
              <span className="text-sm font-semibold">{group.name}</span>
              {group.hint && (
                <span className="text-xs text-muted-foreground">{group.hint}</span>
              )}
              <ChecklistProgressBar docs={group.docs} className="ml-auto" />
            </div>

            {open &&
              (group.docs.length === 0 ? (
                <p className="pl-8 text-xs text-muted-foreground">Chưa có hồ sơ.</p>
              ) : (
                <div className="space-y-1.5">
                  {group.docs.map((doc) => (
                    <ChecklistRow
                      key={doc.id}
                      doc={doc}
                      onEdit={onEdit}
                      onToggleDone={onToggleDone}
                      busy={busy}
                      itemTag={itemTagOf?.(doc)}
                    />
                  ))}
                </div>
              ))}
          </div>
        )
      })}
    </div>
  )
}

/**
 * Thanh tiến độ của một nhóm — chép `PhaseProgressBar` của bản gốc **từng lớp
 * một**: fill màu MỀM chạy theo %, chữ `hoàn tất/tổng · %` nằm ĐÈ ở giữa thanh
 * chứ không đứng cạnh, để đọc rõ trên cả phần đã tô lẫn phần trống.
 *
 * `barClassName` / `labelClassName` để dùng lại ở ô tổng (thanh cao hơn, cả bề
 * ngang) mà không đẻ thêm một component thanh thứ hai — y như bản gốc.
 */
export function ChecklistProgressBar({
  docs,
  className,
  barClassName,
  labelClassName,
}: {
  docs: ApplicableDossier[]
  className?: string
  barClassName?: string
  labelClassName?: string
}) {
  const total = docs.length
  const done = docs.filter(isDossierDone).length
  const percent = donePercent(docs)
  const complete = total > 0 && done === total
  return (
    <div
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${done}/${total} hồ sơ đã có giấy, ${percent}%`}
      title={`${done}/${total} hồ sơ đã có giấy · ${percent}%`}
      className={cn(
        'relative h-5 w-32 shrink-0 overflow-hidden rounded-full border bg-muted/50',
        className,
        barClassName,
      )}
    >
      <div
        className={cn(
          'absolute inset-y-0 left-0 rounded-full transition-[width] duration-500',
          complete ? 'bg-success/35' : 'bg-primary/30',
        )}
        style={{ width: `${percent}%` }}
      />
      <span
        className={cn(
          'absolute inset-0 flex items-center justify-center gap-1 px-2 text-[10px] font-semibold tabular-nums text-foreground/85',
          labelClassName,
        )}
      >
        {done}/{total} · {percent}%
      </span>
    </div>
  )
}

/**
 * Viên NGÀY trên dòng hồ sơ — chỗ của `DocDateChip` bên *Báo cáo thực hiện*:
 * hạn hết hiệu lực, tô theo mức khẩn. Tờ vô thời hạn thì KHÔNG dựng gì, y như
 * bản gốc bỏ qua hồ sơ không có ngày nào — không phải dựng một ô gạch ngang.
 */
function DossierDateChip({ doc }: { doc: ApplicableDossier }) {
  if (!doc.expiry_date) return null
  return (
    <span
      title={`Hết hiệu lực ${formatDate(doc.expiry_date)} · ${doc.expiry_state_label}`}
      className={cn(
        'flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums',
        EXPIRY_TONE_CLASS[expiryTone(doc.expiry_state)],
      )}
    >
      <CalendarClock className="size-3" />
      {formatDate(doc.expiry_date)}
    </span>
  )
}

/**
 * Viên TIẾN ĐỘ — bốn mức, màu chép đúng `STATUS_PILL` của khối *Báo cáo thực
 * hiện* để cùng một trạng thái ra cùng một màu ở cả hai thẻ.
 *
 * ⚠️ Đây là tiến độ CỦA PHIẾU (`progress_status`), không phải tình trạng tờ
 * giấy trong kho (`status`). Xem `dossier-applicability.ts`.
 */
const STATUS_PILL: Record<number, string> = {
  [DOSSIER_PROGRESS.IDLE]: 'bg-muted text-muted-foreground',
  [DOSSIER_PROGRESS.DOING]: 'bg-warning/15 text-warning',
  [DOSSIER_PROGRESS.REVIEW]: 'bg-primary/10 text-primary',
  [DOSSIER_PROGRESS.DONE]: 'bg-success/15 text-success',
}

/** Ô «Dự định hoàn tất» trên dòng — chép `DocPlannedChip`, đỏ khi trễ hẹn. */
function PlannedChip({ doc }: { doc: ApplicableDossier }) {
  if (!doc.planned_date) return null
  //  Trễ = quá ngày hẹn mà việc CHƯA xong. Xong rồi thì không còn gì để trễ,
  //  y như bản gốc — nhuộm đỏ một việc đã hoàn thành chỉ gây hoảng vô ích.
  const late = !isDossierDone(doc) && doc.planned_date < new Date().toISOString().slice(0, 10)
  return (
    <span
      title={`Dự định hoàn tất ${formatDate(doc.planned_date)}`}
      className={cn(
        'flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums',
        late ? EXPIRY_TONE_CLASS.overdue : 'bg-muted text-muted-foreground',
      )}
    >
      <CalendarCheck className="size-3" />
      {formatDate(doc.planned_date)}
    </span>
  )
}

/** Vòng tròn chữ viết tắt của người thực hiện — chép `DocAssignee` bản gốc. */
function AssigneeAvatar({ name }: { name: string }) {
  if (!name) return null
  return (
    <span
      title={`Người thực hiện: ${name}`}
      className="grid size-6 shrink-0 place-items-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary"
    >
      {nameInitials(name)}
    </span>
  )
}

/**
 * MỘT dòng hồ sơ — chép `ReportDocRow`: thẻ rời, ô tick, nhãn, tên, mô tả, viên
 * ngày, viên trạng thái. Dùng chung cho cả hai chế độ xem (danh sách gập và dải
 * sổ dưới một dòng của bảng), y như bản gốc dùng chung `ReportDocRow`.
 */
export function ChecklistRow({
  doc,
  onEdit,
  onToggleDone,
  busy,
  itemTag,
}: {
  doc: ApplicableDossier
  onEdit?: (doc: ApplicableDossier) => void
  onToggleDone?: (doc: ApplicableDossier) => void
  busy?: boolean
  itemTag?: string
}) {
  const done = isDossierDone(doc)
  //  Câu giải thích dùng ở cả ô tick lẫn biểu tượng khóa — một chỗ khai, hai
  //  chỗ đọc, khỏi lệch chữ.
  const waitText = doc.waiting.map((w) => w.name).join(', ')

  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border bg-card py-1.5 pr-1.5 pl-3',
        //  Làm mờ CẢ DÒNG khi đang khóa, chép bản gốc: mắt lướt danh sách nhận
        //  ra ngay đâu là việc làm được, khỏi đọc từng biểu tượng.
        doc.locked && 'opacity-70',
      )}
    >
      {/*  Ô tick THẬT — gạt tiến độ của tờ hồ sơ này TRÊN PHIẾU ĐANG MỞ. Trước
           21/09/2026 nó là `<span>` chỉ đọc, vì chưa có chỗ lưu trạng thái theo
           từng phiếu; nay có `tab_dossier_progress` nên bấm được.
           Thiếu quyền ghi trên phiếu thì KHÔNG dựng nút, dựng dạng chỉ đọc —
           nút khóa là mời người ta bấm vào một thứ chắc chắn trả 403. */}
      {onToggleDone ? (
        <button
          type="button"
          aria-label={done ? 'Mở lại hồ sơ' : 'Đánh dấu hoàn thành'}
          //  ⚠️ Đang khóa thì NÓI RA CHỜ AI, không chỉ khóa nút. Nút mờ không
          //  lời giải thích là thứ người dùng báo lỗi «bấm không được».
          title={
            doc.locked
              ? `Chờ hồ sơ tiên quyết hoàn thành trước: ${waitText}`
              : done
                ? 'Mở lại hồ sơ'
                : 'Đánh dấu hoàn thành cho phiếu này'
          }
          //  Khóa nút là để tiện, KHÔNG phải để gác: backend chặn lại lần nữa.
          disabled={busy || doc.locked}
          className={cn(
            'grid size-5 shrink-0 place-items-center rounded-md border-2 transition-colors',
            done
              ? 'border-success bg-success text-white'
              : 'border-input bg-muted/50 text-transparent hover:border-success/60',
            doc.locked ? 'cursor-not-allowed' : 'cursor-pointer',
          )}
          onClick={() => onToggleDone(doc)}
        >
          <Check className="size-3.5" />
        </button>
      ) : (
        <span
          title={done ? 'Đã hoàn thành cho phiếu này' : 'Chưa hoàn thành cho phiếu này'}
          className={cn(
            'grid size-5 shrink-0 place-items-center rounded-md border-2',
            done
              ? 'border-success bg-success text-white'
              : 'border-input bg-muted/50 text-transparent',
          )}
        >
          <Check className="size-3.5" />
        </span>
      )}

      {itemTag !== undefined && (
        <span
          title={itemTag || 'Chung (cả phiếu)'}
          className={cn(
            'max-w-36 shrink-0 truncate rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase',
            itemTag ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground',
          )}
        >
          {itemTag || 'Chung'}
        </span>
      )}

      <span className="max-w-[45%] shrink-0 truncate text-sm font-medium" title={doc.name}>
        {doc.name}
      </span>
      {doc.required && (
        <span className="shrink-0 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-destructive uppercase">
          Bắt buộc
        </span>
      )}

      {/*  Mô tả chiếm phần còn lại của dòng — cũng là khoảng đệm khi rỗng.
           GHI CHÚ RIÊNG của phiếu được ưu tiên hơn mô tả dùng chung của tờ
           giấy: người vừa gõ ghi chú cho phiếu này phải thấy nó ở đây, không
           thì họ tưởng gõ xong không lưu. */}
      <span
        className="min-w-0 flex-1 truncate text-xs text-muted-foreground"
        title={doc.progress_note || doc.note}
      >
        {doc.progress_note || doc.note}
      </span>

      <Link
        to={appRoutes.dossier.detail(doc.id)}
        target="_blank"
        rel="noreferrer"
        title={`Mở hồ sơ ${doc.code}`}
        aria-label={`Mở hồ sơ ${doc.code}`}
        className="grid size-7 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground"
      >
        <ExternalLink className="size-3.5" />
      </Link>

      {doc.locked && (
        <span
          className="shrink-0 text-destructive"
          title={`Chờ hồ sơ tiên quyết: ${waitText}`}
        >
          <Lock className="size-3.5" />
        </span>
      )}

      <PlannedChip doc={doc} />
      <DossierDateChip doc={doc} />
      <AssigneeAvatar name={doc.assignee_name} />

      <span
        className={cn(
          'shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap',
          STATUS_PILL[doc.progress_status] ?? STATUS_PILL[DOSSIER_PROGRESS.IDLE],
        )}
      >
        {doc.progress_status_label}
      </span>

      {onEdit && (
        //  ⚠️ `type="button"` — dòng này nằm trong `<form>` của trang YCBG, để
        //  mặc định `submit` thì bấm «sửa» là LƯU cả phiếu rồi mới mở hộp thoại
        //  (bẫy thứ ba của duoc-CR-317).
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="size-7 shrink-0"
          aria-label={`Sửa nhanh ${doc.code}`}
          title="Sửa hồ sơ"
          onClick={() => onEdit(doc)}
        >
          <Pencil className="size-3.5" />
        </Button>
      )}
    </div>
  )
}
