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
  // Có/không in ảnh chữ ký (mẫu thường). Bản ký tay vẫn giữ họ tên dưới ô cho đúng
  // "(Ký, ghi rõ họ tên)" — chỉ bỏ ảnh chữ ký số đi.
  const [showSign, setShowSign] = useState(true);

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
    // Phiếu dài sang trang 2: đừng để dải tiêu đề mục nằm trơ cuối trang 1 còn nội dung
    // của nó lật sang trang sau.
    breakAfter: "avoid",
    pageBreakAfter: "avoid",
  } as const;
  const cell = {
    border: "1px solid #999",
    padding: "5px 8px",
    fontSize: 12,
  } as const;
  // Khối thông tin dưới mỗi tiêu đề — giãn dòng cho dễ đọc (vẫn vừa 1 trang)
  const info = { fontSize: 12, padding: "6px 4px", lineHeight: 1.75 } as const;

  return (
    <div className="print-wrap" style={{ background: "#f0f0f0", minHeight: "100vh", padding: 20 }}>
      {/* `@page { margin: 0 }`: trình duyệt vẽ ngày giờ / tên tab / đường dẫn / số trang vào
          đúng dải lề của khổ giấy — bỏ lề đi thì không còn chỗ cho mấy dòng đó, bản in sạch
          mà người dùng không phải tự tắt "Headers and footers" trong hộp thoại In.
          Lề thật của phiếu chuyển xuống padding của .print-doc (dùng !important vì padding
          hiện đặt bằng style inline). */}
      <style>{`@media print {
        @page { size: A4 portrait; margin: 0; }
        html, body { margin: 0 !important; background: #fff !important; }
        .print-wrap { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
        /* min-height 297mm chỉ để dựng tờ giấy giả lập trên màn hình; giữ lại lúc in thì
           phiếu ngắn cũng bị đẩy dư ra tờ thứ hai vì phần padding cộng thêm.
           box-decoration-break: clone -> phiếu tràn sang trang 2 thì MỖI mảnh đều có đủ
           lề trên/dưới; không có nó, trang 1 chạy sát mép giấy (máy in cắt mất dòng cuối)
           và trang 2 bắt đầu ngay mép trên. */
        .print-doc {
          padding: 10mm 12mm !important; min-height: 0 !important;
          -webkit-box-decoration-break: clone; box-decoration-break: clone;
        }
        .sign-block { break-inside: avoid; page-break-inside: avoid; }
        /* Phiếu nhiều dòng hàng thì tràn sang trang 2 và khối XÉT DUYỆT đi theo. Neo ghi chú
           theo .print-doc (absolute) sẽ khiến nó rơi vào giữa trang cuối; đổi sang fixed để
           trình duyệt in lại ở đúng góc phải dưới của MỌI tờ giấy. */
        .print-note { position: fixed !important; right: 12mm; bottom: 6mm; }
      }`}</style>
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
        {/* Chỉ mẫu thường mới có chữ ký sẵn để mà tắt/bật — mẫu thuế vốn để trống toàn bộ. */}
        {!taxMode && (
          <div style={{ display: "inline-flex", border: "1px solid #d9e0ea", borderRadius: 8, overflow: "hidden" }}>
            {[{ v: true, t: "Có chữ ký" }, { v: false, t: "Không chữ ký" }].map((tab) => (
              <button
                key={tab.t}
                onClick={() => setShowSign(tab.v)}
                title={tab.v
                  ? "In kèm ảnh chữ ký đã lưu trong hệ thống"
                  : "Để trống ô chữ ký (chỉ in họ tên) — dành cho bản in ký tay"}
                style={{
                  padding: "7px 16px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 500,
                  background: showSign === tab.v ? "#00AEEF" : "#fff",
                  color: showSign === tab.v ? "#fff" : "#475569",
                }}
              >
                {tab.t}
              </button>
            ))}
          </div>
        )}
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
          // Chừa thêm đáy 46px: bản xem trên màn hình neo ghi chú vào đáy khối này (bottom 7mm
          // ~ 26px + chiều cao dòng), phiếu nhiều dòng hàng mà không chừa chỗ thì chữ ghi chú
          // đè lên họ tên người ký.
          padding: "22px 30px 46px",
          fontFamily: "Inter, Arial, sans-serif",
          color: "#000",
          // Cao tối thiểu bằng 1 tờ A4 + mốc định vị: để dòng ghi chú neo được xuống đúng
          // góc phải DƯỚI của tờ giấy, thay vì bám ngay dưới khối chữ ký giữa trang.
          position: "relative",
          minHeight: "297mm",
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
              <td style={cell}>VAT%</td>
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
                <td style={{ ...cell, textAlign: "right" }}>{Number(it.vat_pct) || 0}%</td>
                <td style={{ ...cell, textAlign: "right" }}>
                  {fmt((Number(it.qty) || 0) * (Number(it.price) || 0))}
                </td>
                <td style={cell}>{whCode(it.warehouse)}</td>
                <td style={cell}>{it.note}</td>
              </tr>
            ))}
            <tr>
              <td style={{ ...cell, fontWeight: 700 }} colSpan={7}>
                Tiền hàng (chưa VAT)
              </td>
              <td style={{ ...cell, textAlign: "right", fontWeight: 700 }}>
                {fmt(pr.subtotal)}
              </td>
              <td style={cell} colSpan={2} />
            </tr>
            <tr>
              <td colSpan={7} style={{ border: "none", textAlign: "right", padding: "8px 8px 4px", fontSize: 13 }}>
                Tiền VAT:
              </td>
              <td style={{ border: "none", textAlign: "right", padding: "8px 8px 4px", fontSize: 13, fontWeight: 700 }}>
                {Number(pr.vat) ? fmt(pr.vat) : "0"}
              </td>
              <td style={{ border: "none" }} colSpan={2} />
            </tr>
            <tr>
              <td colSpan={7} style={{ border: "none", textAlign: "right", padding: "4px 8px 8px", fontSize: 13 }}>
                Tổng cộng thanh toán (gồm VAT):
              </td>
              <td style={{ border: "none", textAlign: "right", padding: "4px 8px 8px", fontSize: 13, fontWeight: 700 }}>
                {fmt(pr.total)}
              </td>
              <td style={{ border: "none" }} colSpan={2} />
            </tr>
          </tbody>
        </table>

        {/* Task 4: NCC 2 cụm — theo quyền. Cụm 'req' (bộ phận đề xuất) luôn in.
            Cụm 'pur' (khảo sát/thu mua) chỉ có dữ liệu khi người in có quyền xem NCC
            (BE trả rỗng nếu không) -> in theo quyền, không cần kiểm tra ở FE. */}
        <div style={SH}>NHÀ CUNG CẤP DO BỘ PHẬN ĐỀ XUẤT</div>
        <div style={info}>
          <div>
            <b>Tên nhà cung cấp:</b> {pr.supplier_req?.name || "Nhà cung cấp tối ưu nhất"}
          </div>
          <div>
            <b>Mã số thuế:</b> {pr.supplier_req?.tax_code || ""}
          </div>
          <div>
            <b>Liên hệ:</b> {pr.supplier_req?.contact || ""}
          </div>
          <div>
            <b>Báo giá đính kèm:</b> {pr.quote_file_url ? "☑" : "☐"} Có &nbsp;&nbsp; {pr.quote_file_url ? "☐" : "☑"} Không
          </div>
        </div>

        {(pr.supplier_pur?.name || pr.supplier_pur?.tax_code || pr.supplier_pur?.contact) && (
          <>
            <div style={SH}>
              NHÀ CUNG CẤP TỪ KHẢO SÁT / THU MUA{pr.supplier_from_survey ? " (nguồn: Yêu cầu báo giá)" : ""}
            </div>
            <div style={info}>
              <div>
                <b>Tên nhà cung cấp:</b> {pr.supplier_pur?.name || ""}
              </div>
              <div>
                <b>Mã số thuế:</b> {pr.supplier_pur?.tax_code || ""}
              </div>
              <div>
                <b>Liên hệ:</b> {pr.supplier_pur?.contact || ""}
              </div>
            </div>
          </>
        )}

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
              (r) => {
                // Mẫu thường: tự chèn ảnh chữ ký + họ tên cho 3 ô có dữ liệu trong hệ thống.
                //   Người lập      = người yêu cầu trên phiếu
                //   TP/BP đề xuất  = người bấm Duyệt (bước 1)
                //   TP/BP mua hàng = người bấm Điều phối (bước 2, CR-034)
                // Ô "Giám đốc" không có bước duyệt tương ứng -> để trống, ký tay.
                // Mẫu thuế để trống toàn bộ như cũ.
                const filled: Record<string, { sign?: string; name?: string }> = taxMode
                  ? {}
                  : {
                      "Người lập": { sign: pr.requester_signature, name: pr.requester },
                      "TP/BP đề xuất": { sign: pr.approver_signature, name: pr.approver_name },
                      "TP/BP mua hàng": { sign: pr.dispatcher_signature, name: pr.dispatcher_name },
                    };
                // Chọn "Không chữ ký" -> bỏ ảnh, giữ họ tên để người ký tự ký tay lên trên.
                const sign = showSign ? filled[r]?.sign || "" : "";
                const name = filled[r]?.name || "";
                return (
                  <div key={r}>
                    <b>{r}</b>
                    <div style={{ fontStyle: "italic", fontSize: 11 }}>
                      (Ký, ghi rõ họ tên)
                    </div>
                    {/* Cụm chữ ký + họ tên căn GIỮA theo chiều dọc: dồn xuống đáy (flex-end)
                        sẽ tách rời khỏi dòng "(Ký, ghi rõ họ tên)" trông như bị rớt xuống.
                        Ô trống (Giám đốc) vẫn giữ nguyên chiều cao để ký tay. */}
                    <div
                      style={{
                        height: 94,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        // Giãn khoảng cách chữ ký -> họ tên: in ra bản giấy thì tên dính sát
                        // nét ký, đọc rối.
                        gap: 10,
                        marginTop: 4,
                        fontWeight: 700,
                      }}
                    >
                      {sign && (
                        <img
                          src={sign}
                          alt=""
                          // 40px in ra giấy nhỏ quá không rõ nét ký -> nâng lên 56px.
                          style={{ maxHeight: 56, maxWidth: 180, objectFit: "contain" }}
                        />
                      )}
                      {name}
                    </div>
                  </div>
                );
              },
            )}
          </div>

        </div>

        {/* Ghi chú nguồn gốc bản in. Trên màn hình: neo vào đáy tờ giấy giả lập (.print-doc có
            position: relative + cao tối thiểu 1 trang A4). Khi IN: đổi sang position: fixed
            (xem thẻ <style> đầu trang) — neo tuyệt đối vào cuối .print-doc thì phiếu dài 2 trang
            sẽ đẩy nó xuống giữa trang 2 chứ không nằm ở góc giấy. In ở cả 2 mẫu. */}
        <div
          className="print-note"
          style={{
            position: "absolute",
            right: "12mm",
            bottom: "7mm",
            fontStyle: "italic",
            fontSize: 8,
            color: "#8a8a8a",
          }}
        >
          Phiếu đề xuất này được in từ hệ thống thu mua
        </div>
      </div>
    </div>
  );
}
