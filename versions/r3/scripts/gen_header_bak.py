#
# Copyright @  2021  苏州领慧立芯科技有限公司
# 苏州领慧立芯科技有限公司内部保密技术代码， 您需要对代码保密负责， 不得转发给任何外部实体和个人
# Autor: Henry512@legendsemi.com
#
# Usage, 
#    - get help
#       'python gen_header.py -h'
#    - generator c header file for mcu from command line, example:
#       'python gen_header.py ..\lh003reg.db -f my_header.h'
#    - generator c header file for afe from command line, example:
#       'python gen_header.py ..\lh001.db -f my_header.h -afe'
#

import argparse
from datetime import date
#from re import T
from regdb import MODULE,BIT_VALUE,BIT,REG,create_db_app,db
import os


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
".format(HEADER_YEAR,HEADER_COMPANY)

# HEADER_TYPEDEF = '\n#ifdef cplusplus \n\
#     #define __RO volatile  \n\
# #else\n\
#     #define __RO volatile const    //Read Only \n\
# #endif\n\
# #define __WO volatile     //Write Only \n\
# #define __RW volatile     //Read and Write \n\
# '

# RESET_ENABLE_TYPE = 'typedef enum {RESET = 0, SET = !RESET} FlagStatus, ITStatus;\n\
# \n\
# typedef enum {DISABLE = 0, ENABLE = !DISABLE} FunctionalState;\n\
# #define IS_FUNCTIONAL_STATE(STATE) (((STATE) == DISABLE) || ((STATE) == ENABLE))\n\
# \n\
# typedef enum {ERROR = 0, SUCCESS = !ERROR} ErrorStatus;\n\
# \n\
# '

# END_MACRO_FUNC = '#define SET_BIT(REG, BIT)     ((REG) |= (BIT))\n\
# \n\
# #define CLEAR_BIT(REG, BIT)   ((REG) &= ~(BIT))\n\
# \n\
# #define READ_BIT(REG, BIT)    ((REG) & (BIT))\n\
# \n\
# #define CLEAR_REG(REG)        ((REG) = (0x0))\n\
# \n\
# #define WRITE_REG(REG, VAL)   ((REG) = (VAL))\n\
# \n\
# #define READ_REG(REG)         ((REG))\n\
# \n\
# #define MODIFY_REG(REG, CLEARMASK, SETMASK)  WRITE_REG((REG), (((READ_REG(REG)) & (~(CLEARMASK))) | (SETMASK)))\n\
# \n\
# '
# class GEN_HEADER():
#     def __init__(self,modules,header_file="Default_C_Header",header_type='MCU'):

#         if ".h" in header_file:
#             self.headerFile = header_file
#         else:
#             self.headerFile = header_file +'.h'
#         self.device_name = os.path.basename(self.headerFile).split('.h')[0].upper()

#         self.header_end = "\n#ifdef __cplusplus\n}}\n#endif //__cplusplus\n#endif //__{0}__H\n\n".format(self.device_name)

#         HEADER_START = '\n#ifndef __{0}__H\n#define __{0}__H\n\n#ifdef __cplusplus\nextern \"C\" {{\n#endif\n\n#include <stdint.h>\n#include "{1}_irq.h"\n'.format(self.device_name,self.device_name.lower())

#         self.modules = modules
#         self.headerType=header_type
#         self.content = '/*\n'
#         self.content += HEADER_COMMENT_SEPERATOR
#         self.content += HEADER_COPYRIGHT
#         self.content += HEADER_COMMENT_SEPERATOR
#         self.content += "@file    {0}\n".format(self.device_name+'.h')
#         self.content += "@date    {0}\n".format(HEADER_DATE)
#         self.content += '\n*/\n'
#         self.content += HEADER_START
#         self.content += HEADER_TYPEDEF
#         self.content += RESET_ENABLE_TYPE


