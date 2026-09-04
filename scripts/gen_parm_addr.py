#       python .\gen_parm_addr.py .\LH1282_TOP.db -f Parm_Addr
import argparse ,os , sys, shutil
import configparser
from datetime import date
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db
import design_settings

HEADER_DATE = date.today()
HEADER_YEAR = date.today().year
HEADER_COMMENT_SEPERATOR = '***********************************************************************\n'
HEADER_COMPANY = r"苏州领慧立芯科技有限公司"
HEADER_COPYRIGHT = "Copyright @  {0}  {1}\n\
\n\
Permission is hereby granted, free of charge, to any person obtaining a copy of this software\n\
and associated documentation files (the “Software”), to deal in the Software without\n\
restriction, including without limitation the rights to use, copy, modify, merge, publish,\n\
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the\n\
Software is furnished to do so, subject to the following conditions:\n\
\n\
The above copyright notice and this permission notice shall be included in all copies or\n\
substantial portions of the Software.\n\
\n\
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING\n\
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND\n\
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,\n\
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING\n\
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\
".format(HEADER_YEAR, HEADER_COMPANY)


class GEN_PARM_ADDR():
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
        self.base_addr_en = 1

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'MODULE NAME '+module.name.lower(), '*'*50)
        for reg in module.regs:
            reg_sheet_list += '{0}{1}{2}\n'.format('-'*50, reg.name.lower(), '-'*50)
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR')
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('-'*25, '-'*15, '-'*30, '-'*15, '-'*10, '-'*10, )
            for bit in reg.bits:
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format(bit.name.lower(), '['+str(bit.position+bit.width-1)+':'+str(bit.position)+']', \
                                                                    bit.access, str(bit.key), str(bit.set), str(bit.clr))
            reg_sheet_list += '{0}\n\n'.format('-'*110)
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'end '+module.name.lower(), '*'*50+'/')
        return reg_sheet_list

    def gen_addr_parameters(self, module, include_base_address=False):
        addr_offet_parm = ''
        addr_offet_parm += '//Reg address parameter define \n'
        for reg in module.regs:
            if include_base_address:
                reg_address = str(hex(module.address + reg.address))
            else:
                reg_address = str(hex(reg.address))
            addr_offet_parm += '{:<15}{:<20}{:<3}{:<20}{}'.format("parameter", "addr_"+reg.name.lower() , "=", '\'h'+reg_address[2:]+";", "\n")
        addr_offet_parm += '\n'
        return addr_offet_parm

    def config_parser(self):
        config_path = design_settings.runtime_path("design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))
        self.base_addr_en = int(cofig.get("design_param", "param_base_addr_en"))

    def generate_content(self, include_base_address=False):
        content = ''
        if include_base_address:
            content += '// Address mode: module base address + register offset\n\n'
        else:
            content += '// Address mode: register offset only\n\n'
        for module in self.modules:
            content += self.gen_reg_sheet_comment(module)
        for module in self.modules:
            content += self.gen_addr_parameters(module, include_base_address)
        return content

    def run(self):
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'Parm_Addr')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)
        outputs = (
            ('parm_addr_offset.v', False),
            ('parm_addr_absolute.v', True),
        )
        for output_name, include_base_address in outputs:
            filename = os.path.join(folder_path_name, output_name)
            filename = filename.replace('\\', '/')
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.generate_content(include_base_address))

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
    h = GEN_PARM_ADDR(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
