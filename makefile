CC = gcc
CFLAGS = -g -Iinclude -O3
SRC_DIR = src
OBJ_DIR = bin
INCLUDE_DIR = include

SRC = main.c inout.c graphic.c genetic.c location.c
OBJ = $(addprefix $(OBJ_DIR)/, $(SRC:.c=.o))

vrp: $(OBJ)
	$(CC) -o vrp $(OBJ)

# Règle générique pour compiler les .o à partir des .c
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) -c $< -o $@ $(CFLAGS)

clean:
	rm -f $(OBJ_DIR)/*.o
	rm -f *~
	rm -f vrp
