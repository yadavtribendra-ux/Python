numbers = [10, 15, 20, 25, 30, 35]

sum_even = 0

for num in numbers:
    if num % 2 == 0:
        sum_even += num

print("Sum of even numbers:", sum_even)