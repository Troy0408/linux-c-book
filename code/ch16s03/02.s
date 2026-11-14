ret = scanf("%d", &man);
if (ret != 1 || man < 0 || man > 2) {
	printf("Invalid input! Please input 0, 1 or 2.\n");
	continue;
}