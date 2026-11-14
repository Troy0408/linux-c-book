double real_part(struct complex_struct z)
{
	if (z.t == RECTANGULAR)
		return z.a;
	else
		return z.a * cos(z.b);
}