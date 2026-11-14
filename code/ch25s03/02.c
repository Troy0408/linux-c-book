#include <stdlib.h>

long int strtol(const char *nptr, char **endptr, int base);
double strtod(const char *nptr, char **endptr);
返回值：转换结果，出错时设置errno