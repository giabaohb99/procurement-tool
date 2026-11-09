import { Download, ListTree, Undo2 } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'

import { downloadCustomsBatchFile } from '../../api/customs-api'
import type { CustomsImportBatch } from '../../types/customs'
import { resolveRevertState } from '../../utils/customs'

interface CustomsBatchHistoryActionsProps {
  batch: CustomsImportBatch
  canRevert: boolean
  /** Đang có lệnh hoàn tác chạy — khóa mọi nút hoàn tác cho khỏi bắn hai lệnh. */
  revertPending: boolean
  onOpenLogs: (batch: CustomsImportBatch) => void
  onRevert: (batch: CustomsImportBatch) => void
}

/**
 * Ba nút của một lô nạp: tải lại tệp gốc · nhật ký lô · hoàn tác. Tách khỏi cột "Thao tác" để
 * bảng (khổ rộng) và thẻ (khổ điện thoại) bày CÙNG một bộ nút — viết hai lần thì một bên sớm
 * muộn quên lời giải thích vì sao nút hoàn tác bị khóa.
 */
export function CustomsBatchHistoryActions({
  batch,
  canRevert,
  revertPending,
  onOpenLogs,
  onRevert,
}: CustomsBatchHistoryActionsProps) {
  const revertState = canRevert ? resolveRevertState(batch) : 'hidden'
  return (
    <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
      {batch.has_file && (
        <IconTooltip label="Tải lại tệp gốc đã nạp">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="Tải lại tệp gốc đã nạp"
            onClick={() =>
              downloadCustomsBatchFile(batch.id, batch.filename).catch((error: Error) =>
                toast.error(error.message),
              )
            }
          >
            <Download className="size-4" />
          </Button>
        </IconTooltip>
      )}
      <IconTooltip label="Nhật ký lô — kết quả từng dòng, lỗi, cảnh báo">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label="Nhật ký lô — kết quả từng dòng, lỗi, cảnh báo"
          onClick={() => onOpenLogs(batch)}
        >
          <ListTree className="size-4" />
        </Button>
      </IconTooltip>
      {revertState !== 'hidden' && (
        <IconTooltip
          label={
            revertState === 'blocked'
              ? `Lô này nạp theo cách cũ, đã thay ${batch.deleted_count} dòng cũ nên không hoàn tác được.`
              : 'Hoàn tác: xóa dòng lô này đã thêm, trả lại dòng lô đã ghi đè / xóa'
          }
        >
          {/*  Bọc `span`: nút `disabled` không nhận sự kiện chuột nên tooltip
               giải thích VÌ SAO bị khóa sẽ không bao giờ hiện nếu gắn thẳng. */}
          <span className="inline-flex">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label="Hoàn tác lô nạp"
              disabled={revertState === 'blocked' || revertPending}
              onClick={() => onRevert(batch)}
            >
              <Undo2 className="size-4" />
            </Button>
          </span>
        </IconTooltip>
      )}
    </div>
  )
}
