"""按「慈悲组购生明细表」模板样式导出单据明细。

模板结构（与桌面模板《慈悲组购生明细表2026.xlsx》一致）：
- 按放生日期分组，每个日期一个 sheet（sheet 名「M月D日」）
- 第 2 行标题（同日期有服务费 -> 7 列版合并 B2:H2；全无 -> 6 列版合并 B2:G2）
- 第 3 行表头：序号/品种/重量(斤)/单价(元)/总计[/服务费/]实付
- 数据行第 4 行起：总计=重量×单价（公式）、实付=总计+服务费（公式，7 列版）
- 右侧收款区：与数据行同排起固定四行 支付宝 / 微信 / 微信 / 随喜放生（金额取自单据录入金额，
  微信按录入顺序拆两行；没有金额的行留空，不影响导出），末行「本周随喜」=SUM 公式
- 表尾汇总块：车费（灰底）/船费（黄底）留空行、购生总重量 =SUM、慈悲护生购生实付金额 =SUM（绿底，
  含车费/船费行）、上周余款（=上个 sheet 本周余款）、本周随喜（=收款区合计）、本周现场随喜（同日第一条录入值）、
  本周随喜累计 =SUM、本周余款 =累计-实付；每行整行 thin 边框 + 模板对应底色
- 样式：微软雅黑 10、标题浅棕底 FFF8CBAD、表头灰底 FFD9D9D9、thin 边框、金额列 0.00 数字格式、列宽照模板
"""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import models

CENT = Decimal("0.01")

# 三种随喜类型 -> 单据金额字段（顺序与模板一致）
PAYMENT_ORDER = [
    ("支付宝", "alipay_amount"),
    ("微信", "wechat_amount"),
    ("随喜放生", "suixi_amount"),
]

