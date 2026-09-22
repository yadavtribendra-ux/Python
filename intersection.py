list1 = [1, 2, 3, 4, 5]
list2 = [2, 3, 4, 6, 7]
list3 = [2, 3, 8, 9]

intersection = list(set(list1) & set(list2) & set(list3))

print("Common elements:", intersection)