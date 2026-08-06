import { useState, useEffect, useRef } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { toast } from "../components/toast";
import { api } from "../api/client";
import NotificationBell from "../components/NotificationBell";
import PwaInstallPrompt from "../components/PwaInstallPrompt";
import TicketCreateModal from "../components/TicketCreateModal";
import { TICKET_ENABLED } from "../config/features";
import { canInstall, onInstallChange, promptInstall } from "../pwa-install";

// Trung tâm Hướng dẫn sử dụng là app riêng (thư mục help-center/, cổng 8082) — mở ở tab mới.
// Khu người dùng bên đó CÔNG KHAI, không cần đăng nhập.
export const HELP_URL =
  (import.meta as any).env?.VITE_HELP_URL || "http://localhost:8082";

/**
 * Link sang Help Center. Người quản trị tài liệu (help_article/write) được "bàn giao" phiên
 * qua HASH `#t=...&r=...` để bên đó hiện nút "Truy cập quản trị" mà không phải đăng nhập lại
 * (2 app khác cổng → không dùng chung localStorage).
 * Hash KHÔNG được trình duyệt gửi lên server, và help-center xóa nó khỏi URL ngay khi nạp.
 * User thường không kèm token — khu người dùng vốn công khai.
 */
export function helpCenterUrl(canManageHelp: boolean): string {
  if (!canManageHelp) return HELP_URL;
  const t = localStorage.getItem("token");
  if (!t) return HELP_URL;
  const r = localStorage.getItem("refresh_token");
  const q = new URLSearchParams({ t, ...(r ? { r } : {}) });
  return `${HELP_URL}#${q.toString()}`;
}

