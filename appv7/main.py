import time
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition, SlideTransition
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle,Color
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.spinner import SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.factory import Factory
import webbrowser
from country_handling import *
from get_date import *
from sendmail import *
import mysql.connector

class AppDB:
    def __init__(self, db:mysql.connector.MySQLConnection):
        self.db = db
        self.today_date = datetime.date.today()
        self.logged_out = []
        if db != None:
            self.cursor = self.db.cursor()
            self.logged_account = []
            self.update_school_list()
            self.update_account_list()
        else:
            self.cursor = None
            self.local_school_db = None
            self.local_accounts_db = None
    
    def update_school_list(self):
        self.local_school_db = self.get_data(SCHOOLS)
    
    def update_account_list(self):
        self.local_accounts_db = self.get_data(ACCOUNTS)

    def update_date(self):
        self.today_date = extract_date()

    def update_account(self, account):
        self.logged_account = account
    
    def update_password(self, new_password):
        self.logged_account[PASSWORD_INDEX] = new_password
    
    def update_key(self, activation_key):
        self.logged_account[ACTIVATED_INDEX] = activation_key
    
    def update_penpals(self, new_penpal):
        self.logged_account[MATCHED_INDEX] += new_penpal + ";"

    def get_data(self, table):
        self.cursor.execute(f"SELECT * FROM {table}")
        return self.cursor.fetchall()

def db_connect():
    return mysql.connector.connect(host="bcgvls0if7wlqriv6qp4-mysql.services.clever-cloud.com", database="bcgvls0if7wlqriv6qp4", user="unxncuiaesoklyxu", password="0fGzCUVlSUyFsHb9rmGs", port="3306")

connection_error = False
app_db = AppDB(None)
try:
    app_db.__init__(db_connect())
    app_db.update_date()
except:
    connection_error = True


def upload_data(data, table):
    query = f"INSERT INTO {table} VALUES ("
    for i in range(len(data)):
        query += "%s"
        if i != len(data) - 1:
            query += ","
    query += ");"
    app_db.cursor.execute(query, data)
    app_db.db.commit()

def format_email(email_address:str):
    return "".join([char for char in email_address if isalphadigit(char)]).lower()

def paragraph_to_list(chaine:str):
    if not chaine.endswith(' '):
        chaine += ' '
    final_list = []
    last_word_index = 0
    for i in range(len(chaine)):
        if chaine[i] == " ":
            final_list.append(chaine[last_word_index:i])
            last_word_index = i + 1
        elif chaine[i] == "\n":
            final_list.append(chaine[last_word_index:i])
            final_list.append("\n")
            last_word_index = i + 1
    return final_list

    

def split_filename(filename):
    for i in range(-1, -len(filename) - 1, -1):
        if filename[i] == ".":
            return filename[:i], filename[i:]
    return filename, ""

def get_files(file_extension, directory="."):
    return [file for file in os.listdir(directory) if split_filename(file)[1] == file_extension]

def notnull(value):
    return "" if value == "NULL" else value

def read_matches(user_account, include_invisible=True):
    if include_invisible:
        entire_string = notnull(user_account[MATCHED_INDEX]) + notnull(user_account[INV_MATCH_INDEX])[:-1]
        return entire_string.split(";")
    return notnull(user_account[MATCHED_INDEX])[:-1].split(";")

def locate_record(table, requested_id, id_index):
    table_data = retrieve_data(table)
    for record in table_data:
        if record[id_index] == requested_id:
            return record
    return ()

def advanced_search(table, **kwargs):
    query = f"SELECT * FROM {table} WHERE "
    query_part, parameters = build_where_statement(**kwargs)
    query += query_part
    app_db.cursor.execute(query, tuple(parameters))
    content = app_db.cursor.fetchall()
    if len(content) == 1:
        return content[0]
    return content

def build_where_statement(**kwargs):
    statement = ""
    parameters = []
    for i, key in enumerate(kwargs):
        statement += key + '=' + '%s'
        parameters.append(kwargs[key])
        if i != len(kwargs) - 1:
            statement += " AND "
    return statement, parameters

def search_by_id(local_db, targeted_id, id_name):
    for record in local_db:
        if targeted_id == record[id_name]:
            return record
    return ()

def get_school_attribute(user_account, attribute_name=None):
    school_profile = search_by_id(app_db.local_school_db, user_account[SCHOOL_ID_INDEX], SCHOOL_ID_INDEX)
    if len(school_profile) == 0:
        school_profile = advanced_search(SCHOOLS, school_id=user_account[SCHOOL_ID_INDEX])
    if attribute_name != None:
        return school_profile[attribute_name]
    return school_profile
    

def get_account_value(account_email, value):
    app_db.cursor.execute(f"SELECT {value} FROM accounts WHERE email=" + "%s;",(account_email,))
    return notnull(app_db.cursor.fetchone()[0])

def del_data(table, **kwargs):
    query = f"DELETE FROM {table} WHERE "
    query_rest, parameters = build_where_statement(**kwargs)
    query += query_rest
    app_db.cursor.execute(query, parameters)
    app_db.db.commit()

def update_matches(user_account, new_match, visible=True):
    targeted_column = "matches" if visible else "invisible_matches"
    current_matches = get_account_value(user_account[EMAIL_INDEX], targeted_column)   
    update_attribute(ACCOUNTS, targeted_column, current_matches + new_match + ";", email=user_account[EMAIL_INDEX])

def find_penpal(user_account, account_list:list):
    unauthorized_accounts = [user_account[EMAIL_INDEX]] + read_matches(user_account)
    user_school = get_school_attribute(user_account)
    random.shuffle(account_list)
    if user_account[PREFERENCES_INDEX] != "all":
        countries = [get_country_by_code(country_code).lower() for country_code in user_account[PREFERENCES_INDEX].split(",")]
    print(account_list)
    print(unauthorized_accounts)
    for penpal in account_list:
        if penpal[EMAIL_INDEX] not in unauthorized_accounts:
            penpal_school = get_school_attribute(penpal)
            if penpal_school[COUNTRY_INDEX].lower() != user_school[COUNTRY_INDEX].lower() and penpal_school[SCHOOL_TYPE_INDEX].lower() == user_school[SCHOOL_TYPE_INDEX].lower():
                if user_account[PREFERENCES_INDEX] == "all":
                    return penpal
                if penpal_school[COUNTRY_INDEX].lower() in countries:
                    return penpal
    return ()

def penpal_match(user_account):
    accounts = advanced_search(ACCOUNTS, account_status='student', activation_key='0')
    matched_penpal = find_penpal(user_account, accounts)
    if matched_penpal == ():
        return ()
    update_attribute(ACCOUNTS, "timer_end", app_db.today_date + datetime.timedelta(30), email=user_account[EMAIL_INDEX])
    #app_db.update_penpals(matched_penpal[EMAIL_INDEX])
    update_matches(user_account, matched_penpal[EMAIL_INDEX])
    update_matches(matched_penpal, user_account[EMAIL_INDEX], visible=False)
    return matched_penpal

def update_attribute(table, attribute, new_value, **kwargs):
    query = f"UPDATE {table} SET {attribute}=" + "%s WHERE "
    for i, key in enumerate(kwargs):
        query += f"{key}='{kwargs[key]}'"
        if i != len(kwargs) - 1:
            query += " AND "
    app_db.cursor.execute(query, (new_value,))
    app_db.db.commit()

def shared_elements(ls1:list, ls2:list):
    shared = 0
    if len(ls1) <= len(ls2):
        selected_list = ls1
        other_list = ls2
    else:
        selected_list = ls2
        other_list = ls1
    for i in range(len(selected_list)):
        if selected_list[i] in other_list:
            shared += 1
    return shared

def retrieve_data(table, columns=None):
    if columns != None:
        app_db.cursor.execute(f"SELECT {','.join(columns)} FROM {table}")
    else:    
        app_db.cursor.execute(f"SELECT * FROM {table}")
    return app_db.cursor.fetchall()

def display_info(screen, profile, country_id, is_school=False, display=None, excluded_ids=[]):
    if display == None:    
        if is_school:
            school_search = profile
        else:
            school_search = get_school_attribute(profile)
        display = [profile[FIRST_NAME_INDEX] + " " + profile[LAST_NAME_INDEX], school_search[SCHOOL_ADDRESS_INDEX], school_search[CITY_INDEX].capitalize(), school_search[POSTCODE_INDEX], school_search[COUNTRY_INDEX].capitalize(), school_search[SCHOOL_NAME_INDEX].capitalize()]
        if is_school:
            display[0] = display[-1]
            display[-1] = school_search[SCHOOL_TYPE_INDEX].capitalize()
    disp_country = False
    for i, infos in enumerate(screen.ids):
        if infos not in excluded_ids:
            if infos.endswith("_country"):
                screen.ids[infos].text = " "*26 + display[i]
                disp_country = True
            else:    
                screen.ids[infos].text = "  " + display[i]
    if disp_country:    
        add_flag(screen, school_search[COUNTRY_INDEX], country_id)

def add_flag(screen, country_name, country_id):
    screen.ids[country_id].children[0].children[0].source = f"images/flags/{get_code_by_country(country_name)}.png"

