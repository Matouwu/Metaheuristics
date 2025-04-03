CC=gcc
CFLAGS=-Wall -ansi
LDFLAGS=
OBJ=main.o inout.o graphic.o genetic.o location.o

recuit: $(OBJ)
	$(CC) -o recuit $(OBJ) $(CFLAGS) -lMLV

main.o: main.c graphic.h
	$(CC) -c main.c $(CFLAGS)

inout.o: inout.c inout.h
	$(CC) -c inout.c $(CFLAGS)

graphic.o: graphic.c graphic.h
	$(CC) -c graphic.c $(CFLAGS) -lMLV

genetic.o: genetic.c genetic.h
	$(CC) -c genetic.c $(CFLAGS)

location.o: location.c location.h
	$(CC) -c location.c $(CFLAGS)

clean:
	rm -f *.o
	rm -f *~
	rm -f recuit
