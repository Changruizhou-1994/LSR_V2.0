#       python .\gen_shadow_interface.py .\LH1282_TOP.db -f Shadow_interface


import argparse, os, sys, shutil
from datetime import date
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db

HEADER_DATE = date.today()
HEADER_YEAR = date.today().year
HEADER_COMMENT_SEPERATOR = '***********************************************************************\n'
HEADER_COMPANY = r"苏州领慧立芯科技有限公司"
HEADER_COPYRIGHT = "//Copyright @  {0}  {1}\n\
\n//This is a genetated file, do not modify it by hand\n\n\
".format(HEADER_YEAR, HEADER_COMPANY)


class GEN_SHADOW_INTERFACE():
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
        self.trim_base_address = 5

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'MODULE NAME '+module.name.upper(), '*'*50)
        for reg in module.regs:
            if str(reg.ate_trim) == '1':
                reg_sheet_list += '{0}{1}{2}\n'.format('-'*50, reg.name.upper(), '-'*50)
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR')
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('-'*25, '-'*15, '-'*30, '-'*15, '-'*10, '-'*10)
                for bit in reg.bits:
                    reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format(bit.name.upper(), '['+str(bit.position+bit.width-1)+':'+str(bit.position)+']', \
                                                                        bit.access, str(bit.key), str(bit.set), str(bit.clr))
                reg_sheet_list += '{0}\n\n'.format('-'*110)
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'end '+module.name.upper(), '*'*50+'/')
        return reg_sheet_list

    def gen_inout_list(self, module):
        inout_list_str = ""
        inout_list_str += '//**********module {}**************************//\n'.format(module.name)
        for reg in module.regs:
            if str(reg.ate_trim) == '1':
                inout_list_str += "\t//The reg define of the {0} ,type \"{1}\"\n".format(reg.name, reg.access)
                for bit in reg.bits:
                    bit_name = 'F_'+reg.name.upper()+"_"+bit.name.upper()
                    inout_list_str += '\toutput reg {0:<10} {1:<30}\n'.format('' if bit.width == 1 else '['+str(bit.width - 1)+':0'+']', bit_name + ',')
                inout_list_str += "\n"
        return inout_list_str

    def gen_shadow_assign_list(self, module):
        shadow_assign_list = ''
        shadow_assign_list += '//always assign for module\n'.format(module.name.upper())
        shadow_assign_list += '\talways @(*) begin \n'
        for reg in module.regs:
            if str(reg.ate_trim) == '1':
                for bit in reg.bits:
                    bit_name = 'F_'+ reg.name.upper() + "_" + bit.name.upper()
                    bit_start_address = (module.address)*8 + (reg.address)*(reg.width) + bit.position
                    bit_stop_address = (module.address)*8 + (reg.address)*(reg.width) + bit.position + bit.width -1
                    #print('{0:}-------[{1}:{2}]'.format(bit_name, str(bit_stop_address), str(bit_start_address)))
                    shadow_assign_list += '\t\t{0:<30} = shadow_data[{1}];\n'.format(bit_name, str(bit_stop_address) if bit_start_address == bit_stop_address else str(bit_stop_address)+':'+str(bit_start_address))
        shadow_assign_list += '\tend \n\n'
        return shadow_assign_list

    def run(self):
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'Shadow_interface')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)
        self.content = HEADER_COPYRIGHT
        for module in self.modules:
            if (module.name[-4:]).lower() == 'trim':
                self.content += self.gen_reg_sheet_comment(module)
        self.content += '\n`ifndef ' +'SHADOW_INTERFACE_V\n'
        self.content += '`define ' + 'SHADOW_INTERFACE_V\n\n'
        self.content += 'module shadow_interface(\n'
        for module in self.modules:
            if (module.name[-4:]).lower() == 'trim':
                self.content += self.gen_inout_list(module)
        self.content += '\tinput [255:0] shadow_data \n);\n\n'
        for module in self.modules:
            if (module.name[-4:]).lower() == 'trim':
                self.content += self.gen_shadow_assign_list(module)
        self.content += 'endmodule \n\n`endif'
        filename = os.path.join(folder_path_name,'{}.v'.format('Shadow_Interface'))
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
    h = GEN_SHADOW_INTERFACE(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
