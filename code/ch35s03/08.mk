lock:
	movb $0, %al
	xchgb %al, mutex
	if(al寄存器的内容 > 0){
		return 0;
	} else
		挂起等待;
	goto lock;

unlock:
	movb $1, mutex
	唤醒等待Mutex的线程;
	return 0;