type NavItem = {
  to: string;
  label: string;
  icon: string;
  entity?: string;
  manage?: boolean;
  action?: string;        // hiện khi có ĐÚNG action này trên entity (dùng cho menu riêng của 1 nhóm)
  anyEntity?: string[];   // hiện nếu có read trên BẤT KỲ entity nào (OR)
  external?: boolean;     // link ra ngoài app (mở tab mới) thay vì route nội bộ
};
// Mọi nhóm CÓ tiêu đề đều thu/mở được (đồng bộ trên toàn menu trái).
// `key` là khóa lưu trạng thái thu/mở trong localStorage — đặt cố định, KHÔNG suy ra từ
// tiêu đề để đổi tên hiển thị không làm mất trạng thái người dùng đã lưu.
// Nhóm đầu (không tiêu đề) luôn hiện.
type NavGroup = {
  title?: string;
  key?: string;
  items: NavItem[];
};

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { to: "/", label: "Trang chủ", icon: "ti-layout-dashboard" },
      // Trung tâm HDSD KHÔNG còn ở menu trái — lối vào duy nhất là nút "?" cạnh
      // chuông thông báo trên thanh trên cùng (mở app riêng ở tab mới).
      // Màn QUẢN LÝ phiếu hỗ trợ — chỉ nhóm Hỗ trợ (quyền 'delete' làm proxy handler,
      // vì mọi nhân viên đều có ticket read/write/create nên không lọc được bằng manage).
      // Người dùng thường gửi phiếu qua icon tai nghe + xem ở Trang cá nhân.
      // Ẩn hoàn toàn khi tính năng tắt (prod) — xem config/features.ts
      ...(TICKET_ENABLED
        ? [{ to: "/tickets", label: "Hỗ trợ", icon: "ti-headset", entity: "ticket", action: "delete" }]
        : []),
      {
        to: "/reports",
        label: "Báo cáo mua hàng",
        icon: "ti-chart-bar",
        entity: "report",
      },
    ],
  },
  {
    title: "Mua hàng",
    key: "muahang",
    items: [
      {
        to: "/survey-requests",
        label: "Yêu cầu báo giá",
        icon: "ti-clipboard-list",
        entity: "survey_request",
      },
      {
        to: "/purchase-requests",
        label: "Yêu cầu mua hàng",
        icon: "ti-file-text",
        entity: "purchase_request",
      },
      {
        to: "/purchase-orders",
        label: "Đơn mua hàng",
        icon: "ti-shopping-cart",
        entity: "purchase_order",
      },
      {
        to: "/purchase-progress",
        label: "Tiến độ mua hàng",
        icon: "ti-truck-delivery",
        anyEntity: ["purchase_order", "purchase_request"],
      },
    ],
  },
  {
    title: "Khảo sát",
    key: "khaosat",
    items: [
      {
        to: "/surveys",
        label: "Phiếu khảo sát",
        icon: "ti-clipboard-search",
        entity: "survey",
      },
      {
        to: "/survey-report",
        label: "Báo cáo khảo sát",
        icon: "ti-report-analytics",
        entity: "survey",
      },
    ],
  },
  {
    title: "Kho & Công nợ",
    key: "khocongno",
    items: [
      {
        to: "/inventory",
        label: "Tồn kho",
        icon: "ti-packages",
        entity: "inventory",
      },
      { to: "/payables", label: "Công nợ", icon: "ti-cash", entity: "payable" },
      {
        to: "/payment-requests",
        label: "Yêu cầu thanh toán",
        icon: "ti-receipt",
        entity: "payment_request",
      },
    ],
  },
  {
    title: "Danh mục",
    key: "danhmuc",
    items: [
      {
        to: "/suppliers",
        label: "Nhà cung cấp",
        icon: "ti-truck",
        entity: "supplier",
        manage: true,
      },
      {
        to: "/products",
        label: "Sản phẩm",
        icon: "ti-box",
        entity: "product",
        manage: true,
      },
      {
        to: "/contracts",
        label: "Hợp đồng",
        icon: "ti-file-certificate",
        entity: "contract",
        manage: true,
      },
      {
        to: "/warehouses",
        label: "Kho",
        icon: "ti-building-warehouse",
        entity: "warehouse",
        manage: true,
      },
      {
        to: "/units",
        label: "Đơn vị tính",
        icon: "ti-ruler-2",
        entity: "unit",
        manage: true,
      },
      {
        to: "/item-groups",
        label: "Phân loại",
        icon: "ti-category",
        entity: "item_group",
        manage: true,
      },
      {
        to: "/departments",
        label: "Phòng ban",
        icon: "ti-tag",
        entity: "department",
        manage: true,
      },
      {
        to: "/category-assignees",
        label: "Phân công phụ trách",
        icon: "ti-user-cog",
        entity: "category_assignee",
        manage: true,
      },
    ],
  },
  {
    title: "Hệ thống",
    key: "hethong",
    items: [
      {
        to: "/companies",
        label: "Công ty",
        icon: "ti-building",
        entity: "company",
        manage: true,
      },
      {
        to: "/employees",
        label: "Nhân sự",
        icon: "ti-users",
        entity: "employee",
        manage: true,
      },
      {
        to: "/roles",
        label: "Phân quyền tài khoản",
        icon: "ti-shield",
        entity: "role",
        manage: true,
      },
      {
        to: "/settings",
        label: "Cấu hình hệ thống",
        icon: "ti-settings",
        entity: "setting",
      },
      {
        to: "/import-batches",
        label: "Quản lý Import",
        icon: "ti-file-import",
        entity: "import",
      },
      {
        to: "/backups",
        label: "Sao lưu CSDL",
        icon: "ti-database-export",
        entity: "backup",
      },
    ],
  },
];
const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items);

// Bề rộng menu trái: kéo được trong khoảng NAV_W_MIN..NAV_W_MAX, nháy đúp tay kéo về mặc định.
const NAV_W_MIN = 180;
const NAV_W_MAX = 400;
const NAV_W_DEFAULT = 222;

const isActive = (path: string, to: string) =>
  to === "/" ? path === "/" : path.startsWith(to);

