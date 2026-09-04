# python3 gen_mmr_APB.py .\LH1282_TOP.db -f APB_mmr
# python3 gen_mmr_APB.py .\RW_all.db -f APB_mmr
# python3 gen_mmr_APB.py .\Rubens_MMR.db -f APB_mmr
# python3 gen_mmr_APB.py .\Zeus.db -f Zeus
# python gen_mmr_APB.py .\Zeus.db -f Zeus
#python3 gen_mmr_APB.py .\Test.db -f Test
#python3 gen_mmr_APB.py .\ADS131M08.db -f ADS131M08

import flask
import argparse, sys, shutil
import configparser
from datetime import date
from regdb import BIT_VALUE, BIT, REG, MODULE, create_db_app, db
import os
import os.path
import design_settings

HEADER_DATE = date.today()
HEADER_YEAR = date.today().year
HEADER_COMMENT_SEPERATOR = '***********************************************************************\n'
HEADER_COMPANY = r"苏州领慧立芯科技有限公司"
HEADER_COPYRIGHT = "//Copyright @  {0}  {1}\n\
\n//This is a genetated file, do not modify it by hand\n\n\
".format(HEADER_YEAR, HEADER_COMPANY)


class GEN_MMR_APB():
    def __init__(self, modules, header_file="Default_Verilog.v", header_type='VERILOG'):
        self.modules = modules
        self.headerFile = header_file
        self.folder_name = os.path.basename(self.headerFile)
        self.pathname = os.path.dirname(self.headerFile)

        self.headerFile = header_file
        self.headerType = header_type
        self.content = '\n'
        self.repeatedModules = dict()
        # self.data_width = 32
        # self.addr_width = 32
        self.base_addr_en = 0
        self.bus_type = "APB"

    def gen_reg_sheet_comment(self, module):
        reg_sheet_list = ''
        reg_sheet_list += "/*"
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*' * 50, 'MODULE NAME ' + module.name.lower(), '*' * 50)
        for reg in module.regs:
            # print(reg.ate_trim, type(reg.ate_trim))
            reg_sheet_list += '{0}{1}{2}\n'.format('-' * 50, reg.name.lower(), '-' * 50)
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('BIT NAME', 'BIT POSITION','REG_ACCESS', 'REG_KEY','SET', 'CLEAR')
            reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format('-' * 25, '-' * 15, '-' * 30,'-' * 15, '-' * 10,'-' * 10, )
            for bit in reg.bits:
                reg_sheet_list += '|{0:<25}|{1:<15}|{2:<30}|{3:<15}|{4:<10}|{5:<10}\n'.format(bit.name.lower(),'[' + str(bit.position + bit.width - 1) + ':' + str(bit.position) + ']', bit.access, str(bit.key),str(bit.set),str(bit.clr))
            reg_sheet_list += '{0}\n\n'.format('-' * 110)
        reg_sheet_list += '{0}{1}{2}\n\n'.format('*' * 50, 'end ' + module.name.lower(), '*' * 50 + '/')
        return reg_sheet_list

    def gen_inout_bus_list(self):
        self.config_parser()
        inout_bus_list = ''
        inout_bus_list_str = "( \n"
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "userkey", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "lckey", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "clk", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "rstn", ",", "\n")
        if (self.bus_type == "APB"):
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[ADDR_WIDTH-1 : 0]", "p_addr", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "p_sel", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "p_enable", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "p_write", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "[DATA_WIDTH-1 : 0]", "p_wdata", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "["+"{}".format(str(self.addr_width//8-1))+":0]", "p_strb", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output", "", "p_ready", ",", "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "[DATA_WIDTH-1 : 0]", "p_rdata", ",",
                                                                  "\n")
            inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output", "", "p_slaverr", ",", "\n")
        inout_bus_list_str += '\n'
        return inout_bus_list_str

    def gen_module_name(self, module):
        module_name_str = ""
        module_name_str += '\n`ifndef ' + module.name.upper() + '_MMR_V\n'
        module_name_str += '`define ' + module.name.upper() + '_MMR_V\n\n'
        module_name_str += "module " + module.name.lower() + "_mmr"
        return module_name_str

    def gen_addr_offset(self, module):
        addr_offet_parm = ''
        addr_offet_parm += '\t//Reg address parameter define \n'
        for reg in module.regs:
            if self.base_addr_en:
                reg_address = str(hex(module.address + reg.address))
            else:
                reg_address = str(hex(reg.address))
            addr_offet_parm += '\t{}{:<20}{:<3}{}{}{}'.format("parameter [ADDR_WIDTH-1 : 0] ", "addr_" + reg.name.lower(), "=", '\'h' + reg_address[2:], ",", "\n")
        addr_offet_parm += '\n'
        return addr_offet_parm

    def gen_macro_parm(self, module):
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
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'W(WriteOnly)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'RC(readclear)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'W1C(Write1/auto-clear 0)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'W0S(Write0/auto-set1)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'W1(WriteOnce)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'WRS(WR/hardware update)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("output reg", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "O_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                elif bit.access == 'R(ReadOnly)':
                    inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     ", "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]", "I_" + reg.name.lower() + "_" + bit.name.lower(), ",", "\n")
                if bit.set != 'None':
                    if (bit.set == '1') & (bit.access != 'R(ReadOnly)'):
                        # inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     ","" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]","I_" + reg.name.lower() + "_" + bit.name.lower() + "_set", ",", "\n")
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     "," ", "I_" + reg.name.lower() + "_" + bit.name.lower() + "_set", ",", "\n")
                if bit.clr != 'None':
                    if (bit.clr == '1') & (bit.access != 'R(ReadOnly)'):
                        inout_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input     "," ", "I_" + reg.name.lower() + "_" + bit.name.lower() + "_clr",",", "\n")
            inout_list_str += "\n"
        inout_list_str = inout_list_str[:-3] + "\n" + ");" + "\n\n"
        return inout_list_str

    def gen_enable_assign(self, module):
        enable_assign_cond = ""
        # define the wire include wr_en and rd_en , wen for the reg
        enable_assign_cond += "//Write and read enable wire define \n"
        enable_assign_cond += "wire    wr_en; \n"
        enable_assign_cond += "wire    rd_en; \n"
        for reg in module.regs:
            if reg.access != 'R(ReadOnly)':
                enable_assign_cond += "wire    wen_{0}; \n".format(reg.name.lower())

        enable_assign_cond += "\n//Write enable assign for bus \n"
        enable_assign_cond += "assign   {0:<20} = p_sel & p_enable & p_write; \n".format('wr_en')
        enable_assign_cond += "assign   {0:<20} = p_sel & p_enable & !p_write; \n".format('rd_en')

        for reg in module.regs:
            if reg.access != 'R(ReadOnly)':
                enable_assign_cond += "assign   {0:<20} = wr_en & (p_addr ==  addr_{1}); \n".format('wen_' + reg.name.lower(), reg.name.lower())
            # if reg.access == 'RC(readclear)':
            #     enable_assign_cond += "assign   {0:<20} = rd_en & (p_addr ==  addr_{1}); \n".format('rd_clr_' + reg.name.lower(), reg.name.lower())
            # if reg.access == 'RC(readclear)':
            #     enable_assign_cond += "assign   {0:<20} = rd_en & (p_addr ==  addr_{1}); \n".format('rd_clr_' + reg.name.lower(), reg.name.lower())
        enable_assign_cond += '\n'
        return enable_assign_cond

    def gen_always_write(self, clr_input_signal, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr,bit_default_val, bit_width):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''

        sensitive_list += "posedge clk or negedge rstn "
        # define the the Asy rstn and the sync clear of the clear signal
        if (clr_input_signal != ''):
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend ''else if({2}) begin \n\t\t{0} <= {3}\'b{4};\n\tend '.format(out_reg_signal, bit_width + "'h" + hex(int(bit_default_val))[2:], clr_input_signal, bit_width, "0"*int(bit_width))
        else:
            gen_always_list += ''
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend '.format(out_reg_signal,bit_width + "'h" + hex(int(bit_default_val))[2:])
        # define the sync set of the set output to 1
        if (set_input_signal != ''):
            set_condition += 'else if ({0}) begin\n\t\t{1} <= {2}\'b{3};\n\tend '.format(set_input_signal, out_reg_signal, bit_width, "1"*int(bit_width))
        else:
            gen_always_list += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        bus_condition += '\t\t{0}; \n\tend\nend\n'.format(bus_wr)
        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    # use for read clear register
    def gen_always_write_rc(self, clr_input_signal, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, bit_default_val, read_clr_signal, bit_width):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''

        sensitive_list += "posedge clk or negedge rstn "
        # define the the Asy rstn and the sync clear of the clear signal
        if (clr_input_signal != ''):
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend ''else if({2}) begin \n\t\t{0} <= {3};\n\tend '.format(out_reg_signal, bit_width + "'h" + hex(int(bit_default_val))[2:], clr_input_signal, bit_width+"'b"+"0"*int(bit_width))
        else:
            gen_always_list += ''
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend '.format(out_reg_signal, bit_width + "'h" + hex(int(bit_default_val))[2:])
        # define the sync set of the set output to 1
        if (set_input_signal != ''):
            set_condition += 'else if({0}) begin\n\t\t{1} <= {2}\'b{3};\n\tend '.format(set_input_signal, out_reg_signal, bit_width,"1"*int(bit_width))
        else:
            gen_always_list += ''
        read_clr_condition = 'else if({0}) begin\n\t\t{1} <= {2};\n\tend\nend '.format(read_clr_signal, out_reg_signal, bit_width+"'b"+"0"*int(bit_width))
        bus_condition += 'else if({0}) begin\n\t\t{1}; \n\tend '.format(bus_wr_condition, bus_wr)
        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += read_clr_condition
        gen_always_list += '\n\n'
        return gen_always_list

    def gen_always_write_w1c(self, clr_input_signal, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr,bit_default_val, bit_width):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''

        sensitive_list += "posedge clk or negedge rstn "
        # define the the Asy rstn and the sync clear of the clear signal
        if (clr_input_signal != ''):
            rst_condition += "\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend else if({2}) begin \n\t\t{0} <= {3}'b{4};\n\tend ".format(out_reg_signal, bit_width + "'h" + hex(int(bit_default_val))[2:], clr_input_signal, bit_width, "0"*int(bit_width))
        else:
            gen_always_list += ''
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend '.format(out_reg_signal,bit_width + "'h" + hex(int(bit_default_val))[2:])
        # define the sync set of the set output to 1
        if (set_input_signal != ''):
            set_condition += 'else if ({0}) begin\n\t\t{1} <= {2}\'b{3};\n\tend '.format(set_input_signal, out_reg_signal, bit_width, "1"*int(bit_width))
        else:
            gen_always_list += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        # bus_condition += "\t\t{0} <= {1}'b{2}; \n\tend\nend\n".format(out_reg_signal, bit_width, "0"*int(bit_width))
        bus_condition += "\t\t{0}\n\tend\nend\n".format(bus_wr)
        # bus_condition += bus_wr
        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)

        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def gen_always_write_w0s(self, clr_input_signal, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr,bit_default_val, bit_width):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''
        sensitive_list += "posedge clk or negedge rstn "
        # define the the Asy rstn and the sync clear of the clear signal
        if (clr_input_signal != ''):
            rst_condition += "\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend else if({2}) begin \n\t\t{0} <= {3}'b{4};\n\tend ".format(out_reg_signal, bit_width + "'h" + hex(int(bit_default_val))[2:], clr_input_signal, bit_width, "0"*int(bit_width))
        else:
            gen_always_list += ''
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend '.format(out_reg_signal,bit_width + "'h" + hex(int(bit_default_val))[2:])
        # define the sync set of the set output to 1
        if (set_input_signal != ''):
            set_condition += 'else if ({0}) begin\n\t\t{1} <= {2}\'b{3};\n\tend '.format(set_input_signal, out_reg_signal, bit_width, "1"*int(bit_width))
        else:
            gen_always_list += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        # bus_condition += "\t\t{0} <= {1}'b{2}; \n\tend\nend\n".format(out_reg_signal, bit_width, "1"*int(bit_width))
        bus_condition += "\t\t{0} \n\tend\nend\n".format(bus_wr)
        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def gen_always_write_wr_once(self, clr_input_signal, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr,w_once_flag, w_once_flag_write, flag_assign, bit_default_val, bit_width):
        gen_always_list = ''
        sensitive_list = ''
        flag_wr = ''
        gen_always_list += 'reg    {0};\n'.format(w_once_flag)
        sensitive_list += "posedge clk or negedge rstn "
        flag_wr += "\tif(!rstn) begin \n\t\t{0} <= 1'b1;\n\tend else if({2}) begin \n\t\t{0} <= 1'b0;\n\tend \nend \n".format(w_once_flag, bit_width + "'h" + hex(int(bit_default_val))[2:], bus_wr_condition)
        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += flag_wr
        gen_always_list += '\n'

        rst_condition = ''
        set_condition = ''
        bus_condition = ''
        gen_always_list += 'wire {0};\n'.format(w_once_flag_write)
        gen_always_list += flag_assign + "\n"
        if (clr_input_signal != ''):
            rst_condition += "\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend else if({2}) begin \n\t\t{0} <= {3}'b{4};\n\tend ".format(out_reg_signal, bit_width + "'h" + hex(int(bit_default_val))[2:], clr_input_signal, bit_width, "0"*int(bit_width))
        else:
            gen_always_list += ''
            rst_condition += '\tif(!rstn) begin \n\t\t{0} <= {1};\n\tend '.format(out_reg_signal,bit_width + "'h" + hex(int(bit_default_val))[2:])
        # define the sync set of the set output to 1
        if (set_input_signal != ''):
            set_condition += 'else if ({0}) begin\n\t\t{1} <= {2}\'b{3};\n\tend '.format(set_input_signal, out_reg_signal, bit_width, "1"*int(bit_width))
        else:
            gen_always_list += ''
        bus_condition += 'else if({0}) begin\n'.format(w_once_flag_write)
        # bus_condition += '\t\t{0}; \n\t\t{1} <= \'b0; \n\tend\nend\n'.format(bus_wr, w_once_flag)
        bus_condition += '\t\t{0}; \n\tend\nend\n'.format(bus_wr)
        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def p_stb_fun(self, i, bit):
        stb_postion = bit.position + i
        if (stb_postion >= 0) & (stb_postion <= 7):
            p_stb_num = 0
        if (stb_postion >= 8) & (stb_postion <= 15):
            p_stb_num = 1
        if (stb_postion >= 16) & (stb_postion <= 23):
            p_stb_num = 2
        if (stb_postion >= 24) & (stb_postion <= 31):
            p_stb_num = 3
        if (stb_postion >= 32) & (stb_postion <= 39):
            p_stb_num = 4
        if (stb_postion >= 40) & (stb_postion <= 47):
            p_stb_num = 5
        if (stb_postion >= 48) & (stb_postion <= 55):
            p_stb_num = 6
        if (stb_postion >= 56) & (stb_postion <= 63):
            p_stb_num = 7
        if (stb_postion >= 64) & (stb_postion <= 71):
            p_stb_num = 8
        if (stb_postion >= 72) & (stb_postion <= 79):
            p_stb_num = 9
        return p_stb_num

    def gen_bus_hw_write(self, module):
        always_bus_hw_wr_str = ''
        for reg in module.regs:
            reg_default_val = str('{:0>{def_val_width}b}'.format(reg.default_value, def_val_width=self.data_width))
            for bit in reg.bits:
                if bit.access != 'R(ReadOnly)':
                    always_bus_hw_wr_str += '//define always write for reg {1} / type-{0}\n'.format(bit.access,reg.name.lower() + "_" + bit.name.lower())
                if (bit.access == 'RW') or (bit.access == 'W(WriteOnly)') or (bit.access == 'WRS(WR/hardware update)'):
                    p_stb_cnt = self.p_stb_fun(0, bit) #after modify,the number of p_stb is assigned by first bit
                    bus_wr_condition = 'wen_{0} & p_strb[{1}]'.format(reg.name.lower(), p_stb_cnt)
                    #1 bit of clear or reset signal
                    if bit.clr == '1':
                        clr_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_clr")
                    else:
                        clr_input_signal = ''
                    if bit.set == '1':
                        set_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_set")
                    else:
                        set_input_signal = ''
                    out_reg_signal = '{0}{1}'.format("O_" + reg.name.lower() + "_" + bit.name.lower(), "[" + str(bit.width - 1) + ":0]" if (bit.width > 1) else "")
                    if (bit.key != 'None') & (bit.key != ''):
                        bus_wr = '{0} <= {1} ? {2} : {0}'.format(out_reg_signal, bit.key.lower(), 'p_wdata' + '[' + str(bit.position + bit.width -1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']')
                    else:
                        bus_wr = '{0} <= {1}'.format(out_reg_signal, 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']')
                    always_bus_hw_wr_str += self.gen_always_write(clr_input_signal, set_input_signal, out_reg_signal,bus_wr_condition, bus_wr, str(bit.default_value), str(bit.width))
                elif bit.access == 'RC(readclear)':
                    w1_en_signal = 'wen_{0}'.format(reg.name.lower())
                    read_clr_signal = 'rd_clr_{0}'.format(reg.name.lower() + "_" + bit.name.lower())
                    read_clr_condition = 'assign\t{0:<15} = rd_en & (p_addr == addr_{1});\n'.format(read_clr_signal, reg.name.lower())
                    always_bus_hw_wr_str += 'wire\t{0};\n'.format(read_clr_signal)
                    always_bus_hw_wr_str += read_clr_condition
                    p_stb_cnt = self.p_stb_fun(0, bit)  # after modify,the number of p_stb is assigned by first bit
                    if bit.clr == '1':
                        clr_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_clr")
                    else:
                        # clr_input_signal.append('{0}'.format(read_clr_signal))
                        clr_input_signal = ''
                    if bit.set == '1':
                        set_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_set")
                    else:
                        set_input_signal = ''
                    out_reg_signal = '{0}{1}'.format("O_" + reg.name.lower() + "_" + bit.name.lower(), "[" + str(bit.width - 1) + ":0]" if (bit.width > 1) else "")
                    if (bit.key != 'None') & (bit.key != ''):
                        bus_wr = '{0} <= {1} ? {2} : {0}'.format(out_reg_signal, bit.key.lower(), 'p_wdata' + '[' + str(bit.position + bit.width -1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']')
                    else:
                        bus_wr = '{0} <= {1}'.format(out_reg_signal, 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']')
                    bus_wr_condition = "{0} & p_strb[{1}]".format(w1_en_signal, p_stb_cnt)
                    always_bus_hw_wr_str += self.gen_always_write_rc(clr_input_signal, set_input_signal, out_reg_signal,bus_wr_condition, bus_wr, str(bit.default_value), read_clr_signal, str(bit.width))
                elif bit.access == 'W1C(Write1/auto-clear 0)':
                    p_stb_cnt = self.p_stb_fun(0, bit)  # after modify,the number of p_stb is assigned by first bit
                    bus_wr_condition = 'wen_{0} & p_strb[{1}]'.format(reg.name.lower(), p_stb_cnt)
                    if bit.clr == '1':
                        clr_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_clr")
                    else:
                        clr_input_signal = ''
                    if bit.set == '1':
                        set_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_set")
                    else:
                        set_input_signal = ''
                    out_reg_signal = '{0}{1}'.format("O_" + reg.name.lower() + "_" + bit.name.lower(), "[" + str(bit.width - 1) + ":0]" if (bit.width > 1) else "")
                    if (bit.key != 'None') & (bit.key != ''):
                        bus_wr = "{0} <= ({1} & p_wdata[{2}]) ? 1'b0 : {0};".format(out_reg_signal, str.lower(bit.key),str(bit.position))

                    else:
                        bus_wr = "{0} <= p_wdata[{1}] ? 1'b0 : {0};".format(out_reg_signal, str(bit.position))
                    always_bus_hw_wr_str += self.gen_always_write_w1c(clr_input_signal, set_input_signal,out_reg_signal, bus_wr_condition, bus_wr, str(bit.default_value) , str(bit.width))
                elif bit.access == 'W0S(Write0/auto-set1)':
                    p_stb_cnt = self.p_stb_fun(0, bit)  # after modify,the number of p_stb is assigned by first bit
                    if bit.clr == '1':
                        clr_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_clr")
                    else:
                        clr_input_signal = ''
                    if bit.set == '1':
                        set_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_set")
                    else:
                        set_input_signal = ''
                    out_reg_signal = '{0}{1}'.format("O_" + reg.name.lower() + "_" + bit.name.lower(), "[" + str(bit.width - 1) + ":0]" if (bit.width > 1) else "")
                    bus_wr_condition = 'wen_{0} & p_strb[{1}]'.format(reg.name.lower(), p_stb_cnt)
                    if (bit.key != 'None') & (bit.key != ''):
                        # bus_wr = '{0} <= {1} ? {2} : {0}'.format(out_reg_signal, bit.key.lower(), 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']')
                        bus_wr = "{0} <= ({1} & !{2}) ? {3}'b{4} : {0};".format(out_reg_signal, str.lower(bit.key), 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']', bit.width, "1" * bit.width)
                    else:
                        bus_wr = "{0} <= (!{1}) ? {2}'b{3} : {0};".format(out_reg_signal, 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ':' + str(bit.position) + ']' if (bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']', bit.width, "1" * bit.width)
                    always_bus_hw_wr_str += self.gen_always_write_w0s(clr_input_signal, set_input_signal,out_reg_signal, bus_wr_condition, bus_wr, str(bit.default_value), str(bit.width))
                elif bit.access == 'W1(WriteOnce)':
                    w_once_flag = 'flag_w1_' + reg.name.lower() + "_" + bit.name.lower()
                    w_once_flag_write = 'flag_w1_' + reg.name.lower() + "_" + bit.name.lower() + "_write"
                    out_reg_signal = '{0}{1}'.format("O_" + reg.name.lower() + "_" + bit.name.lower(),
                                                     "[" + str(bit.width - 1) + ":0]" if (bit.width > 1) else "")
                    if bit.clr == '1':
                        clr_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_clr")
                    else:
                        clr_input_signal = ''
                    if bit.set == '1':
                        set_input_signal = '{0}'.format("I_" + reg.name.lower() + "_" + bit.name.lower() + "_set")
                    else:
                        set_input_signal = ''
                    if (bit.key != 'None') & (bit.key != ''):
                        bus_wr = '{0} <= {1} ? {2} : {0}'.format(out_reg_signal, bit.key.lower(), 'p_wdata' + '[' + str(
                            bit.position + bit.width - 1) + ':' + str(bit.position) + ']' if (
                                    bit.width > 1) else 'p_wdata' + '[' + str(bit.position + bit.width - 1) + ']')
                    else:
                        bus_wr = '{0} <= {1}'.format(out_reg_signal,
                                                     'p_wdata' + '[' + str(bit.position + bit.width - 1) + ':' + str(
                                                         bit.position) + ']' if (
                                                                 bit.width > 1) else 'p_wdata' + '[' + str(
                                                         bit.position + bit.width - 1) + ']')
                    p_stb_cnt = self.p_stb_fun(0, bit)  # after modify,the number of p_stb is assigned by first bit
                    bus_wr_condition = 'wen_{0} & p_strb[{1}]'.format(reg.name.lower(), p_stb_cnt)
                    flag_assign = "assign {0} = {1} & {2};".format(w_once_flag_write, bus_wr_condition, w_once_flag)
                    always_bus_hw_wr_str += self.gen_always_write_wr_once(clr_input_signal, set_input_signal,
                                                                          out_reg_signal, bus_wr_condition, bus_wr,
                                                                          w_once_flag, w_once_flag_write, flag_assign,
                                                                          str(bit.default_value), str(bit.width))
        return always_bus_hw_wr_str

    def gen_bus_read(self, module):
        bus_read_list = ''
        bus_read_list += '//For the bus read for module {0}\n'.format(module.name)
        bus_read_list += "always @(*) begin \n\tp_rdata = \'b0;\n\tif(1'b1) begin \n\t\tcase(p_addr)\n"
        for reg in module.regs:
            bus_read_list += '\t\t\t{} : begin \n'.format("addr_" + reg.name.lower())
            for bit in reg.bits:
                if (bit.access != 'R(ReadOnly)') & (bit.access != 'W(WriteOnly)'):
                    bus_read_list += '\t\t\t\t{0:<20} = {1};\n'.format('p_rdata' + '[' + (str(bit.position) if bit.width == 1 else (
                                    str(bit.position + bit.width - 1) + ':' + str(bit.position))) + ']', \
                                                                       'O_' + reg.name.lower() + '_' + bit.name.lower() + (
                                                                           '' if bit.width == 1 else ('[' + str(
                                                                               bit.width - 1) + ':0]')))
                if bit.access == 'R(ReadOnly)':
                    bus_read_list += '\t\t\t\t{0:<20} = {1};\n'.format('p_rdata' + '[' + (
                        str(bit.position) if bit.width == 1 else (
                                    str(bit.position + bit.width - 1) + ':' + str(bit.position))) + ']', \
                                                                       'I_' + reg.name.lower() + '_' + bit.name.lower() + (
                                                                           '' if bit.width == 1 else ('[' + str(
                                                                               bit.width - 1) + ':0]')))
                if bit.access == 'W(WriteOnly)':
                    bus_read_list += '\t\t\t\t{0:<20} = {1};\n'.format('p_rdata' + '[' + (str(bit.position) if bit.width == 1 else (str(bit.position + bit.width - 1) + ':' + str(bit.position))) + ']', str(bit.width) + '\'h0')
            bus_read_list += '\t\t\tend \n'
        bus_read_list += '\t\t\tdefault: p_rdata = \'b0;\n'.format(str(bit.width))
        bus_read_list += '\t\tendcase \n'
        bus_read_list += '\tend else \n\t\tp_rdata = \'b0;\nend\n\n'.format(str(bit.width))
        return bus_read_list

    def gen_bus_err_flag(self, module):
        bus_err_list = ''
        bus_err_list += 'wire reg_map;\nassign reg_map = \n'
        for reg in module.regs:
            bus_err_list += "\t\t(p_addr ==  addr_{0:<15}) |\n".format(reg.name.lower())
        bus_err_list = bus_err_list[:-2] + ' ;'
        # print(bus_err_list)
        bus_err_list += '\n\n'
        bus_err_list += 'assign p_slaverr = p_sel & p_enable & reg_map;\n\n'
        bus_err_list += 'assign p_ready = p_enable;\n\n'
        return bus_err_list

    def config_parser(self):
        config_path = design_settings.runtime_path("design_param.cfg.txt")
        cofig = configparser.ConfigParser()
        cofig.read(config_path, encoding="utf-8")
        # global addr_width
        self.data_width = int(cofig.get("design_param", "data_width"))
        self.addr_width = int(cofig.get("design_param", "addr_width"))
        self.base_addr_en = int(cofig.get("design_param", "design_base_addr_en"))
        # addr_width = self.addr_width

    def run(self):
        self.config_parser()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # folder_path_name = os.path.join(BASE_DIR, "APB_mmr\mmr_verilog_APB")
        folder_path_name = os.path.join(self.pathname, self.folder_name, 'APB_mmr')
        folder_path_name = folder_path_name.replace('\\', '/')
        folder_exist = os.path.exists(folder_path_name)
        if not folder_exist:
            os.makedirs(folder_path_name)
        else:
            shutil.rmtree(folder_path_name)
            os.makedirs(folder_path_name)
        for module in self.modules:
            # if (module.name[-4:]).lower() != 'trim':
            self.content = HEADER_COPYRIGHT
            self.content += self.gen_reg_sheet_comment(module)
            self.content += self.gen_module_name(module) + "\n"
            self.content += self.gen_macro_parm(module)
            self.content += self.gen_inout_list(module)
            self.content += self.gen_enable_assign(module)
            self.content += self.gen_bus_hw_write(module)
            self.content += self.gen_bus_read(module)
            self.content += self.gen_bus_err_flag(module)
            self.content += 'endmodule \n\n`endif'
            filename = os.path.join(folder_path_name, '{}.v'.format(module.name.lower() + '_' + 'mmr'))
            filename = filename.replace('\\', '/')
            # print(filename)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.content)

##    def connect_db(self):
##        return sqlite3.connect(db_path)


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
    h = GEN_MMR_APB(modules, cmd.f, 'VERILOG')
    # h.genHeader()
    h.run()

