#       python .\gen_scan_handler.py .\LH1282_TOP.db -f Scan_handler
import argparse ,os , sys, shutil
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


class GEN_SCAN_HANDLER():
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

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'MODULE NAME '+module.name.upper(), '*'*50)
        for reg in module.regs:
            if reg.access == 'RW':
                reg_sheet_list += '{0}{1}{2}\n'.format('-'*50, reg.name.upper(), '-'*50)
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR')
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('-'*25, '-'*15, '-'*30, '-'*15, '-'*10, '-'*10, )
                for bit in reg.bits:
                    reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format(bit.name.upper(), '['+str(bit.position+bit.width-1)+':'+str(bit.position)+']', \
                                                                        bit.access, str(bit.key), str(bit.set), str(bit.clr))
                reg_sheet_list += '{0}\n\n'.format('-'*110)
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'end '+module.name.upper(), '*'*50+'/')
        return reg_sheet_list

    def gen_inout_list(self, module):
        inout_list_str = ""
        for reg in module.regs:
            inout_list_str += "\t//The signal define of the {0} ,type \"{1}\"\n".format(reg.name, reg.access)
            for bit in reg.bits:
                if bit.access == 'RW':
                    inout_list_str += '\t{:<10}{:<10}{:<10}{}{}'.format("input", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                    inout_list_str += '\t{:<10}{:<10}{:<10}{}{}'.format("output", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]", reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
        return inout_list_str

    def gen_enable_assign(self,module):
        enable_assign_cond = ""
        for reg in module.regs:
            enable_assign_cond += "\t//Scan handler assign {0} \n".format(reg.name.upper())
            for bit in reg.bits:
                if bit.access == 'RW':
                    scan_value = bit.scan
                    if scan_value is not None and str(scan_value).strip() != '':
                        try:
                            if isinstance(scan_value, str):
                                try:
                                    scan_integer = int(scan_value.strip(), 0)
                                except ValueError:
                                    scan_integer = int(scan_value.strip(), 10)
                            else:
                                scan_integer = int(scan_value)
                        except (TypeError, ValueError):
                            raise ValueError(
                                "BIT {}_{}的SCAN值不是有效整数：{}".format(
                                    reg.name, bit.name, scan_value
                                )
                            )
                        if scan_integer < 0 or scan_integer >= (1 << bit.width):
                            raise ValueError(
                                "BIT {}_{}的SCAN值{}超出{}位范围".format(
                                    reg.name, bit.name, scan_integer, bit.width
                                )
                            )
                        enable_assign_cond += "\tassign   {0:<30} = scan_mode? {1:<5} : {2:<30} \n".format(reg.name.upper()+"_"+bit.name.upper()+("" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]"), \
                                                                                                           str(bit.width)+'\'h'+format(scan_integer, 'X'), \
                                                                                                           'O'+'_'+reg.name.upper()+"_"+bit.name.upper()+(";" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "];"))
                    else:
                        enable_assign_cond += "\tassign   {0:<30} = {1:<30} \n".format(reg.name.upper()+"_"+bit.name.upper()+("" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]"), \
                                                                                      'O'+'_'+reg.name.upper()+"_"+bit.name.upper()+(";" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "];"))
        enable_assign_cond += '\n'
        return enable_assign_cond

    def config_parser(self):
        #config_path = r'C:\Users\chang\Desktop\work_area\WORK_AREA\reg_software\Register\Register_V1.0.0\Register\scripts\design_param.cfg.txt'
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(BASE_DIR, "design_param.cfg.txt")
        # print(config_path)
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))

    def run(self):
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'Scan_Handler')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)

        self.content = HEADER_COPYRIGHT
        for module in self.modules:
            self.content += self.gen_reg_sheet_comment(module)
        self.content += '\n`ifndef ' +'SCAN_HANDLER_V\n'
        self.content += '`define ' + 'SCAN_HANDLER_V\n\n'
        self.content += '//The O_ signal is the output of the MMR ,the input of Scan_Handler\n'
        self.content += 'module scan_handler (\n'
        self.content += '\t{:<10}{:<10}{:<10}{}{}'.format("input", "", "scan_mode", ",", "\n")
        for module in self.modules:
            self.content += self.gen_inout_list(module)
        self.content = self.content[:-2] + "\n" + ");" + "\n\n"
        for module in self.modules:
            self.content += self.gen_enable_assign(module)
        self.content += 'endmodule \n\n`endif'
        filename = os.path.join(folder_path_name,'{}.v'.format('scan'+ '_' + 'handler'))
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
    h = GEN_SCAN_HANDLER(modules, cmd.f, 'VERILOG')
    h.run()
