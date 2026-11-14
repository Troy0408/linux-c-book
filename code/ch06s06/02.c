int cond = 0; /* bool variable indicating error condition */
for (...) {
	for (...) {
		...
		if (出现错误条件) {
			cond = 1;
			break;
		}
	}
	if (cond)
		break;
}
if (cond)
	出错处理;