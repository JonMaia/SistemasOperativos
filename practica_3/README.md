# Práctica 3
## Multiprogramación


En esta versión, la __CPU__ no accede directamente a la __Memoria__, como hace la __CPU__ para fetchear la instruccion?? Por que??

Existe un componente de hardware llamado Memory Management Unit (__MMU__) que se encarga de transformar las direcciones lógicas (relativas)  en direcciones físicas (absolutas)



## Interrupciones de I/O y Devices

En esta version del emulador agregamos los I/O Devices y el manejo de los mismos

Un I/O device es un componente de hardware (interno o externo) que realiza operaciones específicas.

Una particularidad que tienen estos dispositivos es los tiempos de ejecucion son mas extensos que los de CPU, ej: bajar un archivo de internet, imprimir un archivo, leer desde un DVD, etc.
Por otro lado, solo pueden ejecutar una operacion a la vez, con lo cual nuestro S.O. debe garantizar que no se "choquen" los pedidos de ejecucion.

Para ello implementamos un __IoDeviceController__ que es el encargado de "manejar" el device, encolando los pedidos para ir sirviendolos a medida que el dispositivo se libere.


También se incluyeron 2 interrupciones 

- __#IO_IN__
- __#IO_OUT__



## Lo que tenemos que hacer es:

- __1:__ Describir como funciona el __MMU__ y que datos necesitamos para correr un proceso

- __2:__ Implementar una version con __multiprogramación__ (donde todos los procesos se encuentran en memoria a la vez)

```python
    prg1 = Program("prg1.exe", [ASM.CPU(2)])
    prg2 = Program("prg2.exe", [ASM.CPU(4)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])

    # execute all programs
    kernel.run(prg1)
    kernel.run(prg2)
    kernel.run(prg3)
```


- __3:__ Entender las clases __IoDeviceController__, __PrinterIODevice__ y poder explicar como funcionan

- __4:__ Explicar cómo se llegan a ejecutar __IoInInterruptionHandler.execute()__ y  __IoOutInterruptionHandler.execute()__

- __5:__    Hagamos un pequeño ejercicio (sin codificarlo):

- __5.1:__ Que esta haciendo el CPU mientras se ejecuta una operación de I/O??

- __5.2:__ Si la ejecucion de una operacion de I/O (en un device) tarda 3 "ticks", cuantos ticks necesitamos para ejecuar el siguiente batch?? Cómo podemos mejorarlo??
    (tener en cuenta que en el emulador consumimos 1 tick para mandar a ejecutar la operacion a I/O)

    ```python
    prg1 = Program("prg1.exe", [ASM.CPU(2), ASM.IO(), ASM.CPU(3), ASM.IO(), ASM.CPU(2)])
    prg2 = Program("prg2.exe", [ASM.CPU(4), ASM.IO(), ASM.CPU(1)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])
    ```

- __6:__ Ahora si, a programar... tenemos que "evolucionar" nuestro S.O. para que soporte __multiprogramación__  
         Cuando un proceso este en I/O, debemos cambiar el proceso corriendo por otro para optimizar el uso de __CPU__

    ```python
    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ###################
    prg1 = Program("prg1.exe", [ASM.CPU(2), ASM.IO(), ASM.CPU(3), ASM.IO(), ASM.CPU(2)])
    prg2 = Program("prg2.exe", [ASM.CPU(4), ASM.IO(), ASM.CPU(1)])
    prg3 = Program("prg3.exe", [ASM.CPU(3)])

    # execute all programs "concurrently"
    kernel.run(prg1)
    kernel.run(prg2)
    kernel.run(prg3)

    ## start
    HARDWARE.switchOn()

    ```



- __7:__ Implementar la interrupción #NEW
    ```python
    # Kernel.run() debe lanzar una interrupcion de #New para que se resuelva luego por el S.O. 
    ###################

    ## emulates a "system call" for programs execution
    def run(self, program):
        newIRQ = IRQ(NEW_INTERRUPTION_TYPE, program)
        self._interruptVector.handle(newIRQ)
    ```




NOTAS DEL TP: 

EN ESTA PRACTICA LA IDEA ES HACER MULTIPROGRAMACION Y TENER VARIOS PROGRAMAS CARGADOS EN LA MEMORIA.

