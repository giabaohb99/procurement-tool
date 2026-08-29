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
import { Eye, EyeOff, GripVertical, Pencil, Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'
import {
  BUILTIN_CARD_FIELDS,
  labelFieldId,
  type CardFieldKey,
  type CardFields,
} from '../types/view-options'
import type { WorkLabelField } from '../types/work'
import { FieldEditDialog } from './field-edit-dialog'

interface CardFieldsMenuProps {
  listId: number
  fields: CardFields
  labelFields: WorkLabelField[]
  onChange: (fields: CardFields) => void
  /** Mở màn Thiết lập để khai thêm nhãn tùy biến; vắng = không có quyền. */
  onAddField?: () => void
  /** ADMIN trở lên mới được sửa trường tùy biến — 04 §3. */
  canManage: boolean
}

/**
 * Menu «Tùy chỉnh» — chọn trường nào hiện trên thẻ và XẾP THỨ TỰ, đúng khuôn
 * *Customize* của Lark.
 *
 * Thứ tự trong danh sách này chính là thứ tự các dòng vẽ trên thẻ, nên phải kéo
 * thả được: đọc thẻ mà «Bình luận» nằm trên «Độ ưu tiên» thì mắt phải dò lại từ
 * đầu mỗi lần.
 *
 * `DndContext` RIÊNG của menu, không dùng chung với bảng kanban: hai ngữ cảnh
 * lồng nhau thì mọi cú kéo thẻ việc cũng bắn vào đây.
 *
 * Nút BÚT CHÌ mở hộp thoại «Sửa trường» — MỘT khuôn cho mọi trường tùy biến,
 * Tag và Độ ưu tiên cũng vậy: tên · kiểu · bộ giá trị kéo xếp được · xóa trường.
 *
 * Trước đây muốn sửa một chữ trong bộ giá trị phải đóng menu, mở *Quản lý dự án
 * → Thiết lập*, rồi tìm lại đúng trường đó. Bốn trường dựng sẵn (Phụ trách ·
 * Hạn chót · Việc con · Số bình luận) không có gì để sửa nên không có bút chì.
 */
export function CardFieldsMenu({
  listId,
  fields,
  labelFields,
  onChange,
  onAddField,
  canManage,
}: CardFieldsMenuProps) {
  const [truongDangSua, setTruongDangSua] = useState<WorkLabelField | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const from = fields.findIndex((f) => f.key === active.id)
    const to = fields.findIndex((f) => f.key === over.id)
    if (from === -1 || to === -1) return
    const next = [...fields]
    const [moved] = next.splice(from, 1)
    next.splice(to, 0, moved)
    onChange(next)
  }

  function toggle(key: CardFieldKey) {
    onChange(fields.map((f) => (f.key === key ? { ...f, visible: !f.visible } : f)))
  }

  /** Trường tùy biến đứng sau dòng này, hoặc `null` nếu dòng đó không sửa được. */
  function editableField(key: CardFieldKey): WorkLabelField | null {
    if (!canManage) return null
    const id = labelFieldId(key)
    if (id === null) return null
    return labelFields.find((f) => f.id === id) ?? null
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between px-1 pb-1">
        <p className="text-sm font-medium">Hiện trên thẻ</p>
        {onAddField && (
          <Button variant="ghost" size="sm" className="h-7 px-2" onClick={onAddField}>
            <Plus className="size-3.5" />
            Trường mới
          </Button>
        )}
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext
          items={fields.map((f) => f.key)}
          strategy={verticalListSortingStrategy}
        >
          {fields.map((field) => {
            const target = editableField(field.key)
            return (
              <FieldRow
                key={field.key}
                fieldKey={field.key}
                label={fieldLabel(field.key, labelFields)}
                visible={field.visible}
                onEdit={target ? () => setTruongDangSua(target) : undefined}
                onToggle={() => toggle(field.key)}
              />
            )
          })}
        </SortableContext>
      </DndContext>

      <FieldEditDialog
        listId={listId}
        field={truongDangSua}
        onClose={() => setTruongDangSua(null)}
      />
    </div>
  )
}

/** Tên hiện ra cho một khóa trường; nhãn tùy biến lấy tên do dự án tự đặt. */
function fieldLabel(key: CardFieldKey, labelFields: WorkLabelField[]): string {
  const id = labelFieldId(key)
  if (id !== null) return labelFields.find((f) => f.id === id)?.name ?? 'Nhãn đã xóa'
  return BUILTIN_CARD_FIELDS.find((f) => f.key === key)?.label ?? key
}

function FieldRow({
  fieldKey,
  label,
  visible,
  onEdit,
  onToggle,
}: {
  fieldKey: CardFieldKey
  label: string
  visible: boolean
  /** Vắng = trường này không sửa được (dựng sẵn, hoặc không đủ quyền). */
  onEdit?: () => void
  onToggle: () => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: fieldKey,
  })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={cn(
        'flex items-center gap-1 rounded px-1 py-1 hover:bg-accent',
        isDragging && 'opacity-50',
      )}
    >
      {/*  Tay cầm RIÊNG, không phải cả dòng: kéo cả dòng thì bấm con mắt cũng
          bị nuốt thành một cú kéo dài 0 pixel. */}
      <span
        {...attributes}
        {...listeners}
        className="cursor-grab text-muted-foreground"
        aria-label={`Kéo để đổi thứ tự ${label}`}
      >
        <GripVertical className="size-4" />
      </span>

      <span className={cn('flex-1 truncate text-sm', !visible && 'text-muted-foreground')}>
        {label}
      </span>

      {onEdit && (
        <IconTooltip label={`Sửa trường ${label}`}>
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            aria-label={`Sửa trường ${label}`}
            onClick={onEdit}
          >
            <Pencil className="size-3.5" />
          </Button>
        </IconTooltip>
      )}

      <Button
        variant="ghost"
        size="icon"
        className="size-7"
        aria-label={visible ? `Ẩn ${label} khỏi thẻ` : `Hiện ${label} trên thẻ`}
        aria-pressed={visible}
        onClick={onToggle}
      >
        {visible ? (
          <Eye className="size-4" />
        ) : (
          <EyeOff className="size-4 text-muted-foreground" />
        )}
      </Button>
    </div>
  )
}
