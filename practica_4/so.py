#!/usr/bin/env python

from hardware import *
import log
from enum import Enum


# emulates a compiled program
class Program:

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
                # is a list of instructions
                expanded.extend(i)
            else:
                # a single instr (a String)
                expanded.append(i)

        # now test if last instruction is EXIT
        # if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


# emulates an Input/Output device controller (driver)
class IoDeviceController:

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
            # pop(): extracts (deletes and return) the first element in queue
            pair = self._waiting_queue.pop(0)

            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {deviceID} running: {currentPCB} waiting: {waiting_queue}".format(
            deviceID=self._device.deviceId, currentPCB=self._currentPCB, waiting_queue=self._waiting_queue)


# emulates the  Interruptions Handlers
class AbstractInterruptionHandler:
    def __init__(self, kernel):
        self._kernel = kernel

    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))

    def poner_proceso_en_running(self):
        if len(self.kernel.scheduler.ready_queue) > 0:
            head_ready_queue = self.kernel.scheduler.getNext()
            head_ready_queue.state = State.RUNNING
            self.kernel.pcb_table.running_pcb = head_ready_queue
            self.kernel.dispatcher.load(head_ready_queue)


class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq0):
        kernel = self.kernel
        pcb_table = self.kernel.pcb_table

        pcb_actual = pcb_table.running_pcb
        pcb_table.running_pcb = None

        kernel.dispatcher.save(pcb_actual)
        pcb_actual.state = State.TERMINATED

        log.logger.info(" Program Finished ")

        self.poner_proceso_en_running()


class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        kernel = self.kernel
        pcb_table = self.kernel.pcb_table

        running_pcb = pcb_table.running_pcb
        pcb_table.running_pcb = None

        kernel.dispatcher.save(running_pcb)  # guarda el pcb del proceso
        running_pcb.state = State.WAITING
        log.logger.info(kernel.ioDeviceController)
        kernel.ioDeviceController.runOperation(running_pcb, operation)
        self.poner_proceso_en_running()


class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        io_pcb = self.kernel.ioDeviceController.getFinishedPCB()  # devuelve el pcb que se estaba ejecutando en ioIn
        pcb_table = self.kernel.pcb_table
        kernel = self.kernel

        if pcb_table.running_pcb is None:
            kernel.dispatcher.load(io_pcb)
            io_pcb.state = State.RUNNING
            pcb_table.running_pcb = io_pcb
        elif kernel.scheduler.esExpropiativo() and io_pcb.prioridad < pcb_table.running_pcb.prioridad:
        	kernel.dispatcher.save(pcb_table.running_pcb)  # guarda el pcb del proceso
        	pcb_table.running_pcb.state = State.READY
        	kernel.scheduler.add(pcb_table.running_pcb)
        	kernel.dispatcher.load(io_pcb)
        	io_pcb.state = State.RUNNING
        	kernel.pcb_table.running_pcb = io_pcb
        else:
        	io_pcb.state = State.READY
        	kernel.scheduler.add(io_pcb)

        log.logger.info(kernel.ioDeviceController)


class NewInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq0):
        dictNewParam = irq0.parameters  # IRQ0.parameters devuelve un program.
        priority = dictNewParam['priority']
        program = dictNewParam['program']
        kernel = self.kernel
        pcb_table = self.kernel.pcb_table

        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

        # set CPU program counter at program's first intruction
        HARDWARE.cpu.pc = 0

        base_dir = kernel.loader.load(program)
        pcb = PCB(program, pcb_table.get_new_pid(), base_dir, priority)

        pcb_table.add_pcb(pcb)

        if pcb_table.running_pcb is None:
            kernel.dispatcher.load(pcb)
            pcb.state = State.RUNNING
            pcb_table.running_pcb = pcb
        elif kernel.scheduler.esExpropiativo() and pcb.prioridad < pcb_table.running_pcb.prioridad:
        	kernel.dispatcher.save(pcb_table.running_pcb)  # guarda el pcb del proceso
        	pcb_table.running_pcb.state = State.READY
        	kernel.scheduler.add(pcb_table.running_pcb)
        	kernel.dispatcher.load(pcb)
        	pcb.state = State.RUNNING
        	kernel.pcb_table.running_pcb = pcb
        else: 
        	pcb.state = State.READY
        	kernel.scheduler.add(pcb)

class TimeOutInterruptionHandler(AbstractInterruptionHandler):

	def execute(self, irq0):
		kernel = self.kernel
		pcb_table = self.kernel.pcb_table
		if len(kernel.scheduler.ready_queue) == 0:
			HARDWARE.timer.reset()
		else:
			kernel.dispatcher.save(pcb_table.running_pcb)
			pcb_table.running_pcb.state = State.READY
			kernel.scheduler.add(pcb_table.running_pcb)
			self.poner_proceso_en_running()


# emulates the core of an Operative System
class Kernel:

    def __init__(self,scheduler):
        # setup interruption handlers
        

        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)

        newHandler = NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)

        timeOut = TimeOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(TIMEOUT_INTERRUPTION_TYPE, timeOut)

        self._scheduler = scheduler

        self._loader = Loader()

        self._pcb_table = PCBTable()

        self._dispatcher = Dispatcher()

        # controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)

    @property
    def loader(self):
        return self._loader

    @property
    def pcb_table(self):
        return self._pcb_table

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def ioDeviceController(self):
        return self._ioDeviceController

    @property
    def scheduler(self):
       return self._scheduler

    # emulates a "system call" for programs execution
    def run(self, program, priority):
        dictNewParam = {'program': program, 'priority': priority}
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, dictNewParam)
        HARDWARE.interruptVector.handle(newIRQ)

        log.logger.info("\n Executing program: {name}".format(name=program.name))
        log.logger.info(HARDWARE)

    def __repr__(self):
        return "Kernel "


