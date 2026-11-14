		val = counter;
		printf("%x: %d\n", (unsigned int)pthread_self(), val + 1);
		counter = val + 1;