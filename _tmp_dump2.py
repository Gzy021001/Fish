import openpyxl
p = r"C:\Users\g018107\Desktop\慈悲组购生明细表2026.xlsx"
wb = openpyxl.load_workbook(p, data_only=True)
for name in ["11月21日"]:
    ws = wb[name]
    print("=== ", name, ws.max_row, ws.max_column)
    for r in range(1, 90):
        vals = []
        for c in range(1, ws.max_column+1):
            v = ws.cell(r, c).value
            if v is not None and str(v).strip() != "":
                vals.append(f"{openpyxl.utils.get_column_letter(c)}{r}={v!r}")
        if vals:
            print(" | ".join(vals))