def isalphadigit(chaine:str):
    return chaine.isdigit() or chaine.isalpha()

def is_consecutive(chaine:str, char_list):
    for char in char_list:
        for i in range(len(chaine) - 1):
            if chaine[i] == char == chaine[i + 1]:
                return True
    return False

def check_domain_char_type(domain:str):
    for char in domain:
        if not (isalphadigit(char) or char == "." or char == "-"):
            return False
    return True

def build_notif(apparition_date, notif_title, desc_content, read, notif_type):
    return [apparition_date, notif_title, desc_content, read, notif_type]

def top_domain_check(top_domain:str):
    return top_domain[0] != "."

def email_syntax_validation(email_address:str):
    if email_address.count("@") != 1:
        return False
    at_location = email_address.find("@")
    recipient_name = email_address[:at_location].lower()
    if len(recipient_name) == 0 or len(recipient_name) > 64:
        return False
    if not (isalphadigit(recipient_name[0]) and isalphadigit(recipient_name[-1])):
        return False
    if is_consecutive(recipient_name, "!#$%&.'*+-/=?^_`{|] "):
        return False
    domain_name = email_address[at_location + 1:]
    if len(domain_name) == 0 or len(domain_name) > 253:
        return False
    if not check_domain_char_type(domain_name):
        return False
    period_location = domain_name.find(".")
    if period_location == -1:
        return False
    return top_domain_check(domain_name) and top_domain_check(domain_name[period_location+1:])

def add_notification(account, notif):
    plus_char = "" if account[NOTIF_INDEX] == "[]" else ","
    updated_notif = account[NOTIF_INDEX][:-1] + plus_char + str(notif) + "]"
    print(updated_notif)
    update_attribute(ACCOUNTS, "notifications", updated_notif, email=account[EMAIL_INDEX])

def del_notification(account, notif):
    notif_list = eval(account[NOTIF_INDEX])
    notif_list.remove(notif)
    update_attribute(ACCOUNTS, "notifications", str(notif_list), email=account[EMAIL_INDEX])
    

class PalsManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.edited_password = ""
        self.logged_school = ""
        self.last_entered = ""
        self.entered_screens = []
        Clock.schedule_once(self.error_setup)

    def set_last_entered(self, screen_name):
        self.last_entered = screen_name
    
    def error_setup(self, dt):
        if connection_error:
            self.current = "lost_connection"
    
    def update_account(self, new_account=None):
        if new_account != None:
            self.logged_account = new_account
        else:    
            self.logged_account = list(advanced_search(ACCOUNTS, email=self.logged_email))
        self.logged_email = self.logged_account[EMAIL_INDEX]
        self.update_cache_file()
        if self.logged_account[ACCOUNT_STATUS_INDEX] == "admin":
            self.update_school()
    
    def update_school(self):
        self.logged_school = advanced_search(SCHOOLS, admin=self.logged_email)
        if self.logged_school == []:
            self.logged_school = ""
    
    def update_cache_file(self):
        filepath = "cache/" + format_email(self.logged_email) + ".cache"
        if not os.path.exists(filepath):
            filepath = "cache/" + format_email(self.logged_email) + ".rcache"
        with open(filepath, "w", encoding="utf-8") as fic:
            fic.write(str(self.logged_account))

class InitScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(self.launch_app)
    
    def launch_app(self, *args):
        self.parent.transition = NoTransition()
        self.parent.current = "login"

class LostConnectionScreen(Screen):
    def reload_app(self):
        self.ids["connect_error"].color = get_color_from_hex("#ffffff")
        self.ids["connect_error"].text = "Loading ..."
        Clock.schedule_once(self.internet_connect, 0.4)
    
    def clear_screen(self):
        self.ids["connect_error"].text = ""

    def internet_connect(self, dt):
        try:
            app_db.__init__(db_connect())
            self.parent.current = "login"
            app_db.update_date()
        except:
            self.ids["connect_error"].color = get_color_from_hex("#f54d53")
            self.ids["connect_error"].text = "Error: couldn't connect to the server"

class LoginScreen(Screen):
    #TODO limit attempts to prevent brute forcing 
    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(self.autologin)
        self.attempts = 0
        self.may_login = True
    
    def setup(self):
        self.parent.transition = SlideTransition()
        Clock.schedule_once(self.fix_inputs)

    def make_cache(self):
        if self.remember_me:
            filename, file_extension = split_filename(self.cache_path[6:])
            if os.path.exists(self.cache_path):    
                os.remove(self.cache_path)
            filepath = "cache/" + filename + ".r" + file_extension[1:]
            with open(filepath, "w", encoding="utf-8") as cache_writer:
                cache_writer.write(str(self.account))
        elif not os.path.exists(self.cache_path):
            with open(self.cache_path, "w", encoding="utf-8") as cache_writer:
                cache_writer.write(str(self.account))
    
    def generate_cache_path(self):
        self.cache_path = "cache/" + format_email(self.ids["email_login"].text) + ".cache"
    
    def fix_inputs(self, *args):
        self.ids["password_login"].font_size = self.ids["password_login"].height / 2.5
        self.ids["password_login"].padding =  self.ids["password_login"].padding = [7,(self.ids["password_login"].height - self.ids["password_login"].font_size) / 2.5,7,0]
        self.ids["email_login"].font_size = self.ids["password_login"].font_size
        self.ids["email_login"].padding = self.ids["password_login"].padding
    
    def autologin(self, dt):
        cache_files = get_files(".rcache", "cache")
        if len(cache_files) > 0:
            with open("cache/" + cache_files[0]) as login_fic:
                self.account = eval(login_fic.read())
                self.success_login()
    
    def access_cache_account(self):
        self.generate_cache_path()
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r", encoding="utf-8") as cache_reader:
                self.account = eval(cache_reader.readline())
                return True
        return False   

    def login_check(self):
        if len(self.ids["password_login"].text) < 8 or not email_syntax_validation(self.ids["email_login"].text):
            self.ids["password_login"].text = ""
            return False
        if not self.access_cache_account():
            self.account = advanced_search(ACCOUNTS, email=self.ids["email_login"].text)
        self.parent.logged_email = self.ids["email_login"].text
        saved_password = self.ids["password_login"].text
        self.ids["password_login"].text = ""
        return len(self.account) != 0 and self.account[PASSWORD_INDEX] == saved_password
    
    def success_login(self):
        if self.account[ACCOUNT_STATUS_INDEX] == "admin" and len(self.account[ACTIVATED_INDEX]) == 1:
            self.parent.logged_school = get_school_attribute(self.account)
        self.parent.update_account(self.account)
        app_db.logged_out.append(self.account[EMAIL_INDEX])
        app_db.update_account(self.account)
        self.attempts = 0
        self.parent.update_account()
        self.parent.current = "menu"

    def update_limit_timer(self, *args):
        captured_time = time.time()
        delta_time = int(captured_time - self.limit_timer) 
        if delta_time > 60:
            self.may_login = True
            self.attempts = 0
            self.timer_event.cancel()
            self.ids["wrong_login"].text = ""
        else:
            self.ids["wrong_login"].text = f"   10 attempts limit\nreached (reset in {60 - delta_time}s)"
    
    def login(self):
        try:  
            if self.may_login:
                if self.attempts == 10:
                    self.ids["wrong_login"].text = "   10 attempts limit\nreached (reset in 60s)"
                    self.may_login = False
                    self.limit_timer = time.time()
                    self.timer_event = Clock.schedule_interval(self.update_limit_timer, 1)
                    self.attempts += 1
                elif self.ids["password_login"].text != "" and self.ids["email_login"].text != "":
                    if self.login_check():
                        self.remember_me = self.ids["remember_checkbox"].active
                        self.make_cache()
                        self.success_login()
                    else:
                        self.ids["wrong_login"].text = "Wrong email or password"
                        self.attempts += 1
                else:
                        self.ids["wrong_login"].text = "Please enter email and password"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
    
    def clear_texts(self):
        self.ids["email_login"].text = ""
        self.ids["wrong_login"].text = ""
        self.ids["password_login"].text = ""
        self.ids["remember_checkbox"].active = False

class SpinnerOptions(SpinnerOption):
    def __init__(self, **kwargs):
        super(SpinnerOptions, self).__init__(**kwargs)
        self.background_color = get_color_from_hex("#27ffc3")


class MaxCharInput(TextInput):
    ## To check
    def __init__(self, char_limit, **kwargs):
        super().__init__(**kwargs)
        self.char_limit = char_limit

    def insert_text(self, substring, from_undo=False):
        if len(self.text) + substring > self.char_limit:
            added_text = ""
        else:
            added_text = substring
        return super().insert_text(added_text, from_undo)

class DescriptionInputScreen(Screen):
    def setup(self):
        if len(self.parent.logged_account[ACTIVATED_INDEX]) > 1:
            self.next_screen = "menu"
            self.prev_screen = "register_school"
        else:
            self.next_screen = "description_view"
            self.prev_screen = "description_view"
            current_description = self.parent.logged_school[DESCRIPTION_INDEX].split("\0")
            print(current_description)
            self.ids["desc_main"].text = current_description[0]
            self.ids["desc_ongoing"].text = current_description[1]
            self.ids["desc_planned"].text = current_description[2]
    
    def submit_inputs(self):
        final_data = ""
        for desc_id in self.ids:
            final_data += self.ids[desc_id].text
            if desc_id != "desc_planned":
                final_data += "\0"
        update_attribute(SCHOOLS, "description", final_data, admin=self.parent.logged_email)
        self.parent.update_account()
        self.parent.current = self.next_screen

