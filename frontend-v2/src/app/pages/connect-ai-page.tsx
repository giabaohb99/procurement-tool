import { ExternalLink, Plug } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { ConnectGuide } from '@/modules/ai-skill/components/connect-guide'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

/** Bài HDSD dài (seed `seed_help_ai_rieng_lam_duoc_gi.py`); slug theo `slugify()` của help-center. */
const CAPABILITY_ARTICLE_PATH = '/ai-rieng-cua-ban-lam-duoc-gi-trong-erp-cong-cu-va-skill'

const CAPABILITIES = [
  'Tra phiếu, đơn hàng, công nợ, nhà cung cấp, giá đã mua',
  'Xem việc chờ duyệt, công việc, đơn nghỉ phép của bạn',
  'Soạn sẵn phiếu để bạn xác nhận trước khi lưu',
]

/**
 * Trang CÔNG KHAI `/connect-ai` (bao-CR-638): hướng dẫn nối AI riêng (Claude, ChatGPT, Cursor…) với ERP — không cần đăng
 * nhập, đứng ngoài khung ứng dụng. Quản trị gửi link này cho nhân viên từ màn Khóa nhân sự.
 *
 * KHÔNG BAO GIỜ có khóa: nội dung lấy từ `mcp-setup/public` (chỉ địa chỉ cổng + hướng dẫn tĩnh), đoạn cấu hình giữ nguyên
 * chỗ giữ `<KHÓA_CỦA_BẠN>`; khóa thật chỉ lấy được sau khi đăng nhập, ở Trang cá nhân → AI của tôi. `?client=` mở sẵn
 * đúng ứng dụng. kh-AI-ket-noi-giao-dien: giới thiệu gọn vừa một màn, phần dài chuyển sang bài HDSD.
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
            <CardDescription className="space-y-2">
              <span className="block">
                Dùng Claude, ChatGPT… của chính bạn để làm việc với ERP, đúng phạm vi quyền của tài khoản bạn:
              </span>
              <span className="block">
                {CAPABILITIES.map((item) => (
                  <span key={item} className="block before:mr-1.5 before:content-['·']">
                    {item}
                  </span>
                ))}
              </span>
              <a
                href={`${appConfig.helpCenterUrl}${CAPABILITY_ARTICLE_PATH}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-primary underline-offset-4 hover:underline"
              >
                AI riêng của bạn làm được gì trong ERP
                <ExternalLink className="size-3.5" />
              </a>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ConnectGuide
              source="public"
              initialClient={client}
              footer={
                <p className="text-xs text-muted-foreground">
                  Cách 2 cần khóa riêng:{' '}
                  <Link to={`${appRoutes.me}?tab=ai-connect`} className="text-primary underline-offset-4 hover:underline">
                    đăng nhập rồi lấy khóa ở Trang cá nhân → AI của tôi
                  </Link>
                  .
                </p>
              }
            />
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
