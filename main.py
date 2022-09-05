import random
from kivy.app import App 
from kivy.lang import Builder
from accounts_handling import *
from kivy.uix.screenmanager import ScreenManager, Screen

def non_empty_str(chaine:str):
    return len(chaine) > 0 and not chaine.isspace()


def randchar():
    char_type = random.randint(1, 3)
    if char_type == 1:
        return chr(random.randint(65, 65 + 25))
    if char_type == 2:
        return chr(random.randint(97, 97 + 25))
    return str(random.randint(0, 9))

def rand_str(length):
    return "".join([randchar() for _ in range(length)])


class LoginScreenManager(ScreenManager):
    pass

class AdminScreen(Screen):
    pass

class StudentScreen(Screen):
    def penpal_match(self):
        account_info = self.parent.logged_account
        students_list = [account for account in accounts_database if account["account_status"] == "Student" and account != account_info and account["school_type"] == account_info["school_type"] and account["country"].upper() != account_info["country"].upper()]
        return random.choice(students_list)
    
    def write_palinfo(self):
        matched = self.penpal_match()
        self.ids["penpal_name"].text = matched["first_name"] + " " + matched["last_name"]
        for label_id in ["school_name", "school_address", "country"]:
            self.ids["penpal_" + label_id].text = matched[label_id]
        self.ids["penpal_city"].text = matched["city"] + ", " + matched["postal_code"]

class TeacherScreen(Screen):
    pass

class LoginWidget(Screen):
    def login_check(self, email, password, db):
        user_row = row_search(email, "email", db)
        if not user_row or user_row["password"] != password:
            self.ids["password_error"].text = "Wrong email address or password"
            return {}
        return user_row
    
    def login(self):
        get_email = self.ids["email_input"].text
        get_password = self.ids["password_input"].text
        check = self.login_check(get_email, get_password, accounts_database)
        if check:
            self.parent.logged_account = check
            self.parent.current = check["account_status"].upper() +"_screen"

class AdmninSchoolSubscription(Screen):
    def register_school(self):
        id_keys = ["school_name", "street_input", "city_input", "country_input", "postcode_input", "school_type", "register_id"]
        row = [self.ids[key].text for key in id_keys]
        refresh(schools_sheets, schools_database, row)

class SignUpWidget(Screen):
    def sign_up(self):
        new_row = ["0"]*6
        school_data = self.retrieve_school_data()
        input_check = self.valid_input()
        if school_data and input_check:
            for i,id_key in enumerate(["first_name", "last_name", "email_create", "password_create", "account_type"]):
                new_row[i] = self.ids[id_key].text
            new_row += school_data
            refresh(accounts_sheets, accounts_database, new_row)


    def retrieve_school_data(self):
        school_id = self.ids["school_id"].text
        school_information = list(row_search(school_id, "school_id", schools_database).values())
        if school_information: return school_information
        self.ids["id_invalid"].text = "Please enter an existing ID"
        return []


    def valid_input(self):
        fn_check = non_empty_str(self.ids["first_name"].text)
        if not fn_check:
            self.ids["fn_invalid"].text = "Please enter your first name"
        ln_check = non_empty_str(self.ids["last_name"].text)
        if not ln_check:
            self.ids["ln_invalid"].text = "Please enter your last name"
        em_check = self.email_isvalid()
        if not em_check:
            self.ids["email_invalid"].text = "Invalid email address"
        pw_check = self.password_isvalid()
        return em_check and pw_check and fn_check and ln_check



    def email_isvalid(self):
        get_mail = self.ids["email_create"].text
        if get_mail.count('@') != 1:
            return False
        at_index = get_mail.index('@')
        if len(get_mail[:at_index]) == 0 or len(get_mail[at_index+1:]) < 3:
            return False 
        if "." in get_mail[at_index+1:]:
            return True
        return False
    
    def password_isvalid(self):
        password = self.ids["password_create"].text
        confirm = self.ids["password_confirm"].text
        if len(password) < 8:
            self.ids["password_invalid"].text = "Password must be at least 8 characters long"
            return False
        if password != confirm:
            self.ids["confirm_invalid"].text = "Inputted information did not match with password"
            return False
        lower_check = upper_check = digit_check = special_check = False
        for char in password:
            if char.islower():
                lower_check = True
            elif char.isupper():
                upper_check = True
            elif char.isdigit():
                digit_check = True
            else:
                special_check = True
        if lower_check and upper_check and digit_check and special_check:return True
        self.ids["password_invalid"].text = "Password must contain at least one of each: upper-case letter, lower-case letter, digit, special character (such as #, %, *, etc)"
        return False

load_file = Builder.load_file("login.kv")

class LoginApp(App):
    def build(self):
        return load_file

LoginApp().run()