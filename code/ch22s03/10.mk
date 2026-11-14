main: main.o stack.o maze.o
	gcc $^ -o $@