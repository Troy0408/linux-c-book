#include <math.h>

struct complex_struct {
	double r, A;
};

double real_part(struct complex_struct z)
{
	return z.r * cos(z.A);
}

double img_part(struct complex_struct z)
{
	return z.r * sin(z.A);
}

double magnitude(struct complex_struct z)
{
	return z.r;
}

double angle(struct complex_struct z)
{
	return z.A;
}

struct complex_struct make_from_real_img(double x, double y)
{
	struct complex_struct z;
	z.A = atan2(y, x);
	z.r = sqrt(x * x + y * y);
}

struct complex_struct make_from_mag_ang(double r, double A)
{
	struct complex_struct z;
	z.r = r;
	z.A = A;
	return z;
}