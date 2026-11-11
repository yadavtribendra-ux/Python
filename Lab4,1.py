numbers =[2, 5, 8, 9, 12, 15, 18,20]
even_numbers =list(filter(lambda x: x%2==0, numbers))
squares = list(map(lambda x: x**2, even_numbers))
reasult = list(filter(lambda x: x>100, squares))
print("Even numbers:",even_numbers)
print ("Square of even numbers:", squares)
print ("Squares greater than 100:", reasult)
