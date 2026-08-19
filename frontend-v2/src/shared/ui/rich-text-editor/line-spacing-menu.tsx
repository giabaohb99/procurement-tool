import type { Editor } from '@tiptap/react'
import { Check, ChevronsUpDown } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { LINE_HEIGHTS } from './editor-options'
import {
  DEFAULT_LINE_SPACING,
  MAX_LINE_SPACING,
  MIN_LINE_SPACING,
  parseLineSpacingInput,
  wordLineSpacingToCss,
} from './word-line-spacing'

interface LineSpacingMenuProps {
  editor: Editor
  /** Giãn dòng của đoạn đang đứng, tính bằng SỐ DÒNG kiểu Word; `null` = theo trang. */
  current: number | null
}

/**
 * Menu GIÃN DÒNG — bày đúng bộ nấc của Word (1,0 · 1,15 · 1,5 · 2,0 · 2,5 · 3,0),
 * tick vào nấc đang dùng, và mở được ô tùy chỉnh cho số nằm ngoài bộ nấc đó.
 *
 * Tách khỏi `editor-toolbar.tsx` vì nó có trạng thái riêng (hộp thoại tùy chỉnh),
 * còn thanh công cụ thì chỉ nên là danh sách lệnh.
 */
export function LineSpacingMenu({ editor, current }: LineSpacingMenuProps) {
  const [customOpen, setCustomOpen] = useState(false)
  const [draft, setDraft] = useState('')

  /** Không đặt gì = đoạn ăn theo giãn dòng của trang, mà trang đang để 1 dòng. */
  const effective = current ?? DEFAULT_LINE_SPACING

  function apply(lines: number) {
    editor.chain().focus().setLineHeight(wordLineSpacingToCss(lines)).run()
  }

  function openCustom() {
    setDraft(String(effective).replace('.', ','))
    setCustomOpen(true)
  }

  function submitCustom(event: FormEvent) {
    event.preventDefault()
    const lines = parseLineSpacingInput(draft)
    if (lines === null) return
    apply(lines)
    setCustomOpen(false)
  }

  const invalid = draft.trim() !== '' && parseLineSpacingInput(draft) === null

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            title="Giãn dòng"
            aria-label="Giãn dòng"
            // Giữ con trỏ trong vùng soạn thảo, nếu không lệnh áp vào chỗ khác.
            onMouseDown={(event) => event.preventDefault()}
          >
            <ChevronsUpDown className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-44">
          {LINE_HEIGHTS.map((option) => (
            <DropdownMenuItem
              key={option.value}
              onSelect={() => apply(option.lines)}
              className="justify-between"
            >
              {option.label}
              {effective === option.lines && <Check className="size-4" />}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={openCustom}>Tùy chỉnh…</DropdownMenuItem>
          <DropdownMenuItem onSelect={() => editor.chain().focus().setLineHeight(null).run()}>
            Theo mặc định của trang
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={customOpen} onOpenChange={setCustomOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Giãn dòng tùy chỉnh</DialogTitle>
            <DialogDescription>
              Nhập số dòng như trong Word, ví dụ 1,3. Áp cho đoạn đang đứng hoặc phần đang bôi
              đen.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={submitCustom} className="space-y-2">
            <Label htmlFor="line-spacing-custom">Số dòng</Label>
            <Input
              id="line-spacing-custom"
              autoFocus
              inputMode="decimal"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              aria-invalid={invalid}
            />
            <p className="text-xs text-muted-foreground">
              {invalid
                ? `Chỉ nhận số từ ${MIN_LINE_SPACING} đến ${MAX_LINE_SPACING}.`
                : `Từ ${MIN_LINE_SPACING} đến ${MAX_LINE_SPACING} dòng.`}
            </p>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setCustomOpen(false)}>
                Hủy
              </Button>
              <Button type="submit" disabled={parseLineSpacingInput(draft) === null}>
                Áp dụng
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  )
}
