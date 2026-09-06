#       python .\gen_dv_mask_default_val.py .\LH1282_TOP.db -f mask_default_value
#       This is a test to generate the verification register mask to write and read , and to get the default value
#       .\Rubens_MMR_bak.db -f dv_mask_default_val
import argparse ,os , sys, shutil
from datetime import date
import configparser
import itsdangerous

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

class GEN_DV_MASK_DEFAULT_VAL():
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

    def gen_reg_information(self, reg):
        reg_information = ''
        reg_information += '\t//|{0:<25}|{1:<15}|{2:<30}|{3:<15}\n'.format('REG NAME', 'REG POSITION', 'REG_ACCESS', 'DEF_VAL')
        reg_information += '\t//|{0:<25}|{1:<15}|{2:<30}|{3:<15}\n'.format('-'*25, '-'*15, '-'*30, '-'*15)
        reg_information += '\t//|{0:<25}|{1:<15}|{2:<30}|{3:<15}\n'.format(reg.name.lower(), '\'h' + str(reg.address), str(reg.access), str(hex(int(reg.default_value))))
        return reg_information

    def gen_addr_offset(self,module):
        addr_offet_parm = ''
        addr_offet_parm += '//Reg address parameter define \n'
        for reg in module.regs:
            reg_address = str(hex(module.address + reg.address))
            addr_offet_parm += '{}{:<20}{:<3}{}{}{}'.format("parameter [ADDR_WIDTH-1 : 0] ", "addr_"+reg.name.lower() , "=", '\'h'+reg_address[2:],";", "\n")
        addr_offet_parm += '\n'
        return addr_offet_parm

    def gen_reg_defult(self):
        reg_default_str = ''
        for module in self.modules:
            for reg in module.regs:
                reg_name = reg.name.lower()
                default_val = str('{0:0>x}'.format(reg.default_value))
                default_val_string = 'parameter [{0:<}: 0]\t{1:<20} = {2}\'h{3};\n'.format(str(self.data_width -1), reg_name + '_def_val', str(self.data_width), default_val)
                reg_default_str += default_val_string
        # print(reg_default_str, '\n')
        reg_default_str += '\n\n'
        return reg_default_str

    def reg_is_key_feature(self, reg):
        # '0'is don't have key feature , '1' is have key feature
        have_key_feature = 0
        for bit in reg.bits:
            if (bit.key.lower() == 'userkey') | (bit.key.lower() == 'lckey'):
                have_key_feature = 1
        return have_key_feature

    def gen_reg_mask(self):
        reg_mask_str = ''
        key_feature = 0
        for module in self.modules:
            for reg in module.regs:
                key_feature = self.reg_is_key_feature(reg)
                reg_address = '\'h' + str(hex(module.address + reg.address))[2:]

                reg_name = reg.name.lower()
                non_rw_mask_init_val = '1' * self.data_width
                dummy_mask_init_val = '0' * self.data_width
                for bit in reg.bits:
                    bit_start_addr = bit.position
                    bit_stop_addr = bit.position + bit.width
                    if bit.access != 'RW':
                        for i in range(bit_start_addr, bit_stop_addr):
                            string_rw = list(non_rw_mask_init_val)
                            string_rw[self.data_width - i - 1] = '0'
                            non_rw_mask_init_val = ''.join(string_rw)
                    for i in range(bit_start_addr, bit_stop_addr):
                        string_dummy = list(dummy_mask_init_val)
                        string_dummy[self.data_width - i - 1] = '1'
                        dummy_mask_init_val = ''.join(string_dummy)
                # convert the string to hex
                non_rw_mask_init_val = str(hex(int(non_rw_mask_init_val, base=2)))[2:]
                dummy_mask_init_val = str(hex(int(dummy_mask_init_val, base=2)))[2:]
                # assign the write and the read mask
                reg_write_mask = 'reg [{0:<}: 0]\t{1:<30} = {2}\'h{3} & {2}\'h{4};\n'.format(str(self.data_width -1), reg_name + '_write_mask', str(self.data_width), non_rw_mask_init_val, dummy_mask_init_val)
                reg_read_mask = 'reg [{0:<}: 0]\t{1:<30} = {2}\'h{3};\n'.format(str(self.data_width -1), reg_name + '_read_mask', str(self.data_width), non_rw_mask_init_val)
                reg_mask_str += reg_write_mask
                reg_mask_str += reg_read_mask

                if key_feature == 1:
                    for bit in reg.bits:
                        dummy_mask_init_val = '0' * self.data_width
                        bit_name = reg.name.lower() + '_' + bit.name.lower()
                        bit_start_addr = bit.position
                        bit_stop_addr = bit.position + bit.width
                        for i in range (bit_start_addr, bit_stop_addr):
                            string_dummy = list(dummy_mask_init_val)
                            string_dummy[self.data_width - i - 1] = '1'
                            dummy_mask_init_val = ''.join(string_dummy)
                        dummy_mask_init_val = str(hex(int(dummy_mask_init_val, base=2)))[2:]
                        bit_mask = 'reg [{0:<}: 0]\t{1:<30} = {2}\'h{3};\n'.format(str(self.data_width -1), bit_name + '_bit_mask', str(self.data_width), dummy_mask_init_val)
                        reg_mask_str += bit_mask
        # print(reg_mask_str)
        return reg_mask_str

    def gen_default_val_check(self):
        reg_def_check = ''
        reg_def_check += '\t//read the default value of all reg , and compare with default value\n\n'
        for module in self.modules:
            for reg in module.regs:
                reg_def_check += self.gen_reg_information(reg)
                reg_name = reg.name.lower()
                read_reg = '\tread_reg({0}, {1});\n'.format('addr_' + reg_name, 'read_data')
                check_data = '\tcheck_reg_data({0}, {1}, {2}, {3});\n'.format('read_data', reg_name + '_def_val', reg_name+'_write_mask', reg_name+'_read_mask')
                reg_def_check += read_reg
                reg_def_check += check_data
                reg_def_check += '\n'
        return reg_def_check

    def gen_write_read_task(self, w_data, exp_data, unlock_key):
        rw_task_string = ''
        for module in self.modules:
            for reg in module.regs:
                key_feature = self.reg_is_key_feature(reg)
                reg_name = reg.name.lower()
                if key_feature == 0:
                    write_reg = '\twrite_reg({0}, {1});\n'.format('addr_' + reg_name, w_data)
                    read_reg = '\tread_reg({0}, {1});\n'.format('addr_' + reg_name, 'read_data')
                    check_data = '\tcheck_reg_data({0}, {1}, {2}, {3});\n'.format('read_data', w_data, reg_name+'_write_mask', reg_name+'_read_mask')
                    rw_task_string += write_reg
                    rw_task_string += read_reg
                    rw_task_string += check_data
                    rw_task_string += '\n'
                if key_feature == 1:
                    for bit in reg.bits:
                        bit_name = reg.name.lower() + '_' + bit.name.lower()
                        if bit.access == 'RW':
                            if bit.key.lower() == 'lckey':
                                if unlock_key == 1 :
                                    rw_task_string += '\tunlock_lckey();\n'
                                rw_task_string += '\twrite_reg({0}, {1});\n'.format('addr_' + reg_name, w_data)
                                rw_task_string += '\tread_reg({0}, {1});\n'.format('addr_' + reg_name, 'read_data')
                                rw_task_string += '\tcheck_reg_data({0}, {1}, {2}, {2});\n'.format('read_data', exp_data, bit_name + '_bit_mask')
                                if unlock_key == 1 :
                                    rw_task_string += '\tlock_lckey();\n'
                            elif bit.key.lower() == 'userkey':
                                if unlock_key == 1:
                                    rw_task_string += '\tunlock_userkey();\n'
                                rw_task_string += '\twrite_reg({0}, {1});\n'.format('addr_' + reg_name, w_data)
                                rw_task_string += '\tread_reg({0}, {1});\n'.format('addr_' + reg_name, 'read_data')
                                rw_task_string += '\tcheck_reg_data({0}, {1}, {2}, {2});\n'.format('read_data', exp_data,
                                                                                                bit_name + '_bit_mask')
                                if unlock_key == 1:
                                    rw_task_string += '\tlock_userkey();\n'
                            else:
                                rw_task_string += '\twrite_reg({0}, {1});\n'.format('addr_' + reg_name, w_data)
                                rw_task_string += '\tread_reg({0}, {1});\n'.format('addr_' + reg_name, 'read_data')
                                rw_task_string += '\tcheck_reg_data({0}, {1}, {2}, {2});\n'.format('read_data', exp_data,
                                                                                                bit_name + '_bit_mask')
                            rw_task_string += '\n'
        return rw_task_string

    def gen_reg_rw_test_case(self):
        test_case = ''
        test_case += 'task check_reg\n\n\treg [{0:<} : 0]\t read_data;\n\n'.format(str(self.data_width -1))
        test_case += self.gen_default_val_check()
        w_data_str_05 = '\'h' + '05' * int(self.data_width / 8)
        w_data_str_50 = '\'h' + '50' * int(self.data_width / 8)
        test_case += '\t//unlock all the key , write 05 to all the reg ,  then close the key\n'
        test_case += self.gen_write_read_task(w_data_str_05, w_data_str_05, 1)
        test_case += '\t//unlock all the key , write 50 to all the reg ,  then close the key\n'
        test_case += self.gen_write_read_task(w_data_str_50, w_data_str_50, 1)
        test_case += '\t//unlock all the key , write 05 to all the reg , then close the key\n'
        test_case += self.gen_write_read_task(w_data_str_05, w_data_str_05, 1)
        test_case += '\t//write 05 to all the reg , lock all the key , then must can\'t be write in\n'
        test_case += self.gen_write_read_task(w_data_str_50, w_data_str_05, 0)
        test_case += 'endtask \n\n'
        return test_case

    def gen_base_test_task(self):
        base_task = ''
        base_task += 'task check_reg_data(output reg  [{0:<}:0] read_data, input [{0:<}:0] exp_data, input [{0:<}:0] write_mask, input [{0:<}:0] read_mask);\n' \
                     '\treg [{0:<}:0]\t read_data;\n\n' \
                     '\tif((read_data & read_mask) == (exp_data & write_mask))\n' \
                     '\t\t`uvm_info(get_type_name(), $sformatf("success compare, read_data is %s, exp_data is %s", read_data & read_mask, exp_data & write_mask), UVM_LOW)\n' \
                     '\telse\n\t\t`uvm_error(get_type_name(), $sformatf("Error compare, read_data is %s, read_mask is %s, exp_data is %s, write_mask is %s", read_data ,read_mask, exp_data, write_mask))\n' \
                     'endtask\n\n'.format(str(self.data_width -1))
        base_task += 'task read_reg(input [{0:<}:0] read_addr, output reg [{1:<}:0] read_data);\n' \
                     '\nendtask\n\n'.format(str(self.addr_width - 1), str(self.data_width - 1))
        base_task += 'task write_reg(input [{0:<}:0] write_addr, input [{1:<}:0] write_data);\n' \
                     '\nendtask\n\n'.format(str(self.addr_width - 1), str(self.data_width - 1))
        base_task += 'task unlock_lckey();\n' \
                     '\twrite_reg();\nendtask\n\n' \
                     'task unlock_userkey();\n' \
                     '\twrite_reg();\nendtask\n\n' \
                     'task lock_lckey();\n' \
                     '\twrite_reg();\nendtask\n\n' \
                     'task lock_userkey();\n' \
                     '\twrite_reg();\nendtask\n\n'
        return base_task

    def config_parser(self):
        #config_path = r'C:\Users\chang\Desktop\work_area\WORK_AREA\reg_software\Register\Register_V1.0.0\Register\scripts\design_param.cfg.txt'
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # config_path = os.path.join(BASE_DIR, "design_param.cfg.txt")
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(BASE_DIR, "design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))

    def run(self):
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'reg_mask')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)

        # gen the mask , default value , and the address
        self.content = ''
        for module in self.modules:
            self.content += self.gen_reg_sheet_comment(module)
        self.content += 'parameter ADDR_WIDTH = \'d{0:<5};\n'.format(self.addr_width)
        self.content += 'parameter DATA_WIDTH = \'d{0:<5};\n'.format(self.data_width)
        for module in self.modules:
            self.content += self.gen_addr_offset(module)
        self.content += self.gen_reg_defult()
        self.content += self.gen_reg_mask()

        # print(self.content, '\n')
        filename = os.path.join(folder_path_name, '{}.v'.format('reg'+ '_' + 'mask_default'))
        filename = filename.replace('\\', '/')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.content)

        self.content =''
        self.content += self.gen_reg_rw_test_case()
        filename = os.path.join(folder_path_name, '{}.v'.format('check' + '_' + 'reg'))
        filename = filename.replace('\\', '/')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.content)

        self.content = ''
        filename = os.path.join(folder_path_name, '{}.v'.format('base' + '_' + 'task'))
        self.content += self.gen_base_test_task()
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
    h = GEN_DV_MASK_DEFAULT_VAL(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
