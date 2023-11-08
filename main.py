import os
import sqlite3
import csv
from enum import Enum
from functools import partial

# for readability
class DataType(Enum):
    STUDENT_ID = "StudentId"
    FIRST_NAME = "FirstName"
    LAST_NAME = "LastName"
    GPA = "GPA"
    MAJOR = "Major"
    FACULTY_ADVISOR = "FacultyAdvisor"
    ADDRESS = "Address"
    CITY = "City"
    STATE = "State"
    ZIP_CODE = "ZipCode"
    MOBILE_PHONE_NUMBER = "MobilePhoneNumber"
    IS_DELETED = "isDeleted"

# for modularity
class Menu:
    def __init__(self, items, title=None):
        self.items = items
        self.title = title
        self.valid_choices = [*map(str, range(1, len(self.items) + 1)), 'q', 'b']
        self.menu_stack = [self]

    def __repr__(self):
        menu_str = f"{self.title}\n" if self.title else ""
        for index, item in enumerate(self.items, start=1):
            menu_str += f"{index}. {item.text}\n"
        menu_str += "b. Back"
        return menu_str

    def display(self):
        print(self)

    def get_choice(self):
        user_input = input(">")
        while(user_input not in self.valid_choices):
            user_input = input(">")
        return user_input
    
    def count_lines(self):
        num_lines = len(self.items) + 1
        if self.title is not None:
            num_lines += 1
        return num_lines

    def run(self):
        while True:
            current_menu = self.menu_stack[-1]
            current_menu.display()
            choice = current_menu.get_choice()
            print(choice)
            if choice == 'q':
                break
            elif choice == 'b':
                if len(self.menu_stack) > 1:
                    self.menu_stack.pop()
            else:
                chosen_item = current_menu.items[int(choice)-1]
                if chosen_item.submenu:
                    self.menu_stack.append(chosen_item.submenu)
                if chosen_item.function:
                    chosen_item.function()


class MenuItem:
    def __init__(self, text, function=None, submenu=None):
        self.text = text
        self.function = function
        self.submenu = submenu

    def __repr__(self) -> str:
        return self.text