I/O (imput/output): Dispositivo entrada salida. EJ: impresora

El clock hace un tick "infinito" en todo momento al CPU y al IODEVICE

CPU solo conoce memoria y las instrucciones a ejecutar. No conoce los IO.

La cpu no ejecuta instrucciones de IO,cuando detecta que es instruccion de ASM.IO() ejecuta una interrupcion (irq):
tenemos 4 interrupciones: NEW Handler -  KILL handler - IO_IN handler - IO_OUT handler
En este caso hacemos IO_IN handler.


 
 se agrega el programa a la WAITING  QUEUE, entonces libera ese programa de la cpu para que la cpu tome otra programa y no se pierda tiempo. Luego el IO DEVICE se encarga de ejecutar ese programa y al terminar de ejecutar  hace  INTERRUTHANDLER IO_OUT, lo que hace esta interrupcion es mandar el programa a la READY QUEUE.

 



Idle : _pc = -1    = PC OSIOSA SIN HACER NADA.
Bussy: _pc > -1    = PC UCUPADA EJECUTANDO UN PROGRAMA.

En este TP No quiero ejecutar en batch uno por uno los programas. quiero hacer multiprogramación ejecutar varios al mismo tiempo.

mientras haya espacio en memoria, podemos alojar todos los programas (con sus instrucciones en cada celda) en memoria.

dir logica: DIR LOGICA DEL PROGRAMA 

Dir fisica: DIR DE MEMORIA FISICA REAL

Base dir: indica la dir fisica de la memoria donde arranca el "programa" del proceso en cpu.
#la base dir tiene info de cada uno de los procesos por eso sabe donde empieza cada programa.

baseDir + pc es el calculo para que la cpu haga fetch y ejecute esa instruccion de la memoria fisica.

cpu  maneja dir logicas
memoria maneja dir fisicas

mmu : es el que transforma dir logicas en fisicas. 


se debe crear una clase LOADER:

Loader: es el encargado de cargar programas en memoria , el loader puede guardar el proximo lugar donde se debe cargar el nuevo programa.

pcb table : muentras el estado de todos los procesos ej: proceso 1 Waiting - proceso 2 new



En SO se debe implementar la clase dispatcher con metodos load(pcb) - save(pcb)(deja en idle el cpu)
es el encargado de cuando se hace el context switch, guarda el pcb del proceso actual y carga el pcb del proceso que se seleccionó para ejecutar.



#DEBEMOS MODIFICAR LAS 4 INTERRUPCIONES: KILLER- NEW - IO_IN - IO_OUT



#-Interrupcion de New: 

crear PCB:
- crear pid (id univoco de cada proceso)
- deben estar todos los programas y sus estados(el primer estado de un progrma es NEW)
- agregar programa al PCB table y ponerlo en estado NEW.

-Cargar el progrma en el PCB con todos sus datos.
-Cargar en memoria el programa, esto lo hace el LOADER.(el loader conoce la memoria y tiene un puntero que indica la sig posicion en donde se debe cargar el prox programa)

EN EL PCB TABLE DEBE HABER UN CAMPO QUE DEBE ES PCB.RUNNING es un puntero al proceso running si lo hay, si no debe estar en NONE(NULL).

- Si el no hay un programa en running en la cpu, ejecutamos ese programa pegando los datos de la PCB del programa nuevo en la cpu para ejecutarlo.

#-Interrupcion de KILL:


-Debemos interactuar con el pcb.

-cuando el cpu lee la instruccion EXIT de un programa, ejecuta una interrupcion que es el kill handler. Luego el dispatcher debe ejecutar el Content swith que lo que hace es actualizar el PCB de ese proceso, pone su estado en TERMINATED y guarda el PC = LIMITE DE PROGRAMA. 

-Luego establecemos el PC = -1.

-Analizamos si hay programas por correr en la ready queue:

si hay programas todavia, ejecuta content swith y hace load del programa a ejecutar -> los datos del PCB del programa pisa los valores pc del cpu y base dir del MMU.

si no hay programas en ready queue, queda en un loop tirando NOOP.

funciones:

dispacher.save(pcb)
dispacher.load(pcb)


TENER EN CUENTA QUE EL CONTENT SWITH TIENE 2 PATAS: EL SAVE Y EL LOAD.