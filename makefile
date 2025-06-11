CC = gcc
CFLAGS = -Wall -ansi -g -Iinclude
SRC_DIR = src
OBJ_DIR = bin
INCLUDE_DIR = include
LIBS = -lMLV

SRC = main.c inout.c graphic.c genetic.c location.c
OBJ = $(addprefix $(OBJ_DIR)/, $(SRC:.c=.o))

vrp: $(OBJ)
	$(CC) -o vrp $(OBJ) $(LIBS)

# Règle générique pour compiler les .o à partir des .c
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) -c $< -o $@ $(CFLAGS) $(LIBS)

clean:
	rm -f $(OBJ_DIR)/*.o
	rm -f *~
	rm -f vrp
