import { AiKeyListCard } from './ai-key-list-card'
import {
  useCompanyAiKeys,
  usePatchCompanyAiKey,
  useRemoveCompanyAiKey,
  useSetCompanyAiKey,
} from '../hooks/use-ai-key'

interface CompanyAiKeysPanelProps {
  canWrite: boolean
}

/**
 * Khóa AI CÔNG TY (ai-CR-098, C-04) ở thẻ «Trợ lý AI» của Cấu hình hệ thống. Cùng bảng `tab_ai_key` với khóa cá nhân
 * (`owner_type` = công ty). Trợ lý trên web dùng khóa ưu tiên cao nhất của hãng đang chọn (đi TRƯỚC hai ô khóa bí mật
 * cũ ở phía trên); bot Telegram dùng chuỗi này khi người dùng hết khóa cá nhân, có trần lượt mỗi ngày.
 */
export function CompanyAiKeysPanel({ canWrite }: CompanyAiKeysPanelProps) {
  const { data, isLoading } = useCompanyAiKeys()
  const setKey = useSetCompanyAiKey()
  const patch = usePatchCompanyAiKey()
  const remove = useRemoveCompanyAiKey()

  return (
    <AiKeyListCard
      title="Khóa AI công ty (nhiều hãng, theo ưu tiên)"
      description={
        <p>
          Trợ lý trên web và bot Telegram (khi người dùng hết khóa cá nhân) dùng các khóa này theo thứ tự; khóa trên
          cùng hết tiền / hết hạn mức / sai thì tự chuyển sang khóa kế. Đặt «trần/ngày» cho từng khóa để giới hạn chi
          phí. Khóa ở đây được ưu tiên hơn hai ô khóa bí mật cũ phía trên.
        </p>
      }
      items={data?.items ?? []}
      providers={data?.providers}
      isLoading={isLoading}
      canWrite={canWrite}
      emptyText="Chưa có khóa công ty trong sổ. Trợ lý web đang dùng hai ô khóa bí mật phía trên (nếu có)."
      removeMessage="Trợ lý và bot sẽ dùng khóa công ty kế tiếp."
      saving={setKey.isPending}
      onAdd={(body) => setKey.mutateAsync(body)}
      onPatch={(id, body) => patch.mutate({ id, body })}
      onRemove={(id) => remove.mutate(id)}
    />
  )
}
