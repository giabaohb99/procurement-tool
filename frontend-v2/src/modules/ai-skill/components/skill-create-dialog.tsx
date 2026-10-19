import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
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
import { RequiredMark } from '@/shared/ui/required-mark'
import { SLUG_HINT, TITLE_MAX, validateSlug } from '../config/ai-skill-constants'
import { useCreateSkill } from '../hooks/use-ai-skill'
import type { SkillDetail } from '../types/ai-skill'

interface SkillCreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  setId: number
  onCreated?: (skill: SkillDetail) => void
}

/**
 * Hộp «Thêm skill» trong một bộ: chỉ hỏi TÊN SKILL (mã AI gọi) và tiêu đề, tạo xong mở thẳng trang soạn — nội dung,
 * tóm tắt cho AI, tệp đi kèm soạn ở đó cho đủ chỗ.
 */
export function SkillCreateDialog({ open, onOpenChange, setId, onCreated }: SkillCreateDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Thêm skill</DialogTitle>
          <DialogDescription>Tạo xong sẽ mở trang soạn để viết nội dung và tóm tắt cho AI.</DialogDescription>
        </DialogHeader>
        {open && <CreateForm setId={setId} onDone={onOpenChange} onCreated={onCreated} />}
      </DialogContent>
    </Dialog>
  )
}

function CreateForm({
  setId,
  onDone,
  onCreated,
}: {
  setId: number
  onDone: (open: boolean) => void
  onCreated?: (skill: SkillDetail) => void
}) {
  const create = useCreateSkill(setId)
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')
  const busy = useRef(false)

  async function handleSubmit() {
    if (busy.current) return
    const problem = validateSlug(slug)
    if (problem) return setError(problem)
    setError('')
    busy.current = true
    try {
      const skill = await create.mutateAsync({ slug: slug.trim(), title: title.trim() })
      onDone(false)
      onCreated?.(skill)
    } catch {
      //  Trùng tên trong bộ → backend báo, toast tự động; giữ hộp mở để đổi tên.
    } finally {
      busy.current = false
    }
  }

  return (
    <>
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="skill-slug">
            Tên skill <RequiredMark hint="Bắt buộc" />
          </Label>
          <Input
            id="skill-slug"
            value={slug}
            maxLength={100}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="bao-cao-mua-hang-thang"
            aria-invalid={Boolean(error)}
            aria-describedby="skill-slug-hint"
          />
          <p id="skill-slug-hint" className="text-xs text-muted-foreground">
            {SLUG_HINT} AI gọi skill bằng tên này, đặt rồi thì đừng đổi.
          </p>
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="skill-title">Tiêu đề hiển thị</Label>
          <Input
            id="skill-title"
            value={title}
            maxLength={TITLE_MAX}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Báo cáo mua hàng hằng tháng"
          />
        </div>
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={() => onDone(false)}>
          Hủy
        </Button>
        <Button type="button" onClick={() => void handleSubmit()} disabled={create.isPending}>
          Tạo và soạn
        </Button>
      </DialogFooter>
    </>
  )
}
