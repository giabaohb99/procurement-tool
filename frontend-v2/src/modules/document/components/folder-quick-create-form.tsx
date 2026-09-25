import { FolderPlus, Loader2 } from 'lucide-react'
import { useState } from 'react'

import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { useCreateDocFolder } from '../hooks/use-document-folders'
import type { DocFolderDetail } from '../types/document-folder'

interface FolderQuickCreateFormProps {
  /** Thư mục CHA — luôn là thư mục pháp nhân của văn bản đang tạo (`folder-picker.tsx`). */
  parentFolderId: number
  onCreated: (folder: DocFolderDetail) => void
}

/**
 * Nút nhỏ «Tạo thư mục mới» trong popover chọn thư mục — chỉ tạo được CON của
 * thư mục pháp nhân đang chọn (không cho tự chọn cha khác trong ô này, giữ
 * cho ô chọn văn bản đơn giản; muốn dựng cây sâu thì mở trang Quản lý cây
 * thư mục, phase 05).
 */
export function FolderQuickCreateForm({ parentFolderId, onCreated }: FolderQuickCreateFormProps) {
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const createFolder = useCreateDocFolder()
  //  Chặn BẤM ĐÚP (CR-317) — backend tạo thư mục kiểu check-then-insert, không
  //  có ràng buộc duy nhất trên tên; bấm/Enter liền tay ra hai thư mục trùng tên.
  const runOnce = useSingleFlight()

  async function submit() {
    const trimmed = name.trim()
    if (!trimmed) return
    const created = await createFolder.mutateAsync({ parent_id: parentFolderId, name: trimmed })
    setName('')
    setCreating(false)
    onCreated(created)
  }

  if (!creating) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="w-full justify-start text-muted-foreground"
        onClick={() => setCreating(true)}
      >
        <FolderPlus className="size-4" />
        Tạo thư mục mới
      </Button>
    )
  }

  return (
    <div className="flex items-center gap-1.5">
      <Input
        autoFocus
        placeholder="Tên thư mục mới…"
        value={name}
        onChange={(event) => setName(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault()
            void runOnce(submit)
          }
        }}
      />
      <Button
        type="button"
        size="sm"
        disabled={!name.trim() || createFolder.isPending}
        onClick={() => void runOnce(submit)}
      >
        {createFolder.isPending ? <Loader2 className="size-4 animate-spin" /> : 'Tạo'}
      </Button>
    </div>
  )
}
