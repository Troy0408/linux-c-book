#include <strings.h>

int strcasecmp(const char *s1, const char *s2);
int strncasecmp(const char *s1, const char *s2, size_t n);
返回值：负值表示s1小于s2，0表示s1等于s2，正值表示s1大于s2