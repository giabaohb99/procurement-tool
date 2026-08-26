import { useEffect, useState } from 'react'

import { AssistantAvatar } from './assistant-avatar'

/** Sau chừng này giây thì nói thêm một câu trấn an, kẻo người dùng tưởng treo. */
const SLOW_THRESHOLD_SEC = 8

/**
 * Khối «đang soạn» hiện trong lúc chờ trả lời.
 *
 * Đây mới là chỗ thật sự làm người dùng đỡ sốt ruột — hiệu ứng gõ máy
 * (`use-typewriter`) chỉ chạy SAU khi chữ đã về nên không rút ngắn cái chờ.
 * Ba thứ ở đây đều nhằm trả lời câu "nó còn sống không":
 *  - ba chấm nhấp nháy: có chuyển động = còn chạy;
 *  - ĐỒNG HỒ đếm giây: người dùng biết đã chờ bao lâu, thay vì đoán;
 *  - quá `NGUONG_LAU_GIAY` thì nói rõ là câu khó, đang tra số liệu.
 */
export function AssistantThinking() {
  const [giay, setGiay] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setGiay((truoc) => truoc + 1), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex gap-3">
      <AssistantAvatar />
      <div className="flex min-h-8 flex-col justify-center gap-1">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="flex gap-1" aria-hidden>
            <Cham do={0} />
            <Cham do={160} />
            <Cham do={320} />
          </span>
          <span>Đang soạn trả lời</span>
          {/*  `tabular-nums` để con số không làm dòng chữ giật qua lại mỗi giây. */}
          <span className="tabular-nums">{giay}s</span>
        </div>

        {giay >= SLOW_THRESHOLD_SEC && (
          <p className="text-xs text-muted-foreground/80">
            Câu này cần tra số liệu nên hơi lâu — vẫn đang chạy.
          </p>
        )}
      </div>
    </div>
  )
}

/** Một chấm nhấp nháy; `do` là độ trễ (ms) để ba chấm chạy lệch pha nhau. */
function Cham({ do: treMs }: { do: number }) {
  return (
    <span
      className="size-1.5 animate-pulse rounded-full bg-primary/70"
      style={{ animationDelay: `${treMs}ms` }}
    />
  )
}
