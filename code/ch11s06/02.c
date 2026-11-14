int binarysearch(int number)
{
	int mid, start = 0, end = LEN - 1;

	/* 假定a是排好序的 */
	/* mustbe(start, end, number)，因为a[start..end]就是整个数组a[0..LEN-1] */
	while (start <= end) {
	/* mustbe(start, end, number)，因为一开始进入循环时是正确的，每次循环也都维护了这个条件 */
		mid = (start + end) / 2;
		if (a[mid] < number)
			/* 既然a是排好序的，a[start..mid]应该都比number小，所以mustbe(mid+1, end, number) */
			start = mid + 1;
			/* 维护了mustbe(start, end, number) */
		else if (a[mid] > number)
			/* 既然a是排好序的，a[mid..end]应该都比number大，所以mustbe(start, mid-1, number) */
			end = mid - 1;
			/* 维护了mustbe(start, end, number) */
		else
			/* a[mid] == number，说明找到了 */
			return mid;
	}
	/* 
	 * mustbe(start, end, number)一直被循环维护着，到这里应该仍然成立，在a[start..end]范围之外一定不存在number，
	 * 但现在a[start..end]是空序列，在这个范围之外的正是整个数组a，因此整个数组a中都不存在number
	 */
	return -1;
}