#include <unistd.h>

ssize_t read(int fd, void *buf, size_t count);
返回值：成功返回读取的字节数，出错返回-1并设置errno，如果在调read之前已到达文件末尾，则这次read返回0