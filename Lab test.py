
books = {
    101: "Python",
    102: "Java",
    103: "C++"
}

available = {101, 102, 103}
records = []
counts = {}

while True:
    print("\n1. Display Books")
    print("2. Borrow Book")
    print("3. Return Book")
    print("4. Show Records")
    print("5. Exit")

    n = input("Enter choice: ")

    if n == "1":
        print("Available Books:", available)
        print("All Books:", books)

    elif n == "2":
        sid = input("Student ID: ")
        bid = int(input("Book ID: "))

        if bid in books and bid in available:
            available.remove(bid)
            records.append((sid, bid, "Borrowed"))
            counts[sid] = counts.get(sid, 0) + 1
            print("Book borrowed successfully")
        else:
            print("Book unavailable or does not exist")

    elif n == "3":
        sid = input("Student ID: ")
        bid = int(input("Book ID: "))

        if bid in books and bid not in available:
            available.add(bid)
            records.append((sid, bid, "Returned"))
            print("Book returned successfully")
        else:
            print("Invalid book or book not borrowed")

    elif n == "4":
        print("Records:", records)
        print("Borrow Counts:", counts)

    elif n == "5":
        break

    else:
        print("Invalid choice")