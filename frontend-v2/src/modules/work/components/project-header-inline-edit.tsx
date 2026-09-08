import { useRef, useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import type { WorkList } from '../types/work'

/** Trần khớp cột `tab_work_list.name` — `String(200)` ở `model.py`. */
const NAME_MAX = 200
/** Mô tả là `Text` nên DB không chặn; 1500 là trần do nghiệp vụ đặt. */
const DESCRIPTION_MAX = 1500

interface ProjectHeaderInlineEditProps {
  list: WorkList
  /**
   * Chỉ CHỦ SỞ HỮU mới sửa được — không phải Quản trị. Backend gác `update_list`
   * bằng `CAN_OWN` (`list_service.py`), nên mở ô nhập rộng hơn là người ta gõ
   * xong rồi ăn 403.
   */
  canEdit: boolean
  pending: boolean
  onSave: (values: { name?: string; description?: string }) => void
}

/**
 * TÊN và MÔ TẢ dự án ngay trên tiêu đề trang — bấm thẳng vào chữ là thành ô nhập.
 *
 * Ba luật, cả ba do chủ đầu tư chốt ngày 03/09/2026:
 *
 *  · **Không có cây bút.** Chữ là tiêu đề trang, bấm vào là hành vi đoán được;
 *    thêm icon thì nó dính ngay sau tên nhìn như một phần của tên.
 *  · **Không có nút ✓ / ✗.** Rời ô là LƯU.
 *  · Enter lưu (ô tên), Esc bỏ. Bỏ qua Enter khi bộ gõ tiếng Việt đang ghép chữ
 *    (`isComposing`) — lúc đó Enter nghĩa là "chốt chữ", không phải "lưu".
 *
 * ⚠️ Lưu-khi-rời-ô đi NGƯỢC với `hr/components/role-name-inline-edit.tsx`, chỗ đó
 * cố ý không lưu khi blur. Ghi lại để người sau khỏi tưởng là sót: đây là quyết
 * định của chủ đầu tư cho riêng màn Dự án, không phải hai chỗ quên đồng bộ.
 *
 * Esc phải chặn được nhịp lưu của blur, nếu không thì bấm Esc xong ô mất tiêu
 * điểm và blur lưu đúng cái vừa bảo đừng lưu.
 */
export function ProjectHeaderInlineEdit({
  list,
  canEdit,
  pending,
  onSave,
}: ProjectHeaderInlineEditProps) {
  const [editing, setEditing] = useState<'name' | 'description' | null>(null)
  const [draft, setDraft] = useState('')
  //  Cờ một lần: Esc bật lên, nhịp blur ngay sau đó thấy cờ thì bỏ qua rồi tắt.
  const escapedRef = useRef(false)

  //  Chuyển sang dự án khác thì bỏ dở việc đang sửa. Thiếu nhịp này thì đang sửa
  //  tên dự án A, bấm dự án B ở cây bên trái, ô nhập vẫn mở với chữ của A.
  if (useHasChanged(list.id)) {
    setEditing(null)
    setDraft('')
  }

  function open(field: 'name' | 'description') {
    setDraft(field === 'name' ? list.name : (list.description ?? ''))
    setEditing(field)
  }

  function cancel() {
    escapedRef.current = true
    setEditing(null)
    setDraft('')
  }

  function save() {
    if (editing === null) return
    const value = draft.trim()
    //  Tên rỗng thì BỎ QUA thay vì lưu — xoá trắng rồi rời ô là mất tên dự án mà
    //  không có nút nào hoàn lại. Mô tả rỗng thì hợp lệ, xoá mô tả là việc có thật.
    const current = editing === 'name' ? list.name : (list.description ?? '')
    if (editing === 'name' && !value) {
      setEditing(null)
      return
    }
    if (value !== current) onSave({ [editing]: value })
    setEditing(null)
  }

  function handleBlur() {
    if (escapedRef.current) {
      escapedRef.current = false
      return
    }
    save()
  }

  return (
    //  Nở hết bề ngang còn lại của đầu trang: ô mô tả phải đủ rộng để một câu
    //  bình thường nằm gọn một dòng, không bị bẻ giữa chừng.
    <div className="min-w-0 flex-1">
      {editing === 'name' ? (
        <Input
          autoFocus
          value={draft}
          disabled={pending}
          maxLength={NAME_MAX}
          aria-label="Tên dự án"
          onChange={(e) => setDraft(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={(e) => {
            if (e.nativeEvent.isComposing) return
            //  Enter chỉ cần nhả tiêu điểm — chính blur đứng ra lưu, nhờ vậy hai
            //  đường (Enter và bấm ra ngoài) không thể lệch nhau.
            if (e.key === 'Enter') {
              e.preventDefault()
              e.currentTarget.blur()
            }
            if (e.key === 'Escape') cancel()
          }}
          className="h-9 w-full max-w-2xl text-xl font-semibold"
        />
      ) : (
        <h1 className="flex items-center gap-2 text-xl font-semibold tracking-tight text-navy">
          <EditableText canEdit={canEdit} title="Đổi tên dự án" onOpen={() => open('name')}>
            {list.name}
          </EditableText>
          {list.is_archived === 1 && (
            <span className="shrink-0 rounded bg-muted px-2 py-0.5 text-xs font-normal text-muted-foreground">
              Đã lưu trữ
            </span>
          )}
        </h1>
      )}

      {editing === 'description' ? (
        <div className="mt-1 w-full max-w-3xl">
          <Textarea
            autoFocus
            rows={2}
            value={draft}
            disabled={pending}
            maxLength={DESCRIPTION_MAX}
            aria-label="Mô tả dự án"
            placeholder="Dự án này làm gì, phạm vi tới đâu…"
            onChange={(e) => setDraft(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={(e) => {
              if (e.nativeEvent.isComposing) return
              //  Enter trần ở đây là XUỐNG DÒNG — mô tả hay là hai ba câu. Muốn
              //  lưu nhanh thì Ctrl/Cmd+Enter, hoặc cứ bấm ra ngoài.
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault()
                e.currentTarget.blur()
              }
              if (e.key === 'Escape') cancel()
            }}
            className="w-full text-sm"
          />
          {/*  Bộ đếm hiện suốt lúc đang sửa: `maxLength` chặn im lặng, không có
               số thì gõ tới trần chỉ thấy bàn phím như chết. */}
          <p
            className={cn(
              'mt-0.5 text-right text-xs tabular-nums',
              draft.length >= DESCRIPTION_MAX
                ? 'font-medium text-destructive'
                : 'text-muted-foreground',
            )}
          >
            {draft.length}/{DESCRIPTION_MAX}
          </p>
        </div>
      ) : (
        //  Dự án CHƯA CÓ mô tả vẫn phải có chỗ bấm, không thì không cách nào thêm
        //  mô tả lần đầu. Chữ mờ đóng vai lời mời.
        (list.description || canEdit) && (
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            <EditableText
              canEdit={canEdit}
              title="Sửa mô tả dự án"
              onOpen={() => open('description')}
              muted={!list.description}
            >
              {list.description || 'Thêm mô tả'}
            </EditableText>
          </p>
        )
      )}
    </div>
  )
}

/**
 * Chữ bấm được. Thiếu quyền thì trả chữ trần, không nút.
 *
 * Dấu hiệu "sửa được" là nền sáng lên khi rê chuột — đủ cho một tiêu đề trang,
 * và không chiếm chỗ như một icon.
 */
function EditableText({
  canEdit,
  title,
  onOpen,
  muted,
  children,
}: {
  canEdit: boolean
  title: string
  onOpen: () => void
  muted?: boolean
  children: React.ReactNode
}) {
  if (!canEdit) return <span className="truncate">{children}</span>
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      onClick={onOpen}
      className="group -mx-1.5 flex min-w-0 items-center rounded-md px-1.5 py-0.5 text-left outline-none transition-colors hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50"
    >
      <span className={cn('truncate', muted && 'italic')}>{children}</span>
    </button>
  )
}
