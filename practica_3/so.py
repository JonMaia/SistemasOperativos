#!/usr/bin/env python

from hardware import *
import log
from enum import Enum


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
            # print(pair)
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(
            deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)


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
        log.logger.info(" Program Finished ")

        pcbActual = self.kernel.pcbTable.running_pcb
        kernel = self.kernel
        pcbTable = self.kernel.pcbTable

        pcbActual._state = "Terminated"
        kernel.dispatcher.save(pcbActual)
        pcbTable.set_running_pcb = None

        if len(kernel.readyQueue) > 0:
            headReadyQueue = kernel.readyQueue[0]
            headReadyQueue._state = "Running"
            pcbTable._running_pcb = headReadyQueue
            kernel.dispatcher.load(headReadyQueue)


class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):  # ESTE CODIGO COMENTADO YA VINO, CHEQUEAR QUE SIRVE
        operation = irq.parameters
        kernel = self.kernel
        pcbTable = self.kernel.pcbTable
        # pcb = {'pc': HARDWARE.cpu.pc} # porque hacemos esto ???
        # HARDWARE.cpu.pc = -1   ## dejamos el CPU IDLE
        # self.kernel.ioDeviceController.runOperation(pcb, operation)
        runningPCB = kernel.pcbTable.running_pcb
        runningPCB.set_state("Waiting")
        kernel.dispatcher.save(runningPCB)  # guarda el pcb del proceso
        self.kernel.pcbTable.set_running_pcb(None)  # Ojo que runningPCB esta en none, chequearlo

        if len(kernel.readyQueue) > 0:
            headReadyQueue = kernel.readyQueue[0]
            headReadyQueue._state = "Running"
            pcbTable.set_running_pcb(headReadyQueue)
            kernel.dispatcher.load(headReadyQueue)
            
        log.logger.info(self.kernel.ioDeviceController)
        kernel.ioDeviceController.runOperation(runningPCB, operation)


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):  # ESTE CODIGO COMENTADO YA VINO, CHEQUEAR QUE SIRVE
        # pcb = self.kernel.ioDeviceController.getFinishedPCB()
        # HARDWARE.cpu.pc = pcb['pc']
        ioPCB = self.kernel.ioDeviceController.getFinishedPCB()  # devuelve el pcb que se estaba ejecutando en ioIn
        pcbTable = self.kernel.pcbTable

        ioPCB.set_state("Ready")

        if (pcbTable.running_pcb == None):
            self.kernel.dispatcher.load(ioPCB)
            ioPCB.set_state("Running")
            pcbTable.set_running_pcb(ioPCB)

        else:
            self.kernel.addReadyQueue(ioPCB)

        log.logger.info(self.kernel.ioDeviceController)


class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq0):
        kernel = self.kernel
        program = irq0.parameters
        pcbTable = self.kernel.pcbTable

        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

        # set CPU program counter at program's first intruction
        HARDWARE.cpu.pc = 0

        baseDir = kernel.loader.load(program)
        pcb = PCB(program, pcbTable.getNewPID(), baseDir)

        pcbTable.addPCB(pcb)

        if (pcbTable.running_pcb == None):
            kernel.dispatcher.load(pcb)
            pcb.set_state("Running")
            pcbTable.set_running_pcb(pcb)
        else:
            pcb.set_state("Ready")
            kernel.addReadyQueue(pcb)


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

        self._readyQueue = []

        self._loader = Loader()

        self._pcbTable = PCBTable()

        self._dispatcher = Dispatcher()

        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)

    @property
    def loader(self):
        return self._loader

    @property
    def pcbTable(self):
        return self._pcbTable

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    @property
    def readyQueue(self):
        return self._readyQueue

    def addReadyQueue(self, pcb):
        self._readyQueue.append(pcb)

    ## emulates a "system call" for programs execution
    def run(self, program):
        # TIENE QUE LLAMAR A LA INSTERRUPCION NEW
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, program)
        HARDWARE.interruptVector.handle(newIRQ)

        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

    def __repr__(self):
        return "Kernel "


class Loader():  # chequear!!!

    def __init__(self):
        self._baseDir = 0
        self._limit = 0

    def baseDir(self):
        return self._baseDir

    def limit(self):
        return self._limit

    def load(self, programa):
        progSize = len(programa.instructions)
        myBaseDir = self._baseDir

        for index in range(self.baseDir(), progSize + self.baseDir()):
            HARDWARE.memory.put(index, (programa.instructions[index - self.baseDir()]))

        self._baseDir = index + 1
        self._limit = progSize - 1

        return myBaseDir


class PCBTable():

    def __init__(self):
        self._cpu = HARDWARE.cpu
        self._lista_de_pcb = []  ## Queue
        self._running_pcb = None
        self._pid = 1

    @property
    def listaDePCB(self):
        return self._lista_de_pcb

    @property
    def getPid(self):
        return self._pid

    @property
    def running_pcb(self):
        return self._running_pcb

    def set_running_pcb(self, new_pcb):
        self._running_pcb = new_pcb

    def getNewPID(self):
        pid = self._pid

        self._pid += 1

        return pid

    def addPCB(self, pcb):
        self._lista_de_pcb.append(pcb)
        if pcb.state == "Running":
            self._running_pcb = pcb

    def remove(self, pid):  # CHEQUEAR SI ESTA BIEN
        for pcb in (self._lista_de_pcb):
            if pcb.pid == pid:
                self._lista_de_pcb.remove(pcb)


class PCB():
    def __init__(self, programa, pid, base_dir):
        self._program = programa
        self._pid = pid
        self._state = "New"
        self._pc = 0
        self._path = self.program.name
        self._baseDir = base_dir
        self._limit = len(programa.instructions) - 1

    @property
    def limit(self):
        return self._limit

    @property
    def program(self):
        return self._program

    @property
    def pid(self):
        return self._pid

    @property
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

    def set_state(self, new_state):
        self._state = new_state


# CLASE DISPATCHER


class Dispatcher():  # chequear!!!!

    def load(self, pcb):
        HARDWARE.cpu._pc = pcb.pc
        HARDWARE.mmu._baseDir = pcb.baseDir
        HARDWARE.mmu._limit = pcb.limit

    def save(self, pcb):
        pcb._pc = HARDWARE.cpu.pc
        HARDWARE.cpu._pc = -1


class State(Enum):
    NEW = 1
    READY = 2
    RUNNING = 3
    WAITING = 4
    TERMINATED = 5


class Queue():
    def __init__(self):
        self._queue = []
