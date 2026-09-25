import { FileText, PenLine } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'
import type { DocumentVersionFile } from '../api/document-api'

interface DocumentAttachmentSidebarProps {
  files: DocumentVersionFile[]
  /** Tệp đang xem ở khung chính — `null` = đang ở trình soạn thảo. */
  selectedFileId: number | null
  /** `null` = quay về trình soạn thảo. */
  onSelect: (file: DocumentVersionFile | null) => void
}

/**
 * CỘT TỆP bên phải trình soạn thảo (24/09/2026). Bấm một mục thì KHUNG CHÍNH
 * đổi theo — «Bản soạn thảo» là trình soạn thảo, mỗi tệp là khung xem tệp đó
 * (không mở hộp thoại). Kiểu TỐI GIẢN (phản hồi cùng ngày): mỗi mục một dòng
 * icon + tên, mục đang xem chỉ tô nền; cột cao bằng khung soạn thảo để hai bên
 * cân đối. Không có ô tải tệp lên — thêm/gỡ tệp ở tab Thông tin.
 */
export function DocumentAttachmentSidebar({
  files,
  selectedFileId,
  onSelect,
}: DocumentAttachmentSidebarProps) {
  return (
    <aside className="flex min-w-0 flex-col rounded-lg border bg-card p-2 lg:sticky lg:top-4 lg:h-[calc(100dvh-11rem)]">
      <SidebarItem
        icon={<PenLine className="size-4" />}
        label="Bản soạn thảo"
        active={selectedFileId === null}
        onClick={() => onSelect(null)}
      />
      <p className="mt-3 mb-1 px-2 text-xs text-muted-foreground">Tệp đính kèm ({files.length})</p>
      <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto">
        {files.map((file) => (
          <SidebarItem
            key={file.id}
            icon={<FileText className="size-4" />}
            label={file.filename}
            active={selectedFileId === file.id}
            onClick={() => onSelect(file)}
          />
        ))}
      </div>
    </aside>
  )
}

function SidebarItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: ReactNode
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      title={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-accent/60',
        active && 'bg-accent font-medium',
      )}
    >
      <span className="shrink-0 text-muted-foreground">{icon}</span>
      <span className="min-w-0 flex-1 truncate">{label}</span>
    </button>
  )
}
