/* TICK_USEC_TO_NSEC is the time between ticks in nsec assuming real ACTHZ and  */
/* a value TUSEC for TICK_USEC (can be set bij adjtimex)                */
#define TICK_USEC_TO_NSEC(TUSEC) (SH_DIV (TUSEC * USER_HZ * 1000, ACTHZ, 8))

/* some arch's have a small-data section that can be accessed register-relative
 * but that can only take up to, say, 4-byte variables. jiffies being part of
 * an 8-byte variable may not be correctly accessed unless we force the issue
 */
#define __jiffy_data  __attribute__((section(".data")))

/*
 * The 64-bit value is not volatile - you MUST NOT read it
 * without sampling the sequence number in xtime_lock.
 * get_jiffies_64() will do this for you as appropriate.
 */
extern u64 __jiffy_data jiffies_64;
extern unsigned long volatile __jiffy_data jiffies;