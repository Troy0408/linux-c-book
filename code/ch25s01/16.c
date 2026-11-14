#include <string.h>

char *strtok(char *str, const char *delim);
char *strtok_r(char *str, const char *delim, char **saveptr);
返回值：返回指向下一个Token的指针，如果没有下一个Token了就返回NULL