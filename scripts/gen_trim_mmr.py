#       python .\gen_trim_mmr.py .\LH1282_TOP.db -f Trim_mmr
import argparse ,os , re, sys, shutil
import configparser
from datetime import date
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db

HEADER_DATE = date.today()
HEADER_YEAR = date.today().year
HEADER_COMMENT_SEPERATOR = '***********************************************************************\n'
HEADER_COMPANY = r"苏州领慧立芯科技有限公司"
HEADER_COPYRIGHT = "//Copyright @  {0}  {1}\n\
\n//This is a genetated file, do not modify it by hand\n\n\
".format(HEADER_YEAR, HEADER_COMPANY)


class GEN_TRIM_MMR():
    def __init__(self, modules, header_file="Default_Verilog.v", header_type='VERILOG'):
        self.modules = modules
        self.headerFile = header_file
        self.folder_name = os.path.basename(self.headerFile)
        self.pathname = os.path.dirname(self.headerFile)

        self.headerFile = header_file
        self.headerType = header_type
        self.content = '\n'
        self.repeatedModules = dict()
        self.data_width = 16
        self.addr_width = 16
        self.special_handle_1282X=0

    @staticmethod
    def _is_trim_module(module):
        tokens = [
            token
            for token in re.split(r'[^a-z0-9]+', str(module.name or '').lower())
            if token
        ]
        return 'trim' in tokens

    def _trim_modules(self):
        return [module for module in self.modules if self._is_trim_module(module)]

    @staticmethod
    def _validate_trim_register_widths(trim_modules):
        invalid = [
            '{}.{}={}位'.format(module.name, reg.name, reg.width)
            for module in trim_modules
            for reg in module.regs
            if int(reg.width) != 8
        ]
        if invalid:
            raise ValueError(
                'Trim寄存器仅支持8位，发现：{}'.format(', '.join(invalid))
            )

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'MODULE NAME '+module.name.upper(), '*'*50)
        for reg in module.regs:
            #print(reg.ate_trim, type(reg.ate_trim))
            reg_sheet_list += '{0}{1}{2}\n'.format('-'*50, reg.name.upper(), '-'*50)
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR')
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('-'*25, '-'*15, '-'*30, '-'*15, '-'*10, '-'*10, )
            for bit in reg.bits:
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format(bit.name.upper(), '['+str(bit.position+bit.width-1)+':'+str(bit.position)+']', \
                                                                    bit.access, str(bit.key), str(bit.set), str(bit.clr))
            reg_sheet_list += '{0}\n\n'.format('-'*110)
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'end '+module.name.upper(), '*'*50+'/')
        return reg_sheet_list

    def gen_inout_bus_list(self):
        inout_bus_list = '//Bus interface comment\n'
        inout_bus_list_str = "( \n"
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "UserKey", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "LCKey", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "clk", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "rstn", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "I_wr_stb", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "cs", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[ADDR_WIDTH-1 : 0]", "I_wr_addr", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[DATA_WIDTH-1 : 0]", "I_wr_data", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[ADDR_WIDTH-1 : 0]", "I_rd_addr", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "[DATA_WIDTH-1 : 0]", "O_rd_data", ",","\n\n")
        inout_bus_list_str += '//Fuse input enable signal\n'
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "fuse_w_en", ",", "\n")
        if self.special_handle_1282X == 1:
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "load_ofc", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[23:0]", "ofc_autocal", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "load_fsc", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[23:0]", "fsc_autocal", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output", "", "config_wstb", ",", "\n")
        inout_bus_list_str += '\n'
        return inout_bus_list_str

    def gen_module_name(self, module):
        module_name_str = ""
        module_name_str += '\n`ifndef ' +'TRIM_MMR_V\n'
        module_name_str += '`define ' + 'TRIM_MMR_V\n\n'
        module_name_str += "module " + 'trim' + "_mmr"
        return module_name_str

    def gen_addr_offset(self,module):
        addr_offet_parm = ''
        addr_offet_parm += '\t//Reg address parameter define \n'
        for module in self.modules:
            if self._is_trim_module(module):
                for reg in module.regs:
                    reg_address = str(hex(module.address + reg.address))
                    addr_offet_parm += '\t{}{:<20}{:<3}{}{}{}'.format("parameter ", "ADDR_"+reg.name.upper() , "=", '\'h'+reg_address[2:],",", "\n")
                addr_offet_parm += '\n'
        return addr_offet_parm

    def gen_macro_parm(self,module):
        macro_parm_str = ""
        macro_parm_str = "    #( \n"
        macro_parm_str += "    parameter ADDR_WIDTH     =    " + str(self.addr_width) + "," + "\n"
        macro_parm_str += "    parameter DATA_WIDTH     =    " + str(self.data_width) + "," + "\n"
        macro_parm_str += self.gen_addr_offset(module)
        macro_parm_str = macro_parm_str[:-3]
        macro_parm_str += " ) \n\n"
        return macro_parm_str

    def gen_inout_list(self, module):
        inout_list_str = ""
        for reg in module.regs:
            inout_list_str += "//The signal define of the {0} ,type \"{1}\"\n".format(reg.name, reg.access)
            for bit in reg.bits:
                if bit.access == 'R(ReadOnly)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","I_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access in ('RW', 'W(WriteOnly)', 'WRS(WR/hardware update)'):
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","F_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
        return inout_list_str

    def gen_enable_assign(self,module):
        enable_assign_cond = ""
        enable_assign_cond += "//Write enable wire define \n"
        for reg in module.regs:
            if reg.access != 'R(ReadOnly)':
                enable_assign_cond += "wire    WEN_{0}; \n".format(reg.name.upper())
        enable_assign_cond += "\n//Write enable assign for bus \n"
        for reg in module.regs:
            if reg.access != 'R(ReadOnly)':
                enable_assign_cond += "assign WEN_{0:<20}  = I_wr_stb & cs & (I_wr_addr ==  ADDR_{0}); \n".format(reg.name.upper())

        enable_assign_cond += '\n'
        return enable_assign_cond

    def gen_bus_hw_write(self,module):
        always_bus_hw_wr_str = ''
        for reg in module.regs:
            reg_default_val = format(reg.default_value, '08b')
            reg_val_reverse = reg_default_val[::-1]
            for bit in reg.bits:
                if bit.access != 'R(ReadOnly)':
                    always_bus_hw_wr_str += '//define always write for reg {1} / type-{0}\n'.format(bit.access, reg.name.upper() + "_" + bit.name.upper())
                if (bit.access == 'RW') or (bit.access == 'W(WriteOnly)') or (bit.access == 'WRS(WR/hardware update)'):
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position + i]
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        fuse_in_signal = '{0}{1}'.format("F_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? {2} : {0}'.format(out_reg_signal, bit.key, 'I_wr_data'+'['+str(bit.position+i)+']')
                        else:
                            bus_wr = '{0} <= {1}'.format(out_reg_signal, 'I_wr_data' + '[' + str(bit.position + i) + ']')
                        always_bus_hw_wr_str += 'always @ (posedge clk or negedge rstn) begin\n'
                        always_bus_hw_wr_str += '\tif(!rstn) begin\n'
                        always_bus_hw_wr_str += '\t\t{} <= 1\'b{};\n'.format(out_reg_signal,bit_default_val)
                        always_bus_hw_wr_str += '\tend else if(fuse_w_en) begin \n'
                        always_bus_hw_wr_str += '\t\t{0} <= {1};\n'.format(out_reg_signal, fuse_in_signal)
                        always_bus_hw_wr_str += '\tend else if({0}) begin\n'.format(bus_wr_condition)
                        always_bus_hw_wr_str += '\t\t{};\n\tend\nend\n\n'.format(bus_wr)
            always_bus_hw_wr_str += '\n'
        return always_bus_hw_wr_str

    def gen_1282_ADC_write(self,module):
        always_bus_hw_wr_str = ''
        for reg in module.regs:
            reg_default_val = format(reg.default_value, '08b')
            reg_val_reverse = reg_default_val[::-1]
            ADC_w_ctl_signal = 'load_'+reg.name[0:3].lower()
            for bit in reg.bits:
                if bit.access != 'R(ReadOnly)':
                    always_bus_hw_wr_str += '//define always write for reg {1} / type-{0}\n'.format(bit.access, reg.name.upper() + "_" + bit.name.upper())
                if (bit.access == 'RW') or (bit.access == 'W(WriteOnly)') or (bit.access == 'WRS(WR/hardware update)'):
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position + i]
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        adc_in_signal = '{0}{1}'.format(reg.name[0:3].lower()+'_autocal', "["+str(i+(reg.address if reg.address<3 else reg.address-3)*8)+"]")
                        fuse_in_signal = '{0}{1}'.format("F_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? {2} : {0}'.format(out_reg_signal, bit.key, 'I_wr_data'+'['+str(bit.position+i)+']')
                        else:
                            bus_wr = '{0} <= {1}'.format(out_reg_signal, 'I_wr_data' + '[' + str(bit.position + i) + ']')
                        always_bus_hw_wr_str += 'always @ (posedge clk or negedge rstn) begin\n'
                        always_bus_hw_wr_str += '\tif(!rstn) begin\n'
                        always_bus_hw_wr_str += '\t\t{} <= 1\'b{};\n'.format(out_reg_signal,bit_default_val)
                        always_bus_hw_wr_str += '\tend else if({0}) begin \n'.format(ADC_w_ctl_signal)
                        always_bus_hw_wr_str += '\t\t{0} <= {1};\n'.format(out_reg_signal, adc_in_signal)
                        always_bus_hw_wr_str += '\tend else if(fuse_w_en) begin \n'
                        always_bus_hw_wr_str += '\t\t{0} <= {1};\n'.format(out_reg_signal, fuse_in_signal)
                        always_bus_hw_wr_str += '\tend else if({0}) begin\n'.format(bus_wr_condition)
                        always_bus_hw_wr_str += '\t\t{};\n\tend\nend\n\n'.format(bus_wr)
            always_bus_hw_wr_str += '\n'
        return always_bus_hw_wr_str

    def gen_bus_read(self):
        bus_read_list = ''

        bus_read_list += 'always @(*) begin \n\tO_rd_data = \'b0;\n\tcase(I_rd_addr)\n'
        for module in self.modules:
            if self._is_trim_module(module):
                bus_read_list += '\n\t\t//For the bus read for module {0}\n'.format(module.name)
                for reg in module.regs:
                    bus_read_list += '\t\t{} : begin \n'.format("ADDR_"+reg.name.upper())
                    for bit in reg.bits:
                        if (bit.access != 'R(ReadOnly)') & (bit.access != 'W(WriteOnly)'):
                            bus_read_list += '\t\t\t{0:<20} = {1};\n'.format('O_rd_data' + '['+ (str(bit.position) if bit.width == 1 else (str(bit.position+bit.width-1)+':'+str(bit.position))) + ']', \
                                                                         'O_'+reg.name.upper()+'_'+bit.name.upper()+('' if bit.width == 1 else ('[' + str(bit.width-1) + ':0]')))
                        if bit.access == 'R(ReadOnly)':
                            bus_read_list += '\t\t\t{0:<20} = {1};\n'.format('O_rd_data' + '['+ (str(bit.position) if bit.width == 1 else (str(bit.position+bit.width-1)+':'+str(bit.position))) + ']', \
                                                                         'I_'+reg.name.upper()+'_'+bit.name.upper()+('' if bit.width == 1 else ('[' + str(bit.width-1) + ':0]')))
                        if bit.access == 'W(WriteOnly)':
                            bus_read_list += '\t\t\t{0:<20} = {1};\n'.format('O_rd_data' + '['+ (str(bit.position) if bit.width == 1 else (str(bit.position+bit.width-1)+':'+str(bit.position))) + ']', \
                                                                         '\'b'+str(bit.default_value))
                    bus_read_list += '\t\tend \n'
        bus_read_list += '\t endcase \n'
        bus_read_list += 'end\n\n'
        return bus_read_list

    def config_parser(self):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(BASE_DIR, "design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))

    def run(self):
        trim_modules = self._trim_modules()
        if not trim_modules:
            raise ValueError(
                "未找到名称中包含独立trim字段的Trim Module，不能生成trim_mmr.v"
            )
        self._validate_trim_register_widths(trim_modules)
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'Trim_MMR')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)
        self.content = HEADER_COPYRIGHT
        for module in self.modules:
            if self._is_trim_module(module):
                self.content += self.gen_reg_sheet_comment(module)
        self.content += self.gen_module_name(module) + "\n"
        self.content += self.gen_macro_parm(module)
        self.content += self.gen_inout_bus_list()
        for module in self.modules:
            if self._is_trim_module(module):
                self.content += self.gen_inout_list(module)
        self.content = self.content[:-2] + "\n" + ");" + "\n\n"
        for module in self.modules:
            if self._is_trim_module(module):
                self.content += self.gen_enable_assign(module)
        if self.special_handle_1282X == 1 :
            self.content += 'wire config_wstb = WEN_OFC0 | WEN_OFC1 | WEN_OFC2 | WEN_FSC0 | WEN_FSC1 | WEN_FSC2;\n\n'
        for module in self.modules:
            if self._is_trim_module(module):
                if(self.special_handle_1282X == 0):
                    self.content += self.gen_bus_hw_write(module)
                else:
                    if module.name == 'ADC_1282_trim':
                        self.content += self.gen_1282_ADC_write(module)
                    else:
                        self.content += self.gen_bus_hw_write(module)
        self.content += self.gen_bus_read()
        self.content += 'endmodule \n\n`endif'
        filename = os.path.join(folder_path_name,'{}.v'.format('trim'+ '_' + 'mmr'))
        filename = filename.replace('\\', '/')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Verilog file generator")
    parser.add_argument('database', action='store', help="Specify register database file")
    parser.add_argument('-f', action='store', help="Specify name of header file", default='Default_Header.h')
    parser.add_argument('-afe', action='store_true',
                        help="Generate header file for AFE or MCU, default is MCU if nothing specified")
    cmd = parser.parse_args()

    app = create_db_app(cmd.database)
    app.app_context().push()
    modules = MODULE.query.order_by(MODULE.address).all()
    h = GEN_TRIM_MMR(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
