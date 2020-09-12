CC = gcc -pedantic -pthread
CFLAGS =  -g
SRC=./src
OBJ=./obj
SRCLIB=./srclib
LIB=./lib

all: create_dir clean ${OBJ}/picohttpparser.o ${OBJ}/processrequest.o  main

main: ${OBJ}/main.o 
	$(CC) $(CFLAGS) -o server ${OBJ}/main.o ${LIB}/processrequest.a  ${LIB}/picoparserlib.a 

${OBJ}/processrequest.o: srclib/processrequest.c srclib/processrequest.h
	$(CC) $(CFLAGS) -I./srclib -c $< -o $@ 
	ar rcs ${LIB}/processrequest.a ${OBJ}/processrequest.o

${OBJ}/picohttpparser.o: srclib/picohttpparser.c srclib/picohttpparser.h
	$(CC) $(CFLAGS) -c $< -o $@
	ar rcs ${LIB}/picoparserlib.a ${OBJ}/picohttpparser.o
${OBJ}/main.o: ${SRC}/main.c 
	$(CC) $(CFLAGS) -I./srclib -c $< -o $@ 


clean:
	rm -rf obj/*.o lib/*.a server

create_dir:
	mkdir -p $(OBJ) $(LIB)
	