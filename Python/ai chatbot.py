
# Simple AI Chatbot
# Rule-based chatbot

print("=================================")
print("       🤖 PYTHON AI CHATBOT")
print("=================================")
print("Type 'bye' to exit the chatbot.\n")

while True:
    user = input("You: ").lower()

    # Greeting
    if "hello" in user or "hi" in user or "hey" in user:
        print("Bot: Hello! 👋 How are you?")

    # How are you
    elif "how are you" in user:
        print("Bot: I'm doing great! Thanks for asking. 😊")

    # Name
    elif "your name" in user:
        print("Bot: My name is PyBot 🤖.")

    # Who made you
    elif "who made you" in user or "who created you" in user:
        print("Bot: I was created by Mr.Yadav using Python!")

    # Study
    elif "study" in user or "exam" in user:
        print("Bot: Keep practicing! 📚 Consistency is the key to success.")

    # Python
    elif "python" in user:
        print("Bot: Python is a powerful and beginner-friendly programming language. 🐍")

    # Joke
    elif "joke" in user:
        print("Bot: Why do programmers prefer dark mode?")
        print("Bot: Because light attracts bugs! 😂")

    # Help
    elif "help" in user:
        print("Bot: I can talk about greetings, Python, studying, jokes and more!")

    # Time
    elif "time" in user:
        import datetime
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        print("Bot: The current time is", current_time)

    # Goodbye
    elif "bye" in user or "goodbye" in user:
        print("Bot: Goodbye! 👋 Have a great day!")
        break

    # Unknown message
    else:
        print("Bot: Hmm... I don't understand that yet. 🤔")
        print("Bot: Try asking me about Python, study, jokes, or my name.")

print("\nChatbot closed.")

