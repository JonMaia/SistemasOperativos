#!/usr/bin/env python

from hardware import *
import log



## emulates a compiled program
class Program():

    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController():

    def __init__(self, device):
        self._device = device
        self._waiting_queue = []
        self._currentPCB = None

    def runOperation(self, pcb, instruction):
        pair = {'pcb': pcb, 'instruction': instruction}
        # append: adds the element at the end of the queue
        self._waiting_queue.append(pair)
        # try to send the instruction to hardware's device (if is idle)
        self.__load_from_waiting_queue_if_apply()

    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        self.__load_from_waiting_queue_if_apply()
        return finishedPCB

    def __load_from_waiting_queue_if_apply(self):
        if (len(self._waiting_queue) > 0) and self._device.is_idle:
            ## pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)
            #print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)


    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)

## emulates the  Interruptions Handlers
class AbstractInterruptionHandler():
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq0):
    pcbActual = pcbTable.running

    Dispatcher.save(pcbActual)
    pcbActual.state = "Terminated"
    pcbTable.running = None


    log.logger.info(" Program Finished ")
     
    

    if (len(kernel.readyQueue) != 0 ):
        pcbTable.running = pcbTable.listaDePCB[0]

        Kernel.readyQueue.remove( ((pcbTable.listaDePCB[0]).pid)  ) """Lo saco de la ready Queue"""

        pcbActual = pcbTable.running  
        Dispatcher.load(pcbActual)
        pcbActual.state = "Running"





class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        pcb = {'pc': HARDWARE.cpu.pc} # porque hacemos esto ???
        HARDWARE.cpu.pc = -1   ## dejamos el CPU IDLE
        self.kernel.ioDeviceController.runOperation(pcb, operation)
        log.logger.info(self.kernel.ioDeviceController)


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        HARDWARE.cpu.pc = pcb['pc']
        log.logger.info(self.kernel.ioDeviceController)


class NewInterruptionHandler(AbstractInterruptionHandler):


    def execute(self, irq0):

        


# emulates the core of an Operative System
class Kernel():

    def __init__(self):
        ## setup interruption handlers
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)


        self.readyQueue = []

        loader = Loader()

        pcbTable = PCBTable()

        Dispatcher = Dispatcher()

        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)


    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    ## emulates a "system call" for programs execution
    def run(self, program):
        self.loader.load(program)
        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

        # set CPU program counter at program's first intruction
        HARDWARE.cpu.pc = 0


    def __repr__(self):
        return "Kernel "


class Loader():

    def __init__(self):
        self._baseDir = 0


    def nextDir(self):
        return

    def load(self, programa):
        progSize = len(programa.instructions)
        myBaseDir = self._baseDir

        for index in range(0, progSize):
            HARDWARE.memory.put(self._baseDir + index, programa.instructions[index])

        self._baseDir += progSize

        return myBaseDir




class PCBTable():

    def __init__(self):
        self._cpu = HARDWARE.cpu
        self._lista_de_pcb = [] ## Queue
        self._running_pcb = None
        self. _pid = 1

    @property
    def listaDePCB(self):
        return self._lista_de_pcb


    def crearPCB(self, programa):
        new_pcb = PCB(programa, self.getNewPID())
        loader.load(pcb)

    def getPid(self):
        return self._pid


    def getNewPID(self):
        pid = self._pid

        self._pid += 1

        return pid



    def addPCB(self, pcb):
        if (pcb.state == "Running"):
            self._running_pcb = pcb.state
            self._lista_de_pcb.append(pcb)
        else:
            self._lista_de_pcb.append(pcb)

    def remove(self,pid):        """   CHEQUEAR SI ESTA BIEN """
        for pcb in (self._lista_de_pcb):
            if pcb.pid == pid:
                self._lista_de_pcb.remove(pcb)    


class PCB():
    def __init__(self, programa, pid, state, pc, pathName, baseDir):
        self._program = programa
        self._pid = pid
        self._state = state
        self._pc = pc
        self._path = pathName
        self._baseDir = baseDir

    @property
    def pid(self):
       return self._pid

    def baseDir(self):
        return self._baseDir

    @property
    def pc(self):
        return self._pc

    @property
    def state(self):
        return self._state

    @property
    def path(self):
        return self._path



class Queue():
    def __init__(self):
        self._queue = []





""" CLASE DISPATCHER """


class Dispatcher():

def __init__(self):
    self._cpu = HARDWARE.cpu   """NO SE SI VA """


def load(self,pcb):

    Hardware.cpu.pc = pcb.pc 
    HARDWARE.cpu.mmu.baseDir = pcb.baseDir  

def save(self,pcb):

    pcb.pc = Hardware.cpu.pc
    HARDWARE.cpu.pc = -1