#if MACHINE == 68000
    int x;
#elif MACHINE == 8086
    long x;
#else    /* all others */
    #error UNKNOWN TARGET MACHINE
#endif