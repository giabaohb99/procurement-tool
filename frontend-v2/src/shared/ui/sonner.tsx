"use client"

import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from "lucide-react"
import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      {...props}
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
        ...props.icons,
      }}
      toastOptions={{
        classNames: {
          //  Chừa chỗ cho nút đóng ở góc trên bên PHẢI. Không chừa thì dòng chữ
          //  đầu tiên chạy thẳng xuống dưới nút. `!` vì luật gốc của sonner là
          //  `[data-sonner-toast][data-styled="true"]` (đặc tả 0,2,0) — một lớp
          //  Tailwind thường thua, mà lớp tiện ích lại còn nằm trong `@layer`
          //  nên thua cả luật không-lớp. Quan trọng `!important` thắng cả hai.
          toast: "pr-9!",
        },
        ...props.toastOptions,
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
          //  NÚT ĐÓNG: góc trên bên PHẢI, NẰM TRONG khung (khách báo 25/08/2026).
          //  Mặc định của sonner là `start: 0 / end: unset` kèm
          //  `translate(-35%, -35%)` — tức góc trên bên TRÁI và bị kéo ra NGOÀI
          //  khung, nên nút trôi lên trên viền, đè vào thanh trên cùng của trang.
          //  Đảo lại: bỏ `start`, ghim `end: 0`, rồi kéo VÀO trong 25%.
          //  Đặt bằng `style` (nội tuyến) chứ không bằng lớp CSS: ba biến này
          //  được khai ở `[data-sonner-toaster][dir="ltr"], html[dir="ltr"]` —
          //  style nội tuyến trên chính thẻ toaster là cách chắc thắng, và
          //  biến di truyền xuống nút con.
          "--toast-close-button-start": "unset",
          "--toast-close-button-end": "0",
          "--toast-close-button-transform": "translate(-25%, 25%)",
          ...props.style,
        } as React.CSSProperties
      }
    />
  )
}

export { Toaster }
