import pandas as pd
import datetime
df=pd.read_csv('电商可视化生成文件\\sales_data.csv')
#csv文件列：  月份	商品品类	销售区域	订单量	客单价	销售额	利润率（小数，不是百分数）

primitive_len=len(df)
df = df[df["销售额"] != ""]
df = df[df["订单量"] > 0]

df['利润额'] = round(df['销售额'] * df['利润率'],2)
print(df)

clear_len=len(df)#去除问题行之后的长度

total_sales = df['销售额'].sum()
total_orders = df['订单量'].sum()
mean_profit_rate = df['利润率'].mean()

print('2024年总销售额：',total_sales)
print('2024年总订单量：',total_orders)
print('2024年平均利润率：',mean_profit_rate)



# 按'category'分组，计算各品类的销售额、订单量、平均利润率
grouped = df.groupby('商品品类').agg({
    '销售额': 'sum',       # 计算销售额总和
    '订单量': 'sum',      # 计算订单量总和
    '利润率': 'mean'  # 计算平均利润率
}).reset_index()

# 按销售额降序排列
sorted_df = grouped.sort_values(by='销售额', ascending=False)

# 显示结果
print(sorted_df)

month_sales = df.groupby('月份').agg({
    '销售额': 'sum',
    #'订单量': 'sum',
    '利润率': 'mean'
}).reset_index()

print("月销：",month_sales)

region_sales = df.groupby('销售区域').agg({
    '销售额': 'sum'
}).reset_index()
#['华东', np.float64(0.21099843604341)]
region_sales_rate = [[d[0],float(d[1]/total_sales)] for d in region_sales.values]#内部数组：[地区:销售额]
print("区域销售额占比：",region_sales_rate)


#wenxin#2026.08.11#
# 按品类和区域分组，计算每个组合的销售额总和
grouped_category_region = df.groupby(['商品品类', '销售区域'])['销售额'].sum().reset_index()

# 按销售额降序排序
sorted_category_region = grouped_category_region.sort_values(by='销售额', ascending=False)###

# 选择Top 3
top3 = sorted_category_region.head(3)

print("销售额最高的 Top3 品类 - 区域组合:",top3)

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import io
from reportlab.platypus import Image

