from hardware import *
from so import *
import log


##
##  MAIN 
##

if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(32)

    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel(SchedulerFIFO())

    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ##################
    prg1 = Program("prg1",[ASM.CPU(2), ASM.IO(), ASM.CPU(3), ASM.IO(), ASM.CPU(2)])
    prg2 = Program("prg2",[ASM.CPU(7)])
    prg3 = Program("prg3",[ASM.CPU(4), ASM.IO(), ASM.CPU(1)])

    kernel.fileSystem.write("C:/prg1.exe", prg1)
    kernel.fileSystem.write("C:/prg2.exe", prg2)
    kernel.fileSystem.write("C:/prg3.exe", prg3)

    # execute all programs "concurrently"
    kernel.run("C:/prg1.exe", 0)
    kernel.run("C:/prg2.exe", 2)
    kernel.run("C:/prg3.exe", 1)




