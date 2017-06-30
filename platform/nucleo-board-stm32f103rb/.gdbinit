target remote localhost:3333
monitor reset halt
load
break fault_handler
info break
