import openpyxl, sys
p = r"C:\Users\g018107\Desktop\慈悲组购生明细表2026.xlsx"
wb = openpyxl.load_workbook(p, data_only=True, read_only=False)
print("sheets:", len(wb.sheetnames))
for i, s in enumerate(wb.sheetnames, 1):
    ws = wb[s]
    print(i, repr(s), ws.max_row, ws.max_column)
