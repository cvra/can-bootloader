
# make targets for flashing with openocd

.PHONY: flash
flash: all
	openocd -f oocd.cfg -c "program $(PROJNAME).elf verify reset"

.PHONY: reset
reset:
	openocd -f oocd.cfg -c "init" -c "reset" -c "shutdown"
