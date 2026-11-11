numbers = [10, 20, 10, 30, 10, 40, 20]

num = int(input("Enter the number to count: "))

count = 0

for n in numbers:
    if n == num:
        count += 1

print("The number", num, "occurs", count, "times.")