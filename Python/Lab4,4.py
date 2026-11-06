numbers = [5, 10, 15, 20, 25, 30]
added_numbers = list(map(lambda x: x + 10, numbers))
result = list(filter(lambda x: x > 30, added_numbers))

print("Original list:", numbers)
print("After adding 10:", added_numbers)
print("Elements greater than 30:", result)