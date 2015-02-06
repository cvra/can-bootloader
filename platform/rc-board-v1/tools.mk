
# make targets for flashing with openocd

.PHONY: flash
flash: all
	openocd -f oocd.cfg -c "program $(PROJNAME).elf verify reset"

.PHONY: reset
reset:
	openocd -f oocd.cfg -c "init" -c "reset" -c "shutdown"

# old: command
# openocd -f oocd.cfg -c init -c targets -c "reset halt" -c "flash write_image erase $(PROJNAME).elf" -c "verify_image $(PROJNAME).elf" -c shutdown
