#       python gen_non_trim_mmr.py .\Rubens_MMR_bak.db -f Non_trim_mmr

import argparse, os, sys, shutil
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


class GEN_NON_TRIM_MMR():
    def __init__(self, modules, header_file="Default_Verilog.v", header_type='VERILOG'):
        self.modules = modules
        self.headerFile = header_file
        self.folder_name = os.path.basename(self.headerFile)
        self.pathname = os.path.dirname(self.headerFile)

        self.headerFile = header_file
        self.headerType = header_type
        self.content = '\n'
        self.repeatedModules = dict()
        self.data_width = 32
        self.addr_width = 32
        self.base_addr_en = 0

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'MODULE NAME '+module.name.upper(), '*'*50)
        for reg in module.regs:
            #print(reg.ate_trim, type(reg.ate_trim))
            reg_sheet_list += '{0}{1}{2}\n'.format('-'*50, reg.name.upper(), '-'*50)
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}|{6:<10}\n'.format('BIT NAME', 'BIT POSITION', 'REG_ACCESS', 'REG_KEY', 'SET', 'CLEAR','DOC')
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}|{6:<10}\n'.format('-'*25, '-'*15, '-'*30, '-'*15, '-'*10, '-'*10, '-'*10)
            for bit in reg.bits:
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}|{6:<10}\n'.format(bit.name.upper(), '['+str(bit.position+bit.width-1)+':'+str(bit.position)+']', \
                                                                    bit.access, str(bit.key), str(bit.set), str(bit.clr), str(bit.doc))
            reg_sheet_list += '{0}\n\n'.format('-'*110)
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*'*50, 'end '+module.name.upper(), '*'*50+'/')
        return reg_sheet_list

    def gen_inout_bus_list(self):
        inout_bus_list = ''
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
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "[DATA_WIDTH-1 : 0]", "O_rd_data", ",","\n")
        inout_bus_list_str += '\n'
        return inout_bus_list_str

    def gen_module_name(self, module):
        module_name_str = ""
        module_name_str += '\n`ifndef '+module.name.upper()+ '_MMR_V\n'
        module_name_str += '`define '+module.name.upper()+ '_MMR_V\n\n'
        module_name_str += "module " + module.name.lower() + "_mmr"
        return module_name_str

    def gen_addr_offset(self,module):
        addr_offet_parm = ''
        addr_offet_parm += '\t//Reg address parameter define \n'
        for reg in module.regs:
            if self.base_addr_en:
                reg_address = str(hex(module.address + reg.address))
            else:
                reg_address = str(hex(reg.address))
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
        inout_list_str += self.gen_inout_bus_list()
        for reg in module.regs:
            inout_list_str += "//The signal define of the {0} ,type \"{1}\"\n".format(reg.name, reg.access)
            for bit in reg.bits:
                if bit.access == 'RW':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'W(WriteOnly)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'RC(readclear)':
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'W1C(Write1/auto-clear 0)':
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'W0S(Write0/auto-set1)':
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'W1(WriteOnce)':
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'WRS(WR/hardware update)':
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","O_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                elif bit.access == 'R(ReadOnly)':
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     ", "" if bit.width==1 else "[" + str(bit.width - 1) + ":" + "0" + "]","I_"+reg.name.upper()+"_"+bit.name.upper(), ",", "\n")
                if bit.set != 'None':
                    if (bit.set == '1') & (bit.access != 'R(ReadOnly)'):
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     ", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", ",","\n")
                if bit.clr != 'None':
                    if (bit.clr == '1') & (bit.access != 'R(ReadOnly)'):
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     ", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", ",","\n")
            inout_list_str += "\n"
        inout_list_str = inout_list_str[:-3] + "\n" + ");" + "\n\n"
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

    def gen_always_write(self,local_clr_signal,clr_assign,set_input_signal,out_reg_signal,bus_wr_condition,bus_wr,bit_default_val):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''
        if(clr_assign != ''):
            gen_always_list += clr_assign + '\n'
            sensitive_list += "posedge clk or negedge {0} ".format(local_clr_signal)
            rst_condition += '\tif(!{0}) begin \n\t\t{1} <= {2};\n\tend '.format(local_clr_signal, out_reg_signal, "1'b"+bit_default_val)
        else:
            gen_always_list += ''
            sensitive_list += "posedge clk or negedge rstn "
            rst_condition += '\tif(!rstn) begin \n\t\t{1} <= {2};\n\tend '.format(local_clr_signal, out_reg_signal, "1'b"+bit_default_val)
        if(set_input_signal != ''):
            sensitive_list += 'or posedge {0}'.format(set_input_signal)
            set_condition += 'else if ({0} == 1\'b1) begin\n\t\t{1} <= 1\'b1;\n\tend '.format(set_input_signal, out_reg_signal)
        else:
            sensitive_list += ''
            set_condition += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        bus_condition += '\t\t{0}; \n\tend\nend\n'.format(bus_wr)

        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def gen_always_write_wr_once(self,local_clr_signal,clr_assign,set_input_signal,out_reg_signal,bus_wr_condition,bus_wr,w_once_flag,bit_default_val):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''
        gen_always_list += 'reg    {0};\n'.format(w_once_flag)
        if(clr_assign != ''):
            gen_always_list += clr_assign + '\n'
            sensitive_list += "posedge clk or negedge {0} ".format(local_clr_signal)
            rst_condition += '\tif(!{0}) begin \n\t\t{1} <= {2};\n\t\t{3} <= 1\'b1;\n\tend '.format(local_clr_signal, out_reg_signal, "1'b"+bit_default_val, w_once_flag)
        else:
            gen_always_list += ''
            sensitive_list += "posedge clk or negedge rstn "
            rst_condition += '\tif(!rstn) begin \n\t\t{1} <= {2};\n\t\t{3} <= 1\'b1;\n\tend '.format(local_clr_signal, out_reg_signal, "1'b"+bit_default_val, w_once_flag)
        if(set_input_signal != ''):
            sensitive_list += 'or posedge {0}'.format(set_input_signal)
            set_condition += 'else if ({0} == 1\'b1) begin\n\t\t{1} <= 1\'b1;\n\tend '.format(set_input_signal, out_reg_signal)
        else:
            sensitive_list += ''
            set_condition += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        bus_condition += '\t\t{0}; \n\t\t{1} <= 1\'b0; \n\tend\nend\n'.format(bus_wr, w_once_flag)

        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def gen_bus_hw_write(self,module):
        always_bus_hw_wr_str = ''
        for reg in module.regs:
            reg_default_val = str('{:0>{def_val_width}b}'.format(reg.default_value, def_val_width = self.data_width))
            reg_val_reverse = reg_default_val[::-1]
            for bit in reg.bits:
                #print(bit.name,bit.set,bit.key,type(bit.set))
                if bit.access != 'R(ReadOnly)':
                    always_bus_hw_wr_str += '//define always write for reg {1} / type-{0}\n'.format(bit.access, reg.name.upper() + "_" + bit.name.upper())
                if (bit.access == 'RW') or (bit.access == 'W(WriteOnly)') or (bit.access == 'WRS(WR/hardware update)'):
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position+i]
                        if bit.clr == '1':
                            local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                            clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                            clr_assign        = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                        else:
                            local_clr_signal = ''
                            clr_assign = ''
                        if bit.set == '1':
                            set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                        else:
                            set_input_signal  = ''
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? {2} : {0}'.format(out_reg_signal, bit.key, 'I_wr_data'+'['+str(bit.position+i)+']')
                        else:
                            bus_wr = '{0} <= {1}'.format(out_reg_signal, 'I_wr_data' + '[' + str(bit.position + i) + ']')
                        always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, bit_default_val)
                elif bit.access == 'RC(readclear)':
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position + i]
                        if bit.clr == '1':
                            local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                            clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                            clr_assign = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                        else:
                            local_clr_signal = ''
                            clr_assign = ''
                        if bit.set == '1':
                            set_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                        else:
                            set_input_signal = ''
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = 'cs & (I_rd_addr == ADDR_{0})'.format(reg.name.upper())
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? 1\'b1 : {0}'.format(out_reg_signal, bit.key)
                        else:
                            bus_wr = '{0} <= 1\'b1'.format(out_reg_signal)
                        always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, bit_default_val)
                elif bit.access == 'W1C(Write1/auto-clear 0)':
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position + i]
                        if bit.clr == '1':
                            local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                            clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                            clr_assign        = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                        else:
                            local_clr_signal = ''
                            clr_assign = ''
                        if bit.set == '1':
                            set_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                        else:
                            set_input_signal = ''
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? ({2} & {0}) : {0}'.format(out_reg_signal, bit.key, '~I_wr_data'+'['+str(bit.position+i)+']')
                        else:
                            bus_wr = '{0} <= {1} & {0}'.format(out_reg_signal, '~I_wr_data' + '[' + str(bit.position + i) + ']')
                        always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, bit_default_val)
                elif bit.access == 'W0S(Write0/auto-set1)':
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position + i]
                        if bit.clr == '1':
                            local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                            clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                            clr_assign        = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                        else:
                            local_clr_signal = ''
                            clr_assign = ''
                        if bit.set == '1':
                            set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                        else:
                            set_input_signal  = ''
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? ({2} | {0}) : {0}'.format(out_reg_signal, bit.key, '~I_wr_data'+'['+str(bit.position+i)+']')
                        else:
                            bus_wr = '{0} <= ({1} | {0})'.format(out_reg_signal, '~I_wr_data'+'['+str(bit.position+i)+']')
                        always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, bit_default_val)
                elif bit.access == 'W1(WriteOnce)':
                    for i in range(bit.width):
                        bit_default_val = reg_val_reverse[bit.position + i]
                        if bit.clr == '1':
                            local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                            clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                            clr_assign       = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                        else:
                            local_clr_signal = ''
                            clr_assign = ''
                        if bit.set == '1':
                            set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                        else:
                            set_input_signal  = ''
                        w_once_flag = 'flag_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                        out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                        bus_wr_condition = '(WEN_{0} == 1\'b1) & {1}'.format(reg.name.upper(), w_once_flag)
                        if (bit.key != 'None') & (bit.key != ''):
                            bus_wr = '{0} <= {1}? {2} : {0}'.format(out_reg_signal, bit.key, 'I_wr_data'+'['+str(bit.position+i)+']')
                        else:
                            bus_wr = '{0} <= {1}'.format(out_reg_signal, 'I_wr_data'+'['+str(bit.position+i)+']')
                        always_bus_hw_wr_str += self.gen_always_write_wr_once(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, w_once_flag, bit_default_val)
        return always_bus_hw_wr_str

    def gen_bus_read(self, module):
        bus_read_list = ''
        bus_read_list += '//For the bus read for module {0}\n'.format(module.name)
        bus_read_list += 'always @(*) begin \n\tO_rd_data = \'b0;\n\tcase(I_rd_addr)\n'
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
        #config_path = r'C:\Users\chang\Desktop\work_area\WORK_AREA\reg_software\Register\Register_V1.0.0\Register\scripts\design_param.cfg.txt'
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(BASE_DIR, "design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))

    def run(self):
        self.config_parser()
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'Non_Tirm_mmr')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)
        for module in self.modules:
            #if (module.name[-4:]).lower() != 'trim':
            self.content = HEADER_COPYRIGHT
            self.content += self.gen_reg_sheet_comment(module)
            self.content += self.gen_module_name(module) + "\n"
            self.content += self.gen_macro_parm(module)
            self.content += self.gen_inout_list(module)
            self.content += self.gen_enable_assign(module)
            self.content += self.gen_bus_hw_write(module)
            self.content += self.gen_bus_read(module)
            self.content += 'endmodule \n\n`endif'
            filename = os.path.join(folder_path_name,'{}.v'.format(module.name.lower() + '_' + 'mmr'))
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
    h = GEN_NON_TRIM_MMR(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
