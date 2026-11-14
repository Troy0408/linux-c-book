#include <stdio.h>

int scanf(const char *format, ...);
int fscanf(FILE *stream, const char *format, ...);
int sscanf(const char *str, const char *format, ...);

#include <stdarg.h>

int vscanf(const char *format, va_list ap);
int vsscanf(const char *str, const char *format, va_list ap);
int vfscanf(FILE *stream, const char *format, va_list ap);
返回值：返回成功匹配和赋值的参数个数，成功匹配的参数可能少于所提供的赋值参数，返回0表示一个都不匹配，出错或者读到文件或字符串末尾时返回EOF并设置errno