while (1) {
	cliaddr_len = sizeof(cliaddr);
	connfd = accept(listenfd, 
			(struct sockaddr *)&cliaddr, &cliaddr_len);
	n = read(connfd, buf, MAXLINE);
	...
	close(connfd);
}