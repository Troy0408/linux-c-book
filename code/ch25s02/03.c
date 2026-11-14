#include <stdio.h>

FILE *fopen(const char *path, const char *mode);
返回值：成功返回文件指针，出错返回NULL并设置errno