class DescriptionViewScreen(Screen):
    #TODO: check if correct

    def disp_description(self):
        profile = self.parent.selected_profile
        descriptions = profile[DESCRIPTION_INDEX].split('\0')
        for i, desc_id in enumerate(self.ids):
            if desc_id.endswith("_description"):
                self.paragraph_rendering(descriptions[i], desc_id)
    
    def save_school(self):
        update_matches(self.parent.logged_account, self.parent.selected_profile[SCHOOL_ID_INDEX])
        self.parent.update_account()
    
    def clear_screen(self):
        for desc_id in self.ids:
            if desc_id.endswith("_description"):
                self.ids[desc_id].clear_widgets()
    
    def setup(self):
        if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "admin":
            self.ids["second_button"].text = "Edit"
        else:
            self.ids["second_button"].text = "Save school"
        self.disp_description()
    
    def right_btn_action(self):
        if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "admin":
            self.parent.current = "description_input"
        elif self.parent.selected_profile[SCHOOL_ID_INDEX] not in read_matches(self.parent.logged_account):
            self.save_school()
            self.parent.current = "school_search"

    
    def paragraph_rendering(self, paragraph:str, box_id):
        max_char_per_line = 40
        words = paragraph_to_list(paragraph)
        char_count = 0
        final_text = ""
        for wordtext in words:
            if wordtext !=  '':
                if char_count + len(wordtext) > max_char_per_line or wordtext == "\n":
                    new_label = Label(text=final_text)
                    self.ids[box_id].add_widget(new_label)
                    if wordtext != "\n":
                        final_text = wordtext + " "
                        char_count = len(wordtext) + 1
                    else:
                        final_text = ""
                        char_count = 0
                else:
                    final_text += wordtext + " "
                    char_count += len(wordtext) + 1
        if final_text != "":
            new_label = Label(text=final_text, font_size='16sp')
            self.ids[box_id].add_widget(new_label)
            final_text = ""


class SchoolRegistrationScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
    
    def launch_fixes(self):
        Clock.schedule_once(self.setup)
    
    def setup(self, dt):
        self.ids["spinner_school_type"].option_cls = SpinnerOptions
        for wid_id in self.ids:
            if wid_id.startswith("input_"):
                self.ids[wid_id].font_size = self.ids[wid_id].height / 2
                self.ids[wid_id].padding = [7,(self.ids[wid_id].height - self.ids[wid_id].font_size) / 2,7,0]
    
    def register_school(self):
        try:
            input_infos = [remove_useless_spaces(self.ids[key].text) for key in self.ids if key.startswith("input_")]
            error_labels = [self.ids[key] for key in self.ids if key.startswith("invalid_")]
            valid = True
            for i, info in enumerate(input_infos):
                if is_empty(info):
                    valid = False
                    error_labels[i].text = "This information is required"
            if valid:
                country = get_country_by_code(remove_useless_spaces(self.ids["input_country"].text))
                if country != "":
                    if self.parent.logged_school == "":
                        self.parent.logged_school = (input_infos[0], '0', country, input_infos[2], self.ids["spinner_school_type"].text.lower(),input_infos[3], input_infos[4], self.parent.logged_email, '\0\0')
                        upload_data(self.parent.logged_school, SCHOOLS)
                    else:
                        self.parent.logged_school = (input_infos[0], '0', country, input_infos[2], self.ids["spinner_school_type"].text.lower(),input_infos[3], input_infos[4], self.parent.logged_email, '\0\0')
                        app_db.cursor.execute("DELETE FROM schools WHERE admin=%s", (self.parent.logged_account[EMAIL_INDEX],))
                        app_db.db.commit()
                        upload_data(self.parent.logged_school, SCHOOLS)
                        # Pour remplacer les données (on exploite encore cela à priori)
                    self.parent.update_account()
                    self.parent.current = "description_input"
                else:
                    self.ids["invalid_country"].text = "Invalid country code"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"

class SignupScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.added_widgets = []
    
    def build_anchor(self, content):
        anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        anchor.add_widget(content)
        return anchor
    
    def build_text_input(self, hint_text):
        return TextInput(multiline=False, size_hint_x=0.8, size_hint_y=0.7, hint_text=hint_text)

    def build_label(self, text, color):
        return Label(text=text, color=color)
    
    def struct_add(self, widget):
        self.ids["main_layout"].add_widget(widget)
        self.added_widgets.append(widget)
        return widget

    def clear_added_widgets(self):
        for widget in self.added_widgets:
            self.ids["main_layout"].remove_widget(widget)
        self.added_widgets.clear()

    
    def build_structure(self,label_text, error_text):
        self.struct_add(self.build_label(label_text, get_color_from_hex("#ffffff")))
        self.struct_add(self.build_anchor(self.id_input))
        self.id_error = self.struct_add(Label(text=error_text, color=get_color_from_hex("#f54d53"), font_name="fonts/LunaticSuperstar-8KgB.otf", font_size='18sp'))

    def fix_inputs(self, *args):
        self.id_input.font_size = self.id_input.height / 2.5
        self.id_input.padding = [7,(self.id_input.height - self.id_input.font_size) / 2.5,7,0]
        for id_widget in self.ids:
            if id_widget.startswith("input_"):
                self.ids[id_widget].font_size = self.ids[id_widget].height / 2.5
                self.ids[id_widget].padding = [7,(self.ids[id_widget].height - self.ids[id_widget].font_size) / 2.5,7,0]
    
    def non_admin_build(self):
        self.build_structure("School ID", "")
        #self.id_input.font_size = sp(self.id_input.height / 2.5)
        #self.id_input.padding = [7,(self.id_input.height - self.id_input.height / 2.5) / 2.5,7,0]
        #self.build_structure("superior_email", "input_teacher", "invalid_teacher", "", "")
    
    def setup(self):
        self.account_status = self.parent.account_status
        self.id_input = self.build_text_input("School ID")
        self.clear_added_widgets()
        Clock.schedule_once(self.fix_inputs)
        if self.account_status != "admin":
            button_nav = self.ids["button_box"]
            self.ids["main_layout"].remove_widget(button_nav)
            self.non_admin_build()
            #Clock.schedule_once(self.ajuste_input)
            self.ids["main_layout"].add_widget(button_nav)
    
    def check_password(self):
        return len(self.ids["input_pw"].text) >= 8
    
    def check_password_confirm(self):
        return self.ids["input_pw"].text == self.ids["input_confirm"].text

    def check_email(self):
        return email_syntax_validation(self.ids["input_email"].text)
    
    def check_id(self):
        return advanced_search(SCHOOLS, school_id=remove_useless_spaces(self.id_input.text)) != []
    
    def clear_texts(self, text_list):
        for label_object in text_list:
            label_object.text = ""
    
    def clear_all(self):
        account_inputs, invalid_notices = self.retrieve_ids()
        self.clear_texts(invalid_notices)
        self.clear_texts(account_inputs)
    
    def retrieve_ids(self):
        add_notice = [] if self.account_status == "admin" else [self.id_error]
        add_input = [] if self.account_status == "admin" else [self.id_input]
        invalid_notices = [self.ids[id_item] for id_item in self.ids if id_item.startswith("invalid")] + add_notice
        account_inputs = [self.ids[id_input] for id_input in self.ids if id_input.startswith("input")] + add_input
        return account_inputs, invalid_notices
    
    def create_account(self):
        try:
            account_inputs, invalid_notices = self.retrieve_ids()
            self.clear_texts(invalid_notices)
            valid = True
            for i, info in enumerate(account_inputs):
                if is_empty(info.text):
                    valid = False
                    invalid_notices[i].text = "This information is required"
            if valid:
                if not self.check_email():
                    self.ids["invalid_email"].text = "Invalid email address"
                    valid = False
                elif len(advanced_search(ACCOUNTS, email=self.ids["input_email"].text)) > 0:
                    self.ids["invalid_email"].text = "There's already an account associated to this email"
                    valid = False
                if not self.check_password():
                    self.ids["invalid_pw"].text = "Password must be at least 8 characters long"
                    valid = False
                elif not self.check_password_confirm():
                    self.ids["invalid_confirm"].text = "Passwords do not match"
                    valid = False
                if self.account_status != "admin":
                    if not self.check_id():
                        self.id_error.text = "This school ID does not exist"
                        valid = False
                    else:
                        account_id = self.id_input.text
                else:
                    account_id = generate_activation_key(10) ## Changed need verification
            if valid:
                account = [self.ids["input_email"].text, account_id, self.ids["input_pw"].text, remove_useless_spaces(self.ids["input_fn"].text).capitalize(), remove_useless_spaces(self.ids["input_ln"].text).capitalize(), self.account_status, app_db.today_date, app_db.today_date, "NULL", "NULL", "NULLVL", "all", app_db.today_date, app_db.today_date, 0, '[]']
                self.parent.logged_account = account
                self.parent.current = "confirm_email"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"

