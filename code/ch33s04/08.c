#include <signal.h>

sig_atomic_t a=0;
int main(void)
{
	/* register a sighandler */
	while(!a); /* wait until a changes in sighandler */
	/* do something after signal arrives */
	return 0;
}