import { useQuery } from '@tanstack/react-query'
import { CircleAlert, KeyRound, Loader2, ShieldCheck } from 'lucide-react'
import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

import { apiGet, apiPost, extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'

import { goTo } from './oauth-consent-redirect'

/** Mức khóa — khớp `mcp_keys.SCOPE_READ` / `SCOPE_WRITE` ở backend. */
const SCOPE_READ = 0
const SCOPE_WRITE = 1

interface ConsentRequest {
  client_name: string
  redirect_host: string
  requested_scope: number
  grant_days: number
  user_label: string
}

interface ConsentResult {
  redirect_to: string
}

/**
 * Khóa truy vấn RIÊNG của màn này (ngoại lệ đã khai ở `naming.md`): chỉ một hook dùng, không nơi nào cần làm mới nó.
 * Mỗi yêu cầu cấp quyền là một chuỗi ký khác nhau nên khóa gắn theo chính chuỗi đó.
 */
const consentKeys = { request: (req: string) => ['oauth', 'consent', req] as const }

/**
 * Màn ĐỒNG Ý OAuth của cổng MCP (ai-CR-218, K14 doc/erp/21 §7.2): ChatGPT / claude.ai / Claude Desktop mở
 * `/api/oauth/authorize`, máy chủ kiểm tham số rồi chuyển sang đây kèm chuỗi ký `/oauth/consent/<req>`. Người dùng
 * (đã đăng nhập — route nằm trong `ProtectedRoute`, đăng nhập xong quay lại đúng đường dẫn) chọn mức rồi bấm Cho phép →
 * máy chủ cấp mã một lần → trình duyệt quay về ứng dụng AI.
 *
 * Chuỗi ký nằm ở ĐƯỜNG DẪN chứ không ở `?req=`: màn đăng nhập chỉ nhớ `pathname` khi quay lại.
 */
export function OAuthConsentPage() {
  const { req = '' } = useParams()
  const [scope, setScope] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  //  Chặn bấm đúp NGAY trong tick (luật biểu mẫu): `disabled` theo state chỉ có hiệu lực ở lượt dựng sau.
  const sending = useRef(false)

  const query = useQuery({
    queryKey: consentKeys.request(req),
    queryFn: () => apiGet<ConsentRequest>(`/api/agent-hub/oauth/request/${req}`, { _silent: true } as never),
    enabled: Boolean(req),
    retry: false,
  })
  const info = query.data
  const chosen = scope ?? info?.requested_scope ?? SCOPE_READ

  async function submit(path: 'approve' | 'deny') {
    if (sending.current) return
    sending.current = true
    setBusy(true)
    setError('')
    try {
      const out = await apiPost<ConsentResult>(`/api/agent-hub/oauth/${path}`, { req, scope: chosen }, {
        _silent: true,
      } as never)
      goTo(out.redirect_to)
    } catch (e) {
      setError(extractErrorMessage(e))
      sending.current = false
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <KeyRound className="size-5 text-primary" />
            Cho phép ứng dụng AI dùng ERP thay bạn
          </CardTitle>
          {info && (
            <CardDescription>
              <span className="font-semibold text-foreground">{info.client_name}</span> xin kết nối với tài khoản ERP
              của <span className="font-semibold text-foreground">{info.user_label}</span>.
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {!req && <ErrorBox message="Đường dẫn cấp quyền thiếu mã. Quay lại ứng dụng AI và kết nối lại." />}
          {query.isLoading && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" /> Đang đọc yêu cầu…
            </p>
          )}
          {query.isError && <ErrorBox message={extractErrorMessage(query.error)} />}
          {info && (
            <>
              <p className="text-sm text-muted-foreground">
                Ứng dụng sẽ gọi các công cụ ERP dưới đúng quyền của bạn: chỉ thấy dữ liệu bạn được xem, mọi lượt gọi
                được ghi nhật ký.
              </p>
              <RadioGroup
                value={String(chosen)}
                onValueChange={(v) => setScope(Number(v))}
                className="gap-3"
                aria-label="Mức quyền của ứng dụng"
              >
                <ScopeOption
                  value={SCOPE_READ}
                  title="Chỉ đọc"
                  hint="Tra cứu phiếu, báo cáo, cẩm nang — không tạo hay sửa gì."
                />
                <ScopeOption
                  value={SCOPE_WRITE}
                  title="Được ghi"
                  hint="Thêm soạn nháp và tạo phiếu (luôn hai bước: xem nháp rồi mới tạo)."
                />
              </RadioGroup>
              <ul className="space-y-1 text-xs text-muted-foreground">
                <li>Sau khi cho phép, trình duyệt quay về: {info.redirect_host}</li>
                <li>Kết nối dùng {info.grant_days} ngày; hết hạn thì kết nối lại từ ứng dụng AI.</li>
                <li>Gỡ bất cứ lúc nào ở Trang cá nhân → Khóa AI.</li>
              </ul>
              {error && <ErrorBox message={error} />}
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" disabled={busy} onClick={() => submit('deny')}>
                  Từ chối
                </Button>
                <Button type="button" disabled={busy} onClick={() => submit('approve')}>
                  {busy ? <Loader2 className="size-4 animate-spin" /> : <ShieldCheck className="size-4" />}
                  Cho phép
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function ScopeOption({ value, title, hint }: { value: number; title: string; hint: string }) {
  const id = `oauth-scope-${value}`
  return (
    <div className="flex items-start gap-3 rounded-md border p-3">
      <RadioGroupItem value={String(value)} id={id} className="mt-0.5" />
      <Label htmlFor={id} className="flex flex-col items-start gap-0.5 font-normal">
        <span className="font-medium">{title}</span>
        <span className="text-xs text-muted-foreground">{hint}</span>
      </Label>
    </div>
  )
}

function ErrorBox({ message }: { message: string }) {
  return (
    <p role="alert" className="flex items-start gap-2 rounded-md border border-destructive/40 p-3 text-sm text-destructive">
      <CircleAlert className="mt-0.5 size-4 shrink-0" />
      {message}
    </p>
  )
}