def fig_to_image(fig, dpi=100, width_cm=12):
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    """将 matplotlib Figure 转为 reportlab 可用的 Image 对象（按原始比例缩放，不变形）"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    # 读取图片原始像素宽高，高度按同比例计算，避免被拉伸成椭圆 #2026.08.16#codebuddy#
    iw, ih = ImageReader(buf).getSize()
    target_w = width_cm*cm
    target_h = target_w * ih / iw
    buf.seek(0)
    return Image(buf, width=target_w, height=target_h)  # 可调整尺寸 #

# 设置字体库
plt.rcParams['font.sans-serif'] = ['SimHei']#, 'Microsoft YaHei', 'KaiTi'
plt.rcParams['axes.unicode_minus'] = False

#dpsk#
fig1, ax1 = plt.subplots(figsize=(6, 4))
ax1.plot(month_sales["月份"], month_sales["销售额"], marker='o', label='2025')
ax1.set_title('2024年月度趋势对比', fontsize=14, color='darkblue')
ax1.set_xlabel('月份', fontsize=12)
ax1.set_ylabel('销售额')
img_monthly = fig_to_image(fig1)
plt.close(fig1)  # 关闭释放内存

#品类柱状图
# 先计算 Top1 品类
top1_category = grouped.loc[grouped['销售额'].idxmax(), '商品品类']
top1_sales = grouped['销售额'].max()
total_sales = df['销售额'].sum()
top1_contrib = top1_sales / total_sales * 100

fig2, ax2 = plt.subplots(figsize=(5, 3))
bars = ax2.bar(grouped['商品品类'], grouped['销售额'])
for bar in bars:
    height = bar.get_height()
    ax2.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0,3), textcoords="offset points", ha='center', va='bottom')
ax2.set_title('分类销售额')
img_category = fig_to_image(fig2, dpi=100)
plt.close(fig2)  # 关闭释放内存

#地区饼状图#dpsk#
fig3, ax3 = plt.subplots(figsize=(5, 5))
ax3.pie([d[1] for d in region_sales.values], labels=[rgn[0] for rgn in region_sales.values], autopct='%.f%%')
ax3.set_title('商品市场区域分布')
ax3.axis('equal')
img_region = fig_to_image(fig3)
plt.close(fig3)

#品类-利润率柱状图 
#plt.figure(figsize=(5, 3))
#plt.bar(grouped['商品品类'], grouped['利润率'])
# 创建柱状图
fig, ax = plt.subplots(figsize=(7, 7))
bars = ax.barh(grouped['商品品类'], grouped['利润率'])#水平化
ax.set_xlabel("商品品类")#不能用等号。这是方法，不是属性
ax.set_ylabel("利润率")
plt.show()
img_profit_rate=fig_to_image(fig)###2026.08.13#

from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class ReportDoc(SimpleDocTemplate):#接管目录条目捕获：#2026.08.13#codebuddy#
    """文档模板：为章节标题建立 PDF 书签锚点，并通知目录生成可点击条目"""
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            if style_name == 'Heading1':
                level = 0
            elif style_name == 'Heading2':
                level = 1
            else:
                return
            text = flowable.getPlainText()
            key = 'h%d-%d' % (level, self.seq.next('toc'))
            self.canv.bookmarkPage(key)                                     # 锚点（供目录跳转）
            self.canv.addOutlineEntry(text, key, level=level, closed=False)  # PDF 左侧书签
            # 目录条目文本用 <a> 包起来 → 点击可跳转到对应章节
            self.notify('TOCEntry', (level, f'<a href="#{key}" color="#1155CC">{text}</a>', self.page, key))

doc = ReportDoc(f"table {datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")

#bing#2026.08.13#
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# 注册自定义字体（TTF 字体自带 family 映射，目录 TOC 才能用）
pdfmetrics.registerFont(TTFont("MyCJK", r"C:\Windows\Fonts\simhei.ttf"))
# 显式声明字体族，避免目录报 "Can't map determine family/bold/italic"
pdfmetrics.registerFontFamily("MyCJK", normal="MyCJK", bold="MyCJK",
                              italic="MyCJK", boldItalic="MyCJK")


'''data=[
      [str(datetime.datetime.now())],
      "WAr"]'''
data=[
    ["总销售额","总订单量","总利润率"],
    [f"{total_sales:,.2f}￥",total_orders,f"{mean_profit_rate*100:.2f}%"]
]
table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])

# 设置表格样式
table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'MyCJK'),        # 关键：表格用中文字体 #2026.08.16
    ('FONTSIZE', (0, 0), (-1, -1), 11),
    ('BACKGROUND', (0, 0), (-1, 0), colors.gray),   # 仅标题行：灰底
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # 仅标题行：白字
    ('BACKGROUND', (0, 1), (-1, 1), colors.white),  # 数据行：白底
    ('TEXTCOLOR', (0, 1), (-1, 1), colors.black),   # 数据行：黑字
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),          # 水平居中
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),         # 垂直居中
    ('GRID', (0, 0), (-1, -1), 1, colors.black)     # 边框线
]))

# 内容
story = []

# 添加表格
#story.append(table)

from reportlab.platypus import  Spacer,PageBreak,KeepTogether
#from reportlab.platypus import TableOfContents  # 目录专用
from reportlab.platypus.tableofcontents import TableOfContents  # 正确的导入路径 #2026.08.13#

from reportlab.lib.enums import TA_CENTER, TA_LEFT

#dpsk#标题样式#
styles = getSampleStyleSheet()
#styles.fontName = 'SimHei'#######

# 关键：所有内置样式统一换成中文字体（否则中文渲染成方框）
styles['Normal'].fontName = 'MyCJK'
styles['Heading1'].fontName = 'MyCJK'
styles['Heading2'].fontName = 'MyCJK'

# 直接调整内置 Heading1/Heading2 的参数（不要自定义 MyHeading1/MyHeading2，
# 因为 reportlab 的目录只捕获样式名恰好为 Heading1/Heading2 的段落）
styles['Heading1'].fontSize = 16
styles['Heading1'].alignment = TA_LEFT
styles['Heading1'].spaceAfter = 12
styles['Heading2'].fontSize = 14
styles['Heading2'].alignment = TA_LEFT
styles['Heading2'].spaceAfter = 8

# 目录样式（默认带点状引导线和页码）
# TableOfContents 自带 levelStyles，可以直接修改
toc = TableOfContents()

# 设置目录中各级标题的样式（字体、缩进等）
toc.levelStyles[0].fontName = 'MyCJK'
toc.levelStyles[0].fontSize = 12
toc.levelStyles[0].leading = 18
toc.levelStyles[0].alignment = TA_LEFT
toc.levelStyles[0].spaceAfter = 6
# reportlab 5.0 默认只有一级样式，这里补一个二级样式（缩进）
toc.levelStyles.append(ParagraphStyle(
    'toc2', parent=toc.levelStyles[0],
    fontName='MyCJK', fontSize=11, leftIndent=24))



#构建文档故事（story）的顺序
#story = []

# ---- 标题页 ----
title_style = ParagraphStyle('TitlePage', parent=styles['Title'], alignment=TA_CENTER, fontSize=24, fontName='MyCJK')
story.append(Paragraph("2024 年度电商销售数据分析报告", title_style))
story.append(Spacer(1, 12))

# 居中样式不能直接传给 Paragraph，要放进 ParagraphStyle 里 #先建居中样式
time_style = ParagraphStyle('Time', parent=styles['Heading2'], alignment=TA_CENTER)
story.append(Paragraph(str(datetime.datetime.now()), time_style))

story.append(Paragraph("报告人：War", styles['Normal']))
story.append(PageBreak())  # 分页，使目录独占一页

# ---- 目录 ----
# 目录页标题用独立样式（不能用 Heading1，否则目录会把"目 录"自己也收录进去）
toc_title_style = ParagraphStyle('TocTitle', parent=styles['Heading1'],
                                 alignment=TA_CENTER, fontSize=18, spaceAfter=16)
story.append(Paragraph("目 录", toc_title_style))  # 目录本身的小标题
story.append(toc)  # 目录对象
story.append(PageBreak())  # 目录后分页，正文另起一页

# ---- 正文（各章节） ----
story.append(Paragraph("数据概览", styles['Heading1']))


story.append(Paragraph(f"原始数据表行数: {primitive_len}", styles['Normal']))
story.append(Paragraph(f"去重后的数据表行数：{clear_len}", styles['Normal']))
story.append(table)


# 章节1：月度趋势（标题与图打包同页，放不下时整体移到下一页）#codebuddy#2026.08.16#
story.append(KeepTogether([
    Paragraph("月度销售趋势", styles['Heading1']),  # 该样式会被目录捕获
    img_monthly,  # 之前生成的月度图
    Spacer(1, 12),
]))

# 章节2：品类分析
story.append(KeepTogether([
    Paragraph("各品类销售额分析", styles['Heading1']),
    img_category,
    Paragraph(f"冠销：{top1_sales}", styles['Normal']),  # 字符串要全写在一起
    Spacer(1, 12),
]))

# 章节3：区域分布
story.append(KeepTogether([
    Paragraph("区域销售占比", styles['Heading1']),
    img_region,
    Spacer(1, 12),
]))

# 如果有更多内容，继续添加……

story.append(KeepTogether([
    Paragraph("品类-利润率柱状图:", styles['Heading1']),
    img_profit_rate,
]))

# 构建（两遍）#dpsk#2026.08.13#
doc.multiBuild(story)