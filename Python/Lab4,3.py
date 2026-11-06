numbers = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12]
filtered_numbers = list(filter(lambda x: x % 2 == 0 or x % 3 == 0, numbers))
squares = list(map(lambda x: x ** 2, filtered_numbers))

print("Original numbers:", numbers)
print("Numbers divisible by 2 or 3:", filtered_numbers)
print("Squares:", squares)