#     def genRegAddrDefForAFE(self):
#         headerStr = '\n'
#         for module in self.modules:
#             headerStr += "/*----------------------------------------------------\n"
#             headerStr += "*Regsiter Address Definition for Module {}\n".format(module.name)
#             headerStr += "*----------------------------------------------------*/\n"
#             def takeAddress(elem):
#                 return elem.address
#             module.regs.sort(key=takeAddress)
#             for reg in module.regs:
#                 if '[' in reg.name:
#                             elems = reg.name.split('[')
#                             regname = elems[0]
#                             if ':' in elems[-1]:
#                                 num = elems[-1].split(':')
#                                 num_s = int(num[0])
#                                 num_e = int(num[-1].strip(']'))
#                                 if num_s > num_e:
#                                     t = num_e;num_e = num_s;num_s = t; 
#                                 for i in range(num_s,num_e+1):
#                                     widthByte =  ((reg.width-1)//8) +1
#                                     headerStr += '#define ADDR_{0}_{1:16}  {2}\n'\
#                                     .format(module.name,regname+str(i),hex(module.address + reg.address+widthByte*i))
#                 else:
#                     headerStr += '#define ADDR_{0}_{1:16}  {2}\n'\
#                     .format(module.name,reg.name,hex(module.address + reg.address))
#             headerStr += "\n"
#         return headerStr

#     def width2type(self,width):
#         if width <= 8:
#             return 'uint8_t'
#         elif width <= 16:
#             return 'uint16_t'
#         elif width <= 32:
#             return 'uint32_t'

#     def reserveByteNum(self,addr,preAddr,prewidthByte):
#         padAddr = addr - preAddr - prewidthByte
#         return padAddr

#     def getRepeatedModuleList(self):
#         repeatMlist = []
#         repeatModules = dict()
#         for module in self.modules:
#             if module.name[-1].isnumeric():
#                 moduleName = module.name[:-1]
#                 if moduleName in repeatModules.keys():
#                     repeatModules[moduleName] += [module]
#                 else:
#                     repeatModules[moduleName] = [module]
#         for m in repeatModules.keys():
#             ms = repeatModules[m]
#             max = 0
#             max_m = None
#             for same_m in ms:
#                 if len(same_m.regs) > max:
#                     max = len(same_m.regs)
#                     max_m = same_m      #find the longest module to represent the repeated modules
#             repeatMlist.append(max_m)
#         return repeatMlist


#     def genRegAddrDefForMCU(self):
#         headerStr = ''
#         repeatModuleList = self.getRepeatedModuleList()
#         for module in self.modules:
#             moduleName = module.name.upper()
#             print("register structure define for module {}".format(module.name))
#             doDefFlag = True
#             if module.name[-1].isnumeric():
#                 if module in repeatModuleList:
#                     doDefFlag = True
#                     moduleName = module.name[:-1]
#                 else:
#                     doDefFlag = False
                
#             if doDefFlag:        
#                 headerStr += "//----------------------------------------------------\n"
#                 headerStr += "//Regsiter Structure Definition for Module {}\n".format(module.name)
#                 headerStr += "//----------------------------------------------------\n"
#                 headerStr += 'typedef struct\n{\n'
#                 preAddr = 0
#                 prewidthByte = 0
#                 reservedCnt = 0
#                 def takeAddress(elem):
#                     return elem.address
#                 module.regs.sort(key=takeAddress)   #sort register in address order
#                 for reg in module.regs:
#                     regType = '__RW'
#                     if reg.access == 'W(WriteOnly)':
#                         regType = "__WO"
#                     elif reg.access == 'RW' or reg.access=='RC(readclear)'\
#                         or reg.access=='W1C(Write1/auto-clear 0)' or reg.access=='W0S(Write0/auto-set1)'\
#                             or reg.access=='W1(WriteOnce)' or reg.access=='WRS(WR/hardware update)':
#                         regType = '__RW'
#                     elif reg.access == 'R(ReadOnly)':
#                         regType = '__RO'
#                     else:
#                         pass #keep RW access
#                         #raise Exception("Access Type not supported for register {0}".format(reg.name))
#                     #print("preAddr:0x{:x}".format(preAddr))
#                     #print("reg address:0x{:x}".format(reg.address))
#                     if reg.address - preAddr != 0 or preAddr==0:
#                         n = self.reserveByteNum(reg.address,preAddr,prewidthByte)
#                         if n != 0:
#                             headerStr += "    __RO uint8_t RESERVED{0}[{1}];\n".format(reservedCnt,n)
#                             reservedCnt += 1
#                         if '[' in reg.name:
#                             elems = reg.name.split('[')
#                             regname = elems[0]
#                             if ':' in elems[-1]:
#                                 num = elems[-1].split(':')
#                                 num_s = int(num[0])
#                                 num_e = int(num[-1].strip(']'))
#                                 if num_s > num_e:
#                                     t = num_e;num_e = num_s;num_s = t; 
#                                 for i in range(num_s,num_e+1):
#                                     if module.name+'_' in regname:  #remove module name in register name. e.x RCC->RCC_CON -> RCC->CON 
#                                         regname = regname.split(module.name+'_')[-1]
#                                     headerStr += "    {0} {1} {2};                /*!<{3}*/\n".format(regType,self.width2type(reg.width),regname.upper()+str(i),reg.desc)
#                                 prewidthByte =  ((reg.width-1)//8) +1
#                                 preAddr = reg.address+prewidthByte*num_e
#                         else:
#                             regname = reg.name
#                             if module.name+'_' in regname:  #remove module name in register name. e.x RCC->RCC_CON -> RCC->CON 
#                                 regname = regname.split(module.name+'_')[-1]
#                             headerStr += "    {0} {1} {2};                /*!<{3}*/\n".format(regType,self.width2type(reg.width),regname.upper(),reg.desc)
#                             preAddr = reg.address
#                             prewidthByte =  ((reg.width-1)//8) +1
#                     else:   #same address register
#                         if preAddr != 0:
#                             preAddr = reg.address
#                             prewidthByte =  ((reg.width-1)//8) +1
#                             continue
#                 headerStr += "}}{0}_TypeDef;\n".format(moduleName)
#         return headerStr


