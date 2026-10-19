import { Loader2, Trash2, UploadCloud } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/shared/ui/button'

interface DocumentFilesToolbarProps {
  /** Đang tải lên hoặc đang gỡ tệp — khóa cả hai nút. */
  busy: boolean
  onUpload: (files: File[]) => void
  /** Có = hiện «Xóa tệp» cho tệp đang xem. */
  onDelete?: () => void
}

/**
 * Thanh lệnh tệp của văn bản CHỈ GỒM TỆP khi đã có ít nhất một tệp: «Tải thêm tệp» (chọn nhiều tệp) và «Xóa tệp».
 * Trước đây ô tải lên chỉ hiện lúc 0 tệp nên văn bản đã có tệp không thể bổ sung phụ lục / bản scan.
 */
export function DocumentFilesToolbar({ busy, onUpload, onDelete }: DocumentFilesToolbarProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  return (
    <div className="mb-3 flex flex-wrap items-center gap-2">
      <input
        ref={inputRef}
        type="file"
        multiple
        hidden
        data-testid="document-files-input"
        onChange={(event) => {
          const picked = Array.from(event.target.files ?? [])
          if (picked.length) onUpload(picked)
          event.target.value = ''
        }}
      />
      <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => inputRef.current?.click()}>
        {busy ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}
        Tải thêm tệp
      </Button>
      {onDelete && (
        <Button type="button" variant="outline" size="sm" disabled={busy} onClick={onDelete}>
          <Trash2 className="size-4" />
          Xóa tệp
        </Button>
      )}
    </div>
  )
}
