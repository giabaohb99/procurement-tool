import { Badge } from '@/shared/ui/badge'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Select, SelectContent, SelectItem, SelectSeparator, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { useRevokeFolderAccess, useUpdateFolderAccessLevel } from '../hooks/use-document-folder-access'
import { EFFECT } from '../types/document-access'
import { FOLDER_ACCESS_LEVEL_LABELS, type FolderAccessEntry } from '../types/document-folder'
import { AccessSubjectAvatar } from './access-subject-avatar'

const REVOKE_REASON = 'Thu hồi từ hộp Chia sẻ'
const REMOVE_VALUE = 'remove'

interface FolderSharePeopleListProps {
  folderId: number
  rows: FolderAccessEntry[]
  /** `my_level >= Quản lý` — dưới mức này chỉ XEM, không có ô đổi mức/gỡ nào cả. */
  canManage: boolean
  /** Bấm tên thư mục nguồn của dòng KẾ THỪA — mở thư mục đó (đóng hộp hiện tại). Bỏ trống = hiện chữ thường, không bấm được. */
  onNavigateToFolder?: (folderId: number) => void
}

/**
 * Danh sách «Người có quyền» của hộp «Chia sẻ» kiểu Drive (đặc tả §C, chốt
 * lead 23/09/2026) — mỗi dòng đổi mức NGAY TẠI CHỖ qua `PATCH .../access/{id}`
 * (không thu hồi rồi cấp lại), và «Gỡ quyền» nằm NGAY TRONG cùng ô thả xuống
 * đó (mục cuối, tô đỏ) thay vì một nút riêng — đúng khuôn hộp Chia sẻ của
 * Drive.
 *
 * Dòng KẾ THỪA (từ tổ tiên) hiện mờ, ghi rõ nguồn kèm liên kết mở thư mục đó
 * — sửa/thu hồi phải làm đúng ở thư mục nguồn, sửa ở đây sẽ âm thầm không có
 * tác dụng gì trên thư mục đó. `canManage=false` (người xem dưới mức Quản lý)
 * ép TOÀN BỘ dòng về chỉ đọc, kể cả dòng của chính thư mục này.
 */
export function FolderSharePeopleList({ folderId, rows, canManage, onNavigateToFolder }: FolderSharePeopleListProps) {
  const updateLevel = useUpdateFolderAccessLevel(folderId)
  const revoke = useRevokeFolderAccess(folderId)
  //  Phòng thủ (rà UI 23/09/2026) — kiểu khai `rows: FolderAccessEntry[]`
  //  không rỗng-hoá được `undefined` thật sự lọt qua lúc chạy (nơi gọi cũng đã
  //  tự chắn ở `folder-share-dialog.tsx`, đây là lớp thứ hai).
  const list = rows ?? []

  if (list.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {canManage
          ? 'Chưa khai dòng quyền nào trên nhánh này.'
          : 'Bạn cần mức Quản lý để xem đầy đủ danh sách này.'}
      </p>
    )
  }

  async function handleSelectChange(row: FolderAccessEntry, value: string) {
    if (value === REMOVE_VALUE) {
      const ok = await confirm({
        title: `Thu hồi quyền của ${row.subject_name}?`,
        message: 'Dòng này vẫn ở lại bảng kèm mốc thu hồi.',
        confirmLabel: 'Thu hồi',
      })
      if (ok) revoke.mutate({ accessId: row.id, reason: REVOKE_REASON })
      return
    }
    updateLevel.mutate({ accessId: row.id, level: Number(value) })
  }

  return (
    <ul className="divide-y rounded-md border">
      {list.map((row) => {
        const editable = canManage && !row.is_inherited && row.is_active && row.effect !== EFFECT.deny
        const subjectName = row.subject_name || '(đã xóa)'
        return (
          <li key={row.id} className={cn('flex items-center gap-3 px-3 py-2', !row.is_active && 'opacity-55')}>
            <AccessSubjectAvatar subjectKind={row.subject_kind} subjectName={row.subject_name} />

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-sm font-medium" title={subjectName}>
                  {subjectName}
                </span>
                {row.effect === EFFECT.deny && (
                  <Badge variant="destructive" className="h-4 shrink-0 px-1.5 text-[10px] font-normal">
                    Cấm
                  </Badge>
                )}
              </div>
              <p className="truncate text-xs text-muted-foreground">
                {row.subject_kind_label} ·{' '}
                {row.is_inherited ? (
                  <>
                    Kế thừa từ{' '}
                    {onNavigateToFolder ? (
                      <button
                        type="button"
                        className="underline underline-offset-2 hover:text-foreground"
                        onClick={() => onNavigateToFolder(row.folder_id)}
                      >
                        «{row.folder_name}»
                      </button>
                    ) : (
                      `«${row.folder_name}»`
                    )}
                  </>
                ) : row.valid_to ? (
                  `Hết hạn ${formatDate(row.valid_to)}`
                ) : (
                  'Không đặt hạn'
                )}
                {row.reason && ` · ${row.reason}`}
              </p>
            </div>

            {editable ? (
              <Select value={String(row.level)} onValueChange={(value) => void handleSelectChange(row, value)}>
                <SelectTrigger className="w-32 shrink-0" aria-label={`Đổi mức quyền của ${row.subject_name}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3].map((level) => (
                    <SelectItem key={level} value={String(level)}>
                      {FOLDER_ACCESS_LEVEL_LABELS[level]}
                    </SelectItem>
                  ))}
                  <SelectSeparator />
                  <SelectItem value={REMOVE_VALUE} className="text-destructive">
                    Gỡ quyền
                  </SelectItem>
                </SelectContent>
              </Select>
            ) : (
              row.effect !== EFFECT.deny && (
                <Badge variant="outline" className="shrink-0">
                  {row.level_label}
                </Badge>
              )
            )}
          </li>
        )
      })}
    </ul>
  )
}