#     def genBaseAddrForMCU(self):
#         baseAdrStr = "\n"
#         for module in self.modules:
#             baseAdrStr += '#define {0}_BASE               ((uint32_t)0x{1:x})    /*{2}*/'.format(module.name.upper(), module.address,module.desc)
#             baseAdrStr += '\n'
#             #print("base address define for module {}".format(module.name))
#         return baseAdrStr

#     def genPeriDeclarForMCU(self):
#         #peripheral definition
#         periDecStr = '\n'
#         for module in self.modules:
#             structName = module.name.upper()
#             #print("register define for module {}".format(module.name))
#             if module.name[-1].isnumeric():
#                 structName = module.name[:-1]
#             periDecStr += '#define p{0}               (({1}_TypeDef *){0}_BASE)\n'.format(module.name.upper(),structName)
#         return periDecStr

#     def calBitMsk(self,bitPos,bitWidth):
#         msk = 0
#         for i in range(bitWidth):
#             msk |= (1<<(bitPos + i))
#         return msk


#     def genBitMask(self):
#         mskStr = '\n'
#         mskStr += '/******************************************************************************/\n'
#         mskStr += '/*                         Peripheral Registers_Bits_Definition               */\n'
#         mskStr += '/******************************************************************************/\n'
#         mskStr = '\n'
#         repeatModuleList = self.getRepeatedModuleList()
#         for module in self.modules:
#             moduleName = module.name.upper()
#             #print("Bit define for module {}".format(module.name))
#             doDefFlag = True
#             if module.name[-1].isnumeric():
#                 if module in repeatModuleList:
#                     doDefFlag = True
#                     moduleName = module.name[:-1]
#                 else:
#                     doDefFlag = False
#             if doDefFlag:
#                 mskStr += '\n'
#                 mskStr += '/******************************************************************************/\n'
#                 mskStr += '/*                    {}                         */\n'.format(moduleName)
#                 mskStr += '/******************************************************************************/\n'
#                 mskStr += '\n'
#                 def takeAddress(elem):
#                     return elem.address
#                 module.regs.sort(key=takeAddress)
#                 for reg in module.regs:
#                     mskStr += '\n'
#                     mskStr += "/******************  Bit Definition for Register {}  *********************/".format(reg.name.upper())
#                     mskStr += '\n'
#                     regname = reg.name
#                     if '[' in reg.name:
#                         elems = reg.name.split('[')
#                         regname = elems[0]
#                     if module.name+'_' in regname:  #remove module name in register name.
#                             regname = regname.split(module.name+'_')[-1]
#                     for bit in reg.bits:
#                         bitname = bit.name
#                         if reg.name+'_' in bitname:  #remove register name in bit name. 
#                                 bitname = bitname.split(reg.name+'_')[-1]
#                         mskStr += '#define {0}_{1}_{2}_Msk             ((uint32_t)0x{3:x})   /* bit mask, {4}*/\n'\
#                         .format(moduleName,regname.upper(),bitname.upper().replace(" ",""),self.calBitMsk(bit.position,bit.width),bit.doc)
#                         mskStr += '#define {0}_{1}_{2}_Pos             ((uint32_t){3:d})   /*bit position, {4}*/\n'\
#                         .format(moduleName,regname.upper(),bitname.upper().replace(" ",""),bit.position,bit.doc)
#         return mskStr
    
