# Grupo 5


### Integrantes:

| Nombre y Apellido              |      Mail                      |     usuario Gitlab   |
| -----------------------------  | ------------------------------ | -------------------  |
| Miguel Enrique Bada            | miguelenriquebada07@gmail.com  | miguelbada           |
| Jonathan Nicolas Maia          | jonathannicolas.maia@gmail.com | Jon_Maia             |
| Facundo Sardi                  | facusardi96@gmail.com          | fsardi96             |


## Entregas:

### Práctica 1:  
- Ok.

### Práctica 2:  
- Ok.

### Práctica 3:  
- Ok.

### Práctica 4:  
- Ok.



## Sugerencias 

- Hablemoslo en clase (Nando)

 - #New IRQ handler
   - HARDWARE.cpu.pc = 0 esta de mas

- Loader.load(): por ahi queda mas legible asi:
   '''
         for index in range(0, prog_size):
            HARDWARE.memory.put(index + self._base_dir, (programa.instructions[index]))

	self._base_dir = self._base_dir  + prog_size
'''



- SchedulerPriorityNoExpropiativo
  - self._ready_queue.sort(): Que pasaria si quiero implementar un nuevo scheduler expropiativo pero ordenando por otro criterio distinto a la prioridad??? 


- asignarDestinoPCB()
  - delegar en el Scheduler la decisión de expropiar, si manana cambiamos el scheduler por otro expropiativo pero que ordena por otro criterio, hay que reescribir el handler    
  '''
  elif kernel.scheduler.esExpropiativo() and pcb.prioridad < pcb_table.running_pcb.prioridad:
 '''
 
  por 
  '''
    elif kernel.scheduler.seDebeExpropiar(pcb_table.running_pcb, pcb):
 '''
  
 - PCBTable
   - cuando se usa la parte del  State.RUNNING ??
   '''
      def add_pcb(self, pcb):
        self._lista_de_pcb.append(pcb)
        if pcb.state is State.RUNNING:
            self._running_pcb = pcb
    '''