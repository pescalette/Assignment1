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


# hack to preserve console history
# while still clearing old menus
def clear_console(num_lines):
    move_cursor_up = f"\033[{num_lines}A"
    clear_line = "\033[K"
    clear_sequence = move_cursor_up + clear_line * num_lines
    
    if os.name == 'posix':
        os.system('tput civis')
        print(clear_sequence, end='')
    elif os.name == 'nt':
        os.system('cls')

    print("\033[0G")

# for modularity
class Menu:
    def __init__(self, items, title=None):
        self.items = items
        self.title = title
        self.valid_choices = [*range(1, len(self.items) + 1), 'q', 'b']
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
            #clear_console(current_menu.count_lines())
            current_menu.display()
            choice = current_menu.get_choice()

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
            self.cursor.executemany("INSERT INTO Students (FirstName, LastName, GPA, FacultyAdvisor , Major, Address, City, State, ZipCode, MobilePhoneNumber, isDeleted) VALUES (" + placeholders + ")", data)
            self.conn.commit()

    def display_all_students(self):
        self.cursor.execute('SELECT * FROM Students')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    def add_student(self, student_entry):
        self.cursor.execute("INSERT INTO Students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    student_entry)
        self.conn.commit()

    def update_student(self, update_column, update_value):              
        self.cursor.execute(f"UPDATE Students SET {update_column} = ?",
                    update_value)
        self.conn.commit()

    def soft_delete(self, studentid):
        self.cursor.execute(f"UPDATE Students SET {DataType.IS_DELETED} = 1 WHERE {DataType.STUDENT_ID} = ?",
                    (studentid,))
        self.conn.commit()
    
    # no pattern matching for strings which I assume is fine
    def query_students(self, query, query_column):
        self.cursor.execute(f"SELECT * FROM Students WHERE {query_column} = {query}")
        self.conn.commit()


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

    update_menu_items = [
        MenuItem("Major", function=partial(db.update_student, DataType.MAJOR, partial(validate, data_type=DataType.MAJOR, prompt="Enter new major:"))),
        MenuItem("GPA", function=partial(db.update_student, DataType.GPA, partial(validate, data_type=DataType.GPA, prompt="Enter new GPA:"))),
        MenuItem("City", function=partial(db.update_student, DataType.CITY, partial(validate, data_type=DataType.CITY, prompt="Enter new city:"))),
        MenuItem("State", function=partial(db.update_student, DataType.STATE, partial(validate, data_type=DataType.STATE, prompt="Enter new state:"))),
        MenuItem("Advisor", function=partial(db.update_student, DataType.FACULTY_ADVISOR, partial(validate, data_type=DataType.FACULTY_ADVISOR, prompt="Enter new advisor:")))
    ]
    update_menu = Menu(update_menu_items, title="Choose an attribute to update")

    query_menu_items = [
        MenuItem("Search by major", function=partial(db.query_students, partial(validate, data_type=DataType.MAJOR, prompt="Major:"), DataType.MAJOR)),
        MenuItem("Search by GPA", function=partial(db.query_students, partial(validate, data_type=DataType.GPA, prompt="GPA:"), DataType.GPA)),
        MenuItem("Search by city", function=partial(db.query_students, partial(validate, data_type=DataType.CITY, prompt="City:"), DataType.CITY)),
        MenuItem("Search by state", function=partial(db.query_students, partial(validate, data_type=DataType.STATE, prompt="State:"), DataType.STATE)),
        MenuItem("Search by advisor", function=partial(db.query_students, partial(validate, data_type=DataType.FACULTY_ADVISOR, prompt="Advisor:"), DataType.FACULTY_ADVISOR))
    ]
    query_menu = Menu(query_menu_items, title="Search/Display students by Major, GPA, City, State, or Advisor")

    add_student_argument = [
        partial(validate, f"{data_type.value}:", data_type)
        for data_type in DataType.__members__.values()
    ]

    main_menu_items = [
        MenuItem("Display all students", function=db.display_all_students),
        MenuItem("Add new student", function=partial(db.add_student, *add_student_argument)),  
        MenuItem("Update student", submenu=update_menu),
        MenuItem("Delete student", function=partial(db.soft_delete, partial(validate, data_type=DataType.STUDENT_ID, prompt="Student ID to be deleted:"))),
        MenuItem("Query students", submenu=query_menu)
    ]
    main_menu = Menu(main_menu_items, title='Student Database Menu')
    main_menu.run()
