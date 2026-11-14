int main(void)
{
	int i, histogram[10];

	gen_random(10);
	for (i = 0; i < 10; i++)
		histogram[i] = howmany(i);
	...
}