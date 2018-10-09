CC=gcc
CFLAGS= -g -I.
DEPS = sim.h tsQueue.h 

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

c_app: sim.o tsQueue.o example.o
	gcc -Wall -g -o example sim.o example.o tsQueue.o -lm -lpthread -lncurses -I.
clean:
	rm example example.o sim.o tsQueue.o
