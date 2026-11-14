#include <stdio.h>

int fseek(FILE *stream, long offset, int whence);
返回值：成功返回0，出错返回-1并设置errno

long ftell(FILE *stream);
返回值：成功返回当前读写位置，出错返回-1并设置errno

void rewind(FILE *stream);