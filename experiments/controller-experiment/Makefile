CC = gcc
CFLAGS = -c -Wall -pthread -lm -lrt
LDFLAGS = -pthread -lm -lrt
TARGETS = controller_client server sequencer
CLIENT_OBJS = queue.o common.o cdf.o conn.o client.o
CONTROLLER_CLIENT_OBJS = queue.o common.o cdf.o conn.o controller_client.o sim.o tsQueue.o
SERVER_OBJS = common.o server.o
SEQ_OBJS = common.o sequencer.o
BIN_DIR = bin
RESULT_DIR = result
CLIENT_DIR = src/client
COMMON_DIR = src/common
SERVER_DIR = src/server
SEQ_DIR = src/sequencer
SCRIPT_DIR = src/script
CAPI_DIR=src/cAPI

all: $(TARGETS) move

move:
	mkdir -p $(RESULT_DIR)
	mkdir -p $(BIN_DIR)
	mv *.o $(TARGETS) $(BIN_DIR)
	cp $(SCRIPT_DIR)/* $(BIN_DIR)

client: $(CLIENT_OBJS)
	$(CC) $(CLIENT_OBJS) -o client $(LDFLAGS)

controller_client: $(CONTROLLER_CLIENT_OBJS)
	$(CC) $(CONTROLLER_CLIENT_OBJS) -o controller_client $(LDFLAGS)

server: $(SERVER_OBJS)
	$(CC) $(SERVER_OBJS) -o server $(LDFLAGS)

sequencer: $(SEQ_OBJS)
	$(CC) $(SEQ_OBJS) -o sequencer $(LDFLAGS)

%.o: $(CLIENT_DIR)/%.c
	$(CC) $(CFLAGS) $^ -o $@

%.o: $(SERVER_DIR)/%.c
	$(CC) $(CFLAGS) $^ -o $@

%.o: $(SEQ_DIR)/%.c
	$(CC) $(CFLAGS) $^ -o $@

%.o: $(COMMON_DIR)/%.c
	$(CC) $(CFLAGS) $^ -o $@

%.o: $(CAPI_DIR)/%.c
	$(CC) $(CFLAGS) $^ -o $@

clean:
	rm -rf $(BIN_DIR)/*
