import { SendHorizonal } from 'lucide-react'
import { useState, type KeyboardEvent } from 'react'

import { Button } from '@/shared/ui/button'
import { Textarea } from '@/shared/ui/textarea'

interface ChatComposerProps {
  disabled: boolean
  onSend: (message: string) => void
}

/** Ô soạn câu hỏi. Enter để gửi, Shift+Enter xuống dòng. */
export function ChatComposer({ disabled, onSend }: ChatComposerProps) {
  const [text, setText] = useState('')

  const submit = () => {
    const value = text.trim()
    if (!value || disabled) return
    onSend(value)
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t p-3">
      <div className="flex items-end gap-2">
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nhập câu hỏi… (Enter để gửi, Shift+Enter xuống dòng)"
          rows={2}
          className="max-h-40 min-h-[2.5rem] flex-1 resize-none"
        />
        <Button
          type="button"
          size="icon"
          onClick={submit}
          disabled={disabled || text.trim().length === 0}
          title="Gửi"
        >
          <SendHorizonal className="size-4" />
        </Button>
      </div>
    </div>
  )
}
