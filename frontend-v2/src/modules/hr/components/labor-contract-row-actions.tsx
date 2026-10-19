import {
  Archive,
  Ban,
  ChevronDown,
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
import { useRef, type ReactNode } from 'react'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
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
  /** Mục «Xem bản ký» cần quyền đọc; có thể tắt riêng. */
  canReadSigned: boolean
}

interface MenuEntry {
  key: string
  label: string
  icon: typeof PenLine
  /** Bỏ trống = mục «Tải lên / Thay bản đã ký» (mở hộp chọn tệp — gắn thẳng ở JSX, xem `openFilePicker`). */
  onSelect?: () => void
  danger?: boolean
}

/**
 * Thao tác của MỘT dòng hợp đồng — MỘT nút «Thao tác ▾» mở menu, mỗi mục có ICON + CHỮ, chia nhóm
 * Xem / Soạn / Trạng thái, Xóa tách riêng cuối (duoc-CR-633, đại ca: «icon + chữ, dropdown tường minh
 * hơn» — dãy 8 icon trơn trước đây nhìn na ná nhau, phải rê chuột đoán).
 *
 * Mục nào hiện vẫn hoàn toàn theo cờ backend (`can_*`, `transitions`) — FE không tự suy từ trạng
 * thái. Nút kích hoạt `type="button"` vì tab nằm trong `<form>` hồ sơ.
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

  //  Hàm xử lý sự kiện (đọc ref lúc BẤM, không lúc vẽ) — `react-hooks/refs` cấm đọc `.current` khi render.
  function openFilePicker() {
    fileInput.current?.click()
  }

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

  const view: MenuEntry[] = []
  if (row.can_open_document && row.document_id > 0)
    //  Mở TAB MỚI: tab Hợp đồng nằm trong <form> hồ sơ, điều hướng tại chỗ sẽ mất dữ liệu đang sửa.
    view.push({ key: 'archive', label: 'Mở bản lưu trữ ở Văn bản', icon: Archive,
      onSelect: () => window.open(appRoutes.document.documentDetail(row.document_id), '_blank', 'noopener') })
  if (row.has_signed_file && canReadSigned)
    view.push({ key: 'view-signed', label: 'Xem bản đã ký', icon: FileCheck2, onSelect: () => onDownloadSigned(row) })
  if (row.can_print)
    view.push({ key: 'download', label: 'Tải hợp đồng (.docx)', icon: Download, onSelect: () => onDownloadDocument(row) })

  const compose: MenuEntry[] = []
  if (row.can_edit) compose.push({ key: 'edit', label: 'Sửa hợp đồng', icon: Pencil, onSelect: () => onEdit(row) })
  if (row.can_generate)
    compose.push({ key: 'generate', label: row.has_generated_file ? 'Sinh lại tệp' : 'Sinh tệp hợp đồng', icon: FileCog,
      onSelect: () => onGenerate(row) })
  if (row.can_upload_signed)
    compose.push({ key: 'upload', label: row.has_signed_file ? 'Thay bản đã ký' : 'Tải lên bản đã ký', icon: Upload,
    })

  const status: MenuEntry[] = row.transitions
    .map((to) => transitionSpecOf(to))
    .filter((s): s is TransitionSpec => s !== undefined)
    .map((spec) => ({ key: `to-${spec.toStatus}`, label: spec.actionLabel, icon: TRANSITION_ICONS[spec.toStatus] ?? PenLine,
      danger: spec.danger, onSelect: () => onTransition(row, spec) }))

  const groups: { title: string; items: MenuEntry[] }[] = [
    { title: 'Xem', items: view },
    { title: 'Soạn', items: compose },
    { title: 'Trạng thái', items: status },
  ].filter((g) => g.items.length > 0)

  //  Không có mục nào thì không dựng nút (khỏi mở ra một menu rỗng).
  if (groups.length === 0 && !row.can_delete) return null

  const sections: ReactNode[] = groups.map((g, i) => (
    <div key={g.title}>
      {i > 0 && <DropdownMenuSeparator />}
      <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">{g.title}</DropdownMenuLabel>
      {g.items.map((it) => (
        <DropdownMenuItem key={it.key} variant={it.danger ? 'destructive' : 'default'} onSelect={it.onSelect ?? openFilePicker}>
          <it.icon />
          {it.label}
        </DropdownMenuItem>
      ))}
    </div>
  ))

  return (
    // Chặn nổi bọt: bấm nút không được kích `onRowClick` của bảng.
    <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
      {row.can_upload_signed && (
        <input ref={fileInput} type="file" accept={SIGNED_FILE_ACCEPT} className="hidden"
          aria-label="Chọn bản đã ký" onChange={handleFile} />
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5" disabled={busy}
            aria-label={`Thao tác với hợp đồng ${row.contract_no || row.code}`}>
            {busy ? <Loader2 className="size-4 animate-spin" aria-label="Đang xử lý" /> : null}
            Thao tác
            <ChevronDown className="size-4 opacity-60" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-60">
          {sections}
          {row.can_delete && (
            <>
              {groups.length > 0 && <DropdownMenuSeparator />}
              <DropdownMenuItem variant="destructive" onSelect={() => onDelete(row)}>
                <Trash2 />
                Xóa hợp đồng
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