class StatusScreen(Screen):
    def send_status(self, status):
        self.parent.account_status = status
        self.parent.current = "signup"
    
    def setup(self):
        Clock.schedule_once(self.fix_images)
    
    def fix_images(self, *args):
        for img_id in self.ids:
            if img_id.startswith("image_"):
                self.ids[img_id].size = [self.parent.parent.height, self.parent.parent.height]

class MenuScreen(Screen):
    def setup(self):
        try:
            activation_key = self.parent.logged_account[ACTIVATED_INDEX]
            self.active_button = True
            self.ids["status_label"].text = f"Account status : {self.parent.logged_account[ACCOUNT_STATUS_INDEX]}"
            self.ids["earth_planet"].source = "images/earth_planet.png"
            self.ids["main_text"].font_size = '20sp'
            if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "admin":
                if self.parent.logged_school == "":
                    self.ids["main_text"].text = "You haven't registered"
                    self.ids["secondary_text"].text = "your establishment yet."
                    self.ids["secondary_text"].color = self.ids["main_text"].color
                    self.ids["secondary_text"].font_size = self.ids["main_text"].font_size
                    self.ids["main_button"].text = "Register School"
                    self.next_screen = "register_school"
                elif self.parent.logged_school[SCHOOL_ID_INDEX] == "0":
                    self.ids["main_text"].text = "Your account hasn't been"
                    self.ids["secondary_text"].text = "activated yet."
                    self.ids["secondary_text"].color = self.ids["main_text"].color
                    self.ids["secondary_text"].font_size = self.ids["main_text"].font_size
                    self.ids["main_button"].text = "Activate account"
                    self.next_screen = "admin_activate"
                else:
                    self.ids["secondary_text"].color = get_color_from_hex("#87e84f")
                    self.ids["secondary_text"].font_size = '30sp'
                    self.ids["main_text"].text = "School ID :"
                    self.ids["secondary_text"].text = f"{self.parent.logged_account[SCHOOL_ID_INDEX]}"
                    self.ids["main_button"].text = "School Information"
                    self.parent.selected_profile = self.parent.logged_school
                    self.next_screen = "school_info"
            elif len(activation_key) == 1:    
                if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "student":
                    self.ids["main_button"].text = "Find Penpal"
                    self.ids["main_text"].text = "Next search available in:"
                    self.ids["secondary_text"].color = get_color_from_hex("#87e84f")
                    self.ids["secondary_text"].font_size = '30sp'
                    self.date_countdown()
                    self.next_screen = "penpal"
                else:
                    self.ids["main_button"].text = "Browse Schools"
                    self.next_screen = "school_search"
                    self.ids["main_text"].text = "School ID :"
                    self.ids["secondary_text"].text = f"{self.parent.logged_account[SCHOOL_ID_INDEX]}"
                    self.ids["secondary_text"].color = get_color_from_hex("#87e84f")
                    self.ids["secondary_text"].font_size = '30sp'
            else:
                self.ids["main_text"].text = "Waiting for admin"
                self.ids["secondary_text"].text = "permissison."
                self.ids["secondary_text"].color = self.ids["main_text"].color
                self.ids["secondary_text"].font_size = self.ids["main_text"].font_size
                self.ids["main_button"].text = "Pending..."

                self.next_screen = ""
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
    
    def send_notif(self, account):
        notification = build_notif(app_db.today_date, f"{account[ACCOUNT_STATUS_INDEX].capitalize()} account activation request", self.parent.logged_account[FIRST_NAME_INDEX] + " " + self.parent.logged_account[LAST_NAME_INDEX] + " | "  + self.parent.logged_account[ACCOUNT_STATUS_INDEX] + " | " + self.parent.logged_account[EMAIL_INDEX], False, "activation_request")
        add_notification(account, notification)
    
    def date_countdown(self):
        if app_db.today_date >= self.parent.logged_account[TIMER_END_INDEX]:
            self.ids["secondary_text"].text = "Available"
            self.available_match = True
        else:
            self.available_match = False
            left_days = self.parent.logged_account[TIMER_END_INDEX] - app_db.today_date
            self.ids["secondary_text"].text = f"{left_days.days} day"
            if left_days.days > 1:
                self.ids["secondary_text"].text += "s"
    
    def penpal_loading(self, dt):
        self.parent.matched_penpal = penpal_match(self.parent.logged_account)
        self.parent.update_account()
        Clock.schedule_once(self.penpal_switch, 1)
        
    def goto_screen(self, screen_name):
        if self.active_button:
            self.parent.transition = NoTransition()
            self.parent.current = screen_name
    
    def logout(self):
        if self.active_button:
            rcache_files = get_files(".rcache", "cache")
            for file in rcache_files:
                filename, _ = split_filename(file)
                os.rename("cache/" + file, "cache/" + filename + ".cache")
            self.parent.transition = SlideTransition()
            self.parent.current = "login"

    def penpal_switch(self, dt): 
        self.parent.transition = SlideTransition()
        if len(self.parent.logged_account[ACTIVATED_INDEX]) == 1:
            self.parent.current = "penpal"
        else:
            Factory.WarningPopup().open()
            self.setup()
    
    def transition(self):
        if self.active_button:
            if self.next_screen == "penpal":
                if self.available_match:
                    self.active_button = False
                    self.ids["earth_planet"].source = "images/earth_planet_joyful.png"
                    self.ids["secondary_text"].text = ""
                    self.ids["main_text"].text = "Loading ..."
                    self.ids["main_text"].font_size = '40sp'
                    Clock.schedule_once(self.penpal_loading, 1.3)
            elif self.next_screen != "":
                if self.next_screen in ["school_info", "admin_activate", "register_school", "school_search"]:
                    self.parent.transition = SlideTransition()
                self.parent.current = self.next_screen
            else:
                self.send_notif(advanced_search(ACCOUNTS, account_status="admin", school_id=self.parent.logged_account[SCHOOL_ID_INDEX]))

class WarningPopup(Popup):
    def __init__(self, parent_screen, **kwargs):
        super().__init__(**kwargs)
        self.auto_dismiss = False
        self.parent_screen = parent_screen
        self.size_hint = [0.8, 0.35]
        self.separator_color = get_color_from_hex("#29bc90")
        self.title = "Error: disabled account"
        self.title_font = "fonts/LunaticSuperstar-8KgB.otf"
        self.title_color = get_color_from_hex("#61f1ea")
        self.title_size = '18sp'
        self.main_layout = BoxLayout(orientation="vertical")
        label_1 = Label(text="Your school's admin decided")
        label_2 = Label(text="to disable your account.")
        label_3 = Label(text="You must re-activate it.")
        self.label_box = BoxLayout(orientation="vertical")
        self.label_box.add_widget(label_1)
        self.label_box.add_widget(label_2)
        self.label_box.add_widget(label_3)
        self.close_button = Button(text="Got it", background_color=get_color_from_hex("#29bc90"), size_hint_y=0.5)
        self.close_button.bind(on_press=self.dismiss)
        self.main_layout.add_widget(self.label_box)
        self.main_layout.add_widget(self.close_button)

class SchoolSearchScreen(Screen):
    #TODO school search engine
    def __init__(self, **kw):
        super().__init__(**kw)
        self.search_start = 0
        self.button_height = 150
        self.display_more_button = Button(text="Display more", color=get_color_from_hex("#89e1c7"), font_size='21sp', italic=True, background_color=get_color_from_hex("#0f1034"))
        self.display_more_anchor = AnchorLayout(anchor_x="center", anchor_y="top")
        self.display_more_button.bind(on_press=self.display_more)
        self.display_more_anchor.add_widget(self.display_more_button)
        self.may_shuffle = True
    
    def fix_inputs(self, *args):
        self.ids["search_input"].font_size = self.ids["search_input"].height / 2.5
        self.ids["search_input"].padding = [7,(self.ids["search_input"].height - self.ids["search_input"].font_size) / 2.5,7,0]
        #self.display_schools()
    
    def setup(self):
        try:
            self.schools_list = app_db.local_school_db
            if self.may_shuffle:
                random.shuffle(self.schools_list)
                self.display_schools()
                self.may_shuffle= False
            Clock.schedule_once(self.fix_inputs)
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
    
    def clear_screen(self):
        self.parent.set_last_entered("school_search")
        #self.parent.selected_profile = ""   Vérifier si cette ligne est nécessaire
    
    def display_more(self, *args):
        self.ids["school_display"].remove_widget(self.display_more_anchor)
        self.display_schools()
    
    def get_criterias(self):
        criterias = self.ids["search_input"].text.split(",")
        criterias = list(map(remove_useless_spaces, criterias))
        criterias = [criteria.upper() for criteria in criterias if criteria != '']
        return criterias

    def get_val(self, dict_object):
        return dict_object["val"]

    def return_upper(self, text:str):
        return text.upper()

    def get_search_results(self):
        search_criterias = self.get_criterias()
        if search_criterias == []:
            return app_db.local_school_db
        found_schools = []
        for school in app_db.local_school_db:
            school_upper = list(map(self.return_upper, list(school)))
            sharing = shared_elements(school_upper, search_criterias)
            if sharing > 0:
                found_schools.append({"name":school, "val":sharing})
        if found_schools == []:
            return []
        random.shuffle(found_schools)
        sorted_values = sorted(found_schools, key=self.get_val, reverse=True)
        return [school_info["name"] for school_info in sorted_values]
    
    def search_schools(self):
        self.search_start = 0
        self.ids["school_display"].clear_widgets()
        self.schools_list = self.get_search_results()
        self.display_schools()

    def display_schools(self, *args):
        try:
            if len(self.schools_list[self.search_start:]) < 10:
                search_end = len(self.schools_list[self.search_start:])
                extra_height = search_end
            else:
                search_end = 10
                extra_height = 11
            self.ids["school_display"].height = self.button_height * (self.search_start + extra_height)
            for i in range(self.search_start, self.search_start + search_end):
                new_school = self.schools_list[i]#.pop(0)
                anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=self.button_height)
                school_button = ProfileButton(new_school, self, "school_info", text=new_school[SCHOOL_NAME_INDEX], height=self.button_height, color=get_color_from_hex("#c2e4ed"), font_size='15sp', italic=True, background_color=get_color_from_hex("#0f1034"))
                school_button.bind(on_press=school_button.select_profile)
                anchor.add_widget(school_button)
                self.ids["school_display"].add_widget(anchor)    
            self.search_start += search_end
            if len(self.schools_list[self.search_start:]) > 0:
                self.ids["school_display"].add_widget(self.display_more_anchor)
        except ZeroDivisionError:
            self.parent.current = "lost_connection"

