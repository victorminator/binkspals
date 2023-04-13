from bs4 import BeautifulSoup
import requests
import datetime

def is_empty(text:str):
    return len(text) == 0 or text.isspace()

def datetext(date_obj:datetime.date):
    return str(date_obj.day) + "/" + str(date_obj.month) + "/" + str(date_obj.year)

def remove_useless_spaces(text):
    if is_empty(text):return ""   
    i = 0
    while text[i] == " ":
        i += 1
    new_text = text[i:]
    j = len(new_text) - 1
    while new_text[j] == " ":
        j -= 1
    return new_text[:j + 1]

def date_convert(chaine:str):
    if len(chaine) != 10:
        return ""
    year = chaine[:4]
    sep_1 = chaine[4]
    month = chaine[5:7]
    sep_2 = chaine[7]
    day = chaine[8:]
    if year.isdigit() and month.isdigit() and day.isdigit() and sep_1 == sep_2 == "-":
        return datetime.date(int(year), int(month), int(day))
    return ""

def extract_date():
    calendar_page = requests.get("https://www.calendardate.com/todays.htm")
    soup = BeautifulSoup(calendar_page.content, 'html.parser')
    tags = soup.find_all(id="tprg")
    dates = []
    for tag in tags:
        try:
            date_val = date_convert(remove_useless_spaces(tag.text))
        except:
            continue
        if date_val != "":
            dates.append(date_val)
    return dates[-1]

def check_internet():
    try:
        requests.get('http://google.com')
        return True
    except:
        try:
            requests.get("https://www.wikipedia.org/")
            return True
        except:    
            return False

