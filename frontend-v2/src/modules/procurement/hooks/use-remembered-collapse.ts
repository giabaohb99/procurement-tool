import { useCallback, useState } from 'react'

import { useAuthStore } from '@/core/auth/auth-store'

/** Một khóa `localStorage` cho MỌI khối báo cáo, chứ không một khóa mỗi phiếu. */
export const COLLAPSE_STORAGE_KEY = 'erp.report-collapse'

/**
 * Nhớ tối đa bấy nhiêu phiếu gần nhất. Mỗi phiếu chỉ vài id, nhưng người thu mua mở
 * hàng trăm phiếu một năm — không có trần thì khóa này phình mãi.
 */
export const MAX_REMEMBERED_SCOPES = 100

type Stored = Record<string, (string | number)[]>

function readAll(): Stored {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(COLLAPSE_STORAGE_KEY) ?? '{}')
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? (parsed as Stored) : {}
  } catch {
    return {}
  }
}

function readIds<T extends string | number>(key: string): Set<T> {
  const ids = readAll()[key]
  return Array.isArray(ids) ? new Set(ids as T[]) : new Set()
}

function writeIds(key: string, ids: Set<string | number>) {
  try {
    const all = readAll()
    //  Xóa rồi chèn lại để khóa vừa dùng nằm CUỐI — thứ tự khóa của object chính là
    //  thứ tự "mới dùng", cắt từ đầu là bỏ phiếu lâu không mở nhất.
    delete all[key]
    if (ids.size > 0) all[key] = [...ids]
    const keys = Object.keys(all)
    for (const old of keys.slice(0, Math.max(0, keys.length - MAX_REMEMBERED_SCOPES))) {
      delete all[old]
    }
    localStorage.setItem(COLLAPSE_STORAGE_KEY, JSON.stringify(all))
  } catch {
    //  Trình duyệt chặn bộ nhớ: gấp/mở vẫn ăn, chỉ không nhớ cho lần sau.
  }
}

/**
 * Tập nhóm đang GẤP của một khối báo cáo, nhớ theo NGƯỜI DÙNG và theo PHIẾU
 * (kh-TM2-1, doc `erp/thu-mua/18` §6): mở lại phiếu hôm sau vẫn thấy đúng mấy giai
 * đoạn mình đã gấp.
 *
 * Dùng như `useState<Set<T>>`. `scope` là chuỗi nói rõ khối nào của phiếu nào (vd
 * `survey-report:survey_request:12`); chưa đăng nhập thì vẫn gấp/mở được, chỉ không nhớ.
 *
 * Khóa có mã tài khoản: máy dùng chung trong kho / văn phòng thì người sau không
 * thừa hưởng bố cục của người trước.
 */
export function useRememberedCollapse<T extends string | number>(scope: string) {
  const userId = useAuthStore((state) => state.user?.id)
  const storageKey = userId ? `${userId}:${scope}` : null

  //  State GẮN KÈM khóa nó được đọc ra. Chi tiết YCBG / ĐMH là route `/:id`: chuyển
  //  sang phiếu khác cùng màn thì React Router GIỮ component, `useState` không khởi
  //  tạo lại — thiếu bước so khóa dưới đây là thẻ hiện tập đã gấp của phiếu CŨ, và
  //  lần bấm kế tiếp ghi tập đó vào khóa của phiếu MỚI (A2 bắt ở bản rà kh-TM2-1).
  const [state, setState] = useState(() => ({
    key: storageKey,
    ids: storageKey ? readIds<T>(storageKey) : new Set<T>(),
  }))

  //  Khóa đổi → đọc lại ngay lúc dựng (cách React khuyên cho state suy từ prop), không
  //  chờ effect: effect chạy sau khi vẽ, tức có một lượt vẽ tập của phiếu cũ.
  let current = state
  if (state.key !== storageKey) {
    current = { key: storageKey, ids: storageKey ? readIds<T>(storageKey) : new Set<T>() }
    setState(current)
  }

  const setCollapsed = useCallback(
    (next: Set<T> | ((current: Set<T>) => Set<T>)) => {
      setState((prev) => {
        //  `prev` của khóa khác (đổi phiếu rồi bấm ngay trong cùng nhịp) thì lấy bản
        //  nhớ của khóa HIỆN TẠI làm gốc, không lấy tập của phiếu kia.
        const base =
          prev.key === storageKey ? prev.ids : storageKey ? readIds<T>(storageKey) : new Set<T>()
        const value = typeof next === 'function' ? next(base) : next
        if (storageKey) writeIds(storageKey, value)
        return { key: storageKey, ids: value }
      })
    },
    [storageKey],
  )

  const collapsed = current.ids
  return [collapsed, setCollapsed] as const
}
