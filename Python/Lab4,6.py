words = ["Python", "Java", "Design", "Computer", "Human", "Artificial"]
filtered_words = list(filter(lambda x: x.endswith('n'), words))
result = list(map(lambda x: len(x), filtered_words))

print("Original words:", words)
print("Words ending with n:", filtered_words)
print("Lengths:", result)