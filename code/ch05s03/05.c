int factorial(int n)
{
	int recurse = factorial(n-1);
	int result = n * recurse;
	return result;
}