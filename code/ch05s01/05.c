int 临时变量 = !(x % 2);
函数退出，局部变量x的存储空间释放;
if (临时变量) { /* 临时变量用完就释放 */
	/* do something */
} else {
	/* do some other thing */
}