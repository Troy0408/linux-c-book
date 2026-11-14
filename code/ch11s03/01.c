void insertion_sort(void)			执行时间
{
	int i, j, key;
	for (j = 1; j < LEN; j++) {
		key = a[j];			c1
		i = j - 1;			c2
		while (i >= 0 && a[i] > key) {
			a[i+1] = a[i];		c3
			i--;			c4
		}
		a[i+1] = key;			c5
	}
}