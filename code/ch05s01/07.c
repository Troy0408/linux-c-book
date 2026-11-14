void foo(int x, int y)
{
	if (x >= 0 || y >= 0) {
		printf("both x and y are positive.\n");
		return;
	} else if (x < 0 || y < 0) {
		printf("both x and y are negetive.\n");
		return;
	}
	printf("x has a different sign from y.\n");
}