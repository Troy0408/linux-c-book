/* 从start到end之间找出第k小的元素 */
int order_statistic(int start, int end, int k)
{
	用partition函数把序列分成两半，中间的pivot元素是序列中的第i个;
	if (k == i)
		返回找到的元素;
	else if (k > i)
		从后半部分找出第k-i小的元素并返回;
	else
		从前半部分找出第k小的元素并返回;
}