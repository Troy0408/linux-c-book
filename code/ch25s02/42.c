#include <stdio.h>
#include <unistd.h>

int main()
{
	char buf[20];
	printf("Please input a line: ");
	fgets(buf, 20, stdin);
	return 0;
}