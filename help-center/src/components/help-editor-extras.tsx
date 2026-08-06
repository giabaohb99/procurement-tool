import { useState } from 'react'
import { ChevronDown, Code2, FileCode2, Table2, WandSparkles } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { TABLE_ACTIONS, TABLE_GRID_MAX, type TableCommand } from '@/lib/quill-table-actions'
import { cn } from '@/lib/utils'

// Ba nút riêng của khu quản trị — chèn bảng, nhúng mã, xem/sửa HTML — được portal vào CUỐI
// thanh công cụ do Quill dựng (xem help-rich-editor). Không bọc thêm khung nào ở đây: phần tử
// gốc là <span class="hc-editor-extras"> do bên gọi tạo sẵn trong thanh công cụ.

export interface EditorExtrasProps {
  /** Đang ở chế độ sửa mã HTML nguồn. */
  htmlMode: boolean
  onToggleHtml: () => void
  /** Bản Quill đang chạy có module bảng hay không — không có thì ẩn nút Bảng. */
  tableEnabled: boolean
  onInsertTable: (rows: number, columns: number) => void
  onTableAction: (key: TableCommand) => void
  onOpenEmbed: () => void
}

export default function HelpEditorExtras({
  htmlMode, onToggleHtml, tableEnabled, onInsertTable, onTableAction, onOpenEmbed,
}: EditorExtrasProps) {
  return (
    <>
      {tableEnabled && !htmlMode && (
        <TableMenu onInsert={onInsertTable} onAction={onTableAction} />
      )}

      {!htmlMode && (
        <Button
          type="button" variant="ghost" size="icon" className="size-7"
          aria-label="Nhúng mã"
          title="Nhúng mã — dán mã nhúng của Guideflow, YouTube, Google Sheets... (kể cả đoạn có <script>)"
          onClick={onOpenEmbed}
        >
          <Code2 className="size-4" />
        </Button>
      )}

      <Button
        type="button" variant="ghost" size="icon" className="size-7"
        // Trạng thái bật tô bằng CSS (xem article-content.css) — variant="default" của shadcn
        // bị `background: none` của quill.snow.css đè mất
        data-active={htmlMode}
        aria-label={htmlMode ? 'Soạn trực quan' : 'Mã HTML'}
        title={htmlMode
          ? 'Quay lại soạn thảo trực quan'
          : 'Mã HTML — xem và sửa trực tiếp mã nguồn của bài viết'}
        onClick={onToggleHtml}
      >
        {htmlMode ? <WandSparkles className="size-4" /> : <FileCode2 className="size-4" />}
      </Button>
    </>
  )
}

/** Nút "Bảng": lưới chọn nhanh số hàng × cột + các thao tác trên bảng đang đặt con trỏ. */
function TableMenu({
  onInsert, onAction,
}: {
  onInsert: (rows: number, columns: number) => void
  onAction: (key: TableCommand) => void
}) {
  const [hover, setHover] = useState<{ rows: number; cols: number } | null>(null)
  const [rows, setRows] = useState('3')
  const [cols, setCols] = useState('3')

  const submitSize = () => {
    const r = Math.min(Math.max(parseInt(rows, 10) || 0, 1), 50)
    const c = Math.min(Math.max(parseInt(cols, 10) || 0, 1), 20)
    onInsert(r, c)
  }

  return (
    <DropdownMenu onOpenChange={(open) => { if (!open) setHover(null) }}>
      <DropdownMenuTrigger asChild>
        <Button
          type="button" variant="ghost" size="sm" className="h-7 gap-0.5 px-1.5"
          aria-label="Bảng"
          title="Bảng — chèn bảng, thêm/xóa hàng cột, gộp ô"
        >
          <Table2 className="size-4" /> <ChevronDown className="size-3" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-56">
        <div className="px-2 pb-1 pt-1.5 text-xs font-medium text-muted-foreground">
          {hover ? `Chèn bảng ${hover.rows} × ${hover.cols}` : 'Chọn số hàng × cột'}
        </div>

        <div
          className="grid gap-0.5 px-2 pb-2"
          style={{ gridTemplateColumns: `repeat(${TABLE_GRID_MAX}, 1fr)` }}
          onMouseLeave={() => setHover(null)}
        >
          {Array.from({ length: TABLE_GRID_MAX * TABLE_GRID_MAX }, (_, i) => {
            const rows = Math.floor(i / TABLE_GRID_MAX) + 1
            const cols = (i % TABLE_GRID_MAX) + 1
            const active = !!hover && rows <= hover.rows && cols <= hover.cols
            return (
              <button
                key={i}
                type="button"
                aria-label={`Bảng ${rows} hàng ${cols} cột`}
                onMouseEnter={() => setHover({ rows, cols })}
                onClick={() => onInsert(rows, cols)}
                className={cn(
                  'h-5 rounded-[3px] border transition-colors',
                  active ? 'border-primary bg-primary/25' : 'border-border bg-background',
                )}
              />
            )
          })}
        </div>

        {/* Lưới chỉ tới 6×6 — bảng to hơn thì gõ thẳng số vào đây.
            stopPropagation là BẮT BUỘC: menu Radix có typeahead + điều hướng bằng phím mũi tên,
            không chặn thì ký tự gõ vào ô số bị menu nuốt và con trỏ nhảy sang mục khác. */}
        <div
          className="flex items-center gap-1.5 px-2 pb-2 text-xs text-muted-foreground"
          onKeyDown={(e) => e.stopPropagation()}
        >
          <span className="shrink-0">Hoặc</span>
          <Input
            type="number" min={1} max={50} value={rows} aria-label="Số hàng"
            onChange={(e) => setRows(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') submitSize() }}
            className="h-7 w-12 px-1.5 text-center text-xs"
          />
          <span className="shrink-0">×</span>
          <Input
            type="number" min={1} max={20} value={cols} aria-label="Số cột"
            onChange={(e) => setCols(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') submitSize() }}
            className="h-7 w-12 px-1.5 text-center text-xs"
          />
          <Button size="sm" className="h-7 px-2 text-xs" onClick={submitSize}>Chèn</Button>
        </div>

        <DropdownMenuSeparator />

        {TABLE_ACTIONS.map((action) => (
          <DropdownMenuItem
            key={action.key}
            variant={action.danger ? 'destructive' : 'default'}
            onClick={() => onAction(action.key)}
          >
            {action.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
