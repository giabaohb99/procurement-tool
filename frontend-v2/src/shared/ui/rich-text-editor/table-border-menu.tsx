import type { Editor } from '@tiptap/react'
import { Grid2X2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { ColorPalette } from './color-palette'
import { setCellBorders, type TableBorderPreset } from './table-commands'

const BORDER_WIDTHS = [
  { label: '0,5 pt', value: '0.67px' },
  { label: '0,75 pt', value: '1px' },
  { label: '1 pt', value: '1.33px' },
  { label: '1,5 pt', value: '2px' },
  { label: '2,25 pt', value: '3px' },
]

const BORDER_STYLES = [
  { label: 'Nét liền', value: 'solid' },
  { label: 'Nét đứt', value: 'dashed' },
  { label: 'Nét chấm', value: 'dotted' },
]

const BORDER_PRESETS: Array<{ label: string; value: TableBorderPreset }> = [
  { label: 'Tất cả viền', value: 'all' },
  { label: 'Viền bên ngoài', value: 'outside' },
  { label: 'Viền bên trong', value: 'inside' },
  { label: 'Không viền', value: 'none' },
  { label: 'Viền trên', value: 'top' },
  { label: 'Viền dưới', value: 'bottom' },
  { label: 'Viền trái', value: 'left' },
  { label: 'Viền phải', value: 'right' },
]

interface TableBorderMenuProps {
  editor: Editor
}

/** Công cụ viền chỉ hiện khi con trỏ đang nằm trong bảng. */
export function TableBorderMenu({ editor }: TableBorderMenuProps) {
  const [open, setOpen] = useState(false)
  const [color, setColor] = useState('#334155')
  const [width, setWidth] = useState('1px')
  const [style, setStyle] = useState('solid')

  function applyBorder(preset: TableBorderPreset) {
    setCellBorders(editor, preset, `${width} ${style} ${color}`)
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Viền bảng"
          aria-label="Chỉnh sửa viền bảng"
          aria-expanded={open}
          onMouseDown={(event) => event.preventDefault()}
        >
          <Grid2X2 className="size-4" />
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="w-[19rem] max-w-[calc(100vw-1rem)] p-3"
        onCloseAutoFocus={(event) => event.preventDefault()}
      >
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium">Viền bảng</p>
            <p className="text-xs text-muted-foreground">Áp dụng cho ô hoặc vùng đang chọn.</p>
          </div>
          <span
            aria-label={`Màu viền hiện tại ${color}`}
            className="size-5 shrink-0 rounded border border-border"
            style={{ backgroundColor: color }}
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <label className="space-y-1 text-xs font-medium">
            Kiểu nét
            <Select value={style} onValueChange={setStyle}>
              <SelectTrigger size="sm" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BORDER_STYLES.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>

          <label className="space-y-1 text-xs font-medium">
            Độ dày
            <Select value={width} onValueChange={setWidth}>
              <SelectTrigger size="sm" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BORDER_WIDTHS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        </div>

        <div className="mt-3">
          <p className="mb-1 text-xs font-medium">Màu viền</p>
          <ColorPalette
            clearLabel="Màu viền mặc định"
            onPick={setColor}
            onClear={() => setColor('#9ca3af')}
          />
        </div>

        <div className="mt-2 border-t pt-2">
          <p className="mb-2 text-xs font-medium">Áp dụng viền</p>
          <div className="grid grid-cols-2 gap-1.5">
            {BORDER_PRESETS.map((preset) => (
              <Button
                key={preset.value}
                type="button"
                variant="outline"
                size="sm"
                className="justify-start px-2"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => applyBorder(preset.value)}
              >
                <BorderPreview preset={preset.value} />
                {preset.label}
              </Button>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

/** Hình xem trước bằng CSS để từng kiểu viền nhận ra được ngay khi lướt. */
function BorderPreview({ preset }: { preset: TableBorderPreset }) {
  const showOuter = preset === 'all' || preset === 'outside'
  const showInner = preset === 'all' || preset === 'inside'

  return (
    <span aria-hidden className="relative size-4 shrink-0 text-current">
      <span
        className={cn(
          'absolute inset-0',
          showOuter && 'border border-current',
          preset === 'none' && 'border border-dashed border-muted-foreground/60',
          preset === 'top' && 'border-t-2 border-current',
          preset === 'right' && 'border-r-2 border-current',
          preset === 'bottom' && 'border-b-2 border-current',
          preset === 'left' && 'border-l-2 border-current',
        )}
      />
      {showInner && (
        <>
          <span className="absolute top-1/2 right-0 left-0 border-t border-current" />
          <span className="absolute top-0 bottom-0 left-1/2 border-l border-current" />
        </>
      )}
    </span>
  )
}
