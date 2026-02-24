import pandas as pd

# Sample student data for 64 students
students_data = {
    'Roll No': list(range(1, 65)),
    'Student Name': [
        'Aarthy S', 'Adhithya R', 'Aishwarya M', 'Akash K', 'Anand S',
        'Anitha V', 'Aravind P', 'Ashok Kumar S', 'Aswath R', 'Bavana S',
        'Bharath K', 'Bhavya S', 'Charan S', 'Darshini R', 'David S',
        'Deepak K', 'Divya S', 'Ganesh R', 'Gokul S', 'Harini V',
        'Harsha V', 'Hemalatha S', 'Ishwarya S', 'Jagan S', 'Jai Surya P',
        'Janani S', 'Kavin S', 'Keerthana S', 'Kiran S', 'Kishore R',
        'Lakshmi S', 'Madhan S', 'Mahesh K', 'Malini S', 'Manoj K',
        'Meena S', 'Mithra S', 'Murali S', 'Naveen K', 'Nivetha S',
        'Padma S', 'Praveen K', 'Preethi S', 'Priya S', 'Rahul S',
        'Rajesh K', 'Ramesh S', 'Ranjeeth S', 'Sabari S', 'Sai Kiran R',
        'Sanjay S', 'Sarath K', 'Sathish S', 'Sharon S', 'Siddarth S',
        'Siva S', 'Sneha S', 'Sowmiya S', 'Sri Ranjani S', 'Sudharsan S',
        'Surya P', 'Swetha S', 'Teja S', 'Venkatesh K'
    ]
}

df = pd.DataFrame(students_data)
df.to_excel('students.xlsx', index=False)
print('students.xlsx created successfully with', len(df), 'students')
