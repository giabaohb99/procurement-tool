import { KeyRound, Plug } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { ConnectGuide } from '@/modules/ai-skill/components/connect-guide'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

/**
 * Trang CÔNG KHAI `/connect-ai` (bao-CR-638): hướng dẫn nối AI riêng (Claude, ChatGPT, Cursor…) với ERP — không cần đăng
 * nhập, đứng ngoài khung ứng dụng. Quản trị gửi link này cho nhân viên từ màn Khóa nhân sự.
 *
 * KHÔNG BAO GIỜ có khóa: nội dung lấy từ `mcp-setup/public` (chỉ địa chỉ cổng + hướng dẫn tĩnh), đoạn cấu hình giữ nguyên
 * chỗ giữ `<KHÓA_CỦA_BẠN>`; khóa thật chỉ lấy được sau khi đăng nhập, ở Trang cá nhân → AI của tôi. `?client=` mở sẵn
 * đúng ứng dụng.
 */
export function ConnectAiPage() {
  const [params] = useSearchParams()
  const client = (params.get('client') ?? '').slice(0, 40)

  return (
    <main className="min-h-dvh bg-muted/30 px-4 py-8">
      <div className="mx-auto max-w-3xl space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Plug className="size-5" />
              Nối AI riêng của bạn với ERP DEGO
            </CardTitle>
            <CardDescription>
              Dùng Claude, ChatGPT, Cursor… của chính bạn để tra cứu phiếu, đơn hàng, công việc trong ERP — đúng phạm vi
              quyền của tài khoản bạn. Chọn ứng dụng đang dùng rồi làm theo các bước.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ConnectGuide source="public" initialClient={client} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-wrap items-center gap-3 pt-6 text-sm">
            <KeyRound className="size-5 text-muted-foreground" />
            <p className="min-w-0 flex-1 text-muted-foreground">
              Ứng dụng cần khóa (Claude Desktop, Cursor…): đăng nhập ERP, vào Trang cá nhân → AI của tôi để tạo khóa, rồi
              bấm Sao chép đoạn cấu hình — khóa được điền sẵn. ChatGPT và claude.ai không cần khóa.
            </p>
            <Button asChild size="sm">
              <Link to={`${appRoutes.me}?tab=ai-connect`}>Lấy khóa</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