class SchoolScreen(Screen):
    #TODO display school info
    def setup(self):
        self.next_screen = "menu"
        Clock.schedule_once(self.set_screen)
        display_info(self, self.parent.selected_profile, "school_country", True)
    
    def set_screen(self, *args):
        self.next_screen = self.parent.last_entered

    def reset(self):
        pass

class ConfirmationScreen(Screen):
    def setup(self):
        try:
            self.waiting_validation = True
            self.saved_key = self.parent.logged_account[ACTIVATED_INDEX]
            self.may_resend = True
            self.ids["mail_notify"].text = f"{self.parent.logged_account[EMAIL_INDEX]}"
            self.ids["pre_loading"].text = "Loading ..."
            self.ids["pre_loading"].background_color = get_color_from_hex("#110f1b")
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
        Clock.schedule_once(self.fix_inputs)
    
    def fix_inputs(self, *args):
        self.ids["input_code"].font_size = self.ids["input_code"].height / 2.5
        self.ids["input_code"].padding = [7,(self.ids["input_code"].height - self.ids["input_code"].font_size) / 2.5,7,0]
    
    def launch_event(self):
        Clock.schedule_once(self.clear_loading)

    def clear_loading(self, *args):
        self.send_code()
        self.pre_loading_button = self.ids["pre_loading"]
        self.remove_widget(self.ids["pre_loading"])
    
    
    def code_expire(self, *args):
        self.has_expired = True
    
    def update_resend(self, dt):
        self.may_resend = time.time() >= self.send_moment + 60
        if self.may_resend:
            self.ids["resend_code"].text = "[ref=sendcode][u]Resend Code[/u][/ref]"
            self.send_timer_event.cancel()
        else:
            self.ids["resend_code"].text = f"[ref=sendcode][u]Resend Code (Available in {60 - int(time.time() - self.send_moment)}s)[/u][/ref]"

    def send_code(self, resend=False):
        try:
            if self.waiting_validation:
                self.has_expired = False
                self.attempts = 0
                if resend:
                    if self.may_resend:
                        self.ids["loading_label"].text = "Loading ..."
                        self.ids["invalid_code"].text = ""
                        self.expire_event.cancel()
                        Clock.schedule_once(self.email_event)
                else:
                    self.expire_event = Clock.schedule_once(self.code_expire, 60 * EXPIRATION_MINUTES)
                    self.parent.logged_account[ACTIVATED_INDEX] = send_confirmation_code(self.parent.logged_account[EMAIL_INDEX])
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
    
    def back_button_event(self):
        if len(self.parent.edited_password) > 0:
            self.parent.current = "settings"
        else:
            self.parent.current = "login"

    def email_event(self, dt):
        self.parent.logged_account[ACTIVATED_INDEX] = send_confirmation_code(self.parent.logged_account[EMAIL_INDEX])
        self.send_moment = time.time()
        self.expire_event = Clock.schedule_once(self.code_expire, 60 * EXPIRATION_MINUTES)
        self.may_resend = False
        self.send_timer_event = Clock.schedule_interval(self.update_resend, 1)
        self.ids["loading_label"].text = "A new code has successfully been sent"
        
    def clear_texts(self):
        if not self.may_resend:    
            self.send_timer_event.cancel()
        self.expire_event.cancel()
        if len(self.parent.edited_password) > 1:    
            self.parent.logged_account[ACTIVATED_INDEX] = self.saved_key
            self.parent.edited_password = ""
        self.ids["invalid_code"].text = ""
        self.ids["resend_code"].text = "[ref=sendcode][u]Resend Code[/u][/ref]"
        self.ids["input_code"].text = ""
        self.ids["loading_label"].text = ""
        self.ids["pre_loading"] = self.pre_loading_button
        self.ids["invalid_code"].color = get_color_from_hex("#f54d53")
        self.add_widget(self.pre_loading_button)
    
    def send_notif(self, account):
        notification = build_notif(app_db.today_date, f"{self.parent.logged_account[ACCOUNT_STATUS_INDEX].capitalize()} account activation request", self.parent.logged_account[FIRST_NAME_INDEX] + " " + self.parent.logged_account[LAST_NAME_INDEX] + " | "  + self.parent.logged_account[ACCOUNT_STATUS_INDEX] + " | " + self.parent.logged_account[EMAIL_INDEX], False, "activation_request")
        add_notification(account, notification)
    
    def transition(self, dt):
        if len(self.parent.edited_password) > 1:
            self.parent.current = "menu"
        else:
            if self.parent.logged_account[ACCOUNT_STATUS_INDEX] != "admin":
                self.send_notif(advanced_search(ACCOUNTS, account_status='admin', school_id=self.parent.logged_account[SCHOOL_ID_INDEX]))
            self.parent.current = "login"

    def generate_id(self):
        new_id = generate_activation_key(10)
        while advanced_search(SCHOOLS, school_id=new_id) != []:
            new_id = generate_activation_key(10)
        return new_id
    
    def validate_code(self):
        try:
            if self.waiting_validation:
                if self.ids["input_code"].text.isdigit():
                    self.attempts += 1
                    if self.attempts > 5 or self.has_expired:
                        self.ids["invalid_code"].text = "Your code has expired, please resend one"
                        return
                    if self.ids["input_code"].text == self.parent.logged_account[ACTIVATED_INDEX]:
                        self.waiting_validation = False
                        self.ids["invalid_code"].color = get_color_from_hex("#ffffff")
                        if len(self.parent.edited_password) > 0:
                            self.ids["invalid_code"].text = "Password changed successfully"
                            update_attribute(ACCOUNTS, "password", self.parent.edited_password, email=self.parent.logged_email)
                            self.parent.update_account()
                        else:    
                            self.ids["invalid_code"].text = "Account created successfully"
                            if self.parent.logged_account[ACCOUNT_STATUS_INDEX] != "admin":
                                update_matches(advanced_search(ACCOUNTS, school_id=self.parent.logged_account[SCHOOL_ID_INDEX], account_status="admin"), self.parent.logged_account[EMAIL_INDEX])
                                if len(advanced_search(ACCOUNTS, school_id=self.parent.logged_account[SCHOOL_ID_INDEX], account_status=self.parent.logged_account[ACCOUNT_STATUS_INDEX])) > 0:    
                                    self.parent.logged_account[ACTIVATED_INDEX] = generate_activation_key(10)
                                else:
                                    self.parent.logged_account[ACTIVATED_INDEX] = "0"
                            else:
                                self.parent.logged_account[SCHOOL_ID_INDEX] = self.generate_id()
                                self.parent.logged_account[ACTIVATED_INDEX] = self.parent.logged_account[SCHOOL_ID_INDEX]
                            upload_data(tuple(self.parent.logged_account), ACCOUNTS)
                        Clock.schedule_once(self.transition, 2.2)
                    else:
                        self.ids["invalid_code"].text = "Incorrect confirmation code"
                    self.ids["input_code"].text = ""
                else:
                    self.ids["invalid_code"].text = "Please enter a valid confirmation code"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"


