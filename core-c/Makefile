CC=gcc
CFLAGS=-O3 -march=native -flto -DNDEBUG -fPIC -Wall -Wextra
LDFLAGS=-shared
SRC=src/graph.c src/dijkstra.c src/yen.c src/edge_analysis.c
HDR=src/graph.h src/cost.h
BUILD=build

all: $(BUILD)/libconneccity.so

$(BUILD)/libconneccity.so: $(SRC) $(HDR)
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -I./src -o $(BUILD)/libconneccity.so $(SRC) $(LDFLAGS)

test: all
	@echo "(placeholder) run unit tests here"

clean:
	rm -rf $(BUILD)
