import { useEffect, useRef } from 'react'

import type { AssistantMessage } from '../types/assistant'
import { AssistantThinking } from './assistant-thinking'
import { ChatMessage } from './chat-message'

interface MessageThreadProps {
  messages: AssistantMessage[]
  /** Câu vừa gửi đang chờ trả lời — hiện ngay để không thấy trễ. */
  pending: string | null
  isSending: boolean
  /**
   * MỐC id chốt lúc bấm gửi: tin trợ lý nào có id LỚN HƠN mốc này là câu vừa
   * nhận trong phiên -> chạy hiệu ứng gõ máy. `null` = không gõ gì (mở lại hội
   * thoại cũ mà ngồi xem máy gõ lại từ đầu thì vừa chậm vừa vô nghĩa).
   *
   * ⚠️ Vì sao là MỐC chứ không phải id của chính câu trả lời: id câu trả lời
   * chỉ biết SAU khi server trả về, mà lúc đó React Query đã ghi tin mới vào
   * cache và có thể render TRƯỚC nhịp `setState` id đó. Tin mới mount với
   * `typing=false` -> hiện nguyên khối, rồi mới lật sang `true` -> hook gõ máy
   * chạy lại từ đầu: khối chữ vừa hiện full bị rút ngắn rồi gõ lại, màn neo
   * đáy tụt lên câu TRƯỚC ĐÓ — nhìn như "câu cũ đang gõ, câu mới hiện sẵn".
   * Mốc thì chốt được TRƯỚC khi gửi nên tin mới mount là gõ ngay, hết race.
   */
  typingAfterId: number | null
}

/** Còn cách đáy dưới ngưỡng này thì coi như người dùng đang theo dõi tin mới. */
const NEAR_BOTTOM_PX = 120

/**
 * Cột đọc của hội thoại.
 *
 * Bề ngang khóa ở `max-w-3xl` và căn giữa: dòng chữ dài quá 80–90 ký tự thì mắt
 * mất dấu đầu dòng khi xuống hàng. Bản cũ để chữ chạy hết bề ngang màn 1920px
 * nên câu trả lời dài đọc rất mệt.
 */
export function MessageThread({ messages, pending, isSending, typingAfterId }: MessageThreadProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  /**
   * Có đang bám đáy không.
   *
   * ⚠️ Là một CỜ, không phải phép đo khoảng cách tại chỗ. Bản đầu đo
   * `scrollHeight - clientHeight - scrollTop` ngay trong `ResizeObserver` rồi
   * chỉ bám khi còn dưới 120px — nhưng hiệu ứng gõ làm khối cao lên NHANH hơn
   * mức đó, nên vừa vượt ngưỡng một nhịp là nó buông luôn và chữ chạy ra ngoài
   * tầm nhìn. Đo được: cách đáy 191 → 200 → 200px suốt lúc gõ, tới khi gõ xong
   * mới giật một cái về 0.
   *
   * Cờ chỉ đổi khi CHÍNH NGƯỜI DÙNG cuộn (`onScroll`), nên khối có mọc nhanh
   * cỡ nào cũng không tuột.
   */
  const stickToBottom = useRef(true)

  const scrollToBottom = () => {
    const frame = scrollRef.current
    if (frame && stickToBottom.current) frame.scrollTop = frame.scrollHeight
  }

  /**
   * Tin mới / bắt đầu soạn: xuống đáy **bất kể** cờ bám.
   *
   * Hai luật khác nhau, đừng gộp:
   *  - Người dùng **tự gửi** một câu → luôn kéo xuống đáy, và bám lại từ đầu.
   *    Họ vừa hành động, thứ họ muốn thấy là kết quả của hành động đó — dù
   *    trước đó đang cuộn lên đọc lại đoạn cũ.
   *  - Chữ **tự chạy ra** trong lúc họ đang đọc chỗ khác → KHÔNG được kéo.
   *
   * Nhảy thẳng chứ không cuộn mượt: cuộn mượt đang bay dở mà khối lại cao thêm
   * thì hai bên giành nhau, nhìn giật.
   */
  useEffect(() => {
    stickToBottom.current = true
    scrollToBottom()
  }, [messages.length, pending, isSending])

  //  Khối trả lời CAO DẦN trong lúc chữ chạy ra: `ResizeObserver` bắt đúng cái
  //  đó, vì số tin không đổi nên effect ở trên không chạy lại.
  useEffect(() => {
    const content = contentRef.current
    if (!content) return
    const observer = new ResizeObserver(scrollToBottom)
    observer.observe(content)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={scrollRef}
      onScroll={(e) => {
        //  Người dùng tự kéo lên đọc lại đoạn cũ thì THÔI bám, kẻo cứ bị lôi
        //  xuống đáy giữa chừng. Kéo về gần đáy thì bám lại.
        const el = e.currentTarget
        stickToBottom.current = el.scrollHeight - el.clientHeight - el.scrollTop <= NEAR_BOTTOM_PX
      }}
      className="min-h-0 flex-1 overflow-y-auto"
    >
      {/*  `space-y-6` chứ không phải `space-y-4`: khoảng thở giữa hai LƯỢT phải
           rõ hơn khoảng cách giữa các đoạn BÊN TRONG một câu trả lời, nếu không
           thì nhìn thành một khối chữ liền. */}
      <div ref={contentRef} className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
        {messages.map((m) => (
          <ChatMessage
            key={m.id}
            role={m.role_name}
            content={m.content}
            typing={m.role_name === 'assistant' && typingAfterId != null && m.id > typingAfterId}
          />
        ))}

        {pending && <ChatMessage role="user" content={pending} />}
        {isSending && <AssistantThinking />}
      </div>
    </div>
  )
}
