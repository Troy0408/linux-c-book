#include <sys/mman.h>

 void *mmap(void *addr, size_t len, int prot, int flag, int filedes, off_t off);
 int munmap(void *addr, size_t len);