tuple1 = (10, 20, 30, 40, 50)
tuple2 = (30, 40, 60, 70, 80)

common = []

for x in tuple1:
    if x in tuple2:
        common.append(x)

print("Common elements:", tuple(common))