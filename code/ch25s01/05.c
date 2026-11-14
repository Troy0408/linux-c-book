void *memmove(void *dest, const void *src, size_t n)
{
	char temp[n];
	int i;
	char *d = dest;
	const char *s = src;

	for (i = 0; i < n; i++)
		temp[i] = s[i];
	for (i = 0; i < n; i++)
		d[i] = temp[i];

	return dest;
}