#     def genResetValue(self):
#         rvStr = '\n'
#         rvStr += '/******************************************************************************/\n'
#         rvStr += '/*                         Register Reset Value                               */\n'
#         rvStr += '/******************************************************************************/\n'
#         rvStr = '\n'
#         repeatModuleList = self.getRepeatedModuleList()
#         for module in self.modules:
#             moduleName = module.name.upper()
#             #print("Reset value for module {}".format(module.name))
#             doDefFlag = True
#             if module.name[-1].isnumeric():
#                 if module in repeatModuleList:
#                     doDefFlag = True
#                     moduleName = module.name[:-1]
#                 else:
#                     doDefFlag = False
#             if doDefFlag:
#                 rvStr += '\n'
#                 rvStr += '/******************************************************************************/\n'
#                 rvStr += '/*                    Reset Value for Module {}                            */\n'.format(moduleName)
#                 rvStr += '/******************************************************************************/\n'
#                 rvStr += '\n'
#                 def takeAddress(elem):
#                     return elem.address
#                 module.regs.sort(key=takeAddress)
#                 for reg in module.regs:
#                     regname = reg.name
#                     if '[' in reg.name:
#                         elems = reg.name.split('[')
#                         regname = elems[0]
#                     if module.name+'_' in regname:  #remove module name in register name.
#                             regname = regname.split(module.name+'_')[-1]
#                     try:
#                         if reg.default_value is None:
#                             rvStr += '#define {0}_{1}_RESET             ((uint32_t)0x{2:x})\n'\
#                                 .format(moduleName,regname.upper(),0)
#                         else:
#                             rvStr += '#define {0}_{1}_RESET             ((uint32_t)0x{2:x})\n'\
#                                 .format(moduleName,regname.upper(),reg.default_value)

#                     except:
#                         raise Exception("reset value generate failed for register {0}, value:{1}".format(reg.name,reg.default_value))
#         return rvStr


#     def genIRQn(self):
#         irqNumStr = ""
#         startStr = '\n/**\n\
#     * @brief  Interrupt Number Definition.\n\
#     *\n\
#     */\n\
#     typedef enum IRQn\n\
#     {\n\
#         /************ Cortex Core Processor Exceptions Number  **********/\n\
#         NonMaskableInt_IRQn         = -14,    /*!< 2 Non Maskable Interrupt                                          */\n\
#         MemoryManagement_IRQn       = -12,    /*!< 4 Cortex-M4 Memory Management Interrupt                           */\n\
#         BusFault_IRQn               = -11,    /*!< 5 Cortex-M4 Bus Fault Interrupt                                   */\n\
#         UsageFault_IRQn             = -10,    /*!< 6 Cortex-M4 Usage Fault Interrupt                                 */\n\
#         SVCall_IRQn                 = -5,     /*!< 11 Cortex-M4 SV Call Interrupt                                    */\n\
#         DebugMonitor_IRQn           = -4,     /*!< 12 Cortex-M4 Debug Monitor Interrupt                              */\n\
#         PendSV_IRQn                 = -2,     /*!< 14 Cortex-M4 Pend SV Interrupt                                    */\n\
#         SysTick_IRQn                = -1,     /*!< 15 Cortex-M4 System Tick Interrupt                                */\n\
#         /******  Device specific Interrupt Numbers **********************************************************************/\n\
#     \
#     '
#         endStr = '}IRQn_Type;\n'
#         moduleStr = ""  #fix me! add peripheral interrupt number
#         irqNumStr += startStr + moduleStr+ endStr
#         return irqNumStr
        

#     def run(self):
#         if self.headerType == "MCU":
#             #self.content += self.genIRQn()
#             self.content += self.genRegAddrDefForMCU()
#             self.content += self.genBaseAddrForMCU()
#             self.content += self.genPeriDeclarForMCU()
#             self.content += self.genResetValue()
#             self.content += self.genBitMask()
#             self.content += self.genRegAddrDefForAFE()
#         elif self.headerType == "AFE":
#             for module in self.modules:
#                 print("process module {}".format(module.name))
#                 self.content += self.genRegAddrDefForAFE(module)
#         else:
#             raise Exception("header type not support, MCU or AFE")
#         self.content += END_MACRO_FUNC
#         self.content += self.header_end
#         with open(self.headerFile,'w',encoding='utf-8') as f:
#             f.write(self.content)





