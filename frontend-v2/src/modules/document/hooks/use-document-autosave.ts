import { useCallback, useEffect, useRef, useState } from 'react'

/** Ngưng gõ bao lâu thì tự lưu (ms). */
const AUTOSAVE_DELAY = 1500

interface UseDocumentAutosaveOptions {
  /** `silent`: lưu ngầm theo nhịp gõ, không ghi vào lịch sử thao tác. */
  onSave: (content: string, options: { silent: boolean }) => void
}

/**
 * TỰ ĐỘNG LƯU nội dung soạn thảo.
 *
 * Lưu sau khi ngừng gõ 1,5 giây (ngầm, không ghi lịch sử) và vẫn giữ nút Lưu
 * cho người dùng chốt một mốc — bản ghi nhật ký chỉ sinh ra ở lần bấm tay đó,
 * nếu không thì sổ lịch sử ngập những dòng "Cập nhật" cách nhau vài giây.
 *
 * Tách khỏi trình soạn thảo vì trạng thái này phải hiện ở ĐẦU TRANG (cạnh phụ
 * đề và nút Lưu), tức là ngoài phạm vi của khung soạn thảo.
 */
export function useDocumentAutosave({ onSave }: UseDocumentAutosaveOptions) {
  const latest = useRef('')

  // Giữ hàm lưu trong ref: `onSave` đổi danh tính sau MỖI lần lưu (nó bám theo
  // danh sách văn bản vừa đổi). Nếu để nó trong `deps` của hẹn giờ bên dưới thì
  // lưu xong lại hẹn tiếp một lần nữa — thành vòng lặp tự lưu mỗi 1,5 giây dù
  // người dùng không gõ gì.
  const saveRef = useRef(onSave)
  saveRef.current = onSave
  // Đếm số lần gõ: chỉ dựa vào cờ "đang bẩn" thì effect không chạy lại giữa hai
  // lần gõ liên tiếp, hẹn giờ sẽ không được đặt lại.
  const [revision, setRevision] = useState(0)
  const [dirty, setDirty] = useState(false)
  const [savedAt, setSavedAt] = useState<string | null>(null)

  // Hẹn giờ đặt lại sau mỗi lần gõ (debounce): chỉ lưu khi người dùng đã ngừng
  // gõ đủ 1,5 giây, chứ không phải cứ 1,5 giây lại lưu một lần.
  useEffect(() => {
    if (revision === 0) return
    const timer = setTimeout(() => {
      saveRef.current(latest.current, { silent: true })
      setDirty(false)
      setSavedAt(new Date().toISOString())
    }, AUTOSAVE_DELAY)
    return () => clearTimeout(timer)
  }, [revision])

  // Đóng tab khi còn nội dung chưa kịp lưu -> hỏi lại.
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  const handleChange = useCallback((html: string) => {
    latest.current = html
    setDirty(true)
    setRevision((value) => value + 1)
  }, [])

  const saveNow = useCallback(() => {
    saveRef.current(latest.current, { silent: false })
    setDirty(false)
    setSavedAt(new Date().toISOString())
  }, [])

  return { dirty, savedAt, handleChange, saveNow }
}