class InputActivationScreen(Screen):
    def setup(self):
        if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "student":
            self.ids["label_receivers"].text = "The teacher and student you have chosen"
            self.ids["teacher_key"].hint_text = "Key received by teacher"
            self.ids["pre_teacher_input"].text = "Teacher's key"
            self.ids["pre_student_input"].text = "Student's key"
            self.ids["pre_student_input"].size_hint = [1, 1]
            self.ids["input_contain"].size_hint = [1, 1]
            if len(self.ids["input_contain"].children) == 0:
                self.ids["input_contain"].add_widget(self.ids["input_key"])
        else:
            self.ids["label_receivers"].text = "Your establishment's admin"
            self.ids["teacher_key"].hint_text = "Key received by admin"
            self.ids["pre_student_input"].text = ""
            self.ids["pre_student_input"].size_hint = [0.01, 0.01]
            if len(self.ids["input_contain"].children) > 0:
                self.ids["input_contain"].remove_widget(self.ids["input_key"])
        Clock.schedule_once(self.fix_inputs)
            
    def fix_inputs(self, *args):
        for wid_id in self.ids:
            if wid_id.endswith("key") and wid_id != "invalid_key":
                self.ids[wid_id].font_size = self.ids[wid_id].height / 2.5
                self.ids[wid_id].padding = [7,(self.ids[wid_id].height - self.ids[wid_id].font_size) / 2.5,7,0]
    
    def back_button_event(self):
        if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "student":
            self.parent.current = "activate"
        else:
            self.parent.current = "menu"

    def account_activation(self):
        if self.ids["input_key"].text + self.ids["teacher_key"].text == self.parent.logged_account[ACTIVATED_INDEX]:
            update_attribute(ACCOUNTS, "activation_key", "0", email=self.parent.logged_account[EMAIL_INDEX])
            self.parent.update_account()
            self.parent.current = "menu"
        else:
            self.ids["invalid_key"].text = "Error: one of these keys is invalid"

class IdInputScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def setup(self):
        Clock.schedule_once(self.fix_inputs)

    def fix_inputs(self, *args):
        self.ids["main_input"].font_size = self.ids["main_input"].height / 2.5
        self.ids["main_input"].padding = [7,(self.ids["main_input"].height - self.ids["main_input"].font_size) / 2.5,7,0]
    
    def verify_id(self):
        try:
            if self.ids["main_input"].text == self.parent.logged_account[SCHOOL_ID_INDEX]:
                update_attribute(ACCOUNTS, "activation_key", "0", email=self.parent.logged_email)
                update_attribute(SCHOOLS, "school_id", self.parent.logged_account[SCHOOL_ID_INDEX], admin=self.parent.logged_email)
                self.parent.update_account()
                self.parent.current = "menu"
            else:
                self.ids["id_error"].text = "Incorrect school ID"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"



class AdminActivateScreen(Screen):
    def setup(self):
        self.ids["pre_loading"].text = "Loading ..."
        self.ids["pre_loading"].background_color = get_color_from_hex("#110f1b")
        Clock.schedule_once(self.admin_transition, 1)
    
    def edit_school(self):
        self.parent.current = "register_school"
    
    def admin_transition(self, dt):
        send_admin_mail(self.parent.logged_account, self.parent.logged_school)
        self.pre_loading_button = self.ids["pre_loading"]
        self.remove_widget(self.ids["pre_loading"])

    def refresh(self):
        self.ids["pre_loading"] = self.pre_loading_button
        self.add_widget(self.pre_loading_button)

    def input_school_id(self):
        self.parent.current = "school_id_input"

    def open_doc(self):
        webbrowser.open("victorminator.github.io/binkspals")

class ActivateScreen(Screen):
    def setup(self):
        self.ids["first_text"].text = "Please submit your teacher's email"
        self.ids["second_line"].text = "as well as one of your school's student's email"
            #input_student.font_size = sp(input_student.height / 2.5)
            #input_student.padding = [7,(input_student.height - input_student.height / 2.5) / 2.5,7,0]
        Clock.schedule_once(self.fix_inputs)
    
    def fix_inputs(self, *args):
        for id_widget in self.ids:
            if id_widget.startswith("input_"):
                self.ids[id_widget].font_size = self.ids[id_widget].height / 2.5
                self.ids[id_widget].padding = [7,(self.ids[id_widget].height - self.ids[id_widget].font_size) / 2.5,7,0]
    
    def clear_all(self):
        self.clear_errors()
        self.ids["input_student"].text = ""
        self.ids["input_teacher"].text = ""

    def clear_errors(self):
        error_boxes = [widget for widget in self.ids if widget.endswith("_box")]
        for box in error_boxes:
            for error_text in self.ids[box].children:
                error_text.text = ""
    
    def check_inputs(self):
        self.clear_errors()
        self.teacher_check = self.check_input("teacher")
        if self.teacher_check == []:
            return False
        self.student_check = self.check_input("student")
        if self.student_check == []:
            return False
        return True
    
    
    def check_input(self, input_info, alt_text=None):
        if alt_text == None:
            alt_text = input_info
        input_account = advanced_search(ACCOUNTS, email=self.ids["input_" + input_info].text, school_id=self.parent.logged_account[SCHOOL_ID_INDEX], account_status=alt_text, activation_key="0")
        if input_account == []:
            self.ids["invalid_" + input_info].text = f"There's no {alt_text} account from"
            self.ids["invalid_" + input_info + "2"].text = f"{get_school_attribute(self.parent.logged_account, SCHOOL_NAME_INDEX)}"
            self.ids["invalid_" + input_info + "3"].text = "associated to this email"
            return []
        return input_account
    
    def send_notif(self, account):
        notification = build_notif(app_db.today_date, f"{account[ACCOUNT_STATUS_INDEX].capitalize()} account activation request", self.parent.logged_account[FIRST_NAME_INDEX] + " " + self.parent.logged_account[LAST_NAME_INDEX] + " | "  + self.parent.logged_account[ACCOUNT_STATUS_INDEX] + " | " + self.parent.logged_account[EMAIL_INDEX], False, "activation_request")
        add_notification(account, notification)
    
    def send_key(self):
        try:
            if self.check_inputs():
                self.parent.logged_account[ACTIVATED_INDEX] = generate_activation_key(20)
                self.send_notif(self.teacher_check)
                self.send_notif(self.student_check)
                self.parent.current = "menu"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"


class ForgotScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
    
    def setup(self):
        Clock.schedule_once(self.fix_inputs)
    
    def fix_inputs(self, *args):
        self.ids["recovery_mail"].font_size = self.ids["recovery_mail"].height / 2.5
        self.ids["recovery_mail"].padding = [7,(self.ids["recovery_mail"].height - self.ids["recovery_mail"].font_size) / 2.5,7,0]

    def send_password(self):
        try:
            self.get_mail = self.ids["recovery_mail"].text
            self.locate_account = advanced_search(ACCOUNTS, email=self.get_mail)
            if len(self.locate_account) > 0:
                self.ids["recovery_error"].text = ""
                self.ids["recovery_error"].font_size = '28sp'
                self.ids["recovery_error"].color = get_color_from_hex("#87e84f")
                self.ids["recovery_error"].text = "Loading ..."
                Clock.schedule_once(self.send_event)
            else:
                self.ids["recovery_error"].text = ""
                self.ids["recovery_error"].color = get_color_from_hex("#f54d53")
                self.ids["recovery_error"].font_size = '20.5sp'
                self.ids["recovery_error"].text = "No account is associated with this email"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
        
    def clear_texts(self):
        self.ids["recovery_error"].text = ""
        self.ids["recovery_mail"].text = ""
    
    def send_event(self, dt):
        send_email(self.get_mail, "BinksPals password recovery", f"Hello {self.locate_account[FIRST_NAME_INDEX]},\n\nYou have asked to recover your BinksPals password.\nSo here it is: {self.locate_account[PASSWORD_INDEX]}\n\nWishing you a nice day,\n- The BinksPals team")
        self.parent.current = "login"


class PenpalScreen(Screen):
    def reset_texts(self):
        for label_id in self.ids:
            self.ids[label_id].text = ""

    def match(self):
        try:
            self.parent.update_account()
            matched_penpal = self.parent.matched_penpal
            excluded_label = self.ids.pop("main_title")
            if matched_penpal != ():    
                display_info(self, matched_penpal, "pal_country")
                excluded_label.text = "You have a new penpal !"
                self.parent.update_account()
            else:
                self.reset_texts()
                self.ids["pal_country"].children[0].children[0].source = "images/flags/empty_flag.png"
                excluded_label.text = "Oops! No matches available yet"
            self.ids["main_title"] = excluded_label
        except ZeroDivisionError:
            self.parent.current = "lost_connection"

class SupportScreen(Screen):
    def donation_page_link(self):
        webbrowser.open("https://nuitducode.github.io/DOCUMENTATION/PYTHON/01-presentation/")

