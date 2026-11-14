x := foo
y := $(x) bar

all: 
	@echo "-$(y)-"