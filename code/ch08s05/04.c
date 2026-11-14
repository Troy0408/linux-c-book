struct complex_struct {
	double x, y;
} a[4] = { [0].x = 8.0 };

struct {
	double x, y;
	int count[4];
} s = { .count[2] = 9 };