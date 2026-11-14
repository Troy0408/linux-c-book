libsome.a: foo.o bar.o lose.o win.o 
	ar r libsome.a $?
	ranlib libsome.a