class SchedulerFIFO:

    def __init__(self):
        self._ready_queue = []

    @property
    def ready_queue(self):
        return self._ready_queue

    def add(self, pcb):   
        self._ready_queue.append(pcb)

    def esExpropiativo(self):
        return False

    def getNext(self):
        return self._ready_queue.pop(0) #SACA EL HEAD DE LA LISTA Y TE LO DEVUELVE
        

class SchedulerPriorityNoExpropiativo:

    def __init__(self):
        self._ready_queue = []

    @property
    def ready_queue(self):
        return self._ready_queue

    def add(self, pcb):
        self._ready_queue.append(pcb)
        self._ready_queue.sort()

    def esExpropiativo(self):
        return False

    def getNext(self):
        return self._ready_queue.pop(0)  # El mas prioritario es el de menor valor.

class SchedulerPriorityExpropiativo:

    def __init__(self):
        self._ready_queue = []

    @property
    def ready_queue(self):
        return self._ready_queue

    def add(self, pcb):
        self._ready_queue.append(pcb)
        self._ready_queue.sort()

    def esExpropiativo(self):
        return True

    def getNext(self):
        return self._ready_queue.pop(0)  # El mas prioritario es el de menor valor.


class SchedulerRoundRobin:

    def __init__(self):
        self._ready_queue = []

    @property
    def ready_queue(self):
        return self._ready_queue

    def add(self, pcb):
        self._ready_queue.append(pcb)

    def esExpropiativo(self):
        return False

    def getNext(self):
        return self._ready_queue.pop(0)  # El mas prioritario es el de menor valor.

class Loader:

    def __init__(self):
        self._base_dir = 0
        self._limit = 0

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def limit(self):
        return self._limit

    @base_dir.setter
    def base_dir(self, new_base_dir):
        self._base_dir = new_base_dir

    @limit.setter
    def limit(self, new_limit):
        self._limit = new_limit

    def load(self, programa):
        prog_size = len(programa.instructions)
        my_base_dir = self._base_dir

        for index in range(self._base_dir, prog_size + self._base_dir):
            HARDWARE.memory.put(index, (programa.instructions[index - self._base_dir]))

        self._base_dir = index + 1
        self._limit = prog_size - 1

        log.logger.info(HARDWARE.memory)

        return my_base_dir


class PCBTable:

    def __init__(self):
        self._cpu = HARDWARE.cpu
        self._lista_de_pcb = []
        self._running_pcb = None
        self._pid = 1

    @property
    def cpu(self):
        return self._cpu

    @property
    def lista_de_pcb(self):
        return self._lista_de_pcb

    @property
    def running_pcb(self):
        return self._running_pcb

    @property
    def pid(self):
        return self._pid
    
    @cpu.setter
    def cpu(self, new_cpu):
        self._cpu = new_cpu

    @running_pcb.setter
    def running_pcb(self, new_pcb):
        self._running_pcb = new_pcb

    def get_new_pid(self):
        pid = self._pid

        self._pid += 1

        return pid

    def add_pcb(self, pcb):
        self._lista_de_pcb.append(pcb)
        if pcb.state is State.RUNNING:
            self._running_pcb = pcb


class PCB:
    def __init__(self, programa, pid, base_dir, priority):
        self._program = programa
        self._pid = pid
        self._state = State.NEW
        self._pc = 0
        self._path = self.program.name
        self._base_dir = base_dir
        self._limit = len(programa.instructions) - 1
        self._prioridad = priority

    @property
    def program(self):
        return self._program

    @property
    def pid(self):
        return self._pid

    @property
    def state(self):
        return self._state

    @property
    def pc(self):
        return self._pc

    @property
    def path(self):
        return self._path

    @property
    def base_dir(self):
        return self._base_dir

    @property
    def limit(self):
        return self._limit

    @property
    def prioridad(self):
        return self._prioridad

    @program.setter
    def program(self, new_program):
        self._program = new_program

    @pid.setter
    def pid(self, new_pid):
        self._pid = new_pid

    @state.setter
    def state(self, new_state):
        self._state = new_state

    @pc.setter
    def pc(self, mypc):
        self._pc = mypc

    @path.setter
    def path(self, new_path):
        self._path = new_path

    @base_dir.setter
    def base_dir(self, new_base_dir):
        self._base_dir = new_base_dir

    @limit.setter
    def limit(self, new_limit):
        self._limit = new_limit

    @prioridad.setter
    def prioridad(self, una_prioridad):
        self._prioridad = una_prioridad

    def __eq__(self, other):
        return self.prioridad == other.prioridad

    def __ne__(self, other):
        return self.prioridad != other.prioridad

    def __lt__(self, other):
        return self.prioridad < other.prioridad

    def __le__(self, other):
        return self.prioridad <= other.prioridad

    def __gt__(self, other):
        return self.prioridad > other.prioridad

    def __ge__(self, other):
        return self.prioridad >= other.prioridad

    def __repr__(self):
        return "PCB: pid = {id}".format(id=self.pid) + ", " + "prioridad = {prioridad}".format(prioridad=self.prioridad)


class Dispatcher:

    def load(self, pcb):
        HARDWARE.cpu.pc = pcb.pc
        HARDWARE.mmu.baseDir = pcb.base_dir
        HARDWARE.mmu.limit = pcb.limit
        HARDWARE.timer.reset()

    def save(self, pcb):
        pcb.pc = HARDWARE.cpu.pc
        HARDWARE.cpu.pc = -1


class State(Enum):
    NEW = 1
    READY = 2
    RUNNING = 3
    WAITING = 4
    TERMINATED = 5
