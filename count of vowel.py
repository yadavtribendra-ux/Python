text = input("Enter a string: ")

vowels = 0
consonants = 0

for char in text:
    if char.lower() in "aeiou":
        vowels += 1
    elif char.isalpha():
        consonants += 1

print("Number of vowels:", vowels)
print("Number of consonants:", consonants)