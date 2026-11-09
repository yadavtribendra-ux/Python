import math
numbers = [1, 4, 9, 16, 20, 25, 30, 36, 49]
perfect_squares = list(filter(lambda x: math.isqrt(x)**2 == x, numbers))

print("Perfect square numbers:", perfect_squares)