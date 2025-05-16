def compose_print(l):
    match l:
        case int(a):
            return "".join(f"\033[{x}m" for x in [a])
        case list:
            return "".join(f"\033[{x}m" for x in l)

SINGLE_STYLES = ([1, 3, 4, 5, 7, 21, 53] + list(range(30, 37)) + list(range(40, 48)))
COMPOSITE_STYLES = [[1,3,4,x] for x in range(40,47)] + [[1,4,x] for x in range(40,47)]

PRINT_STYLES = COMPOSITE_STYLES + SINGLE_STYLES

PRINT_RESUME = compose_print(0)

dummy_print = print
def print(*args, **kwargs):
    style = kwargs.get("s", None)
    if style is None:
        dummy_print(*args, **kwargs)
    else:
        kwargs.pop("s")
        dummy_print(compose_print(PRINT_STYLES[style]), *args, PRINT_RESUME, **kwargs)
