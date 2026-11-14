void vector_add(const double *x, const double *y, double *result)
{  
	int i;  
	for (i = 0; i < 64; ++i)  
		result[i] = x[i] + y[i];  
}