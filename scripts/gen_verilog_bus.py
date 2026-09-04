#       'python gen_verilog_bus.py mars_top.db -f my_header.h'

import argparse, configparser, os, sys
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


class GEN_VERILOG_BUS():
    def __init__(self, modules, header_file="Default_Verilog.v", header_type='VERILOG'):
        self.modules = modules
        if ".v" in header_file:
            self.headerFile = header_file
        else:
            self.headerFile = header_file +'.v'
        self.filename = os.path.basename(self.headerFile).split('.v')[0].upper()
        self.pathname = os.path.dirname(self.headerFile)

        self.headerFile = header_file
        self.headerType = header_type
        self.content = '\n'
        self.repeatedModules = dict()
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "design_param.cfg.txt",
        )
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")
        self.data_width = config.getint("design_param", "data_width")
        self.addr_width = config.getint("design_param", "addr_width")

    def gen_inout_bus_list(self):
        inout_bus_list = ''
        inout_bus_list_str = "( \n"
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "userkey", ",", "\n")
        inout_bus_list_str += '{:<15}{:<20}{:<10}{}{}'.format("input", "", "lckey", ",", "\n")
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
        module_name_str = "module " + module.name.lower() + "_mmr"
        return module_name_str

    def gen_macro_parm(self):
        macro_parm_str = ""
        macro_parm_str = "    #( \n"
        macro_parm_str += "    parameter ADDR_WIDTH =" + str(self.addr_width) + "," + "\n"
        macro_parm_str += "    parameter DATA_WIDTH =" + str(self.data_width) + "\n"
        macro_parm_str += "    ) \n"
        return macro_parm_str

    @staticmethod
    def _flag_enabled(value):
        return str(value or '').strip().lower() in ('1', 'true', 'yes', 'on')

    @staticmethod
    def _port_declaration(direction, width, name):
        width_text = '' if width == 1 else '[{}:0]'.format(width - 1)
        return '{:<15}{:<20}{:<10}'.format(direction, width_text, name)

    def gen_inout_list(self, module):
        ports = [
            self._port_declaration('input', 1, 'userkey'),
            self._port_declaration('input', 1, 'lckey'),
            self._port_declaration('input', 1, 'clk'),
            self._port_declaration('input', 1, 'rstn'),
            self._port_declaration('input', 1, 'I_wr_stb'),
            self._port_declaration('input', 1, 'cs'),
            '{:<15}{:<20}{:<10}'.format('input', '[ADDR_WIDTH-1 : 0]', 'I_wr_addr'),
            '{:<15}{:<20}{:<10}'.format('input', '[DATA_WIDTH-1 : 0]', 'I_wr_data'),
            '{:<15}{:<20}{:<10}'.format('input', '[ADDR_WIDTH-1 : 0]', 'I_rd_addr'),
            '{:<15}{:<20}{:<10}'.format('output reg', '[DATA_WIDTH-1 : 0]', 'O_rd_data'),
        ]
        for reg in module.regs:
            for bit in reg.bits:
                base_name = reg.name.upper() + '_' + bit.name.upper()
                if bit.access == 'R(ReadOnly)':
                    ports.append(self._port_declaration('input', bit.width, 'I_' + base_name))
                    ports.append(self._port_declaration('output', bit.width, 'O_' + base_name))
                else:
                    if bit.access == 'W1C(Write1/auto-clear 0)':
                        ports.append(self._port_declaration('input', bit.width, 'I_' + base_name))
                    ports.append(self._port_declaration('output reg', bit.width, 'O_' + base_name))
                    if self._flag_enabled(bit.set):
                        ports.append(self._port_declaration('input', bit.width, 'I_' + base_name + '_set'))
                    if self._flag_enabled(bit.clr):
                        ports.append(self._port_declaration('input', bit.width, 'I_' + base_name + '_clr_n'))
        return "( \n" + ",\n".join(ports) + "\n);\n\n"

    def gen_addr_offset(self,module):
        addr_offet_parm = ''
        addr_offet_parm += '//Reg address parameter define \n'
        #print(str(module.name) + "address is " + str(module.address))
        for reg in module.regs:
            reg_address = str(hex(module.address + reg.address))
            #print(reg_address)
            addr_offet_parm += '{:<15}{:<20}{:<3}{:<20}{}'.format("parameter", "ADDR_"+reg.name.upper() , "=", '\'h'+reg_address[2:]+";", "\n")
        addr_offet_parm += '\n'
        return addr_offet_parm

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

    def gen_read_only_assign(self,module):
        read_only_list = ''
        for reg in module.regs:
            for bit in reg.bits:
                if bit.access == 'R(ReadOnly)':
                    read_only_list += 'assign {0}{2} = {1}{2};\n'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "I_"+reg.name.upper()+"_"+bit.name.upper(), "" if bit.width == 1 else "[" + str(bit.width - 1) + ":" + "0" + "]")
        if read_only_list != '' :
            return_list = '//The Read_only output signal assign for {0} \n'.format(module.name) + read_only_list
        else :
            return_list = read_only_list
        return return_list

    def gen_always_write(self,local_clr_signal,clr_assign,set_input_signal,out_reg_signal,bus_wr_condition,bus_wr):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''
        if(clr_assign != ''):
            gen_always_list += clr_assign + '\n'
            sensitive_list += "posedge clk or negedge {0} ".format(local_clr_signal)
            rst_condition += '\tif(!{0}) begin \n\t\t{1} <= {2};\n\tend '.format(local_clr_signal, out_reg_signal, "1'b0")
        else:
            gen_always_list += ''
            sensitive_list += "posedge clk or negedge rstn "
            rst_condition += '\tif(!rstn) begin \n\t\t{1} <= {2};\n\tend '.format(local_clr_signal, out_reg_signal, "1'b0")
        if(set_input_signal != ''):
            sensitive_list += 'or posedge {0}'.format(set_input_signal)
            set_condition += 'else if ({0} == 1\'b1) begin\n\t\t{1} <= 1\'b1;\n\tend '.format(set_input_signal, out_reg_signal)
        else:
            sensitive_list += ''
            set_condition += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        bus_condition += '\t\t{0}; end\nend\n'.format(bus_wr)

        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def gen_always_write_wr_once(self,local_clr_signal,clr_assign,set_input_signal,out_reg_signal,bus_wr_condition,bus_wr,w_once_flag):
        gen_always_list = ''
        sensitive_list = ''
        rst_condition = ''
        set_condition = ''
        bus_condition = ''
        gen_always_list += 'reg    {0};\n'.format(w_once_flag)
        if(clr_assign != ''):
            gen_always_list += clr_assign + '\n'
            sensitive_list += "posedge clk or negedge {0} ".format(local_clr_signal)
            rst_condition += '\tif(!{0}) begin \n\t\t{1} <= {2};\n\t\t{3} <= 1\'b1;\n\tend '.format(local_clr_signal, out_reg_signal, "1'b0", w_once_flag)
        else:
            gen_always_list += ''
            sensitive_list += "posedge clk or negedge rstn "
            rst_condition += '\tif(!rstn) begin \n\t\t{1} <= {2};\n\t\t{3} <= 1\'b1;\n\tend '.format(local_clr_signal, out_reg_signal, "1'b0", w_once_flag)
        if(set_input_signal != ''):
            sensitive_list += 'or posedge {0}'.format(set_input_signal)
            set_condition += 'else if ({0} == 1\'b1) begin\n\t\t{1} <= 1\'b1;\n\tend '.format(set_input_signal, out_reg_signal)
        else:
            sensitive_list += ''
            set_condition += ''
        bus_condition += 'else if({0}) begin\n'.format(bus_wr_condition)
        bus_condition += '\t\t{0}; \n\t\t{1} <= 1\'b0; end\nend\n'.format(bus_wr, w_once_flag)

        gen_always_list += 'always @({0}) begin \n'.format(sensitive_list)
        gen_always_list += rst_condition
        gen_always_list += set_condition
        gen_always_list += bus_condition
        gen_always_list += '\n'
        return gen_always_list

    def gen_bus_hw_write_legacy_prototype(self,module):
        always_bus_hw_wr_str = ''
        for reg in module.regs:
            for bit in reg.bits:
                always_bus_hw_wr_str += '//define always write for reg {1} / type-{0}\n'.format(bit.access, reg.name.upper() + "_" + bit.name.upper())
                '''
                match(bit.access):
                    case 'RW' | 'W(WriteOnly)' | 'WRS(WR/hardware update)':
                        for i in range(bit.width):
                            if bit.clr:
                                local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                                clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                                clr_assign        = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                            else:
                                local_clr_signal = ''
                                clr_assign = ''
                            if bit.set:
                                set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                            else:
                                set_input_signal  = ''
                            out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                            bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                            bus_wr           = '{0} <= {1}? {2} : {0}'.format(out_reg_signal , bit.key , 'I_wr_data'+'['+str(bit.position+i)+']')
                            always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr)
                    case 'RC(readclear)':
                        for i in range(bit.width):
                            if bit.clr:
                                local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                                clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                                clr_assign = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                            else:
                                local_clr_signal = ''
                                clr_assign = ''
                            if bit.set:
                                set_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                            else:
                                set_input_signal = ''
                            out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                            bus_wr_condition = 'cs & (I_rd_addr == ADDR_{0})'.format(reg.name.upper())
                            bus_wr = '{0} <= {1}? 1\'b1 : {0}'.format(out_reg_signal, bit.key)
                            always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr)
                    case 'W1C(Write1/auto-clear 0)':
                        for i in range(bit.width):
                            if bit.clr:
                                local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                                clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                                clr_assign        = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                            else:
                                local_clr_signal = ''
                                clr_assign = ''
                            if bit.set:
                                set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                            else:
                                set_input_signal  = ''
                            out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                            bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                            bus_wr           = '{0} <= {1}? ({2} & {0}) : {0}'.format(out_reg_signal, bit.key, '~I_wr_data'+'['+str(bit.position+i)+']')
                            always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr)
                    case 'W0S(Write0/auto-set1)':
                        for i in range(bit.width):
                            if bit.clr:
                                local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                                clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                                clr_assign        = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                            else:
                                local_clr_signal = ''
                                clr_assign = ''
                            if bit.set:
                                set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                            else:
                                set_input_signal  = ''
                            out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                            bus_wr_condition = 'WEN_{0} == 1\'b1'.format(reg.name.upper())
                            bus_wr           = '{0} <= {1}? ({2} | {0}) : {0}'.format(out_reg_signal, bit.key, '~I_wr_data'+'['+str(bit.position+i)+']')
                            always_bus_hw_wr_str += self.gen_always_write(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr)
                    case 'W1(WriteOnce)':
                        for i in range(bit.width):
                            if bit.clr:
                                local_clr_signal = 'local_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                                clr_input_signal = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_clr_n", "["+str(i)+"]" if(bit.width>1) else "")
                                clr_assign       = 'wire   ' + local_clr_signal + ';\n' + 'assign '+local_clr_signal+' = ' + 'rstn' + ' & ' + clr_input_signal + ';'
                            else:
                                local_clr_signal = ''
                                clr_assign = ''
                            if bit.set:
                                set_input_signal  = '{0}{1}'.format("I_" + reg.name.upper() + "_" + bit.name.upper() + "_set", "["+str(i)+"]" if(bit.width>1) else "")
                            else:
                                set_input_signal  = ''
                            w_once_flag = 'flag_'+reg.name.upper()+"_"+bit.name.upper()+"_"+str(i)
                            out_reg_signal = '{0}{1}'.format("O_"+reg.name.upper()+"_"+bit.name.upper(), "["+str(i)+"]" if(bit.width>1) else "")
                            bus_wr_condition = '(WEN_{0} == 1\'b1) & {1}'.format(reg.name.upper(), w_once_flag)
                            bus_wr           = '{0} <= {1}? {2} : {0}'.format(out_reg_signal, bit.key, 'I_wr_data'+'['+str(bit.position+i)+']')
                            always_bus_hw_wr_str += self.gen_always_write_wr_once(local_clr_signal, clr_assign, set_input_signal, out_reg_signal, bus_wr_condition, bus_wr, w_once_flag)
                    '''
        return always_bus_hw_wr_str

    def gen_bus_hw_write(self, module):
        """Generate the Python 3.9-compatible register storage logic."""

        generated = ''
        write_accesses = ('RW', 'W(WriteOnly)', 'WRS(WR/hardware update)')
        for reg in module.regs:
            for bit in reg.bits:
                if bit.access == 'R(ReadOnly)':
                    continue
                generated += '//define always write for reg {1} / type-{0}\n'.format(
                    bit.access, reg.name.upper() + '_' + bit.name.upper()
                )
                key_expression = str(bit.key or '').strip()
                has_key = key_expression not in ('', 'None')
                for index in range(bit.width):
                    suffix = '[{}]'.format(index) if bit.width > 1 else ''
                    out_signal = 'O_{}_{}{}'.format(
                        reg.name.upper(), bit.name.upper(), suffix
                    )
                    if self._flag_enabled(bit.clr):
                        local_clear = 'local_{}_{}_{}'.format(
                            reg.name.upper(), bit.name.upper(), index
                        )
                        clear_input = 'I_{}_{}_clr_n{}'.format(
                            reg.name.upper(), bit.name.upper(), suffix
                        )
                        clear_assign = (
                            'wire   {0};\nassign {0} = rstn & {1};'.format(
                                local_clear, clear_input
                            )
                        )
                    else:
                        local_clear = ''
                        clear_assign = ''
                    if self._flag_enabled(bit.set):
                        set_input = 'I_{}_{}_set{}'.format(
                            reg.name.upper(), bit.name.upper(), suffix
                        )
                    else:
                        set_input = ''

                    data_bit = 'I_wr_data[{}]'.format(bit.position + index)
                    if bit.access in write_accesses:
                        condition = "WEN_{} == 1'b1".format(reg.name.upper())
                        if has_key:
                            write = '{0} <= {1} ? {2} : {0}'.format(
                                out_signal, key_expression, data_bit
                            )
                        else:
                            write = '{} <= {}'.format(out_signal, data_bit)
                        generated += self.gen_always_write(
                            local_clear, clear_assign, set_input, out_signal,
                            condition, write
                        )
                    elif bit.access == 'RC(readclear)':
                        condition = 'cs & (I_rd_addr == ADDR_{})'.format(
                            reg.name.upper()
                        )
                        if has_key:
                            write = "{0} <= {1} ? 1'b1 : {0}".format(
                                out_signal, key_expression
                            )
                        else:
                            write = "{} <= 1'b1".format(out_signal)
                        generated += self.gen_always_write(
                            local_clear, clear_assign, set_input, out_signal,
                            condition, write
                        )
                    elif bit.access == 'W1C(Write1/auto-clear 0)':
                        condition = "WEN_{} == 1'b1".format(reg.name.upper())
                        value = '~{} & {}'.format(data_bit, out_signal)
                        if has_key:
                            write = '{0} <= {1} ? ({2}) : {0}'.format(
                                out_signal, key_expression, value
                            )
                        else:
                            write = '{} <= {}'.format(out_signal, value)
                        generated += self.gen_always_write(
                            local_clear, clear_assign, set_input, out_signal,
                            condition, write
                        )
                    elif bit.access == 'W0S(Write0/auto-set1)':
                        condition = "WEN_{} == 1'b1".format(reg.name.upper())
                        value = '~{} | {}'.format(data_bit, out_signal)
                        if has_key:
                            write = '{0} <= {1} ? ({2}) : {0}'.format(
                                out_signal, key_expression, value
                            )
                        else:
                            write = '{} <= ({})'.format(out_signal, value)
                        generated += self.gen_always_write(
                            local_clear, clear_assign, set_input, out_signal,
                            condition, write
                        )
                    elif bit.access == 'W1(WriteOnce)':
                        write_once_flag = 'flag_{}_{}_{}'.format(
                            reg.name.upper(), bit.name.upper(), index
                        )
                        condition = "(WEN_{0} == 1'b1) & {1}".format(
                            reg.name.upper(), write_once_flag
                        )
                        if has_key:
                            write = '{0} <= {1} ? {2} : {0}'.format(
                                out_signal, key_expression, data_bit
                            )
                        else:
                            write = '{} <= {}'.format(out_signal, data_bit)
                        generated += self.gen_always_write_wr_once(
                            local_clear, clear_assign, set_input, out_signal,
                            condition, write, write_once_flag
                        )
        return generated

    def gen_bus_read(self,module):
        bus_read_list = ''
        bus_read_list += '//For the bus read for module {0}\n'.format(module.name)
        bus_read_list += "always @(*) begin \n\tO_rd_data = 'b0;\n\tcase(I_rd_addr)\n"
        for reg in module.regs:
            bus_read_list += '\t\t{} : begin \n'.format("ADDR_"+reg.name.upper())
            for bit in reg.bits:
                if (bit.access != 'R(ReadOnly)') & (bit.access != 'W(WriteOnly)'):
                    bus_read_list += '\t\t\t{0:<20} = {1};\n'.format('O_rd_data' + '['+ (str(bit.position) if bit.width == 1 else (str(bit.position+bit.width-1)+':'+str(bit.position))) + ']', \
                                                                 'O_'+reg.name.upper()+'_'+bit.name.upper()+('' if bit.width == 1 else ('[' + str(bit.width-1) + ':0]')))
                if bit.access == 'R(ReadOnly)' :
                    bus_read_list += '\t\t\t{0:<20} = {1};\n'.format('O_rd_data' + '['+ (str(bit.position) if bit.width == 1 else (str(bit.position+bit.width-1)+':'+str(bit.position))) + ']', \
                                                                 'I_'+reg.name.upper()+'_'+bit.name.upper()+('' if bit.width == 1 else ('[' + str(bit.width-1) + ':0]')))
                if bit.access == 'W(WriteOnly)':
                    bus_read_list += '\t\t\t{0:<20} = {1};\n'.format('O_rd_data' + '['+ (str(bit.position) if bit.width == 1 else (str(bit.position+bit.width-1)+':'+str(bit.position))) + ']', \
                                                                 '\'b'+str(bit.default_value))
            bus_read_list += '\t\tend \n'
        bus_read_list += '\t endcase \n'
        bus_read_list += 'end\n\n'
        return bus_read_list

    def run(self):
        for module in self.modules:
            #self.filename = "D:\\WORK_AREA\\reg_software\\reg_mmr\\verilog_file\\" + module.name + ".v"
            fileName = os.path.join(self.pathname,self.filename)+'_{}.v'.format(module.name)
            # print(fileName)
            self.content = self.gen_module_name(module) + "\n"
            self.content += self.gen_macro_parm()
            self.content += self.gen_inout_list(module)
            self.content += self.gen_addr_offset(module)
            self.content += self.gen_enable_assign(module)
            self.content += self.gen_read_only_assign(module)
            self.content += self.gen_bus_hw_write(module)
            self.content += self.gen_bus_read(module)
            self.content += 'endmodule \n'
            with open(fileName, 'w', encoding='utf-8') as f:
                f.write(self.content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="C header generator")
    parser.add_argument('database', action='store', help="Specify register database file")
    parser.add_argument('-f', action='store', help="Specify name of header file", default='Default_Header.h')
    parser.add_argument('-afe', action='store_true',
                        help="Generate header file for AFE or MCU, defualt is MCU if nothing specified")
    cmd = parser.parse_args()

    app = create_db_app(cmd.database)
    app.app_context().push()
    modules = MODULE.query.order_by(MODULE.address).all()
    h = GEN_VERILOG_BUS(modules, cmd.f, 'VERILOG')
    #h.genHeader()
    h.run()
