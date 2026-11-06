numbers = [-5, 10, -15, 20, -25, 30, -8]
negative_numbers = list(filter(lambda x: x < 0, numbers))
result = list(map(lambda x: abs(x), negative_numbers))

print("Original list:", numbers)
print("Negative numbers:", negative_numbers)
print("Absolute values:", result)