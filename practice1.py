words = ["banana", "fig", "apple"]
print(sorted(words, key=lambda w: len(w)))  

students = [("Ana", 85), ("Ben", 92), ("Cara", 78)]
print(sorted(students, key=lambda s: s[1]))  