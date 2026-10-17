import { CalendarDays, Trash2 } from 'lucide-react'

import { AiKeyListCard } from '@/modules/system/components/ai-key-list-card'
import {
  useAiKey,
  useDisconnectGoogle,
  useGoogleAuthorize,
  useGoogleLink,
  usePatchAiKey,
  useRemoveOneAiKey,
  useSetAiKey,
} from '@/modules/system/hooks/use-ai-key'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Mục «Khóa model AI» ở Trang cá nhân (ai-CR-053, D-01 → ai-CR-098, C-04; tên cũ tab «Khóa AI», đổi tên ở P0 doc 21)
 * — khóa AI CÁ NHÂN cho bot Telegram / Zalo, kèm thẻ nối Google cá nhân.
 *
 * Nhiều khóa, nhiều hãng (Gemini · Claude · OpenAI · OpenRouter) theo thứ tự ưu tiên: khóa trên cùng hết tiền / hết
 * hạn mức / sai thì bot tự nhảy sang khóa kế, hết khóa cá nhân thì lùi về khóa công ty (có trần lượt mỗi ngày).
 * Dán ở đây, KHÔNG dán vào chat: Telegram giữ lịch sử vĩnh viễn, khóa nằm trong chat là khóa đã lộ.
 * Backend kiểm khóa với hãng rồi lưu mã hóa; không cửa nào trả khóa ra, kể cả cho chính chủ — chỉ 4 ký tự cuối.
 */
export function ProfileAiKeyTab() {
  const { data, isLoading } = useAiKey()
  const setKey = useSetAiKey()
  const patch = usePatchAiKey()
  const removeOne = useRemoveOneAiKey()
  const companyKeys = data?.company_keys ?? 0

  //  ai-CR-101 (đại ca 07/10): Khóa AI lên đầu, Google kế. Khối MCP («Nâng cao» mặc định gập) đã TÁCH ra mục riêng
  //  «Kết nối AI riêng» (`profile-ai-connect-section.tsx`, P0 doc 21) — từ 17/10 đó là đường chính, không giấu nữa.
  return (
    <div className="space-y-4">
      <AiKeyListCard
        title="Khóa AI của bạn cho bot Telegram"
        description={
          <p>
            Mọi câu hỏi bạn gửi bot Telegram (và Zalo sau này) chạy bằng khóa của chính bạn, theo thứ tự trong danh
            sách; khóa trên cùng hỏng thì bot tự dùng khóa kế, không nhắn gì. Hỏi bot «còn khóa nào» để xem lượt đã
            dùng hôm nay.{' '}
            {companyKeys > 0
              ? 'Hết khóa cá nhân thì bot dùng khóa công ty, có trần lượt mỗi ngày.'
              : 'Công ty chưa khai khóa chung, nên chưa có khóa nào thì bot chưa trả lời câu hỏi AI.'}{' '}
            Chỉ dán ở đây, không bao giờ gửi khóa vào khung chat.
          </p>
        }
        items={data?.items ?? []}
        providers={data?.providers}
        isLoading={isLoading}
        canWrite
        emptyText="Chưa có khóa. Bot vẫn cho đăng nhập, xem tình trạng việc, nhưng câu hỏi AI chỉ chạy khi có khóa (của bạn hoặc của công ty)."
        removeMessage="Bot sẽ dùng khóa kế trong danh sách."
        saving={setKey.isPending}
        onAdd={(body) => setKey.mutateAsync(body)}
        onPatch={(id, body) => patch.mutate({ id, body })}
        onRemove={(id) => removeOne.mutate(id)}
      />
      <GoogleCard />
    </div>
  )
}

/**
 * Google CÁ NHÂN (ai-CR-064, M-06): nối một lần qua màn đồng ý của Google; ERP giữ token mã hóa. Bot / Trợ lý / MCP
 * đọc lịch và Drive của CHÍNH bạn (tool my_calendar_events, create_calendar_event, drive_search, drive_read),
 * bản tin sáng 7h30 và nhắc trước họp 15 phút về Telegram.
 */
function GoogleCard() {
  const { data, isLoading } = useGoogleLink()
  const authorize = useGoogleAuthorize()
  const disconnect = useDisconnectGoogle()

  async function handleDisconnect() {
    const ok = await confirm({
      title: 'Gỡ kết nối Google',
      message: 'Bot sẽ không đọc được lịch và Drive của bạn nữa; nối lại bất cứ lúc nào.',
      confirmLabel: 'Gỡ kết nối',
    })
    if (ok) disconnect.mutate()
  }

  return (
    <Card>
      <CardHeader>
        <SectionHeading>Google của bạn: Lịch và Drive</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted-foreground">
          Nối tài khoản Google cá nhân để hỏi bot «hôm nay tôi họp gì», «đặt lịch họp NCC X 14h mai», «tìm trên Drive hợp đồng ABC»,
          nhận bản tin sáng 7h30 và nhắc trước họp 15 phút qua Telegram. Bot chỉ thấy lịch và tệp của chính bạn.
        </p>
        {isLoading && <Skeleton className="h-10 w-full" />}
        {!isLoading && data && !data.configured && (
          <p className="rounded-md border border-dashed p-3 text-muted-foreground">Hệ thống chưa cấu hình kết nối Google (quản trị khai GOOGLE_CLIENT_SECRET).</p>
        )}
        {!isLoading && data?.configured && data.linked && (
          <div className="flex flex-wrap items-center gap-3 rounded-md border p-3">
            <span className="min-w-0 flex-1">
              Đang nối <span className="font-medium">{data.email || 'Google'}</span>
              {data.linked_at && <span className="text-muted-foreground"> · từ {formatDateTime(data.linked_at)}</span>}
            </span>
            <Button type="button" variant="ghost" size="sm" onClick={() => void handleDisconnect()} disabled={disconnect.isPending}>
              <Trash2 className="mr-1 size-4" /> Gỡ kết nối
            </Button>
          </div>
        )}
        {!isLoading && data?.configured && !data.linked && (
          <Button type="button" size="sm" onClick={() => authorize.mutate()} disabled={authorize.isPending}>
            <CalendarDays className="mr-1.5 size-4" /> Nối Google
          </Button>
        )}
        <p className="text-xs text-muted-foreground">
          Google có thể hiện màn «ứng dụng chưa được xác minh»: bấm Nâng cao → Tiếp tục. Đây là ứng dụng nội bộ của công ty.
        </p>
      </CardContent>
    </Card>
  )
}
