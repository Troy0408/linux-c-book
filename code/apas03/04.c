#include <stdio.h>
#include <locale.h>

int main(void)
{
	if (!setlocale(LC_CTYPE, "")) {
		fprintf(stderr, "Can't set the specified locale! "
			"Check LANG, LC_CTYPE, LC_ALL.\n");
		return 1;
	}
	printf("%ls", L"你好\n");
	return 0;
}