all: count_words

count_words: count_words.c
	gcc count_words.c -o count_words -lz

shared: count_words.so

count_words.so: count_words.o
	gcc -shared count_words.o -o count_words.so -lz

count_words.o: count_words.c
	gcc -fPIC -c count_words.c