# this keeps the functions smaller and only needs to connect once while the program runs
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('StudentDB.db')
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        self.conn.close()
    
    def import_students(self):
        with open('students.csv','rt') as file:
            data = csv.reader(file)
            next(data)
            placeholders = "?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, 0"  
            self.cursor.executemany(f"INSERT INTO Students (FirstName, LastName, Address, FacultyAdvisor, City, State, ZipCode, MobilePhoneNumber, Major, GPA, isDeleted) VALUES ({placeholders})", data)
            self.conn.commit()

    def display_all_students(self):
        self.cursor.execute('SELECT * FROM Students')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    def add_student(self, student_entry):
        self.cursor.execute("INSERT INTO Students (FirstName, LastName, GPA, Major, FacultyAdvisor, Address, City, State, ZipCode, MobilePhoneNumber, isDeleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                    tuple(student_entry))
        self.conn.commit()

    def update_student(self, ID, update_column, update_value):
        studentID = ID()
        while True:
            self.cursor.execute("SELECT * FROM Students WHERE StudentId = ?", (studentID,))
            if self.cursor.fetchone() is None:
                print("Invalid Student ID. Please enter a valid Student ID.")
                studentID = ID()
            else:
                break
        self.cursor.execute(f"UPDATE Students SET {update_column.value} = ? WHERE StudentId = ?", (update_value(), studentID))
        self.conn.commit()

    def soft_delete(self, ID):
        studentID = ID()
        while True:
            self.cursor.execute("SELECT * FROM Students WHERE StudentId = ?", (studentID,))
            if self.cursor.fetchone() is None:
                print("Invalid Student ID. Please enter a valid Student ID.")
                studentID = ID()
            else:
                break
        self.cursor.execute(f"UPDATE Students SET IsDeleted = 1 WHERE StudentId = ?",
                    (studentID,))
        self.conn.commit()
    
    # no pattern matching for strings which I assume is fine
    def query_students(self, query, query_column):
        self.cursor.execute(f"SELECT * FROM Students WHERE {query_column.value} = ?", (query(),))
        rows = self.cursor.fetchall()
        print(f"{len(rows)} result:")
        for row in rows:
            print(row)

# validates input for a DataType
def validate(prompt, data_type):
    while True:
        user_input = input(prompt)
        try:
            if data_type == DataType.STUDENT_ID:
                student_id = int(user_input)
                if student_id > 0:
                    return student_id
                else:
                    print("Invalid Student ID. Please enter a positive integer.")
            elif data_type in (DataType.FIRST_NAME, DataType.LAST_NAME, DataType.MAJOR, DataType.FACULTY_ADVISOR, DataType.ADDRESS, DataType.CITY, DataType.STATE, DataType.ZIP_CODE, DataType.MOBILE_PHONE_NUMBER):
                return user_input
            elif data_type == DataType.GPA:
                gpa = float(user_input)
                if 0.0 <= gpa <= 4.0:
                    return gpa
                else:
                    print("Invalid GPA. Please enter a number between 0.0 and 4.0.")
            elif data_type == DataType.IS_DELETED:
                is_deleted = int(user_input)
                if is_deleted in [0, 1]:
                    return is_deleted
                else:
                    print("Invalid value for 'isDeleted'. Please enter either 0 or 1.")
            else:
                print("Invalid data type.")
        except ValueError:
            print("Invalid input. Please enter a valid value.")


if __name__ == '__main__':
    db = Database()
    db.import_students()

    # these menus are disgustingly long because of all the input needed in the functions being passed in
    # however I think this is better than moving this code into 10 big functions and passing those functions in
    update_menu_items = [
        MenuItem("Major", function=partial(db.update_student, partial(validate, data_type=DataType.STUDENT_ID, prompt="Enter Student ID:"), DataType.MAJOR, partial(validate, data_type=DataType.MAJOR, prompt="Enter new Major:"))),
        MenuItem("GPA", function=partial(db.update_student, partial(validate, data_type=DataType.STUDENT_ID, prompt="Enter Student ID:"), DataType.GPA, partial(validate, data_type=DataType.GPA, prompt="Enter new GPA:"))),
        MenuItem("City", function=partial(db.update_student, partial(validate, data_type=DataType.STUDENT_ID, prompt="Enter Student ID:"), DataType.CITY, partial(validate, data_type=DataType.CITY, prompt="Enter new City:"))),
        MenuItem("State", function=partial(db.update_student, partial(validate, data_type=DataType.STUDENT_ID, prompt="Enter Student ID:"), DataType.STATE, partial(validate, data_type=DataType.STATE, prompt="Enter new State:"))),
        MenuItem("Advisor", function=partial(db.update_student, partial(validate, data_type=DataType.STUDENT_ID, prompt="Enter Student ID:"), DataType.FACULTY_ADVISOR, partial(validate, data_type=DataType.FACULTY_ADVISOR, prompt="Enter new Advisor:")))
    ]
    update_menu = Menu(update_menu_items, title="Choose an attribute to update")

    query_menu_items = [
        MenuItem("Search by Major", function=partial(db.query_students, partial(validate, data_type=DataType.MAJOR, prompt="Major:"), DataType.MAJOR)),
        MenuItem("Search by GPA", function=partial(db.query_students, partial(validate, data_type=DataType.GPA, prompt="GPA:"), DataType.GPA)),
        MenuItem("Search by City", function=partial(db.query_students, partial(validate, data_type=DataType.CITY, prompt="City:"), DataType.CITY)),
        MenuItem("Search by State", function=partial(db.query_students, partial(validate, data_type=DataType.STATE, prompt="State:"), DataType.STATE)),
        MenuItem("Search by Advisor", function=partial(db.query_students, partial(validate, data_type=DataType.FACULTY_ADVISOR, prompt="Advisor:"), DataType.FACULTY_ADVISOR))
    ]
    query_menu = Menu(query_menu_items, title="Search/Display students by Major, GPA, City, State, or Advisor")

    add_student_argument = [
        partial(validate, f"{data_type.value}:", data_type)
        for data_type in DataType.__members__.values() if data_type not in (DataType.STUDENT_ID, DataType.IS_DELETED)
    ]

    main_menu_items = [
        MenuItem("Display all students", function=db.display_all_students),
        MenuItem("Add new student", function=lambda: db.add_student([arg() for arg in add_student_argument])), # I genuinely do not understand this found it on stackoverflow and it solved my issue
        MenuItem("Update student", submenu=update_menu),
        MenuItem("Delete student", function=partial(db.soft_delete, partial(validate, data_type=DataType.STUDENT_ID, prompt="Student ID to be deleted:"))),
        MenuItem("Query students", submenu=query_menu)
    ]
    main_menu = Menu(main_menu_items, title='Student Database Menu')
    main_menu.run()
