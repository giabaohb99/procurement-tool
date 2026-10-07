import {
  Ban,
  CircleSlash,
  Download,
  FileCheck2,
  FileCog,
  Loader2,
  Pencil,
  PenLine,
  Trash2,
  Upload,
} from 'lucide-react'
import { useRef } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { LaborContract } from '../types/labor-contract'
import {
  CONTRACT_STATUS,
  SIGNED_FILE_ACCEPT,
  transitionSpecOf,
  validateSignedFile,
  type TransitionSpec,
} from '../utils/labor-contract-rules'

const TRANSITION_ICONS: Record<number, typeof PenLine> = {
  [CONTRACT_STATUS.SIGNED]: PenLine,
  [CONTRACT_STATUS.CANCELLED]: Ban,
  [CONTRACT_STATUS.TERMINATED]: CircleSlash,
}

export interface LaborContractRowActionHandlers {
  onEdit: (row: LaborContract) => void
  onGenerate: (row: LaborContract) => void
  onDownloadDocument: (row: LaborContract) => void
  onUploadSigned: (row: LaborContract, file: File) => void
  onDownloadSigned: (row: LaborContract) => void
  onTransition: (row: LaborContract, spec: TransitionSpec) => void
  onDelete: (row: LaborContract) => void
}

interface LaborContractRowActionsProps extends LaborContractRowActionHandlers {
  row: LaborContract
  /** Đang có lệnh chạy trên dòng này — khóa nút. */
  busy: boolean
  /** Nút «Xem bản ký» cần quyền đọc; có thể tắt riêng. */
  canReadSigned: boolean
}

/**
 * Nút hành động của MỘT dòng. Hiện/ẩn hoàn toàn theo cờ backend trả (`can_*`, `transitions`)
 * — FE không tự suy luận từ trạng thái. Mọi nút `type="button"` vì tab nằm trong `<form>` hồ sơ.
 */
export function LaborContractRowActions({
  row,
  busy,
  canReadSigned,
  onEdit,
  onGenerate,
  onDownloadDocument,
  onUploadSigned,
  onDownloadSigned,
  onTransition,
  onDelete,
}: LaborContractRowActionsProps) {
  const fileInput = useRef<HTMLInputElement>(null)

  function handleFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const problem = validateSignedFile(file)
    if (problem) {
      toast.error(problem)
      return
    }
    onUploadSigned(row, file)
  }

  const specs = row.transitions
    .map((to) => transitionSpecOf(to))
    .filter((s): s is TransitionSpec => s !== undefined)

  const iconBtn = 'size-8'
  return (
    // Chặn nổi bọt: bấm nút không được kích `onRowClick` của bảng.
    <div className="flex flex-wrap items-center gap-0.5" onClick={(e) => e.stopPropagation()}>
      {busy && <Loader2 className="size-4 animate-spin text-muted-foreground" aria-label="Đang xử lý" />}
      {row.can_edit && (
        <Button type="button" variant="ghost" size="icon" className={iconBtn} disabled={busy}
          title="Sửa hợp đồng" aria-label="Sửa hợp đồng" onClick={() => onEdit(row)}>
          <Pencil className="size-4" />
        </Button>
      )}
      {row.can_generate && (
        <Button type="button" variant="ghost" size="icon" className={iconBtn} disabled={busy}
          title={row.has_generated_file ? 'Sinh lại tệp' : 'Sinh tệp hợp đồng'}
          aria-label={row.has_generated_file ? 'Sinh lại tệp' : 'Sinh tệp hợp đồng'}
          onClick={() => onGenerate(row)}>
          <FileCog className="size-4" />
        </Button>
      )}
      {row.can_print && (
        <Button type="button" variant="ghost" size="icon" className={iconBtn} disabled={busy}
          title="Tải hợp đồng (.docx)" aria-label="Tải hợp đồng (.docx)"
          onClick={() => onDownloadDocument(row)}>
          <Download className="size-4" />
        </Button>
      )}
      {row.can_upload_signed && (
        <>
          <input ref={fileInput} type="file" accept={SIGNED_FILE_ACCEPT} className="hidden"
            aria-label="Chọn bản đã ký" onChange={handleFile} />
          <Button type="button" variant="ghost" size="icon" className={iconBtn} disabled={busy}
            title={row.has_signed_file ? 'Thay bản đã ký' : 'Tải lên bản đã ký'}
            aria-label={row.has_signed_file ? 'Thay bản đã ký' : 'Tải lên bản đã ký'}
            onClick={() => fileInput.current?.click()}>
            <Upload className="size-4" />
          </Button>
        </>
      )}
      {row.has_signed_file && canReadSigned && (
        <Button type="button" variant="ghost" size="icon" className={iconBtn} disabled={busy}
          title="Xem bản đã ký" aria-label="Xem bản đã ký" onClick={() => onDownloadSigned(row)}>
          <FileCheck2 className="size-4" />
        </Button>
      )}
      {specs.map((spec) => {
        const Icon = TRANSITION_ICONS[spec.toStatus] ?? PenLine
        return (
          <Button key={spec.toStatus} type="button" variant="ghost" size="icon"
            className={cn(iconBtn, spec.danger && 'text-destructive hover:text-destructive')}
            disabled={busy} title={spec.actionLabel} aria-label={spec.actionLabel}
            onClick={() => onTransition(row, spec)}>
            <Icon className="size-4" />
          </Button>
        )
      })}
      {row.can_delete && (
        <Button type="button" variant="ghost" size="icon"
          className={cn(iconBtn, 'text-destructive hover:text-destructive')} disabled={busy}
          title="Xóa hợp đồng" aria-label="Xóa hợp đồng" onClick={() => onDelete(row)}>
          <Trash2 className="size-4" />
        </Button>
      )}
    </div>
  )
}
