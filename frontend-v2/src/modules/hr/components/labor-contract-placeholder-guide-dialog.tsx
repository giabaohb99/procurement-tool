import { Loader2 } from 'lucide-react'
import { useMemo } from 'react'

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { CopyButton } from '@/shared/ui/copy-button'
import { useLaborContractPlaceholders } from '../hooks/use-labor-contract-templates'
import { formatPlaceholderToken, groupPlaceholders } from '../utils/labor-contract-placeholder-groups'

interface GuideDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** Bảng hướng dẫn biến dùng trong mẫu .docx. Danh mục đọc từ API, không chép sang TS. */
export function LaborContractPlaceholderGuideDialog({ open, onOpenChange }: GuideDialogProps) {
  const { data, isLoading, isError } = useLaborContractPlaceholders(open)
  const groups = useMemo(() => groupPlaceholders(data), [data])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[85vh] flex-col sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Danh sách biến trong mẫu hợp đồng</DialogTitle>
          <DialogDescription>
            Gõ biến vào tệp Word đúng dạng <code>{formatPlaceholderToken('ten_bien')}</code>. Biến ngoài
            danh sách này sẽ bị từ chối khi tải mẫu lên. Gõ liền một lần, không định dạng giữa chừng.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto pr-1">
          {isLoading && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Đang tải danh sách biến…
            </p>
          )}
          {isError && <p className="text-sm text-destructive">Không tải được danh sách biến.</p>}
          {groups.map(({ group, items }) => (
            <section key={group}>
              <h3 className="mb-1.5 text-sm font-semibold">{group}</h3>
              <ul className="divide-y rounded-md border">
                {items.map((item) => (
                  <li key={item.key} className="flex items-center gap-3 px-3 py-1.5 text-sm">
                    <code className="w-52 shrink-0 font-mono text-xs">{formatPlaceholderToken(item.key)}</code>
                    <span className="min-w-0 flex-1 truncate">{item.label}</span>
                    <span className="hidden w-48 truncate text-muted-foreground sm:block" title={item.example}>
                      {item.example}
                    </span>
                    <CopyButton value={formatPlaceholderToken(item.key)} label={`biến ${item.label}`} />
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
