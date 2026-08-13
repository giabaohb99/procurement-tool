import { BookUser, Plus, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
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
import { useActiveDocumentPartners } from '../hooks/use-document-catalogs'

interface DocumentRecipientPickerProps {
  /** Danh sách TÊN nơi nhận. */
  value: string[]
  onChange: (value: string[]) => void
}

/**
 * Ô NƠI NHẬN: một văn bản gửi nhiều nơi.
 *
 * Hai đường vào vì thực tế có hai kiểu nơi nhận: đơn vị gửi thường xuyên thì
 * lấy từ danh bạ cho khỏi gõ sai tên, còn nơi chỉ nhận đúng một lần (một cá
 * nhân, một đoàn công tác) thì gõ thẳng — bắt khai vào danh bạ trước mới chọn
 * được thì danh bạ ngập những tên dùng một lần.
 */
export function DocumentRecipientPicker({ value, onChange }: DocumentRecipientPickerProps) {
  const partners = useActiveDocumentPartners()

  // Ô gõ tay chỉ bung ra khi bấm "Thêm nơi nhận": để sẵn thì lần nào cũng có
  // một ô trống lơ lửng dưới danh sách, người dùng tưởng còn thiếu gì đó.
  const [draft, setDraft] = useState<string | null>(null)
  const [pickerOpen, setPickerOpen] = useState(false)
  const [checked, setChecked] = useState<string[]>([])

  /** Bỏ qua tên rỗng và tên đã có — hai dòng trùng nhau chỉ làm bản in xấu đi. */
  function addNames(names: string[]) {
    const next = [...value]
    for (const name of names) {
      const trimmed = name.trim()
      if (trimmed && !next.includes(trimmed)) next.push(trimmed)
    }
    onChange(next)
  }

  function confirmDraft() {
    if (draft?.trim()) addNames([draft])
    setDraft(null)
  }

  function openPicker() {
    setChecked([])
    setPickerOpen(true)
  }

  return (
    <div className="space-y-2">
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((name) => (
            <span
              key={name}
              className="inline-flex items-center gap-1.5 rounded-md border bg-muted/40 py-1 pr-1 pl-2.5 text-sm"
            >
              {name}
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-5"
                title={`Bỏ ${name}`}
                aria-label={`Bỏ ${name}`}
                onClick={() => onChange(value.filter((item) => item !== name))}
              >
                <X className="size-3.5" />
              </Button>
            </span>
          ))}
        </div>
      )}

      {draft !== null && (
        <div className="flex items-center gap-2">
          <Input
            autoFocus
            value={draft}
            placeholder="Tên nơi nhận"
            onChange={(event) => setDraft(event.target.value)}
            // Enter trong form là submit, mà ở đây người dùng chỉ muốn xong một
            // dòng nơi nhận — chặn lại rồi tự thêm.
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
                confirmDraft()
              }
              if (event.key === 'Escape') setDraft(null)
            }}
          />
          <Button type="button" variant="secondary" onClick={confirmDraft}>
            Thêm
          </Button>
          <Button type="button" variant="ghost" onClick={() => setDraft(null)}>
            Bỏ
          </Button>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="button" onClick={() => setDraft('')}>
          <Plus className="size-4" />
          Thêm nơi nhận
        </Button>
        <Button type="button" onClick={openPicker}>
          <BookUser className="size-4" />
          Nhập từ danh bạ
        </Button>
      </div>

      <Dialog open={pickerOpen} onOpenChange={setPickerOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Chọn từ danh bạ</DialogTitle>
            <DialogDescription>
              Danh sách đơn vị đang bật trong danh mục Đối tác văn bản.
            </DialogDescription>
          </DialogHeader>

          <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
            {partners.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Danh bạ chưa có đơn vị nào. Thêm ở màn "Đối tác văn bản".
              </p>
            )}

            {partners.map((partner) => (
              <div key={partner.id} className="flex items-center gap-2">
                <Checkbox
                  id={`recipient-${partner.id}`}
                  checked={checked.includes(partner.name)}
                  disabled={value.includes(partner.name)}
                  onCheckedChange={(state) =>
                    setChecked((current) =>
                      state
                        ? [...current, partner.name]
                        : current.filter((name) => name !== partner.name),
                    )
                  }
                />
                <Label htmlFor={`recipient-${partner.id}`} className="font-normal">
                  {partner.name}
                  {value.includes(partner.name) && (
                    <span className="text-muted-foreground"> — đã chọn</span>
                  )}
                </Label>
              </div>
            ))}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setPickerOpen(false)}>
              Hủy
            </Button>
            <Button
              type="button"
              disabled={checked.length === 0}
              onClick={() => {
                addNames(checked)
                setPickerOpen(false)
              }}
            >
              Thêm {checked.length > 0 && `(${checked.length})`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
