with open(r"d:\Fish\src\lib\importUtils.ts", "r", encoding="utf-8") as f:
    assert "return `\${y}-\${month}`" in f.read(), "parseSheetDate not updated"
with open(r"d:\Fish\backend\schemas.py", "r", encoding="utf-8") as f:
    assert "Optional[str]" in f.read(), "Schema not updated"
print("ALL CHECKS PASSED")
