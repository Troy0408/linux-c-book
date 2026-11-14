lock:
	if(mutex > 0){
		mutex = 0;
		return 0;
	} else
		挂起等待;
	goto lock;

unlock:
	mutex = 1;
	唤醒等待Mutex的线程;
	return 0;