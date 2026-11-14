#define STR(s) #s
fputs(STR(strncmp("ab\"c\0d", "abc", '\4"')
	== 0) STR(: @\n), s);