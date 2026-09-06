#
# Copyright @  2021  苏州领慧立芯科技有限公司
# 苏州领慧立芯科技有限公司内部保密技术代码， 您需要对代码保密负责， 不得转发给任何外部实体和个人
# Autor: Henry512@legendsemi.com
#
# Usage, 
#    - get help
#       'python gen_ds.py -h'
#    - generate register documentation from command line, example:
#       'python gen_ds.py ..\lh003reg.db -f lh003reg.docx'
#





from docx import Document 
from docx.shared import * 
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import argparse
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db
from docx.oxml import OxmlElement


BIT_TABLE_HEADER = ['Bit Name','Position','Description','Default','Access','Key']
BIT_TABLE_WIDTH = [1*914400, 1*914400, 2.8*914400, 1*914400, 1*914400, 1*914400]

class GEN_DS():
    def __init__(self, modules, docName):
        self._modules = modules
        self._doc = Document()


        section = self._doc.sections[0]
        section.left_margin = Inches(0.7874)    # 左1.5厘米
        section.right_margin = Inches(0.7874)   # 右1.5厘米
        section.top_margin = Inches(0.3937)     # 上2.0厘米
        section.bottom_margin = Inches(0.3937)  # 下2.0厘米


        # 设置纸张为 A4
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)

        if '.docx' in docName:
            self._dsName = docName
        else: 
            self._dsName = docName + '.docx'

        styles = self._doc.styles
        
        # 自定义模块标题样式（基于Heading 1）
        if 'ModuleTitle' not in styles:
            style = styles.add_style('ModuleTitle', WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = styles['Heading 4']  # 继承Heading 1，方便目录生成
            font = style.font
            font.name = '等线'
            font.size = Pt(11)
            font.bold = True  # 去掉粗体
            font.italic = False
            font.color.rgb = RGBColor(0, 0, 0)  # 设置字体颜色为黑色
            style.paragraph_format.space_after = Pt(0)
            style.paragraph_format.space_before = Pt(0)

        # 自定义寄存器标题样式（基于Heading 2）
        if 'RegTitle' not in styles:
            style = styles.add_style('RegTitle', WD_STYLE_TYPE.PARAGRAPH)
            style.base_style = styles['Heading 5']
            font = style.font
            font.name = '等线'
            font.size = Pt(11)
            font.bold = True
            font.italic = False
            font.color.rgb = RGBColor(0, 0, 0)  # 设置字体颜色为黑色
            style.paragraph_format.space_after = Pt(0)
            style.paragraph_format.space_before = Pt(0)

        # 普通正文样式
        if 'NormalText' not in styles:
            style = styles.add_style('NormalText', WD_STYLE_TYPE.PARAGRAPH)
            font = style.font
            font.name = '等线'
            font.size = Pt(11)
            font.bold = False
            style.paragraph_format.space_after = Pt(0)
            style.paragraph_format.space_before = Pt(0)

    # def gen_regTable_desc(self, reg, module):
    #     # 生成寄存器标题，使用RegTitle样式
    #     DS_MMR_DESC = ''
    #     if reg.default_value is not None:
    #         DS_MMR_DESC = "Register Name: {0}, Page: 0x{1:<8x},Address: 0x{2:<8x}, Default: 0x{3:<8x}"\
    #             .format(reg.name, module.address, reg.address, reg.default_value)
    #     else:
    #         DS_MMR_DESC = "Register Name: {0}, Address: 0x{1:<8x}"\
    #             .format(reg.name, reg.address + module.address)

    #     para = self._doc.add_paragraph(DS_MMR_DESC)
    #     para.style = self._doc.styles['RegTitle']
        
    #     if reg.desc is not None:
    #         para2 = self._doc.add_paragraph("{}".format(reg.desc))
    #         for run in para2.runs:
    #             run.font.name = '等线'
    #             run.font.bold = False
    #             run.font.size = Pt(10)
    #             r = run._element
    #             r.rPr.rFonts.set(qn('w:eastAsia'), '等线')

    def gen_regTable_desc(self, reg, module):
        # 生成寄存器标题，使用RegTitle样式
        DS_MMR_DESC = ''
        if reg.default_value is not None:
            DS_MMR_DESC = "Register Name: {0}, Page: 0x{1:<8x}, Address: 0x{2:<8x}, Default: 0x{3:<8x}"\
                .format(reg.name, module.address, reg.address, reg.default_value)
        else:
            DS_MMR_DESC = "Register Name: {0}, Address: 0x{1:<8x}"\
                .format(reg.name, reg.address + module.address)

        # 添加寄存器标题段落
        para = self._doc.add_paragraph(DS_MMR_DESC)
        para.style = self._doc.styles['RegTitle']

        # 设置字体格式的辅助函数
        def format_para(p):
            for run in p.runs:
                run.font.name = '等线'
                run.font.bold = False
                run.font.size = Pt(11)
                r = run._element
                r.rPr.rFonts.set(qn('w:eastAsia'), '等线')

        # 添加简要描述（desc）
        if reg.desc:
            para2 = self._doc.add_paragraph("{}".format(reg.desc))
            para2.style=self._doc.styles['NormalText']
            format_para(para2)

        # 添加详细描述（doc）
        if hasattr(reg, 'doc') and reg.doc:
            para3 = self._doc.add_paragraph("{}".format(reg.doc))
            para3.style=self._doc.styles['NormalText']
            format_para(para3)

    def gen_regTable(self, reg):
        row_num = len(reg.bits) + 1
        col_num = len(BIT_TABLE_HEADER)
        table = self._doc.add_table(row_num, col_num)
        table.style = 'Table Grid'
        # table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # 1. 基本表格设置
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.LEFT  # 改为左对齐
        table.autofit = False


        
        # 2. 设置表格缩进与段落对齐
        tbl_pr = table._tbl.tblPr
        tbl_ind = tbl_pr.find(qn('w:tblInd'))
        if tbl_ind is None:
            tbl_ind = OxmlElement('w:tblInd')
            tbl_pr.append(tbl_ind)

        indent_value = 100  # 单位 dxa，必须是整数
        tbl_ind.set(qn('w:w'), str(int(indent_value)))
        tbl_ind.set(qn('w:type'), 'dxa')
        # tbl_ind.set(qn('w:w'), str(total_width_dxa))

        # 设置总宽度 15 cm
        total_width_cm = 17
        total_width_dxa = int(total_width_cm * 567)

        tblW = tbl_pr.find(qn('w:tblW'))
        if tblW is None:
            tblW = OxmlElement('w:tblW')
            tbl_pr.append(tblW)
        tblW.set(qn('w:type'), 'dxa')
        tblW.set(qn('w:w'), str(total_width_dxa))

        # 设置列宽（比例分配）
        width_ratios = [1, 0.8, 3.0, 0.8, 0.8, 0.8]
        sum_ratios = sum(width_ratios)
        col_widths_dxa = [int(total_width_dxa * r / sum_ratios) for r in width_ratios]

        # 设置每个单元格的宽度
        for row in table.rows:
            for i, cell in enumerate(row.cells):
                col_width = col_widths_dxa[i]
                cell.width = col_width

                tc_pr = cell._tc.get_or_add_tcPr()
                tc_w = tc_pr.find(qn('w:tcW'))
                if tc_w is None:
                    tc_w = OxmlElement('w:tcW')
                    tc_pr.append(tc_w)
                tc_w.set(qn('w:type'), 'dxa')
                tc_w.set(qn('w:w'), str(col_width))




        # 设置表头
        header_row = table.rows[0]
        for c in range(col_num):
            cell = header_row.cells[c]
            p = cell.paragraphs[0]
            run = p.add_run(BIT_TABLE_HEADER[c])
            run.bold = True
            run.font.name = '等线'
            run.font.size = Pt(9)
            r = run._element
            r.rPr.rFonts.set(qn('w:eastAsia'), '等线')

        # 按位位置降序排列
        sorted_bits = sorted(reg.bits, key=lambda x: x.position, reverse=True)

        for r, bit in enumerate(sorted_bits, start=1):
            row = table.rows[r]

            # Bit Name
            p = row.cells[0].paragraphs[0]
            run = p.add_run(bit.name)
            run.font.name = '等线'
            run.font.size = Pt(9)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

            # Position
            pos_str = f"[{bit.position}]" if bit.width == 1 else f"[{bit.position + bit.width - 1}:{bit.position}]"
            p = row.cells[1].paragraphs[0]
            run = p.add_run(pos_str)
            run.font.name = '等线'
            run.font.size = Pt(9)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

            # Description
            desc = ''
            if bit.doc:
                desc += bit.doc + '\n'
            for bv in bit.bitvalues:
                desc += f"{bv.value}: {bv.desc}\n"
            p = row.cells[2].paragraphs[0]
            run = p.add_run(desc.strip())
            run.font.name = '等线'
            run.font.size = Pt(9)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

            # Default
            p = row.cells[3].paragraphs[0]
            run = p.add_run(hex(bit.default_value))
            run.font.name = '等线'
            run.font.size = Pt(9)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

            # Access
            p = row.cells[4].paragraphs[0]
            run = p.add_run(str(bit.access))
            run.font.name = '等线'
            run.font.size = Pt(9)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

            # Key
            p = row.cells[5].paragraphs[0]
            run = p.add_run(str(bit.key))
            run.font.name = '等线'
            run.font.size = Pt(9)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')

    def run(self):
        for m in self._modules:
            ms = '\n'
            ms += "---------------------------- MODULE :  {} --------------------------\n".format(m.name)
            ms += '\n'
            ms += '\n'
            para = self._doc.add_paragraph(ms)
            para.style = self._doc.styles['ModuleTitle']

            for reg in m.regs:
                self.gen_regTable_desc(reg, m)
                self.gen_regTable(reg)
            self._doc.add_page_break()
        self._doc.save(self._dsName)


if __name__ == "__main__":
    import argparse
    from regdb import create_db_app, MODULE
    
    parser = argparse.ArgumentParser(description="Register table document generator")
    parser.add_argument('database', action='store', help="Specify register database file")
    parser.add_argument('-f', action='store', help="Specify name of document file", default='Default_Regs.docx')
    cmd = parser.parse_args()
    
    app = create_db_app(cmd.database)
    app.app_context().push()
    modules = MODULE.query.order_by(MODULE.address).all()
    
    doc = GEN_DS(modules, cmd.f)
    doc.run()
