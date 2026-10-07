// duoc-CR-606 (07/10/2026) — khung «Chèn biến» cạnh trình soạn mẫu: bấm một biến là chèn
// `{{ ma_bien }}` vào đúng chỗ con trỏ. Trước đây người soạn phải tự gõ biến trong Word, gõ sai
// một chữ là bị chặn lúc tải lên. Danh mục đọc từ API (backend giữ), KHÔNG chép sang TS.
import { Braces, Loader2 } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Card } from '@/shared/ui/card'
import { SearchField } from '@/shared/ui/search-field'
import { cn } from '@/shared/utils/cn'
import { useLaborContractPlaceholders } from '../hooks/use-labor-contract-templates'
import {
  filterPlaceholders,
  formatPlaceholderToken,
  groupPlaceholders,
} from '../utils/labor-contract-placeholder-groups'

interface PlaceholderInsertPanelProps {
  /** Chèn chuỗi biến (`{{ ma_bien }}`) vào chỗ con trỏ của trình soạn thảo. */
  onInsert: (token: string) => void
  disabled?: boolean
  className?: string
}

export function LaborContractPlaceholderInsertPanel({ onInsert, disabled, className }: PlaceholderInsertPanelProps) {
  const [query, setQuery] = useState('')
  const { data, isLoading, isError } = useLaborContractPlaceholders(true)
  const groups = useMemo(() => groupPlaceholders(filterPlaceholders(data, query)), [data, query])

  return (
    <Card className={cn('flex min-h-0 flex-col gap-3 p-3', className)}>
      <div>
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Braces className="size-4 text-primary" />
          Chèn biến
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Đặt con trỏ vào chỗ cần điền rồi bấm biến. Khi lập hợp đồng, biến tự thay bằng dữ liệu của nhân sự.
        </p>
      </div>
      {/* `flex-none`: ô tìm dùng chung có sẵn `flex-1`, trong cột dọc nó bị kéo cao chiếm hết chỗ trống. */}
      <SearchField value={query} onChange={setQuery} placeholder="Tìm biến…" aria-label="Tìm biến" className="flex-none" />

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        {isLoading && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" /> Đang tải danh sách biến…
          </p>
        )}
        {isError && <p className="text-sm text-destructive">Không tải được danh sách biến.</p>}
        {!isLoading && !isError && groups.length === 0 && (
          <p className="text-sm text-muted-foreground">Không có biến nào khớp «{query.trim()}».</p>
        )}
        {groups.map(({ group, items }) => (
          <section key={group}>
            <h3 className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{group}</h3>
            <ul className="space-y-0.5">
              {items.map((item) => (
                <li key={item.key}>
                  <button
                    type="button"
                    disabled={disabled}
                    title={item.example ? `Ví dụ: ${item.example}` : undefined}
                    aria-label={`Chèn biến ${item.label}`}
                    //  Giữ vùng chọn của trình soạn: bấm nút mà để mất focus trước khi chèn thì biến
                    //  rơi về đầu tài liệu thay vì chỗ con trỏ đang đứng.
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => onInsert(formatPlaceholderToken(item.key))}
                    className="flex w-full flex-col rounded-md px-2 py-1 text-left hover:bg-accent disabled:pointer-events-none disabled:opacity-50"
                  >
                    <span className="text-sm">{item.label}</span>
                    <code className="font-mono text-xs text-muted-foreground">{formatPlaceholderToken(item.key)}</code>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Card>
  )
}
