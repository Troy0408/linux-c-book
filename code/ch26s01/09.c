void insert(link p)
{
	p->next = head;
	if (head)
		head->prev = p;
	head = p;
	p->prev = NULL;
}

void delete(link p)
{
	if (p->prev)
		p->prev->next = p->next;
	else
		head = p->next;
	if (p->next)
		p->next->prev = p->prev;
}