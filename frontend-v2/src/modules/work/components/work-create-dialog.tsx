import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { useCreateWorkGroup, useCreateWorkList } from '../hooks/use-work-lists'

interface WorkCreateDialogProps {
  /** `list` = tạo danh sách công việc · `group` = tạo nhóm chứa danh sách. */
  mode: 'list' | 'group' | null
  /** Nhóm cha (tạo list trong nhóm, hoặc nhóm con). `null` = đứng ngoài. */
  parentGroupId: number | null
  onClose: () => void
}

/**
 * Hộp thoại tạo nhanh nhóm hoặc danh sách (A-01, A-08).
 *
 * Một hộp thoại cho cả hai vì chúng chỉ khác đúng cái tên: ép thành hai tệp là
 * chép hai lần cùng một biểu mẫu một ô.
 */
export function WorkCreateDialog({ mode, parentGroupId, onClose }: WorkCreateDialogProps) {
  const [ten, setTen] = useState('')
  const createList = useCreateWorkList()
  const createGroup = useCreateWorkGroup()

  const laNhom = mode === 'group'
  const dangLuu = createList.isPending || createGroup.isPending

  function luu() {
    const value = ten.trim()
    if (!value) return
    const xong = () => {
      setTen('')
      onClose()
    }
    if (laNhom) {
      createGroup.mutate({ name: value, parent_id: parentGroupId }, { onSuccess: xong })
    } else {
      createList.mutate({ name: value, group_id: parentGroupId }, { onSuccess: xong })
    }
  }

  return (
    <Dialog open={mode !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{laNhom ? 'Nhóm mới' : 'Danh sách công việc mới'}</DialogTitle>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="work-create-name">Tên</Label>
          <Input
            id="work-create-name"
            autoFocus
            value={ten}
            onChange={(e) => setTen(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && luu()}
            placeholder={laNhom ? 'Ví dụ: Khối Thu mua' : 'Ví dụ: Việc phòng Mua hàng'}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Hủy
          </Button>
          <Button onClick={luu} disabled={!ten.trim() || dangLuu}>
            Tạo
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