class SettingsScreen(Screen):
    def setup(self):
        if len(self.parent.logged_account[ACTIVATED_INDEX]) == 1:
            self.ids["is_invisible"].active = bool(int(self.parent.logged_account[ACTIVATED_INDEX]))
        else:
            self.ids["is_invisible"].active = False
        countries = self.parent.logged_account[PREFERENCES_INDEX]
        if countries == "all":    
            self.ids["country_codes"].text = ""
        else:
            self.ids["country_codes"].text = countries
        self.edited = False
        Clock.schedule_once(self.fix_inputs)
    
    def fix_inputs(self, *args):
        for id_widget in ["confirm_new", "new_password", "country_codes"]:
            self.ids[id_widget].font_size = self.ids[id_widget].height / 2.5
            self.ids[id_widget].padding = [7,(self.ids[id_widget].height - self.ids[id_widget].font_size) / 2.5,7,0]

    def invisible_set(self):
        new_val = "1" if self.ids["is_invisible"].active else "0"
        if new_val != self.parent.logged_account[ACTIVATED_INDEX] and len(self.parent.logged_account[ACTIVATED_INDEX]) == 1:
            update_attribute(ACCOUNTS, "activation_key", new_val, email=self.parent.logged_email)
            self.parent.logged_account[ACTIVATED_INDEX] = new_val
            self.edited = True
    
    def check_pw(self):
        if len(self.ids["new_password"].text) < 8:
            self.ids["invalid_new"].text = "Password must be at least 8 characters long"
            return False
        if self.ids["new_password"].text != self.ids["confirm_new"].text:
            self.ids["invalid_new"].text = "Passwords do not match"
            return False
        return True

    def update_settings(self):
        try:
            self.set_countries()
            self.invisible_set()
            if self.edited:
                self.parent.update_account()
            if len(self.ids["new_password"].text) > 0:
                if self.check_pw():
                    self.parent.transition = SlideTransition()
                    self.parent.edited_password = self.ids["new_password"].text
                    self.parent.current = "confirm_email"
            else:
                self.parent.transition = SlideTransition()
                self.parent.current = "menu"
        except ZeroDivisionError:
            self.parent.current = "lost_connection"
    
    def set_countries(self):
        self.country_codes = self.ids["country_codes"].text.split(",")
        if remove_useless_spaces(self.ids["country_codes"].text) != self.parent.logged_account[PREFERENCES_INDEX]:
            if self.country_codes == [''] or self.check_codes():
                self.edited = True
                if self.country_codes != ['']:  
                    new_val = ",".join(self.country_codes)
                else:
                    new_val = "all"
                update_attribute(ACCOUNTS, "country_preferences", new_val, email=self.parent.logged_email)
                self.parent.logged_account[PREFERENCES_INDEX] = new_val
            else:
                self.ids["invalid_countries"].text = "Invalid country codes"

    def check_codes(self):
        for i in range(len(self.country_codes)):
            self.country_codes[i] = remove_useless_spaces(self.country_codes[i].lower())
            if self.country_codes[i] not in get_countries():
                return False
        return True
    
    def clear_errors(self):
        self.ids["invalid_countries"].text = ""
        self.ids["invalid_new"].text = ""
        self.ids["new_password"].text = ""
        self.ids["confirm_new"].text = ""
        self.edited = False

class HelpScreen(Screen):
    def open_doc(self):
        webbrowser.open("victorminator.github.io/binkspals")
    
    def open_safety(self):
        webbrowser.open("victorminator.github.io/binkspals/security")

class ProfileScreen(Screen):
    def profile_display(self):
        display_info(self, self.parent.selected_profile, "profile_country")
    
    def reset(self):
        pass

class ConfirmationPopup(Popup):
    def __init__(self, parent_func, confirmation_text, title="Confirm action", **kwargs):
        super().__init__(**kwargs)
        self.auto_dismiss = False
        self.parent_func = parent_func
        self.size_hint = [0.8, 0.35]
        self.separator_color = get_color_from_hex("#29bc90")
        self.title = title
        self.title_font = "fonts/LunaticSuperstar-8KgB.otf"
        self.title_color = get_color_from_hex("#61f1ea")
        self.title_size = '18sp'
        main_label = Label(text=confirmation_text)
        main_layout = BoxLayout(orientation="vertical")
        button_layout = BoxLayout(orientation="horizontal", size_hint_y=0.5)
        back_button = Button(text="Cancel", background_color=get_color_from_hex("#29bc90"))
        back_button.bind(on_press=self.dismiss)
        disable_button = Button(text="Confirm", background_color=get_color_from_hex("#29bc90"))
        disable_button.bind(on_press=self.popup_confirm)
        button_layout.add_widget(back_button)
        button_layout.add_widget(disable_button)
        main_layout.add_widget(main_label)
        main_layout.add_widget(button_layout)
        self.add_widget(main_layout)
    
    def popup_confirm(self, *args):
        self.parent_func()
        self.dismiss()

class ManageAccountScreen(Screen):
    def information_display(self):
        self.profile = self.parent.selected_profile
        info = [self.profile[FIRST_NAME_INDEX] + " " + self.profile[LAST_NAME_INDEX], self.profile[EMAIL_INDEX], "Created on: " + datetext(self.profile[CREATION_DATE_INDEX]), "Activated: Yes" if len(self.profile[ACTIVATED_INDEX]) == 1 else "Activated: No", "Last connected: " + datetext(self.profile[LAST_CONNECTED_INDEX]), "Act. key: None" if len(self.profile[ACTIVATED_INDEX]) == 1 else "Act. key: " + self.profile[ACTIVATED_INDEX]]
        display_info(self, None, None, display=info, excluded_ids=["action_button"])
    
    def setup(self):
        self.information_display()
        if len(self.profile[ACTIVATED_INDEX]) > 1:
            self.action = "activate"
            self.user_value = "0"
        else:
            self.action = "disable"
            self.user_value = "9999999999"
        self.ids["action_button"].text = f"{self.action.capitalize()} account"

    def confirm_disable(self):
        Factory.ConfirmationPopup(self.alter_state, f" Are you sure you want\nto {self.action} this account?").open()

    def alter_state(self, *args):
        update_attribute(ACCOUNTS, "activation_key", self.user_value, email=self.profile[EMAIL_INDEX])
        app_db.update_account_list()
        #self.parent.update_account()
        self.parent.current = "book"


