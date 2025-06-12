import sqlite3

# Connect to SQLite database (creates 'data.db' if it doesn't exist)
connection = sqlite3.connect("data.db")
cursor = connection.cursor()

# Create table (if not already created)
table = '''
CREATE TABLE Students (name VARCHAR(30),class VARCHAR(10),marks INT,company VARCHAR(30),city VARCHAR(20),graduation_year INT,internship_completed BOOLEAN
)
'''


cursor.execute(table)

# Insert records
cursor.execute("INSERT INTO Students VALUES ('Ishaan', 'BTech', 82, 'IBM', 'Pune', 2023, 1)")
cursor.execute("INSERT INTO Students VALUES ('Kavya', 'MTech', 77, 'Accenture', 'Delhi', 2022, 1)")
cursor.execute("INSERT INTO Students VALUES ('Rohan', 'BSc', 68, 'Infosys', 'Kolkata', 2024, 0)")
cursor.execute("INSERT INTO Students VALUES ('Meera', 'MSc', 91, 'TCS', 'Chennai', 2021, 1)")
cursor.execute("INSERT INTO Students VALUES ('Arjun', 'MCom', 73, 'Wipro', 'Mumbai', 2023, 0)")

cursor.execute("INSERT INTO Students VALUES ('Diya', 'BTech', 85, 'Cyient', 'Hyderabad', 2022, 1)")
cursor.execute("INSERT INTO Students VALUES ('Neeraj', 'MTech', 62, 'HCL', 'Noida', 2023, 0)")
cursor.execute("INSERT INTO Students VALUES ('Sneha', 'BSc', 88, 'IBM', 'Bangalore', 2024, 1)")
cursor.execute("INSERT INTO Students VALUES ('Kabir', 'MSc', 79, 'JSW', 'Indore', 2023, 1)")
cursor.execute("INSERT INTO Students VALUES ('Tanya', 'MCom', 74, 'Tech Mahindra', 'Chandigarh', 2021, 0)")

cursor.execute("INSERT INTO Students VALUES ('Yash', 'BTech', 89, 'Cognizant', 'Pune', 2024, 1)")
cursor.execute("INSERT INTO Students VALUES ('Priya', 'MTech', 66, 'Infosys', 'Delhi', 2022, 0)")
cursor.execute("INSERT INTO Students VALUES ('Varun', 'BSc', 72, 'Capgemini', 'Kolkata', 2023, 1)")
cursor.execute("INSERT INTO Students VALUES ('Riya', 'MSc', 93, 'Wipro', 'Chennai', 2021, 1)")
cursor.execute("INSERT INTO Students VALUES ('Sameer', 'MCom', 71, 'TCS', 'Mumbai', 2023, 0)")

cursor.execute("INSERT INTO Students VALUES ('Anjali', 'BTech', 81, 'HCL', 'Hyderabad', 2022, 1)")
cursor.execute("INSERT INTO Students VALUES ('Nikhil', 'MTech', 76, 'IBM', 'Bangalore', 2023, 1)")
cursor.execute("INSERT INTO Students VALUES ('Lavanya', 'BSc', 87, 'Cyient', 'Chandigarh', 2024, 1)")
cursor.execute("INSERT INTO Students VALUES ('Raj', 'MSc', 65, 'TCS', 'Pune', 2021, 0)")
cursor.execute("INSERT INTO Students VALUES ('Pooja', 'MCom', 90, 'Infosys', 'Noida', 2022, 1)")

cursor.execute("INSERT INTO Students VALUES ('Karan', 'BTech', 70, 'JSW', 'Delhi', 2023, 0)")
cursor.execute("INSERT INTO Students VALUES ('Isha', 'MTech', 84, 'Wipro', 'Kolkata', 2022, 1)")
cursor.execute("INSERT INTO Students VALUES ('Siddharth', 'BSc', 75, 'HCL', 'Chennai', 2024, 1)")
cursor.execute("INSERT INTO Students VALUES ('Neha', 'MSc', 92, 'IBM', 'Mumbai', 2023, 1)")
cursor.execute("INSERT INTO Students VALUES ('Amit', 'MCom', 69, 'Capgemini', 'Bangalore', 2021, 0)")

cursor.execute("INSERT INTO Students VALUES ('Tanvi', 'BTech', 83, 'Accenture', 'Indore', 2022, 1)")
cursor.execute("INSERT INTO Students VALUES ('Rajat', 'MTech', 78, 'Tech Mahindra', 'Pune', 2023, 0)")
cursor.execute("INSERT INTO Students VALUES ('Swati', 'BSc', 86, 'Infosys', 'Delhi', 2024, 1)")
cursor.execute("INSERT INTO Students VALUES ('Dev', 'MSc', 64, 'Wipro', 'Hyderabad', 2021, 0)")
cursor.execute("INSERT INTO Students VALUES ('Muskan', 'MCom', 88, 'TCS', 'Chennai', 2022, 1)")

cursor.execute("INSERT INTO Students VALUES ('Yuvraj', 'BTech', 80, 'JSW', 'Bangalore', 2023, 0)")
cursor.execute("INSERT INTO Students VALUES ('Aisha', 'MTech', 91, 'IBM', 'Kolkata', 2024, 1)")
cursor.execute("INSERT INTO Students VALUES ('Rudra', 'BSc', 77, 'Infosys', 'Mumbai', 2022, 0)")
cursor.execute("INSERT INTO Students VALUES ('Simran', 'MSc', 68, 'HCL', 'Noida', 2023, 1)")
cursor.execute("INSERT INTO Students VALUES ('Aryan', 'MCom', 82, 'Wipro', 'Chandigarh', 2024, 0)")


# Display the inserted records
print("The inserted records:")
df = cursor.execute('''select * from Students''')
for row in df:
    print(row)

# Commit changes and close connection
connection.commit()
connection.close()
