import { create } from 'zustand'

import { logger } from '@/core/telemetry/logger'

const STORAGE_KEY = 'erp.work.sidebar.collapsed'

function read(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch (error) {
    logger.warn('Không đọc được trạng thái ẩn/hiện cây dự án, mặc định hiện', error)
    return false
  }
}

interface SidebarState {
  collapsed: boolean
  toggle: () => void
}

/**
 * Cây «Danh sách dự án» bên trái đang ẨN hay HIỆN.
 *
 * Là STORE dùng chung chứ không phải `useState` trong `WorkLayoutPage`, vì có
 * hai nơi cách xa nhau cùng đọc và cùng ghi: khung layout (route cha) quyết
 * định có dựng cây hay không, còn nút mở lại nằm ở dải TIÊU ĐỀ của từng trang
 * con (route con). Luồn qua `useOutletContext` thì mọi trang con đều phải khai
 * kiểu context ấy dù chỉ một hai trang dùng tới; hai lần `useState` riêng thì
 * mỗi bên nhớ một kiểu.
 *
 * Nhớ trong `localStorage` chứ không lên máy chủ, cùng khuôn với
 * `useCollapsedGroups` và `useWorkViewState`: đây là tùy chọn nhìn của riêng
 * người đang ngồi trước máy, không phải dữ liệu dự án.
 *
 * Nhớ MỘT chỗ cho cả phân hệ, không tách theo từng dự án: ẩn cây là để lấy chỗ
 * cho Gantt / bảng, mà nhu cầu ấy không đổi khi nhảy sang dự án khác — nhớ theo
 * dự án thì mỗi lần đổi dự án cây lại bật ra, đúng thứ vừa cố tắt đi.
 */
export const useWorkSidebarStore = create<SidebarState>((set, get) => ({
  collapsed: read(),

  toggle: () => {
    const next = !get().collapsed
    set({ collapsed: next })
    try {
      localStorage.setItem(STORAGE_KEY, next ? '1' : '0')
    } catch (error) {
      logger.warn('Không ghi được trạng thái ẩn/hiện cây dự án', error)
    }
  },
}))
