import { useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { useUpdateDocFolder } from '../hooks/use-document-folders'

interface FolderRenameDialogProps {
  folderId: number
  currentName: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * ĐỔI TÊN từ khung nội dung (menu chuột phải trên thẻ thư mục, đặc tả §B) —
 * bằng HỘP THOẠI, khác «đổi tên tại chỗ» của cây bên trái (F2/bấm đúp, ô nhập
 * ngay trong dòng, phase 10A). Hai lối vào khác hình dạng nhưng cùng một API
 * (`PATCH /doc-folders/{id}` qua `useUpdateDocFolder`) nên không lệch dữ liệu.
 */
export function FolderRenameDialog({ folderId, currentName, open, onOpenChange }: FolderRenameDialogProps) {
  const [name, setName] = useState(currentName)
  const updateFolder = useUpdateDocFolder()
  const runOnce = useSingleFlight()

  function submit() {
    const trimmed = name.trim()
    if (!trimmed) return
    updateFolder.mutate(
      { id: folderId, payload: { name: trimmed } },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) setName(currentName)
        onOpenChange(next)
      }}
    >
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Đổi tên thư mục</DialogTitle>
        </DialogHeader>

        <div className="space-y-1.5">
          <Label htmlFor="folder-rename-input">Tên mới</Label>
          <Input
            id="folder-rename-input"
            autoFocus
            value={name}
            onChange={(event) => setName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                void runOnce(submit)
              }
            }}
          />
        </div>

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" disabled={!name.trim() || updateFolder.isPending} onClick={() => void runOnce(submit)}>
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
