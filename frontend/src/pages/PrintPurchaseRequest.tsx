import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";

const fmt = (n: any) => Number(n || 0).toLocaleString("vi-VN");
function viDate(d: string) {
  if (!d) return "............";
  const [y, m, dd] = d.split("-");
  return `Ngày ${dd} tháng ${m} năm ${y}`;
}

function fmtDate(d: string) {
  if (!d) return "";
  const parts = d.split("-");
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return d;
}

function getClosestNeedDate(items: any[]) {
  if (!items || items.length === 0) return "";
  const dates = items
    .map((it) => it.required_date)
    .filter((d) => d && typeof d === "string" && d.trim() !== "");

  if (dates.length === 0) return "";

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  let closestDate = "";
  let minDiff = Infinity;

  for (const d of dates) {
    const parts = d.split("-");
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const dObj = new Date(year, month, day);
      dObj.setHours(0, 0, 0, 0);
      const diff = Math.abs(dObj.getTime() - today.getTime());
      if (diff < minDiff) {
        minDiff = diff;
        closestDate = d;
      }
    }
  }

  if (!closestDate && dates.length > 0) {
    closestDate = dates[0];
  }

  return fmtDate(closestDate);
}

export default function PrintPurchaseRequest() {
  const { id } = useParams();
  const [pr, setPr] = useState<any>(null);
  const [company, setCompany] = useState("");
  const [warehouses, setWarehouses] = useState<{ code: string; name: string }[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [taxMode, setTaxMode] = useState(false); // Mẫu thuế: để trống thông tin người yêu cầu

  // Map tên đầy đủ kho -> mã kho (tên viết tắt) để in cột "Nơi giao"
  const whCode = (name: string) =>
    warehouses.find((w) => w.name === name)?.code || name;

  useEffect(() => {
    api
      .get(`/api/purchase-requests/${id}`)
      .then(async (r) => {
        const d = r.data.data;
        setPr(d);
        if (d.company_id) {
          try {
            const c = await api.get(`/api/companies/${d.company_id}`);
            setCompany(c.data.data.name);
          } catch {}
        }
      })
      .catch(() => setNotFound(true));
    api
      .get(`/api/warehouses`, { params: { page_size: 200 } })
      .then((r) =>
        setWarehouses(
          r.data.data.items.map((x: any) => ({ code: x.code, name: x.name })),
        ),
      )
      .catch(() => {});
  }, [id]);

  if (notFound)
    return (
      <div style={{ padding: 40 }}>Không tìm thấy phiếu yêu cầu mua hàng.</div>
    );
  if (!pr) return <div style={{ padding: 40 }}>Đang tải...</div>;

  const SH = {
    background: "#e9edf1",
    fontWeight: 700,
    padding: "5px 8px",
    fontSize: 12.5,
    margin: "12px 0 0",
    WebkitPrintColorAdjust: "exact",
    printColorAdjust: "exact",
    breakInside: "avoid",
  } as const;
  const cell = {
    border: "1px solid #999",
    padding: "5px 8px",
    fontSize: 12,
  } as const;
  // Khối thông tin dưới mỗi tiêu đề — giãn dòng cho dễ đọc (vẫn vừa 1 trang)
  const info = { fontSize: 12, padding: "6px 4px", lineHeight: 1.75 } as const;

  return (
    <div style={{ background: "#f0f0f0", minHeight: "100vh", padding: 20 }}>
      <style>{`@media print { @page { margin: 10mm; } .sign-block { break-inside: avoid; page-break-inside: avoid; } }`}</style>
      <div
        className="no-print"
        style={{
          maxWidth: 820,
          margin: "0 auto 12px",
          display: "flex",
          gap: 8,
          alignItems: "center",
        }}
      >
        <button className="btn" onClick={() => window.print()}>
          In / Lưu PDF
        </button>
        <button className="btn ghost" onClick={() => window.close()}>
          Đóng
        </button>
        <span style={{ flex: 1 }} />
        <div style={{ display: "inline-flex", border: "1px solid #d9e0ea", borderRadius: 8, overflow: "hidden" }}>
          {[{ v: false, t: "Mẫu thường" }, { v: true, t: "Mẫu thuế" }].map((tab) => (
            <button
              key={tab.t}
              onClick={() => setTaxMode(tab.v)}
              style={{
                padding: "7px 16px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 500,
                background: taxMode === tab.v ? "#00AEEF" : "#fff",
                color: taxMode === tab.v ? "#fff" : "#475569",
              }}
            >
              {tab.t}
            </button>
          ))}
        </div>
      </div>

      <div
        className="print-doc"
        style={{
          maxWidth: 820,
          margin: "0 auto",
          background: "#fff",
          padding: "22px 30px",
          fontFamily: "Inter, Arial, sans-serif",
          color: "#000",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div style={{ fontSize: 13 }}>
            <b>Đơn vị:</b> {company || "..."}
          </div>
          <table
            style={{
              borderCollapse: "collapse",
              fontSize: 7.5,
              textAlign: "left",
              width: 126,
            }}
          >
            <tbody>
              {(() => {
                const c = {
                  border: "1px solid #999",
                  padding: "0px 3px",
                  lineHeight: 1.25,
                  whiteSpace: "nowrap",
                } as const;
                return (
                  <>
                    <tr>
                      <td
                        colSpan={2}
                        style={{ ...c, fontWeight: 700, textAlign: "center" }}
                      >
                        Mẫu 003/BM/PKT
                      </td>
                    </tr>
                    <tr>
                      <td style={{ ...c, width: 44 }}>Phiên bản</td>
                      <td style={{ ...c, textAlign: "center" }}>V1-062025</td>
                    </tr>
                    <tr>
                      <td style={{ ...c, width: 44 }}>Ngày update:</td>
                      <td style={{ ...c, textAlign: "center" }}>17/7/2025</td>
                    </tr>
                  </>
                );
              })()}
            </tbody>
          </table>
        </div>

        <h2 style={{ textAlign: "center", fontSize: 17, margin: "11px 0 3px" }}>
          PHIẾU ĐỀ XUẤT MUA HÀNG HÓA/DỊCH VỤ
        </h2>
        <div style={{ textAlign: "center", fontSize: 12 }}>Số: {pr.code}</div>
        <div style={{ textAlign: "center", fontSize: 12, marginBottom: 6 }}>
          {viDate(pr.request_date)}
        </div>

        <div style={SH}>THÔNG TIN CHUNG</div>
        <div style={info}>
          <div>
            <b>Người đề xuất:</b> {taxMode ? "" : pr.requester}
          </div>
          <div>
            <b>Chức vụ:</b> {taxMode ? "" : pr.requester_position || "............"}
          </div>
          <div>
            <b>Hiện công tác tại bộ phận:</b> {taxMode ? "" : pr.department || "............"}
          </div>
          <div>
            <b>Trưởng phòng ban/bộ phận:</b> {taxMode ? "" : pr.head_of_dept || "............"}
          </div>
        </div>

        <div style={SH}>MỤC ĐÍCH &amp; NỘI DUNG ĐỀ XUẤT</div>
        <div style={info}>
          <div>
            <b>Mục đích mua hàng/dịch vụ:</b> {pr.is_urgent ? "[Gấp] " : ""}
            {pr.purpose}
          </div>
          <div>
            <b>Thời gian cần hàng/dịch vụ:</b> {getClosestNeedDate(pr.items) || fmtDate(pr.need_date) || "..."}
          </div>
          <div>
            <b>Nội dung:</b> {pr.note || ""}
          </div>
        </div>

        <table
          style={{ width: "100%", borderCollapse: "collapse", marginTop: 6 }}
        >
          <thead>
            <tr style={{ background: "#e9edf1" }}>
              <td style={cell}>STT</td>
              <td style={cell}>Tên hàng hóa/dịch vụ</td>
              <td style={cell}>Mã hàng</td>
              <td style={cell}>ĐVT</td>
              <td style={cell}>SL yêu cầu</td>
              <td style={cell}>Đơn giá</td>
              <td style={cell}>Thành tiền</td>
              <td style={cell}>Nơi giao</td>
              <td style={cell}>Ghi chú</td>
            </tr>
          </thead>
          <tbody>
            {pr.items.map((it: any, i: number) => (
              <tr key={i}>
                <td style={cell}>{i + 1}</td>
                <td style={cell}>{it.product_name}</td>
                <td style={cell}>{it.product_code}</td>
                <td style={cell}>{it.unit}</td>
                <td style={{ ...cell, textAlign: "right" }}>{fmt(it.qty)}</td>
                <td style={{ ...cell, textAlign: "right" }}>{fmt(it.price)}</td>
                <td style={{ ...cell, textAlign: "right" }}>
                  {fmt(it.amount)}
                </td>
                <td style={cell}>{whCode(it.warehouse)}</td>
                <td style={cell}>{it.note}</td>
              </tr>
            ))}
            <tr>
              <td style={{ ...cell, fontWeight: 700 }} colSpan={6}>
                Tổng cộng
              </td>
              <td style={{ ...cell, textAlign: "right", fontWeight: 700 }}>
                {fmt(pr.subtotal)}
              </td>
              <td style={cell} colSpan={2} />
            </tr>
            <tr>
              <td colSpan={6} style={{ border: "none", textAlign: "right", padding: "8px 8px 4px", fontSize: 13 }}>
                VAT:
              </td>
              <td style={{ border: "none", textAlign: "right", padding: "8px 8px 4px", fontSize: 13, fontWeight: 700 }}>
                {Number(pr.vat) ? fmt(pr.vat) : ""}
              </td>
              <td style={{ border: "none" }} colSpan={2} />
            </tr>
            <tr>
              <td colSpan={6} style={{ border: "none", textAlign: "right", padding: "4px 8px 8px", fontSize: 13 }}>
                Tổng cộng thanh toán:
              </td>
              <td style={{ border: "none", textAlign: "right", padding: "4px 8px 8px", fontSize: 13, fontWeight: 700 }}>
                {fmt(pr.total)}
              </td>
              <td style={{ border: "none" }} colSpan={2} />
            </tr>
          </tbody>
        </table>

        <div style={SH}>THÔNG TIN NHÀ CUNG CẤP</div>
        <div style={info}>
          <div>
            <b>Tên nhà cung cấp:</b> {pr.suggested_supplier || ""}
          </div>
          <div>
            <b>Mã số thuế:</b> {pr.suggested_supplier_tax_code || ""}
          </div>
          <div>
            <b>Liên hệ:</b> {pr.suggested_supplier_contact || ""}
          </div>
          <div>
            <b>Báo giá đính kèm:</b> {pr.quote_file_url ? "☑" : "☐"} Có &nbsp;&nbsp; {pr.quote_file_url ? "☐" : "☑"} Không
          </div>
        </div>

        <div style={SH}>PHẦN DÀNH CHO BỘ PHẬN MUA HÀNG</div>
        <div style={info}>
          <div>
            <b>Thời gian cần hàng/dịch vụ:</b> .............................
          </div>
          <div>
            <b>Yêu cầu khác (nếu có):</b> .............................
          </div>
        </div>

        <div className="sign-block">
          <div style={SH}>XÉT DUYỆT</div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-around",
              textAlign: "center",
              fontSize: 12,
              marginTop: 16,
            }}
          >
            {["Giám đốc", "TP/BP mua hàng", "TP/BP đề xuất", "Người lập"].map(
              (r) => (
                <div key={r}>
                  <b>{r}</b>
                  <div style={{ fontStyle: "italic", fontSize: 11 }}>
                    (Ký, ghi rõ họ tên)
                  </div>
                  <div
                    style={{
                      height: 58,
                      display: "flex",
                      alignItems: "flex-end",
                      justifyContent: "center",
                      fontWeight: 700,
                    }}
                  >
                    {r === "Người lập" && !taxMode ? pr.requester : ""}
                  </div>
                </div>
              ),
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
