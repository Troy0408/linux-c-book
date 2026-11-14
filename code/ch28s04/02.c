#include <unistd.h>

ssize_t write(int fd, const void *buf, size_t count);
返回值：成功返回写入的字节数，出错返回-1并设置errno