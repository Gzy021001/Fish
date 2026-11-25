import openpyxl
p = r"C:\Users\g018107\Desktop\慈悲组购生明细表2026.xlsx"
wb = openpyxl.load_workbook(p, data_only=True)
for name in ["1月3日","2月7日","5月16日","8月1日","10月17日","11月8日","11月14日"]:
    ws = wb[name]
    print("=== ", name, "maxcol", ws.max_column)
    for r in range(1, 60):
        vals = []
        for c in range(1, 12):
            v = ws.cell(r, c).value
            if v is not None and str(v).strip() != "":
                vals.append(f"{openpyxl.utils.get_column_letter(c)}{r}={v!r}")
        if vals:
            print(" | ".join(vals))
    print()