export default function AppLayout() {
  const { user, login, logout, updateUser, can } = useAuth();
  const isDev = import.meta.env.VITE_DEVELOPER_MODE === "dev";
  const devAccounts = [
    "admin",
    "TESTREQ",
    "DEMOAD",
    "DEMOQL",
    "DEMONV",
    "DEMOTP",
  ];

  async function handleDevLogin(username: string) {
    if (!username) return;
    try {
      await login(username, username);
      toast.success(`Đã chuyển sang tài khoản ${username}`);
      window.location.href = "/"; // Tải lại toàn bộ ứng dụng
    } catch (e: any) {
      toast.error(
        "Lỗi chuyển tài khoản: " + (e.response?.data?.message || e.message),
      );
    }
  }

  // Menu "quản lý" (danh mục, hệ thống) chỉ hiện khi được QUẢN LÝ (write/create/delete),
  // không hiện chỉ vì có read (read dùng để đổ dropdown trong form).
  const canManage = (e: string) =>
    can(e, "write") || can(e, "create") || can(e, "delete");
  const visibleItems = (items: NavItem[]) =>
    items.filter(
      (n) =>
        (n.anyEntity ? n.anyEntity.some((e) => can(e, "read")) : true) &&
        (!n.entity ||
          (n.action
            ? can(n.entity, n.action)
            : n.manage
              ? canManage(n.entity)
              : can(n.entity, "read"))),
    );
  const nav = useNavigate();
  const loc = useLocation();
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  // Nút "Cài ứng dụng" trong menu — hiện khi trình duyệt cho cài (Edge/Chrome/Android)
  const [installable, setInstallable] = useState(canInstall());
  useEffect(() => onInstallChange(() => setInstallable(canInstall())), []);
  // Popup "Gửi yêu cầu hỗ trợ" (icon tai nghe ở menu avatar) — mở ngay tại trang đang đứng
  const [supportOpen, setSupportOpen] = useState(false);
  const [supportOrigin, setSupportOrigin] = useState("");
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem("nav_collapsed") || "{}");
    } catch {
      return {};
    }
  });
  const toggle = (k: string) =>
    setCollapsed((s) => {
      const n = { ...s, [k]: !s[k] };
      localStorage.setItem("nav_collapsed", JSON.stringify(n));
      return n;
    });

  // ── Ẩn/hiện + kéo giãn menu trái (chỉ áp dụng màn rộng; màn hẹp dùng drawer + hamburger) ──
  const [navHidden, setNavHidden] = useState(
    () => localStorage.getItem("nav_hidden") === "1",
  );
  const toggleNav = () =>
    setNavHidden((v) => {
      localStorage.setItem("nav_hidden", v ? "0" : "1");
      return !v;
    });
  const [navWidth, setNavWidth] = useState(() => {
    const w = Number(localStorage.getItem("nav_width"));
    return w >= NAV_W_MIN && w <= NAV_W_MAX ? w : NAV_W_DEFAULT;
  });
  const [resizing, setResizing] = useState(false);
  // Bề rộng mới nhất trong lúc kéo — cập nhật NGAY trong onMove (không đợi React render lại)
  // để lúc thả chuột ghi đúng giá trị vào localStorage, kể cả khi kéo rất nhanh.
  const navWidthRef = useRef(navWidth);

  function startResize(e: React.MouseEvent) {
    e.preventDefault();
    setResizing(true);
    document.body.classList.add("col-resizing");
    // Sidebar bám mép trái nên clientX chính là bề rộng cần đặt
    const onMove = (ev: MouseEvent) => {
      const w = Math.min(NAV_W_MAX, Math.max(NAV_W_MIN, ev.clientX));
      navWidthRef.current = w;
      setNavWidth(w);
    };
    const onUp = () => {
      setResizing(false);
      document.body.classList.remove("col-resizing");
      localStorage.setItem("nav_width", String(navWidthRef.current));
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  function resetNavWidth() {
    navWidthRef.current = NAV_W_DEFAULT;
    setNavWidth(NAV_W_DEFAULT);
    localStorage.setItem("nav_width", String(NAV_W_DEFAULT));
  }

  const current = [...ALL_ITEMS]
    .reverse()
    .find((n) => isActive(loc.pathname, n.to));
  const currentGroup = NAV_GROUPS.find((g) =>
    g.items.some((n) => n.to === current?.to),
  );
  const name = user?.full_name || "Người dùng";
  const initials =
    name.trim().split(" ").slice(-1)[0]?.[0]?.toUpperCase() || "U";
  // CR-028: dòng phụ dưới tên ở góc phải — mã NV · chức vụ (bỏ phần nào rỗng).
  // Tài khoản chưa gắn hồ sơ nhân sự thì không có mã, để trống chứ không bịa.
  const subLabel = [user?.emp_code, user?.position].filter(Boolean).join(" · ");

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingAvatar(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post("/api/auth/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      updateUser({ avatar: res.data.data.avatar });
    } catch (err) {
      toast.error("Không thể tải ảnh lên. Vui lòng thử lại.");
    } finally {
      setUploadingAvatar(false);
    }
  }

  return (
    <div
      className={"app" + (navHidden ? " nav-hidden" : "")}
      style={{ ["--sidebar-w" as any]: navWidth + "px" }}
    >
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}
      <aside className={"sidebar" + (open ? " open" : "")}>
        <div className="brand">
          <div className="brand-logo">
            <img src="/logo.svg" alt="DEGO Holding" />
          </div>
        </div>
        {NAV_GROUPS.map((g, gi) => {
          const items = visibleItems(g.items);
          if (items.length === 0) return null;
          const isCol = !!g.key && !!collapsed[g.key];
          return (
            <div key={gi}>
              {g.title && (
                <button
                  className="nav-group-title toggle"
                  onClick={() => toggle(g.key!)}
                  aria-expanded={!isCol}
                  title={isCol ? `Mở ${g.title}` : `Thu gọn ${g.title}`}
                >
                  <i
                    className={
                      "ti " + (isCol ? "ti-chevron-right" : "ti-chevron-down")
                    }
                    style={{ fontSize: 13 }}
                  />
                  {g.title}
                </button>
              )}
              {!isCol &&
                items.map((n) =>
                  n.external ? (
                    <a
                      key={n.to}
                      href={n.to}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => setOpen(false)}
                      className="nav-item"
                    >
                      <i className={"ti " + n.icon} />
                      {n.label}
                    </a>
                  ) : (
                    <Link
                      key={n.to}
                      to={n.to}
                      onClick={() => setOpen(false)}
                      className={
                        "nav-item" +
                        (isActive(loc.pathname, n.to) ? " active" : "")
                      }
                    >
                      <i className={"ti " + n.icon} />
                      {n.label}
                    </Link>
                  ),
                )}
            </div>
          );
        })}
      </aside>
      {/* Tay kéo đổi bề rộng menu — nháy đúp để về mặc định */}
      <div
        className={"sidebar-resizer" + (resizing ? " dragging" : "")}
        onMouseDown={startResize}
        onDoubleClick={resetNavWidth}
        role="separator"
        aria-orientation="vertical"
        title="Kéo để đổi bề rộng menu (nháy đúp để về mặc định)"
      />
      <div className="main">
        <div className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              className="icon-btn hamburger"
              onClick={() => setOpen(true)}
              aria-label="Menu"
            >
              <i className="ti ti-menu-2" />
            </button>
            <button
              className="icon-btn nav-toggle"
              onClick={toggleNav}
              aria-label={navHidden ? "Hiện menu" : "Ẩn menu"}
              title={navHidden ? "Hiện menu" : "Ẩn menu"}
            >
              <i
                className={
                  "ti " +
                  (navHidden
                    ? "ti-layout-sidebar-left-expand"
                    : "ti-layout-sidebar-left-collapse")
                }
              />
            </button>
            <div className="crumb">
              {currentGroup?.title ? `${currentGroup.title} / ` : ""}
              {current?.label || "Trang chủ"}
            </div>
          </div>
          <div
            className="topbar-right"
            style={{
              position: "relative",
              display: "flex",
              alignItems: "center",
              gap: 16,
            }}
          >
            {isDev && (
              <select
                style={{
                  padding: "4px 8px",
                  borderRadius: 4,
                  border: "1px solid #ccc",
                  fontSize: 13,
                  background: "#fff",
                  cursor: "pointer",
                  outline: "none",
                }}
                value=""
                onChange={(e) => handleDevLogin(e.target.value)}
              >
                <option value="" disabled>
                  — Đổi user (Dev) —
                </option>
                {devAccounts.map((acc) => (
                  <option key={acc} value={acc}>
                    {acc}
                  </option>
                ))}
              </select>
            )}
            {/* Lối vào Trung tâm Hướng dẫn sử dụng (app riêng, tab mới) */}
            <a
              className="icon-btn"
              href={helpCenterUrl(can("help_article", "write"))}
              target="_blank"
              rel="noopener noreferrer"
              title="Hướng dẫn sử dụng"
              aria-label="Hướng dẫn sử dụng"
              style={{ display: "flex", alignItems: "center", textDecoration: "none" }}
            >
              <i className="ti ti-help" />
            </a>
            <NotificationBell />
            <div
              style={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                gap: 8,
              }}
              onClick={() => setProfileOpen(!profileOpen)}
            >
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt="avatar"
                  className="avatar"
                  style={{ objectFit: "cover" }}
                />
              ) : (
                <span className="avatar">{initials}</span>
              )}
              {/* CR-028: hiện TÊN NHÂN SỰ + MÃ NV (trước chỉ có mỗi tên hiển thị của tài khoản,
                  nhìn vào không biết đang đăng nhập bằng ai). Dòng 2 gộp mã NV · chức vụ. */}
              <span className="user-name">
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--navy)", whiteSpace: "nowrap" }}>
                  {name}
                </span>
                {subLabel && (
                  <span style={{ fontSize: 11, color: "#7b8aa5", whiteSpace: "nowrap" }}>
                    {subLabel}
                  </span>
                )}
              </span>
              <i
                className="ti ti-chevron-down"
                style={{ fontSize: 12, color: "#666", flexShrink: 0 }}
              />
            </div>

            {profileOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: 8,
                  backgroundColor: "white",
                  borderRadius: 8,
                  boxShadow: "0 12px 28px rgba(15,23,42,0.16)",
                  width: 288,
                  zIndex: 100,
                  overflow: "hidden",
                  border: "1px solid #e2e8f0",
                }}
              >
                <div
                  style={{
                    padding: 16,
                    borderBottom: "1px solid #eee",
                    backgroundColor: "#f8fafc",
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                  }}
                >
                  <label
                    style={{
                      cursor: "pointer",
                      position: "relative",
                      display: "block",
                      flexShrink: 0,
                    }}
                  >
                    {user?.avatar ? (
                      <img
                        src={user.avatar}
                        alt="avatar"
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: "50%",
                          objectFit: "cover",
                          border: "2px solid #fff",
                          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: "50%",
                          backgroundColor: "#0f172a",
                          color: "#fff",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 20,
                          fontWeight: 600,
                        }}
                      >
                        {initials}
                      </div>
                    )}
                    <div
                      style={{
                        position: "absolute",
                        bottom: 0,
                        right: 0,
                        backgroundColor: "#1c9cf0",
                        color: "#fff",
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                      }}
                    >
                      <i
                        className={
                          uploadingAvatar ? "ti ti-loader" : "ti ti-camera"
                        }
                        style={{
                          fontSize: 12,
                          animation: uploadingAvatar
                            ? "spin 1s linear infinite"
                            : "none",
                        }}
                      />
                    </div>
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      disabled={uploadingAvatar}
                    />
                  </label>
                  {/* CR-028: tên nhân sự + MÃ NV ngay dưới, để biết chắc đang đăng nhập bằng hồ sơ nào */}
                  <div style={{ minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 700,
                        fontSize: 14,
                        color: "#1e293b",
                        lineHeight: 1.3,
                      }}
                    >
                      {name}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 5, flexWrap: "wrap" }}>
                      {user?.emp_code ? (
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 700,
                            letterSpacing: 0.3,
                            color: "var(--teal)",
                            background: "#e5f7ff",
                            border: "1px solid #c7ecfb",
                            borderRadius: 999,
                            padding: "1px 8px",
                          }}
                        >
                          {user.emp_code}
                        </span>
                      ) : (
                        <span style={{ fontSize: 11, color: "#94a3b8" }}>Chưa gắn hồ sơ nhân sự</span>
                      )}
                      {user?.position && (
                        <span style={{ fontSize: 11.5, color: "#64748b" }}>{user.position}</span>
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: 12.5,
                        color: "#64748b",
                        marginTop: 5,
                        wordBreak: "break-all",
                      }}
                    >
                      {user?.email}
                    </div>
                  </div>
                </div>
                <div style={{ padding: "8px 0" }}>
                  <div
                    style={{
                      padding: "8px 16px",
                      fontSize: 13,
                      color: "#475569",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <i className="ti ti-building" style={{ fontSize: 15, color: "#94a3b8", flexShrink: 0 }} />{" "}
                    {user?.department_name || "Chưa có phòng ban"}
                  </div>
                  <div
                    style={{
                      padding: "8px 16px",
                      fontSize: 13,
                      color: "#475569",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <i className="ti ti-phone" style={{ fontSize: 15, color: "#94a3b8", flexShrink: 0 }} />{" "}
                    {user?.phone || "Chưa cập nhật SĐT"}
                  </div>
                </div>
                <div style={{ borderTop: "1px solid #eee", padding: 8 }}>
                  {installable && (
                    <button
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "8px 8px",
                        backgroundColor: "transparent",
                        border: "none",
                        color: "var(--teal)",
                        cursor: "pointer",
                        borderRadius: 4,
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        fontSize: 13,
                        fontWeight: 500,
                      }}
                      onClick={async () => { setProfileOpen(false); await promptInstall(); setInstallable(canInstall()); }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <i className="ti ti-download" style={{ fontSize: 16 }} /> Cài ứng dụng
                    </button>
                  )}
                  <button
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 8px",
                      backgroundColor: "transparent",
                      border: "none",
                      color: "var(--navy)",
                      cursor: "pointer",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      fontWeight: 500,
                    }}
                    onClick={() => {
                      setProfileOpen(false);
                      // Tắt phiếu hỗ trợ → nút này quay về Trung tâm HDSD (app riêng, cổng 8082)
                      if (!TICKET_ENABLED) {
                        window.open(helpCenterUrl(can("help_article", "write")), "_blank", "noopener");
                        return;
                      }
                      // Mở popup gửi yêu cầu hỗ trợ ngay tại chỗ, đính kèm trang đang đứng (để debug)
                      setSupportOrigin(loc.pathname + loc.search);
                      setSupportOpen(true);
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    {TICKET_ENABLED ? (
                      <><i className="ti ti-headset" style={{ fontSize: 16 }} /> Gửi yêu cầu hỗ trợ</>
                    ) : (
                      <><i className="ti ti-help" style={{ fontSize: 16 }} /> Hướng dẫn sử dụng</>
                    )}
                  </button>
                  <button
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 8px",
                      backgroundColor: "transparent",
                      border: "none",
                      color: "var(--navy)",
                      cursor: "pointer",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      fontWeight: 500,
                    }}
                    onClick={() => { setProfileOpen(false); nav("/me"); }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f1f5f9")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    <i className="ti ti-user" style={{ fontSize: 16 }} /> Trang cá nhân
                  </button>
                  <button
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 8px",
                      backgroundColor: "transparent",
                      border: "none",
                      color: "#ef4444",
                      cursor: "pointer",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      fontWeight: 500,
                    }}
                    onClick={() => {
                      logout();
                      nav("/login");
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.backgroundColor = "#fef2f2")
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.backgroundColor = "transparent")
                    }
                  >
                    <i className="ti ti-logout" style={{ fontSize: 16 }} /> Đăng
                    xuất
                  </button>
                </div>
              </div>
            )}

            {profileOpen && (
              <div
                style={{ position: "fixed", inset: 0, zIndex: 99 }}
                onClick={() => setProfileOpen(false)}
              />
            )}
          </div>
        </div>
        <div className="content">
          <Outlet />
        </div>
      </div>
      {import.meta.env.VITE_PWA_INSTALL_PROMPT === 'on' && <PwaInstallPrompt />}
      {TICKET_ENABLED && (
        <TicketCreateModal
          open={supportOpen}
          onClose={() => setSupportOpen(false)}
          originUrl={supportOrigin}
        />
      )}
    </div>
  );
}
