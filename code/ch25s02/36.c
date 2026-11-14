char *str = "25 Dec 1988";
int day, year;
char monthname[20];

sscanf(str, "%d %s %d", &day, monthname, &year);