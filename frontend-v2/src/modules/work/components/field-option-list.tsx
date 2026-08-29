import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Plus, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import type { DraftOption } from '../utils/save-field-options'
import { dotClass } from '../utils/work-colors'
import { WorkColorPicker } from './work-color-picker'

interface FieldOptionListProps {
  options: DraftOption[]
  onChange: (next: DraftOption[]) => void
}

/**
 * BỘ GIÁ TRỊ của một trường: kéo xếp thứ tự · đổi màu · đổi tên · bỏ dòng.
 *
 * Chỉ giữ BẢN NHÁP, không tự gọi API — chốt bằng nút Lưu của hộp thoại cha
 * (`saveFieldOptions`). Bắn lệnh theo từng phím gõ thì danh sách nhấp nháy và
 * người dùng không có đường lui.
 *
 * `DndContext` RIÊNG, không dùng chung với bảng kanban hay menu «Tùy chỉnh»:
 * ngữ cảnh lồng nhau thì mọi cú kéo ở ngoài cũng bắn vào đây.
 */
export function FieldOptionList({ options, onChange }: FieldOptionListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function keoXep(su: DragEndEvent) {
    const { active, over } = su
    if (!over || active.id === over.id) return
    const tu = options.findIndex((o) => String(o.id) === active.id)
    const den = options.findIndex((o) => String(o.id) === over.id)
    if (tu === -1 || den === -1) return
    const sau = [...options]
    const [doi] = sau.splice(tu, 1)
    sau.splice(den, 0, doi)
    onChange(sau)
  }

  function sua(id: number, patch: Partial<DraftOption>) {
    onChange(options.map((o) => (o.id === id ? { ...o, ...patch } : o)))
  }

  return (
    <div className="space-y-1.5">
      <div className="max-h-72 space-y-1 overflow-y-auto pr-1">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={keoXep}>
          <SortableContext
            items={options.map((o) => String(o.id))}
            strategy={verticalListSortingStrategy}
          >
            {options.map((o) => (
              <OptionRow
                key={o.id}
                option={o}
                onChange={(patch) => sua(o.id, patch)}
                onRemove={() => onChange(options.filter((x) => x.id !== o.id))}
              />
            ))}
          </SortableContext>
        </DndContext>
        {options.length === 0 && (
          <p className="px-1 py-2 text-sm text-muted-foreground">Chưa có giá trị nào.</p>
        )}
      </div>

      <Button
        variant="ghost"
        size="sm"
        className="h-7 px-1 text-muted-foreground hover:text-foreground"
        onClick={() =>
          onChange([
            ...options,
            //  Id ÂM cho dòng chưa có ở máy chủ, giảm dần để không trùng nhau —
            //  `key` của React và id kéo thả đều dựa vào nó.
            { id: -(options.length + 1), name: '', color: 'sky' },
          ])
        }
      >
        <Plus className="size-4" />
        Thêm giá trị
      </Button>
    </div>
  )
}

function OptionRow({
  option,
  onChange,
  onRemove,
}: {
  option: DraftOption
  onChange: (patch: Partial<DraftOption>) => void
  onRemove: () => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: String(option.id),
  })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={cn('flex items-center gap-1.5', isDragging && 'opacity-50')}
    >
      {/*  Tay cầm RIÊNG, không kéo cả dòng: kéo cả dòng thì không bôi đen được
          chữ trong ô tên. */}
      <span
        {...attributes}
        {...listeners}
        aria-label={`Kéo để đổi thứ tự ${option.name || 'giá trị mới'}`}
        className="cursor-grab text-muted-foreground"
      >
        <GripVertical className="size-4" />
      </span>

      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label={`Màu của ${option.name || 'giá trị mới'}`}
            className={cn(
              'size-5 shrink-0 rounded-full ring-offset-2 ring-offset-background hover:ring-2 hover:ring-ring/50',
              dotClass(option.color),
            )}
          />
        </PopoverTrigger>
        <PopoverContent align="start" className="w-auto p-2">
          <WorkColorPicker
            value={option.color}
            onChange={(color) => onChange({ color })}
            className="max-w-40"
          />
        </PopoverContent>
      </Popover>

      <Input
        value={option.name}
        aria-label="Tên giá trị"
        placeholder="Tên giá trị"
        className="h-8"
        onChange={(su) => onChange({ name: su.target.value })}
      />

      <IconTooltip label="Bỏ giá trị này">
        <Button variant="ghost" size="icon-sm" aria-label="Bỏ giá trị này" onClick={onRemove}>
          <X className="size-4" />
        </Button>
      </IconTooltip>
    </div>
  )
}
