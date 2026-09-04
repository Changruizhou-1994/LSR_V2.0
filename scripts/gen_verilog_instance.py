#       'python gen_verilog_instance.py .\LH1282_TOP.db -f Verilog_instance'

import argparse, os, sys, shutil
import configparser
from datetime import date
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db

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


class GEN_VERILOG_INSTANCE():
    def __init__(self, modules, header_file="Verilog_instance", header_type='VERILOG'):
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

    def gen_header_announcement(self, module):
        header_announce_list = ''
        header_announce_list += '//Define the instance for module {}_mmr\n\n'.format(module.name.lower())
        header_announce_list += '{0}_mmr U_{0}_mmr\n'.format(module.name.lower())
        return header_announce_list

    def gen_module_name(self, module):
        module_name_str = ""
        module_name_str = "module " + module.name.lower() + "_mmr"
        return module_name_str

    def gen_inout_bus_list(self, module):
        inout_bus_list = ''
        inout_bus_list_str = "( \n"
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("UserKey", '(UserKey),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("LCKey", '(LCKey),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("clk", '(clk),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("rstn", '(rstn),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("I_wr_stb", '(wr_stb),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("cs", '(cs),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("I_wr_addr", "(wr_addr),", module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("I_wr_data", "(wr_data),", module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("I_rd_addr", "(rd_addr),", module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//{2}--> output\n'.format("O_rd_data", "(rd_data),", module.name.lower() + "_mmr")
        inout_bus_list_str += '\n'
        return inout_bus_list_str

    def gen_inout_bus_list_APB(self, module):
        inout_bus_list_str = ''
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("UserKey", '(UserKey),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("LCKey", '(LCKey),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("clk", '(clk),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("rstn", '(rstn),', module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_addr", '(p_addr),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_sel", '(p_sel),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_enable", '(p_enable),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_write", '(p_write),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_wdata", '(p_wdata),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_strb", '(p_strb),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_ready", '(p_ready),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_rdata", '(p_rdata),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("p_slaverr", '(p_slaverr),',module.name.lower() + "_mmr")
        inout_bus_list_str += '\n\n'
        return inout_bus_list_str

    def gen_inout_list(self, module):
        inout_list_str = ""
        # inout_list_str += self.gen_inout_bus_list(module)
        inout_list_str += self.gen_inout_bus_list_APB(module)
        for reg in module.regs:
            inout_list_str += "\t//The reg define of the {0} ,type \"{1}\"\n".format(reg.name, reg.access)
            for bit in reg.bits:
                bit_name = reg.name.lower()+"_"+bit.name.lower()
                module_name = module.name.lower()+"_mmr"
                if bit.access != 'R(ReadOnly)':
                    #due to occupy 15 position, so delete 2 space is not use
                    inout_list_str += '\t.{0:<30}{1:15}\n'.format("O_"+bit_name, '('+bit_name+'),')
                else:
                    inout_list_str += '\t.{0:<30}{1:15}\n'.format("I_"+bit_name, '('+bit_name+'),')
                if bit.set != 'None':
                    if (bit.set == 1) & (bit.access != 'R(ReadOnly)'):
                        inout_list_str += '\t.{0:<30}{1:15}\n'.format("I_"+bit_name+"_set", '('+bit_name+'_set'+'),')
                if bit.set != 'None':
                    if (bit.clr == 1) & (bit.access != 'R(ReadOnly)'):
                        inout_list_str += '\t.{0:<30}{1:15}\n'.format("I_"+bit_name+"_clr_n", '('+bit_name+'_clr_n'+'),')
            inout_list_str += "\n"
        inout_list_str = (inout_list_str[:-2]).rstrip()
        inout_list_str = inout_list_str[:-1] + "\n" + ");" + "\n\n"
        return inout_list_str

    def gen_trim_instance(self, module):
        trim_instance_list = ''
        for module in self.modules:
            if (module.name[-4:]).lower() == 'trim':
                trim_instance_list += self.gen_reg_sheet_comment(module)
        trim_instance_list += 'trim_mmr u_trim_mmr\n'
        trim_instance_list += self.gen_inout_bus_list(module)
        trim_instance_list += '\t.{0:<15}{1:<15}\t\t//input -->{2}\n'.format("fuse_w_en", "(fuse_w_en),", "Trim_en_mmr")
        for module in self.modules:
            if (module.name[-4:]).lower() == 'trim':
                for reg in module.regs:
                    trim_instance_list += "\t//The reg define of the {0} ,type \"{1}\"\n".format(reg.name, reg.access)
                    for bit in reg.bits:
                        bit_name = reg.name.lower() + "_" + bit.name.lower()
                        trim_instance_list += '\t.{0:<30}{1:15}\n'.format("O_"+bit_name, '('+bit_name+'),')
                        trim_instance_list += '\t.{0:<30}{1:15}\n'.format("F_" + bit_name, '(F_' + bit_name + '),')
        trim_instance_list = (trim_instance_list[:-1]).rstrip()
        trim_instance_list = trim_instance_list[:-1] + "\n" + ");" + "\n\n"
        return trim_instance_list

    def config_parser(self):
        #config_path = r'C:\Users\chang\Desktop\work_area\WORK_AREA\reg_software\Register\Register_V1.0.0\Register\scripts\design_param.cfg.txt'
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(BASE_DIR, "design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))

    def run(self):
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'MMR_instance')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)
        for module in self.modules:
            # if (module.name[-4:]).lower() != 'trim':
            self.content =  self.gen_reg_sheet_comment(module)
            self.content += self.gen_header_announcement(module)
            self.content += self.gen_inout_list(module)
            filename = os.path.join(folder_path_name,'{}.v'.format(module.name.lower() + '_' + 'instance'))
            filename = filename.replace('\\', '/')
            #print(filename)
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
    h = GEN_VERILOG_INSTANCE(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
