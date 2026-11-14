static inline void down_read(struct rw_semaphore *sem)
{
        might_sleep();
        rwsemtrace(sem,"Entering down_read");
        __down_read(sem);
        rwsemtrace(sem,"Leaving down_read");
}