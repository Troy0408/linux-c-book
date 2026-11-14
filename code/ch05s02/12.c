double area_point(double x1, double y1, double x2, double y2)
{
	double dx = x2 - x1;
	double dy = y2 - y1;
	double radius = sqrt(dx * dx + dy * dy);

	return 3.1416 * radius * radius;
}