class ProfileButton(Button):
    def __init__(self, penpal_profile, parent_screen, next_screen, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.penpal_profile = penpal_profile
        self.next_screen = next_screen
    
    def select_profile(self, arg):
        self.parent_screen.parent.selected_profile = self.penpal_profile
        self.parent_screen.parent.transition = SlideTransition()
        self.parent_screen.parent.current = self.next_screen


class BookScreen(Screen):   
    def build_penpal_info(self):
        self.parent.transition = NoTransition()
        self.penpal_records = []
        for penpal_email in self.penpal_email_list:
            if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "teacher":
                new_record = search_by_id(app_db.local_school_db, penpal_email, SCHOOL_ID_INDEX)
            else:
                new_record = search_by_id(app_db.local_accounts_db, penpal_email, EMAIL_INDEX)
            if new_record != () and new_record not in self.penpal_records:
                self.penpal_records.append(new_record)
        print(self.penpal_records) 
   
    def build_list(self):
        try:
            self.penpal_email_list = read_matches(self.parent.logged_account, include_invisible=False)
            if self.penpal_email_list == [""]:
                self.penpal_email_list = []
            if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "student":
                self.ids["book_title"].text = "Penpal Book"
                next_screen = "profile"
            elif self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "teacher":
                self.ids["book_title"].text = "Starred"
                next_screen = "school_info"
            else:
                self.ids["book_title"].text = "Manage accounts"
                next_screen = "manage"
            self.ids["book_layout"].clear_widgets()
            self.ids["book_layout"].size_hint_y = None
            self.build_penpal_info()
            button_height = 150
            self.ids["book_layout"].height = button_height * len(self.penpal_email_list)
            for penpal in self.penpal_records:
                if self.parent.logged_account[ACCOUNT_STATUS_INDEX] == "teacher":
                    button_text = penpal[SCHOOL_NAME_INDEX]
                else:
                    button_text = penpal[FIRST_NAME_INDEX] + " " + penpal[LAST_NAME_INDEX]
                anchor = AnchorLayout(anchor_x="center", anchor_y="top")
                penpal_button = ProfileButton(penpal, self, next_screen, height=button_height,text=button_text, color=get_color_from_hex("#c2e4ed"), font_size='19sp', italic=True, background_color=get_color_from_hex("#0f1034"))
                penpal_button.bind(on_press=penpal_button.select_profile)
                anchor.add_widget(penpal_button)
                self.ids["book_layout"].add_widget(anchor)
        except ZeroDivisionError:
            self.parent.current = "lost_connection"

class AlignableLabel(Label):
   def on_size(self, *args):
      self.text_size = self.size

class ParagraphLayout(BoxLayout):
    def __init__(self, paragraph_content="", max_labels=3, max_char_per_line=40, text_align="left", font_size='18sp', **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.paragraph_content = paragraph_content
        self.max_char_per_line = max_char_per_line
        self.font_size = font_size
        self.text_align = text_align
        self.max_lines = max_labels
        self.split_paragraph()
        self.build_labels()
    
    def build_labels(self):
        for line in self.lines:
            new_label = AlignableLabel(text=line, size_hint=(1.0, 1.0), halign=self.text_align, valign="middle", font_size=self.font_size)
            self.add_widget(new_label)
        self.add_widget(Label(size_hint_y=1))

    def split_paragraph(self):
        self.lines = [self.paragraph_content[start:start+self.max_char_per_line] for start in range(0, len(self.paragraph_content), self.max_char_per_line)]
        print(self.lines)
        self.fix_lines()
    
    def exceeded_line_limit(self):
        return len(self.lines) > self.max_lines
    
    def pop_char(self, i):
        self.lines[i + 1] = self.lines[i][-1] + self.lines[i + 1]
        self.lines[i] = self.lines[i][:-1]
    
    def rm_exceeding_lines(self):
        initial_len = len(self.lines)
        while self.exceeded_line_limit():
            self.lines.pop(-1)
        if len(self.lines) < initial_len:
            self.lines[-1] = self.lines[-1] + "..."

    def fix_lines(self):
        extra_line = ""
        for i in range(len(self.lines)):
            while self.lines[i][-1] != " " or len(self.lines[i]) > self.max_char_per_line:
                if i < len(self.lines) - 1:
                    self.pop_char(i)
                else:
                    extra_line = self.lines[i][-1] + extra_line
                    self.lines[i] = self.lines[i][:-1]
        if extra_line != "":
            self.lines.append(extra_line)
        self.rm_exceeding_lines()

class NotifWidget(Button):
    def __init__(self, parent_screen, apparition_date, notif_title, desc_content, read, notif_type, **kwargs):
        super().__init__(**kwargs)
        self.logo_images = {"activation_request":"images/user.png"}
        self.background_color = get_color_from_hex("#0f1034")
        self.date = apparition_date
        self.title = notif_title
        self.desc_content = desc_content
        self.left_layout = BoxLayout(orientation="vertical")
        self.read = read
        self.type = notif_type
        self.full_notif = build_notif(self.date, self.title, self.desc_content, self.read, self.type)
        if self.type == "activation_request":
            self.desc_content = self.desc_content.replace(" |", ",")
            self.desc_content += " requires your validation to activate their account. "
        self.parent_screen = parent_screen
        self.content = [self.title, self.desc_content, self.date]
        self.bind(on_press=self.select_notif)
    
    def build_contents(self, *args):
        self.layout = BoxLayout(orientation="horizontal")
        self.layout.center_x = self.parent.center_x  # To check
        self.layout.center_y = self.parent.center_y # To check
        self.layout.size = self.size
        print(self.center_x, self.center_y)
        print(self.pos)
        self.build_left()
        self.build_separator()
        self.layout.add_widget(Label(size_hint_x=0.15, size_hint_y=1.0))
        self.build_main()
        self.add_widget(self.layout)

    def select_notif(self, *args):
        print(self.size)
        print(self.pos)
        if self.type != "":
            self.parent_screen.parent.selected_notif = self.full_notif
            self.parent_screen.parent.current = self.type
    
    def build_main(self):
        body_layout = BoxLayout(orientation="vertical", size_hint_x=3.0)
        title = AlignableLabel(size_hint=(1.0, 0.75), halign="left", valign="middle", text=self.title, bold=True, font_size='14.5sp')
        body = ParagraphLayout(paragraph_content=self.desc_content, max_char_per_line=40, font_size='13sp')
        body_layout.add_widget(title)
        body_layout.add_widget(body)
        self.layout.add_widget(body_layout)

    def build_buttons(self):
        pass

    def get_img_src(self):
        if self.type in self.logo_images.keys():
            return self.logo_images[self.type]
        return "images/text-lines.png"
    
    def build_left(self):
        self.left_layout.add_widget(Label(size_hint_y=0.3))
        self.build_typelogo()
        self.build_date()
        #self.left_layout.add_widget(Label(size_hint_y=0.8))
        self.layout.add_widget(self.left_layout)

    def build_typelogo(self):
        anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=1.5)
        logo = Image(source=self.get_img_src(), size_hint=[1.0, 1.0])
        anchor.add_widget(logo)
        self.left_layout.add_widget(anchor)
    
    def build_separator(self):
        self.sep = Label(size_hint=[0.01, 1.0])
        self.layout.add_widget(self.sep)
        Clock.schedule_once(self.complete_sep)
    
    def complete_sep(self, *args):
        with self.sep.canvas:
            Color(rgba=get_color_from_hex("#c2e4ed"))
            Rectangle(size=self.sep.size, pos=self.sep.pos)

    def build_date(self):
        anchor = AnchorLayout(anchor_x="center", anchor_y="top")
        dt_label = Label(text=datetext(self.date), font_size='11sp', size_hint_y=0.1)
        anchor.add_widget(dt_label)
        self.left_layout.add_widget(anchor)

class AgePopup(Popup):
    def __init__(self, parent_screen, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.size_hint = [0.8, 0.35]
        self.separator_color = get_color_from_hex("#29bc90")
        self.title = "Confirm age"
        self.title_font = "fonts/LunaticSuperstar-8KgB.otf"
        self.title_color = get_color_from_hex("#61f1ea")
        self.title_size = '18sp'
        main_label = Label(text="Please enter this student's\nage to finish activation:")
        main_layout = BoxLayout(orientation="vertical")
        age_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        self.age_input = TextInput(multiline=False, size_hint_x=0.9, hint_text="Student's age")
        age_anchor.add_widget(self.age_input)
        button_layout = BoxLayout(orientation="horizontal", size_hint_y=0.9)
        back_button = Button(text="Cancel", background_color=get_color_from_hex("#29bc90"))
        back_button.bind(on_press=self.dismiss)
        confirm_button = Button(text="Confirm", background_color=get_color_from_hex("#29bc90"))
        confirm_button.bind(on_press=self.confirm_activation)
        button_layout.add_widget(back_button)
        button_layout.add_widget(confirm_button)
        main_layout.add_widget(main_label)
        main_layout.add_widget(age_anchor)
        main_layout.add_widget(Label(size_hint_y=0.2))
        main_layout.add_widget(button_layout)
        self.add_widget(main_layout)
        Clock.schedule_once(self.fix_inputs)
    
    def fix_inputs(self, *args):
        self.age_input.font_size = self.age_input.height / 2.5
        self.age_input.padding = [7,(self.age_input.height - self.age_input.font_size) / 2.5,7,0]
    
    def verify_age(self):
        age = remove_useless_spaces(self.age_input.text)
        return age.isdigit() and 0 < int(age) < 100

    def confirm_activation(self):
        if self.verify_age():
            update_attribute(ACCOUNTS, "activation_key", "0", email=self.parent_screen.person_email)
            update_attribute(ACCOUNTS, "age", remove_useless_spaces(self.age_input.text), email=self.parent_screen.person_email)
            del_notification(self.parent_screen.parent.logged_account, self.parent_screen.parent.selected_notif)
            self.parent_screen.parent.current = "notif"
            self.dismiss()
        else:
            self.title = "Error: Invalid age"
            self.title_color = get_color_from_hex("#f54d53")

class ActivationNotificationScreen(Screen):
    def setup(self):
        person_name, person_status, self.person_email = self.parent.selected_notif[NOTIF_CONTENT_INDEX].split(" | ")
        self.ids["person_name"].text = f"From [color=#87e84f][b]{person_name}[/color][/b]"
        self.ids["person_status"].text = f"This {person_status} requires your"
        self.ids["person_email"].text = f"email: [i]{self.person_email}[/i]"
        
    def open_doc(self):
        webbrowser.open("https://victorminator.github.io/binkspals/security/#students-requirements")
    
    #def fix_inputs(self, *args):
        #self.ids["input_age"].font_size = self.ids["input_age"].height / 2.5
        #self.ids["input_age"].padding = [7,(self.ids["input_age"].height - self.ids["input_age"].font_size) / 2.5,7,0]
    
    def accept(self):
        Factory.AgePopup(self).open()
    
    def refuse(self):
        Factory.ConfirmationPopup(self.block_account, "Are you sure you want\nto reject this request?").open()
    
    def block_account(self, *args):
        add_notification(advanced_search(ACCOUNTS, email=self.person_email), build_notif(app_db.today_date, "Activation Request Denied", f"We sadly inform you that your account's activation was refused by your school's BinksPals admin. Please meet with the admin to understand the reasons behind their decision.", False, "activation_denied"))
        del_notification(self.parent.logged_account, self.parent.selected_notif)
        self.parent.current = "notif"

class NotificationScreen(Screen):
    def setup(self):
        self.ids["loading_label"].text = "Loading..."
        Clock.schedule_once(self.complete_setup)
    
    def complete_setup(self, *args):
        self.parent.update_account()
        self.ids["loading_label"].text = ""
        self.notif_list = eval(self.parent.logged_account[NOTIF_INDEX])
        self.build_notifications()

    def clear_notif(self):
        self.ids["notif_layout"].clear_widgets()
    
    def build_notifications(self):
        button_height = 120
        self.ids["notif_layout"].height = button_height * len(self.notif_list)
        for notif in self.notif_list:
            notification_box = NotifWidget(self, notif[0], notif[1], notif[2], notif[3], notif[4], height=button_height)
            anchor = AnchorLayout(anchor_x="center", anchor_y="top")
            anchor.add_widget(notification_box)
            self.ids["notif_layout"].add_widget(anchor)
            Clock.schedule_once(notification_box.build_contents)

class PalsApp(App):
    pass

PalsApp().run()
try:
    for email_address in app_db.logged_out:
        update_attribute(ACCOUNTS, "last_connected", app_db.today_date, email=email_address)
except:
    pass
app_db.db.close()