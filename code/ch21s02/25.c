#define FOO(a, ...) a##__VA_ARGS__
FOO(1)
FOO(1,2,3,)