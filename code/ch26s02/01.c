typedef struct node *link;
struct node {
	unsigned char item;
	link l, r;
};