import { Command as CommandPrimitive } from 'cmdk'
import { CornerDownLeft, ExternalLink, Search } from 'lucide-react'
import { Fragment, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { allModules } from '@/app/router/module-registry'
import {
  buildModuleSearchEntries,
  searchModuleEntries,
  type ModuleSearchEntry,
} from '@/app/search/module-search-index'
import { splitSearchHighlight } from '@/app/search/split-search-highlight'
import { useNavContext, usePermission } from '@/core/authorization/use-permission'
import { CommandEmpty, CommandGroup, CommandItem, CommandList } from '@/shared/ui/command'
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'

interface ModuleSearchDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Hộp tìm phân hệ và chức năng kiểu trang tài liệu (duoc-CR-781): gõ là ra cả phân hệ lẫn từng mục menu bên
 * trong, gom theo phân hệ; phím mũi tên chọn, Enter mở.
 *
 * Dựng thẳng trên `cmdk` thay vì `CommandDialog` của shadcn vì hai lẽ: cần `shouldFilter={false}` để dùng luật
 * khớp tiếng Việt không dấu + khớp từng chữ của `searchModuleEntries` (bộ lọc sẵn của cmdk so thô, gõ "don mua"
 * không ra "Đơn mua hàng"); và ô nhập phải to, có nhãn `Esc` — khung ô nhập của shadcn cố định cao 36px.
 */
export function ModuleSearchDialog({ open, onOpenChange }: ModuleSearchDialogProps) {
  const navigate = useNavigate()

  function openEntry(entry: ModuleSearchEntry) {
    onOpenChange(false)
    if (entry.externalUrl) {
      window.open(entry.externalUrl(), '_blank', 'noopener,noreferrer')
      return
    }
    navigate(entry.path)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/*  `top-[10vh] translate-y-0`: neo gần đỉnh như hộp tìm của trang tài liệu — canh giữa dọc thì danh sách
           kết quả co giãn theo chữ gõ làm cả hộp nhảy lên nhảy xuống. */}
      <DialogContent
        className="top-[10vh] translate-y-0 gap-0 overflow-hidden rounded-xl border-border/70 p-0 shadow-2xl sm:max-w-2xl"
        showCloseButton={false}
      >
        <DialogTitle className="sr-only">Tìm phân hệ, chức năng</DialogTitle>
        <DialogDescription className="sr-only">
          Gõ tên phân hệ hoặc chức năng, dùng phím mũi tên để chọn và Enter để mở.
        </DialogDescription>
        {/*  Thân hộp là component RIÊNG nằm trong `DialogContent`: Radix gỡ phần này mỗi lần đóng, nên chữ đã gõ
             tự mất dù đóng bằng Esc, bấm ra ngoài hay Ctrl+K — giữ chữ ở hàm ngoài thì đường Ctrl+K quên xóa. */}
        <ModuleSearchPanel onOpenEntry={openEntry} />
      </DialogContent>
    </Dialog>
  )
}