# 模板样式常量
THIN = Side(style="thin")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
TITLE_FONT = Font(name="微软雅黑", size=10, bold=True)
HEADER_FONT = Font(name="微软雅黑", size=10, bold=True, color="FF000000")
DATA_FONT = Font(name="微软雅黑", size=10, color="FF000000")
LABEL_FONT = Font(name="微软雅黑", size=10, bold=True, color="FF000000")
TITLE_FILL = PatternFill(fill_type="solid", fgColor="FFF8CBAD")
HEADER_FILL = PatternFill(fill_type="solid", fgColor="FFD9D9D9")
GREEN_FILL = PatternFill(fill_type="solid", fgColor="FF70AD47")
CREAM_FILL = PatternFill(fill_type="solid", fgColor="FFFFF2CC")
PINK_FILL = PatternFill(fill_type="solid", fgColor="FFF8CBAD")
GREY_FILL = PatternFill(fill_type="solid", fgColor="FFD9D9D9")
YELLOW_FILL = PatternFill(fill_type="solid", fgColor="FFFFFF00")
NO_FILL = PatternFill(fill_type="solid", fgColor="00000000")
RED_FONT = Font(name="微软雅黑", size=10, color="FFFF0000")
CENTER_WRAP = Alignment(horizontal="center", vertical="center", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center")
MONEY_FMT = "0.00;[Red]0.00"
MONEY_FMT_HEADER = "0.00_ "
MONEY_FMT_SUM = "0.00_ "

# 模板列宽（A 为左侧留白列；H 列在模板中未显式设置，保持默认）
COL_WIDTHS = {"A": 5.44, "B": 4.56, "C": 17.77, "D": 10.22, "E": 8.78,
              "F": 10.56, "G": 10.56, "I": 24.77, "J": 8.33, "K": 10.56,
              "L": 10.56, "M": 8.88}


def _q(v: Decimal) -> float:
    """金额转两位小数 float（openpyxl 单元格写入用，显示层不参与运算）。"""
    return float(v.quantize(CENT, rounding=ROUND_HALF_UP))


def _dec(v) -> Decimal:
    if v is None:
        return Decimal("0.00")
    return Decimal(str(v))


def _write(ws, row, col, value, *, font=DATA_FONT, fill=None, align=None,
           number_format=None, border=BORDER):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = font
    if fill is not None:
        cell.fill = fill
    if align is not None:
        cell.alignment = align
    if number_format is not None:
        cell.number_format = number_format
    cell.border = border
    return cell


def _payment_columns(has_fee: bool):
    """收款区列：7 列版用 J/K，6 列版用 I/J。"""
    if has_fee:
        return 10, 11
    return 9, 10


def _build_sheet(wb: openpyxl.Workbook, d: date, bills: list, carry_in, multi_year: bool = False):
    """构建单日 sheet，返回本周余款（供下一 sheet 的「上周余款」使用）。"""
    has_fee = any((b.fee_value is not None and _dec(b.fee_value) > 0) for b in bills)
    end_col = 8 if has_fee else 7  # H(8) / G(7)
    end_letter = get_column_letter(end_col)
    label_col, amount_col = _payment_columns(has_fee)

    # 跨年导出时 sheet 名与标题带年份，避免出现两个「1月1日」重名 sheet
    sheet_title = f"{d.year}年{d.month}月{d.day}日" if multi_year else f"{d.month}月{d.day}日"
    ws = wb.create_sheet(title=sheet_title)

    for col_letter, width in COL_WIDTHS.items():
        ws.column_dimensions[col_letter].width = width

    # 标题行（合并 + 样式）
    ws.merge_cells(f"B2:{end_letter}2")
    ws["B2"] = f"{d.year}年{d.month}月{d.day}日购生付款明细"
    for col in range(2, end_col + 1):
        cell = ws.cell(row=2, column=col)
        cell.font = TITLE_FONT
        cell.fill = TITLE_FILL
        cell.alignment = CENTER_WRAP
        cell.border = BORDER

    # 表头行
    headers = ["序号", "品种", "重量(斤)", "单价(元)", "总计"]
    if has_fee:
        headers.append("服务费")
    headers.append("实付")
    for i, header in enumerate(headers):
        cell = ws.cell(row=3, column=2 + i, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_WRAP
        cell.border = BORDER
        if i >= 2:  # 重量及之后的数值列表头
            cell.number_format = MONEY_FMT_HEADER

    # 数据行（第 4 行起）：总计/实付用公式，与模板一致
    for idx, b in enumerate(bills, start=1):
        row = 3 + idx
        _write(ws, row, 2, idx, align=CENTER_WRAP)
        # 模板里按「件/个」报价的行（蛏子（件）、带子（个））要原样写回，
        # 否则统一折成「斤」与源表对不上：单据记了 unit/unit_jin 时按原单位还原数量与单价，
        # 没记（手工录入/按斤导入）就仍按斤换算。
        unit = (b.unit or "").strip()
        unit_jin = _dec(b.unit_jin) if b.unit_jin is not None else Decimal("0")
        if unit and unit_jin > 0:
            name = f"{b.species.name_zh}（{unit}）" if b.species else unit
            qty = _dec(b.weight) * Decimal("2") / unit_jin
            price = _dec(b.unit_price) / Decimal("2") * unit_jin
        else:
            name = b.species.name_zh if b.species else ""
            qty = _dec(b.weight) * Decimal("2")
            price = _dec(b.unit_price) / Decimal("2")
        _write(ws, row, 3, name, align=CENTER_WRAP)
        # 模板「重量(斤)」「单价(元)」是斤制；系统内部存公斤、元/公斤，导出必须换算，
        # 否则重量/单价数值与表头单位不匹配（往返导入还会再减半）。
        _write(ws, row, 4, _q(qty), align=CENTER, number_format=MONEY_FMT)
        _write(ws, row, 5, _q(price), align=CENTER, number_format=MONEY_FMT)
        _write(ws, row, 6, f"=D{row}*E{row}", align=CENTER, number_format=MONEY_FMT)
        if has_fee:
            fee = b.fee_value if b.fee_value is not None else 0
            _write(ws, row, 7, _q(_dec(fee)), align=CENTER, number_format=MONEY_FMT)
            _write(ws, row, 8, f"=F{row}+G{row}", align=CENTER, number_format=MONEY_FMT)
        else:
            _write(ws, row, 7, _q(_dec(b.total_amount)), align=CENTER, number_format=MONEY_FMT)

    last_data_row = 3 + len(bills)

    # 右侧收款区（固定四行：支付宝 / 微信 / 微信 / 随喜放生；末行「本周随喜」=SUM）
    # 收款行与数据行同排起（第 4 行），与模板一致；没填金额的行留空，不影响导出
    alipay_vals: list = []
    wechat_vals: list = []
    suixi_vals: list = []
    for b in bills:
        has_amt = False
        if b.alipay_amount is not None and _dec(b.alipay_amount) > 0:
            alipay_vals.append(_dec(b.alipay_amount))
            has_amt = True
        if b.wechat_amount is not None and _dec(b.wechat_amount) > 0:
            wechat_vals.append(_dec(b.wechat_amount))
            has_amt = True
        if b.suixi_amount is not None and _dec(b.suixi_amount) > 0:
            suixi_vals.append(_dec(b.suixi_amount))
            has_amt = True
        if not has_amt and b.payment_method:
            # 兼容旧数据：只填了随喜类型没填金额时，用实付金额兜底
            amt = _dec(b.total_amount)
            if b.payment_method == "支付宝":
                alipay_vals.append(amt)
            elif b.payment_method == "微信":
                wechat_vals.append(amt)
            elif b.payment_method == "随喜放生":
                suixi_vals.append(amt)

    alipay_total = sum(alipay_vals, Decimal("0.00")) if alipay_vals else None
    suixi_total = sum(suixi_vals, Decimal("0.00")) if suixi_vals else None
    wechat1 = wechat_vals[0] if wechat_vals else None
    wechat2 = sum(wechat_vals[1:], Decimal("0.00")) if len(wechat_vals) > 1 else None

    entries_total = sum(
        (v for v in (alipay_total, wechat1, wechat2, suixi_total) if v is not None),
        Decimal("0.00"),
    )

    payment_rows = [
        ("支付宝", alipay_total),
        ("微信", wechat1),
        ("微信", wechat2),
        ("随喜放生", suixi_total),
    ]
    for i, (label, val) in enumerate(payment_rows):
        r = 4 + i
        _write(ws, r, label_col, label, align=CENTER_WRAP)
        _write(ws, r, amount_col, _q(val) if val is not None else None,
               align=CENTER_WRAP, number_format=MONEY_FMT_SUM)

    # 「本周随喜」合计行（模板：=SUM 公式）
    sum_row = 4 + len(payment_rows)
    _write(ws, sum_row, label_col, "本周随喜", align=CENTER_WRAP)
    _write(ws, sum_row, amount_col,
           f"=SUM({get_column_letter(amount_col)}4:{get_column_letter(amount_col)}{sum_row - 1})",
           align=CENTER_WRAP, number_format=MONEY_FMT_SUM)

    # 表尾汇总块（填充色/边框与模板一致：整行 thin 边框 + 行底色）
    seq = len(bills) + 1
    row = last_data_row + 1

    def fill_row(r, fill=None):
        for col in range(2, end_col + 1):
            cell = ws.cell(row=r, column=col)
            if fill is not None:
                cell.fill = fill
            cell.border = BORDER

    # 车费（灰底）/ 船费（黄底）：金额由使用者在导出文件里手工填写
    _write(ws, row, 2, seq, align=CENTER_WRAP)
    _write(ws, row, 3, "车费", font=LABEL_FONT, align=CENTER_WRAP)
    fill_row(row, GREY_FILL)
    seq += 1
    boat_row = row + 1
    _write(ws, boat_row, 2, seq, align=CENTER_WRAP)
    _write(ws, boat_row, 3, "船费", font=LABEL_FONT, align=CENTER_WRAP)
    fill_row(boat_row, YELLOW_FILL)

    # 购生总重量（无底色，标签/重量红字）
    seq += 1
    weight_sum_row = boat_row + 1
    _write(ws, weight_sum_row, 2, seq, align=CENTER_WRAP)
    _write(ws, weight_sum_row, 3, "购生总重量", font=RED_FONT, align=CENTER_WRAP)
    _write(ws, weight_sum_row, 4, f"=SUM(D4:D{last_data_row})", font=RED_FONT,
           align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    fill_row(weight_sum_row)

    # 慈悲护生购生实付金额（绿底，合并 C:F，合计含车费/船费行）
    seq += 1
    total_row = weight_sum_row + 1
    _write(ws, total_row, 2, seq, fill=GREEN_FILL, align=CENTER_WRAP)
    _write(ws, total_row, 3, "慈悲护生购生实付金额", font=LABEL_FONT, fill=GREEN_FILL,
           align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    _write(ws, total_row, end_col, f"=SUM({end_letter}4:{end_letter}{boat_row})",
           fill=GREEN_FILL, align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    # 先合并再整行上色：openpyxl 合并会把被合并格样式重置，需在合并后补
    ws.merge_cells(f"C{total_row}:F{total_row}")
    fill_row(total_row, GREEN_FILL)

    # 上周余款（米色底，数值格深米色）
    seq += 1
    last_week_row = total_row + 1
    _write(ws, last_week_row, 2, seq, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, last_week_row, 3, "上周余款", font=LABEL_FONT, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, last_week_row, 6, _q(carry_in) if carry_in is not None else None,
           fill=PINK_FILL, align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    fill_row(last_week_row, CREAM_FILL)
    ws.cell(row=last_week_row, column=6).fill = PINK_FILL

    seq += 1
    week_sum_row = last_week_row + 1
    _write(ws, week_sum_row, 2, seq, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, week_sum_row, 3, "本周随喜", font=LABEL_FONT, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, week_sum_row, 6, f"={get_column_letter(amount_col)}{sum_row}",
           fill=CREAM_FILL, align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    fill_row(week_sum_row, CREAM_FILL)

    seq += 1
    onsite_row = week_sum_row + 1
    weekly = next(
        (_dec(b.weekly_donation) for b in bills if b.weekly_donation is not None),
        None,
    )
    _write(ws, onsite_row, 2, seq, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, onsite_row, 3, "本周现场随喜", font=LABEL_FONT, fill=CREAM_FILL, align=CENTER_WRAP)
    if weekly is not None:
        _write(ws, onsite_row, 6, _q(weekly), fill=CREAM_FILL,
               align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    fill_row(onsite_row, CREAM_FILL)

    seq += 1
    accum_row = onsite_row + 1
    _write(ws, accum_row, 2, seq, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, accum_row, 3, "本周随喜累计", font=LABEL_FONT, fill=CREAM_FILL, align=CENTER_WRAP)
    _write(ws, accum_row, 6, f"=SUM(F{last_week_row}:F{onsite_row})",
           fill=CREAM_FILL, align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    fill_row(accum_row, CREAM_FILL)

    # 本周余款（粉米色底，数值红字）
    seq += 1
    remain_row = accum_row + 1
    _write(ws, remain_row, 2, seq, fill=PINK_FILL, align=CENTER_WRAP)
    _write(ws, remain_row, 3, "本周余款", font=LABEL_FONT, fill=PINK_FILL, align=CENTER_WRAP)
    _write(ws, remain_row, 6, f"=F{accum_row}-{end_letter}{total_row}",
           font=RED_FONT, fill=PINK_FILL, align=CENTER_WRAP, number_format=MONEY_FMT_SUM)
    fill_row(remain_row, PINK_FILL)

    # 本周余款（数值，供下一 sheet「上周余款」链条）
    actual_total = sum((_dec(b.total_amount) for b in bills), Decimal("0.00"))
    carry_out = ((carry_in if carry_in is not None else Decimal("0.00"))
                 + entries_total
                 + (weekly if weekly is not None else Decimal("0.00"))
                 - actual_total)
    return carry_out


def _build_workbook(bills: list):
    groups: dict = {}
    for b in bills:
        groups.setdefault(b.release_date, []).append(b)

    dates = sorted(groups.keys())
    multi_year = len({d.year for d in dates}) > 1

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    carry = None
    for d in dates:
        carry = _build_sheet(wb, d, groups[d], carry, multi_year=multi_year)

    content = BytesIO()
    wb.save(content)
    content.seek(0)

    if len(dates) == 1:
        filename = f"慈悲组购生明细表_{dates[0].strftime('%Y%m%d')}.xlsx"
    else:
        filename = f"慈悲组购生明细表_{dates[0].strftime('%Y%m%d')}_{dates[-1].strftime('%Y%m%d')}.xlsx"
    return content, quote(filename)


def build_bills_export(db: Session, date_from: str, date_to: str):
    try:
        d_from = date.fromisoformat(date_from)
        d_to = date.fromisoformat(date_to)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式无效")
    if d_from > d_to:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
    if (d_to - d_from).days > 366:
        raise HTTPException(status_code=400, detail="导出日期范围不能超过一年")

    bills = (
        db.query(models.Bill)
        .join(models.Species)
        .options(joinedload(models.Bill.species))
        .filter(
            models.Bill.release_date >= d_from,
            models.Bill.release_date < d_to + timedelta(days=1),
            models.Bill.is_deleted.is_(False),
        )
        .order_by(models.Bill.release_date.asc(), models.Bill.id.asc())
        .all()
    )
    if not bills:
        raise HTTPException(status_code=404, detail="该日期范围内没有单据")

    return _build_workbook(bills)


def build_bills_export_by_ids(db: Session, bill_ids: list):
    """按勾选的单据批量导出（勾选行来自最新单据或历史单据列表）。"""
    ids = sorted({int(x) for x in bill_ids})
    if not ids:
        raise HTTPException(status_code=400, detail="请选择需要导出的单据")
    if len(ids) > 500:
        raise HTTPException(status_code=400, detail="单次最多导出 500 条单据")

    bills = (
        db.query(models.Bill)
        .join(models.Species)
        .options(joinedload(models.Bill.species))
        .filter(models.Bill.id.in_(ids), models.Bill.is_deleted.is_(False))
        .order_by(models.Bill.release_date.asc(), models.Bill.id.asc())
        .all()
    )
    if not bills:
        raise HTTPException(status_code=404, detail="选中的单据不存在或已被删除")

    missing_date = [b for b in bills if b.release_date is None]
    if missing_date:
        raise HTTPException(
            status_code=400,
            detail=f"选中的单据中有 {len(missing_date)} 条缺少放生日期，无法按模板导出",
        )

    return _build_workbook(bills)


def build_bills_export_all(db: Session):
    """导出全部单据（列表未勾选任何数据时的全量导出）。"""
    bills = (
        db.query(models.Bill)
        .join(models.Species)
        .options(joinedload(models.Bill.species))
        .filter(
            models.Bill.is_deleted.is_(False),
            models.Bill.release_date.isnot(None),
        )
        .order_by(models.Bill.release_date.asc(), models.Bill.id.asc())
        .all()
    )
    if not bills:
        raise HTTPException(status_code=404, detail="暂无单据可导出")

    return _build_workbook(bills)


def build_species_export(db: Session, species_ids: list | None = None):
    """导出品种库 xlsx：勾选则只导选中的，否则全量（排序与品种列表一致）。"""
    ids = sorted({int(x) for x in species_ids}) if species_ids else []
    if len(ids) > 2000:
        raise HTTPException(status_code=400, detail="单次最多导出 2000 个品种")

    query = db.query(models.Species).filter(models.Species.is_deleted.is_(False))
    if ids:
        query = query.filter(models.Species.id.in_(ids))
    items = (
        query.order_by(
            models.Species.release_date.desc().nullslast(),
            models.Species.id.desc(),
        )
        .all()
    )
    if not items:
        raise HTTPException(status_code=404, detail="选中范围内没有品种可导出")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "品种库"

    widths = {"A": 6.56, "B": 20.78, "C": 10.56, "D": 14.23, "E": 10.23}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    headers = ["序号", "品种", "单价（元）", "放生日期", "默认单位"]
    for i, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=i, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_WRAP
        cell.border = BORDER
        cell.number_format = MONEY_FMT_HEADER

    for idx, sp in enumerate(items, start=1):
        row = idx + 1
        _write(ws, row, 1, idx, align=CENTER_WRAP)
        _write(ws, row, 2, sp.name_zh or "", align=CENTER_WRAP)
        _write(ws, row, 3, _q(_dec(sp.default_price)), align=CENTER, number_format=MONEY_FMT)
        _write(
            ws,
            row,
            4,
            sp.release_date.strftime("%Y-%m-%d") if sp.release_date else "",
            align=CENTER_WRAP,
        )
        _write(ws, row, 5, sp.default_unit or "", align=CENTER_WRAP)

    content = BytesIO()
    wb.save(content)
    content.seek(0)

    filename = f"慈悲组品种库_{date.today().strftime('%Y%m%d')}.xlsx"
    return content, quote(filename)


