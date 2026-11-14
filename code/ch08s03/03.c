int main(void)
{
	int i, histogram[10] = {0};

	gen_random(10);
	for (i = 0; i < N; i++)
		histogram[a[i]]++;
	...
}