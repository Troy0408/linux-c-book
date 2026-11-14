#include <alloca.h>

void *alloca(size_t size);
返回值：返回所分配内存空间的首地址，如果size太大导致栈空间耗尽，结果是未定义的