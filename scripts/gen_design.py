#
# Copyright @  2021  苏州领慧立芯科技有限公司
# Autor: Henry512@legendsemi.com
#
# Usage, 
#    - get help
#       'python gen_design.py -h'
#    - generate register documentation from command line, example:
#       'python gen_design.py ..\lh003reg.db -f lh003.svd'
#

import argparse
from datetime import date
from regdb import BIT_VALUE,BIT,REG,MODULE,create_db_app,db
import os

CORE_NAME = 'CM0'
CORE_VERSION = 'r1p0'
MPU_PRESENT = 'false'
FPU_PRESENT = 'false'
NVIC_PRIO_BITS = '3'
VENDOR_SYSTICK_CONFIG = 'false'

VERSION = "1.0.0"
HEADER_DATE = date.today()
HEADER_YEAR = date.today().year
HEADER_COMPANY = r"LegendSemi"
HEADER_COPYRIGHT = "<!--Copyright @  {0}  {1}\n\
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
-->\n".format(HEADER_YEAR,HEADER_COMPANY)


class GEN_SVD():
    def __init__(self,modules,filename):
        if '.svd' in filename:
            self.__file = filename
        else:
            self.__file = filename+'.svd'
        self.__modules = modules
        self.__name = os.path.basename(self.__file).split('.svd')[0].upper()
        self.__content = ''

    def run(self):
        self.fileElem()
        self.deviceElem()
        self.cpuElem()
        self.peripheralsElem()
        self.__content += '</device>'
        with open(self.__file,'w',encoding='utf-8') as f:
            f.write(self.__content)

    def fileElem(self):
        self.__content += '<?xml version="1.0" encoding="utf-8"?>\n'
        self.__content += '<!-- File naming: {} -->\n'.format(self.__file)
        self.__content += HEADER_COPYRIGHT
        self.__content += '\n'
    
    def deviceElem(self):
        self.__content += '<device schemaVersion="1.1" xmlns:xs="http://www.w3.org/2001/XMLSchema-instance" xs:noNamespaceSchemaLocation="CMSIS-SVD.xsd" >\n'
        self.__content += '  <vendor>{} Ltd.</vendor> \n'.format(HEADER_COMPANY)
        self.__content += '  <vendorID>LH</vendorID> \n'
        self.__content += '  <name>{}</name> \n'.format(self.__name.replace(" ",""))
        self.__content += '  <series>Controller</series> \n'
        self.__content += '  <version>{}</version> \n'.format(VERSION)
        self.__content += '  <description>ARM 32-bit Cortex Microcontroller based device. </description>\n'
        self.__content += '  <licenseText>\n'
        self.__content += '  {}\n'.format(HEADER_COPYRIGHT)
        self.__content += '  </licenseText>\n'

    def cpuElem(self):
        self.__content += '  <cpu>\n'
        self.__content += '    <name>{}</name>\n'.format(CORE_NAME.replace(" ",""))
        self.__content += '    <revision>{}</revision>\n'.format(CORE_VERSION)
        self.__content += '    <endian>little</endian>\n'
        self.__content += '    <mpuPresent>{}</mpuPresent>\n'.format(MPU_PRESENT)
        self.__content += '    <fpuPresent>{}</fpuPresent>\n'.format(FPU_PRESENT)
        self.__content += '    <nvicPrioBits>{}</nvicPrioBits>\n'.format(NVIC_PRIO_BITS)
        self.__content += '    <vendorSystickConfig>{}</vendorSystickConfig>\n'.format(VENDOR_SYSTICK_CONFIG)
        self.__content += '  </cpu>\n'
        self.__content += '  <addressUnitBits>8</addressUnitBits>                            <!-- byte addressable memory -->\n'
        self.__content += '  <width>32</width>                                               <!-- bus width is 32 bits -->\n'
        self.__content += '  <!-- default settings implicitly inherited by subsequent sections -->\n'
        self.__content += '  <size>32</size>                                                 <!-- this is the default size (number of bits) of all peripherals\n'
        self.__content += '                                                                       and register that do not define "size" themselves -->\n'
        self.__content += '  <access>read-write</access>                                     <!-- default access permission for all subsequent registers -->\n'
        self.__content += '  <resetValue>0x00000000</resetValue>                             <!-- by default all bits of the registers are initialized to 0 on reset -->\n'
        self.__content += '  <resetMask>0xFFFFFFFF</resetMask>                               <!-- by default all 32Bits of the registers are used -->\n'

    def peripheralsElem(self):
        self.__content += '  <peripherals>\n'
        for m in self.__modules:
            f_regs = REG.query.filter_by(module_id=m.id).order_by(REG.address).all()
            block_size = f_regs[-1].address - f_regs[0].address +4
            self.__content += '    <!-- {} -->\n'.format(m.name.upper())
            self.__content += '    <peripheral>\n'
            self.__content += '      <name>{}</name>\n'.format(m.name.upper().replace(" ",""))
            self.__content += '      <version>1.0</version>\n'.format(m.name.upper())
            self.__content += '      <description> module {} </description>\n'.format(m.name.upper())
            self.__content += '      <groupName>{}</groupName>\n'.format(self.__name)
            self.__content += '      <baseAddress>{}</baseAddress>\n'.format(m.address)
            self.__content += '      <size>32</size>\n'
            self.__content += '      <access>read-write</access>\n'
            self.__content += '\n'
            self.__content += '    <addressBlock>\n'            
            self.__content += '      <offset>0</offset>\n'            
            #self.__content += '      <size>{}</size>\n'.format(m.regs[-1].address - m.regs[0].address +4)           
            self.__content += '      <size>{}</size>\n'.format(block_size)           
            self.__content += '      <usage>registers</usage>\n'            
            self.__content += '    </addressBlock>\n'            
            self.__content += '\n'
            self.registerElem(m)
            self.__content += '    </peripheral>\n'
            self.__content += '\n'
        self.__content += '  </peripherals>\n'
             
            #address block TBD
            #interrupt TBD

    def registerElem(self,module):
        self.__content += '\n'
        self.__content += '      <registers>\n'
        for r in module.regs:
            if 'RESERVED' not in r.name:
                self.__content += '        <!-- {0} -->\n'.format(r.name)
                self.__content += '        <register>\n'
                self.__content += '          <name>{}</name>\n'.format(r.name.replace(" ",""))
                self.__content += '          <description>{}</description>\n'.format(module.name.upper()+r.name.upper())
                self.__content += '          <addressOffset>{}</addressOffset>\n'.format(r.address)
                self.__content += '          <size>32</size>\n'
                #self.__content += '          <access>{}</access>\n'.format(r.access)
                self.__content += '          <access>read-write</access>\n'
                self.__content += '          <resetValue>{}</resetValue>\n'.format(r.default_value)
                self.__content += '          <resetMask>0xFFFFFFFF</resetMask>\n'
                self.__content += '\n'
                self.bitElem(r)
                self.__content += '        </register>\n'
                self.__content += '\n'
        self.__content += '      </registers>\n'
        self.__content += '\n'
        

    def bitElem(self,reg):
        self.__content += '\n'
        self.__content += '          <fields>\n'
        for b in reg.bits:
            if 'RESERVED' not in b.name:
                self.__content += '            <!-- {0} -->\n'.format(b.name)
                self.__content += '            <field>\n'
                self.__content += '              <name>{}</name>\n'.format(b.name.replace(" ",""))
                self.__content += '              <description>{}</description>\n'.format(reg.name.upper()+b.name.upper())
                self.__content += '              <bitRange>[{1}:{0}]</bitRange>\n'.format(b.position,b.position+b.width-1)
                #self.__content += '              <access>{}</access>\n'.format(b.access)
                self.__content += '              <access>read-write</access>\n'
                self.__content += '            </field>\n'
                self.__content += '            \n'
        self.__content += '          </fields>\n'
        




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="KEIL svd debug file generator")
    parser.add_argument('database', action='store', help="Specify register database file")
    parser.add_argument('-f', action='store', help="Specify name of SVD file",default='Default_SVD.h')
    cmd = parser.parse_args()
    
    app = create_db_app(cmd.database)
    app.app_context().push()
    modules = MODULE.query.order_by(MODULE.address).all()
    h = GEN_SVD(modules,cmd.f)
    h.run()