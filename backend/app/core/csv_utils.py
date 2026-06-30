import csv
from io import StringIO
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.core.utils import generate_code

def export_csv_response(items, headers_map, filename):
    def iter_csv():
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(list(headers_map.values()) + ["Trạng thái"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for item in items:
            row = []
            for field in headers_map.keys():
                val = getattr(item, field, "")
                row.append(val)
            is_active = getattr(item, "is_active", True)
            row.append("Đang dùng" if is_active else "Ngừng")
            
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            
    headers = {"Content-Disposition": f"attachment; filename={filename}.csv"}
    return StreamingResponse(iter_csv(), media_type="text/csv", headers=headers)