/** Ô nhập + danh sách kết quả + chân hộp; giữ chữ đang gõ (xem ghi chú chỗ dựng ở `ModuleSearchDialog`). */
function ModuleSearchPanel({ onOpenEntry }: { onOpenEntry: (entry: ModuleSearchEntry) => void }) {
  const { can } = usePermission()
  const navCtx = useNavContext()
  const [query, setQuery] = useState('')

  //  Phụ thuộc theo TỪNG TRƯỜNG: `useNavContext` dựng object mới mỗi lượt vẽ, phụ thuộc cả object là dựng lại
  //  danh mục mỗi lần gõ một chữ.
  const { isDriver, reportKeys } = navCtx
  const entries = useMemo(
    () => buildModuleSearchEntries(allModules, can, { isDriver, reportKeys }),
    [can, isDriver, reportKeys],
  )
  const groups = useMemo(() => searchModuleEntries(entries, query), [entries, query])
  const typing = query.trim().length > 0
  const resultCount = groups.reduce((total, group) => total + group.entries.length, 0)

  return (
    <CommandPrimitive shouldFilter={false} loop className="flex flex-col">
      <div className="flex h-14 items-center gap-3 border-b px-4">
        <Search className="size-5 shrink-0 text-primary" />
        <CommandPrimitive.Input
          value={query}
          onValueChange={setQuery}
          placeholder="Tìm phân hệ, chức năng…"
          className="h-full flex-1 bg-transparent text-base outline-hidden placeholder:text-muted-foreground"
        />
        <Kbd className="max-sm:hidden">Esc</Kbd>
      </div>

      <CommandList className="max-h-[min(62vh,30rem)] overscroll-contain p-2">
        <CommandEmpty className="px-4 py-12 text-center text-sm text-muted-foreground">
          Không có phân hệ hay chức năng nào khớp "{query.trim()}".
        </CommandEmpty>

        {/*  Chưa gõ thì `searchModuleEntries` trả MỘT nhóm "Phân hệ" — vẽ y như kết quả tìm: danh sách dọc, mỗi
             dòng kèm mô tả nhỏ. */}
        {groups.map((group) => (
          <CommandGroup
            key={group.moduleId || 'modules'}
            heading={group.moduleTitle}
            className="p-0 pb-1 [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:pt-3 [&_[cmdk-group-heading]]:pb-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:uppercase"
          >
            {group.entries.map((entry) => (
              <ResultRow
                key={entry.id}
                entry={entry}
                query={query}
                onSelect={() => onOpenEntry(entry)}
              />
            ))}
          </CommandGroup>
        ))}
      </CommandList>

      <div className="flex items-center justify-between gap-3 border-t bg-muted/40 px-4 py-2.5 text-xs text-muted-foreground">
        <span className="flex items-center gap-3 max-sm:hidden">
          <span className="flex items-center gap-1">
            <Kbd>↑</Kbd>
            <Kbd>↓</Kbd> chọn
          </span>
          <span className="flex items-center gap-1">
            <Kbd>↵</Kbd> mở
          </span>
        </span>
        <span className="max-sm:mx-auto">
          {typing
            ? `${resultCount} kết quả`
            : `${groups[0]?.entries.length ?? 0} phân hệ đang dùng`}
        </span>
      </div>
    </CommandPrimitive>
  )
}

/** Một dòng kết quả: biểu tượng · tên (tô chữ khớp) · đường dẫn mờ · dấu ↵ khi đang chọn. */
function ResultRow({
  entry,
  query,
  onSelect,
}: {
  entry: ModuleSearchEntry
  query: string
  onSelect: () => void
}) {
  //  Dòng phụ: phân hệ thì mô tả việc của nó; mục con thì đường dẫn "Phân hệ › Nhóm" để phân biệt hai mục cùng
  //  tên ở hai phân hệ (vd "Tổng quan", "Báo cáo").
  const subtitle =
    entry.kind === 'module' ? entry.description : [entry.moduleTitle, ...entry.trail].join(' › ')
  return (
    <CommandItem
      value={entry.id}
      onSelect={onSelect}
      className="group gap-3 rounded-lg px-3 py-2 data-[selected=true]:bg-primary/10"
    >
      <EntryIcon entry={entry} className="size-8" />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-foreground">
          {/*  Khúc KHÔNG khớp để chữ trơn, không bọc `<span>`: mỗi khúc một thẻ thì trình đọc màn hình ghép tên
               bỏ mất khoảng trắng ở mép thẻ ("Đơn mua hàng" đọc thành "Đơnmuahàng"). */}
          {splitSearchHighlight(entry.label, query).map((part, index) =>
            part.match ? (
              <mark key={index} className="bg-transparent font-semibold text-primary">
                {part.text}
              </mark>
            ) : (
              <Fragment key={index}>{part.text}</Fragment>
            ),
          )}
        </span>
        {subtitle && (
          <span className="block truncate text-xs text-muted-foreground">{subtitle}</span>
        )}
      </span>
      {entry.externalUrl ? (
        <ExternalLink className="size-3.5 shrink-0 text-muted-foreground" aria-label="Mở tab mới" />
      ) : (
        <CornerDownLeft className="size-4 shrink-0 text-primary opacity-0 group-data-[selected=true]:opacity-100" />
      )}
    </CommandItem>
  )
}

function EntryIcon({ entry, className }: { entry: ModuleSearchEntry; className?: string }) {
  const Icon = entry.icon
  return (
    <span className={cn('grid shrink-0 place-items-center rounded-md', entry.accent, className)}>
      <Icon className="size-4" />
    </span>
  )
}

function Kbd({ children, className }: { children: string; className?: string }) {
  return (
    <kbd
      className={cn(
        'inline-grid h-5 min-w-5 place-items-center rounded border bg-background px-1 font-sans text-[11px] text-muted-foreground shadow-xs',
        className,
      )}
    >
      {children}
    </kbd>
  )
}
