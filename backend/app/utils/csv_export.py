import csv
import io
from datetime import datetime
from typing import Any


def export_csv(rows: list[Any], columns: list[str], filename_prefix: str = "export") -> tuple[bytes, str]:
    """Returns CSV bytes and filename."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        vals = []
        for col in columns:
            v = getattr(row, col, "") if hasattr(row, col) else row.get(col, "")
            if isinstance(v, datetime):
                v = v.isoformat()
            vals.append(v)
        writer.writerow(vals)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return output.getvalue().encode("utf-8"), f"{filename_prefix}_{ts}.csv"
