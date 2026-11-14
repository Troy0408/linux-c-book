#include <stdio.h>

char *fgets(char *s, int size, FILE *stream);
char *gets(char *s);
返回值：成功时s指向哪返回的指针就指向哪，出错或者读到文件末尾时返回NULL