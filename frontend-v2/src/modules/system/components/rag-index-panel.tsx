import { Loader2, RefreshCw, RotateCcw, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'

import { settingApi } from '../api/setting-api'
import { useRagIndexStatus } from '../hooks/use-settings'
import type { RagReindexMode } from '../types/setting'

/**
 * CHỈ MỤC TÀI LIỆU của Trợ lý AI — chỗ bấm tay để nạp bài HDSD + FAQ vào kho tìm kiếm.
 *
 * Vì sao phải có màn này (bao-CR-451). Hook nạp chỉ mục bắn từ *service* của Trung tâm trợ
 * giúp, còn script seed bài HDSD ghi thẳng ORM — bài do seed dựng ra không bao giờ vào kho,
 * và **không chỗ nào nói ra điều đó**. Rà ngày 21/09/2026 thì kho chỉ có 55/87 bài, hụt suốt
 * nhiều tháng mà không ai thấy. Nên thẻ này bày SỐ trước, nút sau: con số là thứ khiến người
 * ta bấm đúng lúc.
 *
 * Hai nút cố ý tách đôi, đừng gộp lại thành một:
 *   - *Nạp bù bài thiếu* — chỉ nhúng bài chưa có trong kho. Việc thường ngày, rẻ.
 *   - *Nạp lại toàn bộ* — nhúng lại cả trăm nguồn. Chỉ khi đổi model nhúng hoặc nghi kho
 *     lệch nội dung; nhúng có trần request/phút nên chạy bừa là dính lỗi quá hạn mức.
 *
 * Người không có `help_article.write` KHÔNG thấy thẻ này (trang cha gác) — backend cũng đòi
 * đúng quyền đó ở cả hai đường, nên vẽ ra chỉ để người dùng ăn 403.
 */
export function RagIndexPanel() {
  const { data, isPending, isFetching, refetch } = useRagIndexStatus(true)
  const [running, setRunning] = useState<'' | RagReindexMode>('')

  async function runReindex(mode: RagReindexMode) {
    setRunning(mode)
    try {
      await settingApi.reindexDocs(mode)
      // Chạy nền: chỉ báo ĐÃ XẾP HÀNG, không hứa hẹn xong ngay. Cũng vì vậy mà KHÔNG tự
      // gọi lại số liệu ở đây — worker chưa nhúng xong thì con số y như cũ, người dùng đọc
      // ra là "bấm không ăn thua". Để họ tự bấm *Kiểm tra lại* sau ít phút.
      toast.success(
        mode === 'missing'
          ? 'Đã xếp hàng nạp bù các tài liệu còn thiếu — worker chạy nền ít phút'
          : 'Đã xếp hàng nạp lại toàn bộ chỉ mục — worker chạy nền, có thể lâu',
      )
    } catch {
      // http client đã hiện toast lỗi (kể cả 400 khi RAG chưa bật).
    } finally {
      setRunning('')
    }
  }

  const missing = data?.missing ?? 0
  const disabled = running !== ''

  return (
    <FormCard title="Chỉ mục tài liệu" icon={Sparkles} iconClassName="text-muted-foreground">
      <div className="space-y-3">
        <div className="text-sm">
          {isPending ? (
            <span className="text-muted-foreground">Đang đọc kho tìm kiếm...</span>
          ) : !data?.enabled ? (
            <span className="text-muted-foreground">
              Tìm kiếm tài liệu đang tắt (AI_RAG_ENABLED). Bật cờ đó rồi mới nạp được chỉ mục.
            </span>
          ) : (
            <>
              <span>
                Kho tìm kiếm đang có <b>{data.help_indexed ?? 0}</b>/{data.help_total ?? 0} bài
                hướng dẫn và <b>{data.faq_indexed ?? 0}</b>/{data.faq_total ?? 0} câu hỏi thường
                gặp.
              </span>{' '}
              {missing > 0 ? (
                <span className="text-warning">
                  Còn {missing} tài liệu chưa vào chỉ mục — Trợ lý AI trả lời như thể chúng
                  không tồn tại.
                </span>
              ) : (
                <span className="text-muted-foreground">Không thiếu tài liệu nào.</span>
              )}
              {(data.orphans ?? 0) > 0 && (
                <span className="text-muted-foreground">
                  {' '}
                  Kho còn {data.orphans} tài liệu đã bị xóa dưới dữ liệu gốc; nạp lại toàn bộ
                  không dọn được chúng, phải xóa riêng.
                </span>
              )}
            </>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button disabled={disabled} onClick={() => void runReindex('missing')}>
            {running === 'missing' ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
            Nạp bù bài thiếu
          </Button>
          <Button variant="outline" disabled={disabled} onClick={() => void runReindex('all')}>
            {running === 'all' ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <RotateCcw className="size-4" />
            )}
            Nạp lại toàn bộ
          </Button>
          <Button
            variant="ghost"
            disabled={isFetching}
            onClick={() => void refetch()}
            title="Đọc lại số liệu kho tìm kiếm"
          >
            {isFetching ? <Loader2 className="size-4 animate-spin" /> : null}
            Kiểm tra lại
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">
          Nạp bù chạy sau mỗi lần thêm bài hướng dẫn bằng script — script không tự báo cho kho
          tìm kiếm. Nạp lại toàn bộ nhúng lại mọi tài liệu, chỉ dùng khi đổi model nhúng hoặc
          nghi chỉ mục lệch nội dung. Cả hai đều chạy nền, xong rồi bấm Kiểm tra lại để xem số.
        </p>
      </div>
    </FormCard>
  )
}
