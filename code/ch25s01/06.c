void *memcpy(void *dest, const void *src, size_t n)
{
	char *d = dest;
	const char *s = src;
	int *di;
	const int *si;
	int r = n % 4;
	while (r--)
		*d++ = *s++;
	di = (int *)d;
	si = (const int *)s;
	n /= 4;
	while (n--)
		*di++ = *si++;

	return dest;
}