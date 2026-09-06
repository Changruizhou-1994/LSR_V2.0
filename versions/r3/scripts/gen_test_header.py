#
# Copyright @  2021  苏州领慧立芯科技有限公司
# 苏州领慧立芯科技有限公司内部保密技术代码， 您需要对代码保密负责， 不得转发给任何外部实体和个人
# Autor: Henry512@legendsemi.com
#
# Usage, 
#    - get help
#       'python gen_header.py -h'
#    - generator c header file for mcu from command line, example:
#       'python gen_test_header.py ..\lh003reg.db -f my_header.h'
#    - generator c header file for afe from command line, example:
#       'python gen_test_header.py ..\lh001.db -f my_header.h -afe'
#

import argparse
from datetime import date
from gen_header import GEN_HEADER
from regdb import BIT_VALUE,BIT,REG,MODULE,create_db_app,db
import os


HEADER_DATE = date.today()
HEADER_YEAR = date.today().year
HEADER_COMMENT_SEPERATOR = '######################################################################\n'
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
".format(HEADER_YEAR,HEADER_COMPANY)

class GEN_TEST_HEADER():
    def __init__(self,modules,header_file="Default_python_Header.py",header_type='MCU'):

        if '.py' in header_file:
            self.headerFile = header_file
        else:
            self.headerFile = header_file + '.py'
        self.device_name = os.path.basename(self.headerFile).split('.py')[0].upper()

        self.modules = modules
        self.headerFile=header_file
        self.headerType=header_type
        self.content = "'''\n"
        self.content += HEADER_COMMENT_SEPERATOR
        self.content += HEADER_COPYRIGHT
        self.content += HEADER_COMMENT_SEPERATOR
        self.content += "@file    {0}\n".format(self.device_name+'.py')
        self.content += "@date    {0}\n".format(HEADER_DATE)
        self.content += "\n'''\n"
        self.repeatedModules = dict()


    def genRegAddrDefForAFE(self):
        headerStr = '\n'
        for module in self.modules:
            headerStr += "'''----------------------------------------------------\n"
            headerStr += "Regsiter Address Definition for Module {}\n".format(module.name)
            headerStr += "----------------------------------------------------'''\n"
            def takeAddress(elem):
                return elem.address
            module.regs.sort(key=takeAddress)
            for reg in module.regs:
                headerStr += 'ADDR_{0}_{1:16} = {2}\n'\
                .format(module.name,reg.name,hex(module.address + reg.address))
            headerStr += "\n"
        return headerStr

    def calBitMsk(self,bitPos,bitWidth):
        msk = 0
        for i in range(bitWidth):
            msk |= (1<<(bitPos + i))
        return msk


    def genBitMask(self):
        mskStr = '\n'
        mskStr += "'''****************************************************************************'''\n"
        mskStr += "'''                         Peripheral Registers_Bits_Definition               '''\n"
        mskStr += "'''*****************************************************************************'''\n"
        mskStr = '\n'
        self.repeatedModules = dict()
        for module in self.modules:
            moduleName = module.name.upper()
            print("Bit define for module {}".format(module.name))
            doDefFlag = True
            if module.name[-1].isnumeric():
                moduleName = module.name[:-1]
                if moduleName in self.repeatedModules.keys():
                    self.repeatedModules[moduleName] += 1
                    doDefFlag = False #only define one structure for repeated module
                else:
                    self.repeatedModules[moduleName] = 1
                    doDefFlag = True
            if doDefFlag:
                mskStr += '\n'
                mskStr += '#/******************************************************************************/\n'
                mskStr += '#/*                    {}                         */\n'.format(moduleName)
                mskStr += '#/******************************************************************************/\n'
                mskStr += '\n'
                def takeAddress(elem):
                    return elem.address
                module.regs.sort(key=takeAddress)
                for reg in module.regs:
                    mskStr += '\n'
                    mskStr += "#/******************  Bit Definition for Register {}  *********************/".format(reg.name.upper())
                    mskStr += '\n'
                    regname = reg.name
                    if module.name+'_' in regname:  #remove module name in register name.
                            regname = regname.split(module.name+'_')[-1]
                    for bit in reg.bits:
                        bitname = bit.name
                        if reg.name+'_' in bitname:  #remove register name in bit name. 
                                bitname = bitname.split(reg.name+'_')[-1]
                        mskStr += "{0}_{1}_{2}_Msk   =   0x{3:x}   \n"\
                        .format(moduleName,regname.upper().replace(' ',''),bitname.upper().replace(' ',''),self.calBitMsk(bit.position,bit.width))
                        mskStr += "{0}_{1}_{2}_Pos   =    {3:d}   \n"\
                        .format(moduleName,regname.upper().replace(' ',''),bitname.upper().replace(' ',''),bit.position)
        return mskStr
    
    def genResetValue(self):
        rvStr = '\n'
        rvStr += '#/******************************************************************************/\n'
        rvStr += '#/*                         Register Reset Value                               */\n'
        rvStr += '#/******************************************************************************/\n'
        rvStr = '\n'
        self.repeatedModules = dict()
        for module in self.modules:
            moduleName = module.name.upper()
            print("Reset value for module {}".format(module.name))
            doDefFlag = True
            if module.name[-1].isnumeric():
                moduleName = module.name[:-1]
                if moduleName in self.repeatedModules.keys():
                    self.repeatedModules[moduleName] += 1
                    doDefFlag = False #only define one structure for repeated module
                else:
                    self.repeatedModules[moduleName] = 1
                    doDefFlag = True
            if doDefFlag:
                rvStr += '#\n'
                rvStr += '#/******************************************************************************/\n'
                rvStr += '#/*                    Reset Value for Module {}                            */\n'.format(moduleName)
                rvStr += '#/******************************************************************************/\n'
                rvStr += '#\n'
                def takeAddress(elem):
                    return elem.address
                module.regs.sort(key=takeAddress)
                for reg in module.regs:
                    regname = reg.name
                    if module.name+'_' in regname:  #remove module name in register name.
                            regname = regname.split(module.name+'_')[-1]
                    try:
                        if reg.default_value is None:
                            rvStr += '{0}_{1}_RESET      =       0x{2:x}\n'\
                                .format(moduleName,regname.upper(),0)
                        else:
                            rvStr += '{0}_{1}_RESET       =      0x{2:x}\n'\
                                .format(moduleName,regname.upper(),reg.default_value)

                    except:
                        raise Exception("reset value generate failed for register {0}, value:{1}".format(reg.name,reg.default_value))
        return rvStr



    def run(self):
        if self.headerType == "MCU":
            self.content += self.genResetValue()
            self.content += self.genBitMask()
            self.content += self.genRegAddrDefForAFE()
        elif self.headerType == "AFE":
            for module in self.modules:
                print("process module {}".format(module.name))
                self.content += self.genRegAddrDefForAFE(module)
        else:
            raise Exception("header type not support, MCU or AFE")
        with open(self.headerFile,'w',encoding='utf-8') as f:
            f.write(self.content)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="C header generator")
    parser.add_argument('database', action='store', help="Specify register database file")
    parser.add_argument('-f', action='store', help="Specify name of header file",default='Default_Header.h')
    parser.add_argument('-afe', action='store_true', help="Generate header file for AFE or MCU, defualt is MCU if nothing specified")
    cmd = parser.parse_args()
    
    app = create_db_app(cmd.database)
    app.app_context().push()
    modules = MODULE.query.order_by(MODULE.address).all()
    if cmd.afe:
        h = GEN_TEST_HEADER(modules,cmd.f,'AFE')
    else:
        h = GEN_TEST_HEADER(modules,cmd.f,'MCU')
    h.run()


