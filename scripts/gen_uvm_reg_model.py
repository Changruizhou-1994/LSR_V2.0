#       python .\gen_uvm_reg_model.py .\LHE790X.db -f UVM_Reg_Model
import argparse ,os , re, sys, shutil
import configparser
from datetime import date
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db
import threading
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


class GEN_UVM_REG_MODEL():
    def __init__(self, modules, header_file="Default_Verilog.v", header_type='VERILOG', db_name="790X"):
        self.modules = modules
        self.headerFile = header_file
        self.headerType = header_type
        self.folder_name = os.path.basename(self.headerFile)
        self.pathname = os.path.dirname(self.headerFile)

        self.content = '\n'
        self.repeatedModules = dict()
        self.access_dict = {'RW': 'RW', 'W(WriteOnly)': 'WO', 'RC(readclear)': 'RC', 'W1C(Write1/auto-clear 0)': 'W1C', \
                            'W0S(Write0/auto-set1)': 'W0S', 'W1(WriteOnce)':'W1', 'WRS(WR/hardware update)':'WRS', 'R(ReadOnly)':'RO'}
        self.data_width = 16
        self.addr_width = 16
        self.top_project = '790X'

        # self.top_project = cmd.database[2:-3]
        database_basename = os.path.basename(str(db_name or 'registers'))
        database_stem = os.path.splitext(database_basename)[0]
        self.top_project = re.sub(r'[^A-Za-z0-9_]', '_', database_stem)
        self.top_project = re.sub(r'_+', '_', self.top_project).strip('_')
        if not self.top_project:
            self.top_project = 'registers'
        elif not re.match(r'[A-Za-z_]', self.top_project):
            self.top_project = 'db_' + self.top_project
        # self.top_project = self.database_name
        # database_name


        # database_name = self.origin_fname
        # database_name = database_name[database_name.rfind('/'):]
        # database_name = database_name[1:]

        # global database_name
        # print('this is database_name')
        # print(database_name)

        # self.top_project = database_name
        # print(database_name)

        # print(dir(self))
        # print(self.keys())
        # print(self.values())


        self.ENDIAN = 'UVM_BIG_ENDIAN'
        self.module_name = ''
        self.reg_name = ''
        self.bit_name = ''

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1:*<30}{2}\n\n'.format('*'*50, 'MODULE NAME '+module.name.upper(), '*'*30)
        for reg in module.regs:
            reg_sheet_list += '{0}{1:-<30}{2}\n'.format('-'*50, reg.name.upper(), '-'*30)
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR')
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('-'*25, '-'*15, '-'*30, '-'*15, '-'*10, '-'*10, )
            for bit in reg.bits:
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format(bit.name.upper(), '['+str(bit.position+bit.width-1)+':'+str(bit.position)+']', \
                                                                    bit.access, str(bit.key), str(bit.set), str(bit.clr))
            reg_sheet_list += '{0}\n\n'.format('-'*110)
        reg_sheet_list += '{0}{1:*<30}{2}\n\n'.format('*'*50, 'end '+module.name.upper(), '*'*30+'/')
        return reg_sheet_list

    def gen_reg_class_header(self, module):
        reg_class_header = ''
        reg_class_header += 'package regmem_{}_pkg;\n\t'.format(self.top_project)
        reg_class_header += 'import uvm_pkg::*;\n\t'
        reg_class_header += '`include "uvm_macros.svh"\n'
        reg_class_header += '\n'
        return  reg_class_header

    def gen_reg_class_field_define(self, reg):
        reg_define_list = '\t/*{0}\n\t\tClass\t: {1}\n\t{2}*/\n'.format('-'*70, self.reg_name, '-'*70)
        # Define the class tittle, and uvm_object_utils
        reg_define_list += '\tclass {0} extends uvm_reg;\n'.format(self.reg_name)
        reg_define_list += '\t\t`uvm_object_utils({0})\n\n'.format(self.reg_name)
        # Define the uvm_reg_field for all the bits
        for bit in reg.bits:
            self.bit_name = reg.name.upper() + '_' + bit.name.upper()
            reg_define_list += '\t\trand uvm_reg_field {0};\n'.format(self.bit_name)
        reg_define_list += "\n"
        # Define the build function for the reg_field
        reg_define_list += "\t\t//Function : build \n"
        reg_define_list += "\t\tvirtual function void build();\n"
        for bit in reg.bits:
            self.bit_name = reg.name.upper() + '_' + bit.name.upper()
            reg_define_list += "\t\t\tthis.{0} = uvm_reg_field::type_id::create(\"{0}\");\n".format(self.bit_name)
            # configure parameter
            # |   0   |   1   |   2   |   3   |   4    |   5   |   6   |   7   |   8          |
            # |this   |width  |start_p|access |volatile|default|reset  |random |access-lonely |
            reg_define_list += "\t\t\tthis.{0}.configure(this, {1}, {2}, \"{3}\", {4}, {5}, {6}, {7}, {8});\n".format(self.bit_name,\
                str(bit.width), str(bit.position), self.access_dict[bit.access], '0', '\'d'+str(bit.default_value), '1', '1', '0')
        reg_define_list += '\t\tendfunction\n\n'
        # define the new function for the reg
        reg_define_list += "\t\t//Function new\n"
        reg_define_list += "\t\tfunction new(string name = \"{0}\");\n".format(self.reg_name)
        reg_define_list += "\t\t\tsuper.new(name, {0}, build_coverage(UVM_NO_COVERAGE));\n".format(reg.width)
        reg_define_list += "\t\tendfunction\n\n"
        reg_define_list += "\tendclass\n\n\n"
        return reg_define_list

    def gen_reg_class_define(self, module):
        block_define_list = ''
        for reg in module.regs:
            self.reg_name = module.name.upper() + '_' + reg.name.upper()
            block_define_list += self.gen_reg_class_field_define(reg)
        return block_define_list

    def gen_block_define(self, module):
        block_define_list = ''
        block_define_list += '\t/*{0}\n\t\tClass\t: {1}_block\n\t{2}*/\n'.format('-'*70, self.module_name, '-'*70)
        block_define_list += '\tclass {}_block extends uvm_reg_block;\n'.format(self.module_name)
        block_define_list += '\t\t`uvm_object_utils({}_block)\n\n'.format(self.module_name)
        for reg in module.regs:
            self.reg_name = self.module_name.upper() + '_' + reg.name.upper()
            block_define_list += '\t\trand {0:<25} {1:<25};\n'.format(self.reg_name, reg.name.upper())
        block_define_list += '\n\t\t//Function : new\n'
        block_define_list += '\t\tfunction new(string name = "{}_block");\n'.format(self.module_name)
        block_define_list += '\t\t\tsuper.new(name, UVM_NO_COVERAGE);\n'
        block_define_list += '\t\tendfunction\n\n'
        # Define the build function for block
        block_define_list += '\t\t//Function : build\n'
        block_define_list += '\t\tvirtual function void build();\n\t\t\t//create\n'
        for reg in module.regs:
            self.reg_name = self.module_name.upper() + '_' + reg.name.upper()
            block_define_list += '\n\t\t\tthis.{0:<25} = {1}::type_id::create("{0}");\n'.format(reg.name.upper(), self.reg_name)
            #block_define_list += '\t\t\t//config\n'
        #for reg in module.regs:
            self.reg_name = self.module_name.upper() + '_' + reg.name.upper()
            #block_define_list += '\t\t\tthis.{0}.configure(this, null, "{0}");\n'.format(reg.name.upper())
            block_define_list += '\t\t\tthis.{0}.configure(this, null);\n'.format(reg.name.upper())
            #block_define_list += '\n\t\t\t//build\n'
        #for reg in module.regs:
            self.reg_name = self.module_name.upper() + '_' + reg.name.upper()
            block_define_list += '\t\t\tthis.{0}.build();\n'.format(reg.name.upper())
        #adding hdl_path in here
            #block_define_list += '\t\t\t`ifdef VERILOG_RTL\n'
            for bit in reg.bits:
                block_define_list += '\t\t\t    this.{0}.add_hdl_path_slice("O_{1}_{2}", {3}, {4});\n'.format(reg.name.upper(),reg.name.lower(),str(bit.name.lower()),str(bit.position),str(bit.width))
        #.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR')
        block_define_list += '\n\t\t\t//define default map and add reg/regfiles\n'
        # Configure parameter
        # |   0   |    1    |    2    |    3     |     4     |
        # | name  |base_addr|bus_width|b/s-endain|byte_search|
        block_define_list += '\t\t\tdefault_map= create_map("default_map", \'h{0:<x}, {1}, {2}, {3});\n\n'.format(module.address, '1', self.ENDIAN, '1')
        for reg in module.regs:
            self.reg_name = self.module_name.upper() + '_' + reg.name.upper()
            block_define_list += '\t\t\tdefault_map.add_reg({0:<}, \'h{1:<x}, "{2}");\n'.format(reg.name.upper(), reg.address, self.access_dict[reg.access])
        block_define_list += '\n\t\t\tlock_model();\n\n'
        block_define_list += '\t\tendfunction\n\n'
        block_define_list += '\t endclass : {0}_block\n\n\n'.format(self.module_name)
        return block_define_list

    def gen_reorg_block(self):
        reorg_block_list = ''
        reorg_block_list += '\t/{0}REORG BLOCK{0}/\n\n'.format('*' * 50)
        reorg_block_list += '\t/*{0}\n\t\tClass\t: regmem_{1}_block\n\t{2}*/\n\n'.format('-' * 70,self.top_project,'-' * 70)
        reorg_block_list += '\tclass regmem_{}_block extends uvm_reg_block;\n\n'.format(self.top_project)
        for module in self.modules:
            self.module_name = module.name.upper()
            # reorg_block_list += '\t\trand {0:<25} {1};\n'.format(self.module_name+'_block', self.module_name+'_ins')
            reorg_block_list += '\t\trand {0:<25} {1};\n'.format(self.module_name + '_block', self.module_name)
        reorg_block_list += '\n'
        reorg_block_list += '\t\tvirtual function void build();\n'
        reorg_block_list += '\t\t\tdefault_map = create_map("default_map", \'h{0:<x}, {1}, {2}, {3});\n\n'.format(0, '1', self.ENDIAN, '1')
        for module in self.modules:
            self.module_name = module.name.upper()
            reorg_block_list += '\t\t\t{0} = {1}::type_id::create("{0}");\n'.format(self.module_name, self.module_name+'_block')
            reorg_block_list += '\t\t\t{0}.configure(this, "");\n'.format(self.module_name)
            reorg_block_list += '\t\t\t{0}.build();\n'.format(self.module_name)
            reorg_block_list += '\t\t\t{0}.lock_model();\n'.format(self.module_name)
            reorg_block_list += '\t\t\tdefault_map.add_submap({0}.default_map, \'h{1:x});\n\n'.format(self.module_name, module.address)
        reorg_block_list += '\t\tendfunction\n\n'
        reorg_block_list += '\t\t`uvm_object_utils(regmem_{0}_block)\n\n'.format(self.top_project)
        reorg_block_list += '\t\tfunction new(input string name="regmem_{0}_block");\n'.format(self.top_project)
        reorg_block_list += '\t\t\tsuper.new(name, UVM_NO_COVERAGE);\n'
        reorg_block_list += '\t\tendfunction\n\n'
        reorg_block_list += '\tendclass\n\n'
        return reorg_block_list

    def config_parser(self):
        config_path = design_settings.runtime_path("design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))

    def run(self):
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'UVM_Reg_Model')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)

        self.content = ''
        for module in self.modules:
            self.content += self.gen_reg_sheet_comment(module)
        self.content += self.gen_reg_class_header(module)
        # Define the reg class include the reg_field define
        self.content += '\t/{0}REG DEFINE{0}/\n\n'.format('*' * 50)
        for module in self.modules:
            self.content += self.gen_reg_class_define(module)
        # Define the block for the module , include the reg in the module
        self.content += '\t/{0}BLOCK DEFINE{0}/\n\n'.format('*'*50)
        for module in self.modules:
            self.module_name = module.name.upper()
            self.content += self.gen_block_define(module)
        self.content += self.gen_reorg_block()
        self.content += 'endpackage\n'
        filename = os.path.join(folder_path_name,'{}.sv'.format('reg'+ '_' + 'model'))
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
    db_name = cmd.database[2:-3]
    app = create_db_app(cmd.database)
    app.app_context().push()
    modules = MODULE.query.order_by(MODULE.address).all()
    h = GEN_UVM_REG_MODEL(modules, cmd.f, 'VERILOG', db_name)
    #h.genHeader()
    h.run()