HEADER_TYPEDEF = '\n#ifdef cplusplus \n\
    #define __RO volatile  \n\
#else\n\
    #define __RO volatile const    //Read Only \n\
#endif\n\
#define __WO volatile     //Write Only \n\
#define __RW volatile     //Read and Write \n\
'

RESET_ENABLE_TYPE = 'typedef enum {RESET = 0, SET = !RESET} FlagStatus, ITStatus;\n\
\n\
typedef enum {DISABLE = 0, ENABLE = !DISABLE} FunctionalState;\n\
#define IS_FUNCTIONAL_STATE(STATE) (((STATE) == DISABLE) || ((STATE) == ENABLE))\n\
\n\
typedef enum {ERROR = 0, SUCCESS = !ERROR} ErrorStatus;\n\
\n\
'

END_MACRO_FUNC = '#define SET_BIT(REG, BIT)     ((REG) |= (BIT))\n\
\n\
#define CLEAR_BIT(REG, BIT)   ((REG) &= ~(BIT))\n\
\n\
#define READ_BIT(REG, BIT)    ((REG) & (BIT))\n\
\n\
#define CLEAR_REG(REG)        ((REG) = (0x0))\n\
\n\
#define WRITE_REG(REG, VAL)   ((REG) = (VAL))\n\
\n\
#define READ_REG(REG)         ((REG))\n\
\n\
#define MODIFY_REG(REG, CLEARMASK, SETMASK)  WRITE_REG((REG), (((READ_REG(REG)) & (~(CLEARMASK))) | (SETMASK)))\n\
\n\
'
class GEN_HEADER():
    def __init__(self,modules,header_file="Default_C_Header",header_type='MCU'):

        if ".h" in header_file:
            self.headerFile = header_file
        else:
            self.headerFile = header_file +'.h'
        self.device_name = os.path.basename(self.headerFile).split('.h')[0].upper()

        self.header_end = "\n#ifdef __cplusplus\n}}\n#endif //__cplusplus\n#endif //__{0}__H\n\n".format(self.device_name)

        HEADER_START = '\n#ifndef __{0}__H\n#define __{0}__H\n\n#ifdef __cplusplus\nextern \"C\" {{\n#endif\n\n#include <stdint.h>\n#include "{1}_irq.h"\n'.format(self.device_name,self.device_name.lower())

        self.modules = modules
        self.headerType=header_type
        self.content = '/*\n'
        self.content += HEADER_COMMENT_SEPERATOR
        self.content += HEADER_COPYRIGHT
        self.content += HEADER_COMMENT_SEPERATOR
        self.content += "@file    {0}\n".format(self.device_name+'.h')
        self.content += "@date    {0}\n".format(HEADER_DATE)
        self.content += '\n*/\n'
        self.content += HEADER_START
        self.content += HEADER_TYPEDEF
        self.content += RESET_ENABLE_TYPE


    def genRegAddrDefForAFE(self):
        headerStr = '\n'
        for module in self.modules:
            headerStr += "/*----------------------------------------------------\n"
            headerStr += "*Regsiter Address Definition for Module {}\n".format(module.name)
            headerStr += "*----------------------------------------------------*/\n"
            def takeAddress(elem):
                return elem.address
            module.regs.sort(key=takeAddress)
            for reg in module.regs:
                if not reg.visibility:  # 检查寄存器可见性
                    continue
                if '[' in reg.name:
                            elems = reg.name.split('[')
                            regname = elems[0]
                            if ':' in elems[-1]:
                                num = elems[-1].split(':')
                                num_s = int(num[0])
                                num_e = int(num[-1].strip(']'))
                                if num_s > num_e:
                                    t = num_e;num_e = num_s;num_s = t; 
                                for i in range(num_s,num_e+1):
                                    widthByte =  ((reg.width-1)//8) +1
                                    headerStr += '#define ADDR_{0}_{1:16}  {2}\n'\
                                    .format(module.name,regname+str(i),hex(module.address + reg.address+widthByte*i))
                else:
                    headerStr += '#define ADDR_{0}_{1:16}  {2}\n'\
                    .format(module.name,reg.name,hex(module.address + reg.address))
            headerStr += "\n"
        return headerStr

    def width2type(self,width):
        if width <= 8:
            return 'uint8_t'
        elif width <= 16:
            return 'uint16_t'
        elif width <= 32:
            return 'uint32_t'

    def reserveByteNum(self,addr,preAddr,prewidthByte):
        padAddr = addr - preAddr - prewidthByte
        return padAddr

    def getRepeatedModuleList(self):
        repeatMlist = []
        repeatModules = dict()
        for module in self.modules:
            if module.name[-1].isnumeric():
                moduleName = module.name[:-1]
                if moduleName in repeatModules.keys():
                    repeatModules[moduleName] += [module]
                else:
                    repeatModules[moduleName] = [module]
        for m in repeatModules.keys():
            ms = repeatModules[m]
            max = 0
            max_m = None
            for same_m in ms:
                if len(same_m.regs) > max:
                    max = len(same_m.regs)
                    max_m = same_m      #find the longest module to represent the repeated modules
            repeatMlist.append(max_m)
        return repeatMlist


    def genRegAddrDefForMCU(self):
        headerStr = ''
        repeatModuleList = self.getRepeatedModuleList()
        for module in self.modules:
            moduleName = module.name.upper()
            print("register structure define for module {}".format(module.name))
            doDefFlag = True
            if module.name[-1].isnumeric():
                if module in repeatModuleList:
                    doDefFlag = True
                    moduleName = module.name[:-1]
                else:
                    doDefFlag = False
                
            if doDefFlag:        
                headerStr += "//----------------------------------------------------\n"
                headerStr += "//Regsiter Structure Definition for Module {}\n".format(module.name)
                headerStr += "//----------------------------------------------------\n"
                headerStr += 'typedef struct\n{\n'
                preAddr = 0
                prewidthByte = 0
                reservedCnt = 0
                def takeAddress(elem):
                    return elem.address
                module.regs.sort(key=takeAddress)   #sort register in address order
                for reg in module.regs:
                    if not reg.visibility:  # 检查寄存器可见性
                        continue
                        
                    regType = '__RW'
                    if reg.access == 'W(WriteOnly)':
                        regType = "__WO"
                    elif reg.access == 'RW' or reg.access=='RC(readclear)'\
                        or reg.access=='W1C(Write1/auto-clear 0)' or reg.access=='W0S(Write0/auto-set1)'\
                            or reg.access=='W1(WriteOnce)' or reg.access=='WRS(WR/hardware update)':
                        regType = '__RW'
                    elif reg.access == 'R(ReadOnly)':
                        regType = '__RO'
                    else:
                        pass #keep RW access
                        #raise Exception("Access Type not supported for register {0}".format(reg.name))
                    #print("preAddr:0x{:x}".format(preAddr))
                    #print("reg address:0x{:x}".format(reg.address))
                    if reg.address - preAddr != 0 or preAddr==0:
                        n = self.reserveByteNum(reg.address,preAddr,prewidthByte)
                        if n != 0:
                            headerStr += "    __RO uint8_t RESERVED{0}[{1}];\n".format(reservedCnt,n)
                            reservedCnt += 1
                        if '[' in reg.name:
                            elems = reg.name.split('[')
                            regname = elems[0]
                            if ':' in elems[-1]:
                                num = elems[-1].split(':')
                                num_s = int(num[0])
                                num_e = int(num[-1].strip(']'))
                                if num_s > num_e:
                                    t = num_e;num_e = num_s;num_s = t; 
                                for i in range(num_s,num_e+1):
                                    if module.name+'_' in regname:  #remove module name in register name. e.x RCC->RCC_CON -> RCC->CON 
                                        regname = regname.split(module.name+'_')[-1]
                                    headerStr += "    {0} {1} {2};                /*!<{3}*/\n".format(regType,self.width2type(reg.width),regname.upper()+str(i),reg.desc)
                                prewidthByte =  ((reg.width-1)//8) +1
                                preAddr = reg.address+prewidthByte*num_e
                        else:
                            regname = reg.name
                            if module.name+'_' in regname:  #remove module name in register name. e.x RCC->RCC_CON -> RCC->CON 
                                regname = regname.split(module.name+'_')[-1]
                            headerStr += "    {0} {1} {2};                /*!<{3}*/\n".format(regType,self.width2type(reg.width),regname.upper(),reg.desc)
                            preAddr = reg.address
                            prewidthByte =  ((reg.width-1)//8) +1
                    else:   #same address register
                        if preAddr != 0:
                            preAddr = reg.address
                            prewidthByte =  ((reg.width-1)//8) +1
                            continue
                headerStr += "}}{0}_TypeDef;\n".format(moduleName)
        return headerStr


    def genBaseAddrForMCU(self):
        baseAdrStr = "\n"
        for module in self.modules:
            baseAdrStr += '#define {0}_BASE               ((uint32_t)0x{1:x})    /*{2}*/'.format(module.name.upper(), module.address,module.desc)
            baseAdrStr += '\n'
            #print("base address define for module {}".format(module.name))
        return baseAdrStr

    def genPeriDeclarForMCU(self):
        #peripheral definition
        periDecStr = '\n'
        for module in self.modules:
            structName = module.name.upper()
            #print("register define for module {}".format(module.name))
            if module.name[-1].isnumeric():
                structName = module.name[:-1]
            periDecStr += '#define p{0}               (({1}_TypeDef *){0}_BASE)\n'.format(module.name.upper(),structName)
        return periDecStr

    def calBitMsk(self,bitPos,bitWidth):
        msk = 0
        for i in range(bitWidth):
            msk |= (1<<(bitPos + i))
        return msk


    def genBitMask(self):
        mskStr = '\n'
        mskStr += '/******************************************************************************/\n'
        mskStr += '/*                         Peripheral Registers_Bits_Definition               */\n'
        mskStr += '/******************************************************************************/\n'
        mskStr = '\n'
        repeatModuleList = self.getRepeatedModuleList()
        for module in self.modules:
            moduleName = module.name.upper()
            #print("Bit define for module {}".format(module.name))
            doDefFlag = True
            if module.name[-1].isnumeric():
                if module in repeatModuleList:
                    doDefFlag = True
                    moduleName = module.name[:-1]
                else:
                    doDefFlag = False
            if doDefFlag:
                mskStr += '\n'
                mskStr += '/******************************************************************************/\n'
                mskStr += '/*                    {}                         */\n'.format(moduleName)
                mskStr += '/******************************************************************************}/\n'
                mskStr += '\n'
                def takeAddress(elem):
                    return elem.address
                module.regs.sort(key=takeAddress)
                for reg in module.regs:
                    if not reg.visibility:  # 检查寄存器可见性
                        continue
                        
                    # 检查该寄存器是否有可见的bit位
                    has_visible_bits = any(bit.visibility for bit in reg.bits)
                    if not has_visible_bits:
                        continue
                        
                    mskStr += '\n'
                    mskStr += "/******************  Bit Definition for Register {}  *********************/".format(reg.name.upper())
                    mskStr += '\n'
                    regname = reg.name
                    if '[' in reg.name:
                        elems = reg.name.split('[')
                        regname = elems[0]
                    if module.name+'_' in regname:  #remove module name in register name.
                            regname = regname.split(module.name+'_')[-1]

                    for bit in reg.bits:
                        # 首先打印调试信息
                        print(f"[Debug] Bit name: {bit.name}, visibility: {bit.visibility}, type: {type(bit.visibility)}")
                        
                        # 确保visibility是整数类型
                        visibility = int(bit.visibility) if hasattr(bit, 'visibility') else 1  # 默认为可见
                        
                        # 明确的可见性检查
                        if visibility == 0:  # 明确检查等于0
                            print(f"[Debug] Skipping bit {bit.name} because visibility is 0")
                            continue
                        
                        print(f"[Debug] Processing bit {bit.name}")    
                        bitname = bit.name
                        if reg.name+'_' in bitname:  # remove register name in bit name
                            bitname = bitname.split(reg.name+'_')[-1]
                        
                        mskStr += '#define {0}_{1}_{2}_Msk             ((uint32_t)0x{3:x})   /* bit mask, {4}*/\n'\
                            .format(moduleName, regname.upper(), bitname.upper().replace(" ",""), 
                                    self.calBitMsk(bit.position, bit.width), bit.doc)
                        mskStr += '#define {0}_{1}_{2}_Pos             ((uint32_t){3:d})   /*bit position, {4}*/\n'\
                            .format(moduleName, regname.upper(), bitname.upper().replace(" ",""), 
                                    bit.position, bit.doc)
        return mskStr
    
    def genResetValue(self):
        rvStr = '\n'
        rvStr += '/******************************************************************************/\n'
        rvStr += '/*                         Register Reset Value                               */\n'
        rvStr += '/******************************************************************************/\n'
        rvStr = '\n'
        repeatModuleList = self.getRepeatedModuleList()
        for module in self.modules:
            moduleName = module.name.upper()
            #print("Reset value for module {}".format(module.name))
            doDefFlag = True
            if module.name[-1].isnumeric():
                if module in repeatModuleList:
                    doDefFlag = True
                    moduleName = module.name[:-1]
                else:
                    doDefFlag = False
            if doDefFlag:
                rvStr += '\n'
                rvStr += '/******************************************************************************/\n'
                rvStr += '/*                    Reset Value for Module {}                            */\n'.format(moduleName)
                rvStr += '/******************************************************************************/\n'
                rvStr += '\n'
                def takeAddress(elem):
                    return elem.address
                module.regs.sort(key=takeAddress)
                for reg in module.regs:
                    if not reg.visibility:  # 检查寄存器可见性
                        continue
                        
                    regname = reg.name
                    if '[' in reg.name:
                        elems = reg.name.split('[')
                        regname = elems[0]
                    if module.name+'_' in regname:  #remove module name in register name.
                            regname = regname.split(module.name+'_')[-1]
                    try:
                        if reg.default_value is None:
                            rvStr += '#define {0}_{1}_RESET             ((uint32_t)0x{2:x})\n'\
                                .format(moduleName,regname.upper(),0)
                        else:
                            rvStr += '#define {0}_{1}_RESET             ((uint32_t)0x{2:x})\n'\
                                .format(moduleName,regname.upper(),reg.default_value)

                    except:
                        raise Exception("reset value generate failed for register {0}, value:{1}".format(reg.name,reg.default_value))
        return rvStr


    def genIRQn(self):
        irqNumStr = ""
        startStr = '\n/**\n\
    * @brief  Interrupt Number Definition.\n\
    *\n\
    */\n\
    typedef enum IRQn\n\
    {\n\
        /************ Cortex Core Processor Exceptions Number  **********/\n\
        NonMaskableInt_IRQn         = -14,    /*!< 2 Non Maskable Interrupt                                          */\n\
        MemoryManagement_IRQn       = -12,    /*!< 4 Cortex-M4 Memory Management Interrupt                           */\n\
        BusFault_IRQn               = -11,    /*!< 5 Cortex-M4 Bus Fault Interrupt                                   */\n\
        UsageFault_IRQn             = -10,    /*!< 6 Cortex-M4 Usage Fault Interrupt                                 */\n\
        SVCall_IRQn                 = -5,     /*!< 11 Cortex-M4 SV Call Interrupt                                    */\n\
        DebugMonitor_IRQn           = -4,     /*!< 12 Cortex-M4 Debug Monitor Interrupt                              */\n\
        PendSV_IRQn                 = -2,     /*!< 14 Cortex-M4 Pend SV Interrupt                                    */\n\
        SysTick_IRQn                = -1,     /*!< 15 Cortex-M4 System Tick Interrupt                                */\n\
        /******  Device specific Interrupt Numbers **********************************************************************/\n\
    \
    '
        endStr = '}IRQn_Type;\n'
        moduleStr = ""  #fix me! add peripheral interrupt number
        irqNumStr += startStr + moduleStr+ endStr
        return irqNumStr
        

    def run(self):
        if self.headerType == "MCU":
            #self.content += self.genIRQn()
            self.content += self.genRegAddrDefForMCU()
            self.content += self.genBaseAddrForMCU()
            self.content += self.genPeriDeclarForMCU()
            self.content += self.genResetValue()
            self.content += self.genBitMask()
            self.content += self.genRegAddrDefForAFE()
        elif self.headerType == "AFE":
            for module in self.modules:
                print("process module {}".format(module.name))
                self.content += self.genRegAddrDefForAFE(module)
        else:
            raise Exception("header type not support, MCU or AFE")
        self.content += END_MACRO_FUNC
        self.content += self.header_end
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
        h = GEN_HEADER(modules,cmd.f,'AFE')
    else:
        h = GEN_HEADER(modules,cmd.f,'MCU')
    h.run()


