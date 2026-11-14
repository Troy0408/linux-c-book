void delete(link p)
{
	link *pnext;
	for (pnext = &head; *pnext; pnext = &(*pnext)->next)
		if (*pnext == p) {
			*pnext = p->next;
			return;
		}
}