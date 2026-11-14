main.o: main.h stack.h maze.h

main.o: main.c
	gcc -c main.c