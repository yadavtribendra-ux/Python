strings = ["apple","Red", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew"]
Long_strings = list(filter(lambda x: len(x) >3, strings))
Upper_case = list(map(lambda x: x.upper(), Long_strings))
print ("Strings with more than 3 characters:", Long_strings)
print ("Uppercase strings:", Upper_case)
