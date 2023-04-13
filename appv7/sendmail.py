from email.message import EmailMessage
from code_generation import *
import smtplib

EXPIRATION_MINUTES = 10
ACCOUNTS = "accounts"
SCHOOLS = "schools"
SCHOOL_NAME_INDEX = 0
COUNTRY_INDEX = 2
CITY_INDEX = 3
SCHOOL_TYPE_INDEX = 4
SCHOOL_ADDRESS_INDEX = 5
POSTCODE_INDEX = 6
ADMIN_INDEX = 7
DESCRIPTION_INDEX = 8
EMAIL_INDEX = 0
SCHOOL_ID_INDEX = 1
PASSWORD_INDEX = 2
FIRST_NAME_INDEX = 3
LAST_NAME_INDEX = 4
ACCOUNT_STATUS_INDEX = 5
TIMER_END_INDEX = 7
MATCHED_INDEX = 8
INV_MATCH_INDEX = 9
ACTIVATED_INDEX = 10
PREFERENCES_INDEX = 11
LAST_CONNECTED_INDEX = 12
CREATION_DATE_INDEX = 13
AGE_INDEX = 14
NOTIF_INDEX = 15

NOTIF_DATE_INDEX = 0
NOTIF_TITLE_INDEX = 1
NOTIF_CONTENT_INDEX = 2
NOTIF_READ_INDEX = 3
NOTIF_TYPE_INDEX = 4

def send_confirmation_code(target_email):
    subject = "Verification code"
    confirmation_code = generate_confirmation_code(10)
    body = f"""Your account verification code is {confirmation_code}.\nPlease note this code will expire in {EXPIRATION_MINUTES} minutes or after 5 consecutive submissions.\n\nWe hope you'll have a nice experience on BinksPals.\nWishing you a nice day,\n- The BinksPals team"""
    send_email(target_email, subject, body)
    return confirmation_code

def send_activation_key(key, sender_profile, *addresses):
    key_splits = []
    interval = len(key) // len(addresses)
    for start in range(0, len(key), interval):
        key_part = key[start:start + interval]
        if len(key_part) != interval:
            key_splits[-1] += key_part
        else:
            key_splits.append(key_part)
    for i in range(len(key_splits)):
        email_content = f"""{sender_profile[FIRST_NAME_INDEX]} {sender_profile[LAST_NAME_INDEX]} ({sender_profile[0]}) is asking for a BinksPals activation key in order to create a {sender_profile[5]} account.\n\nOnly communicate this key if you do recognise this person as a {sender_profile[5]} from your educational establishment!!\n\nActivation key: {key_splits[i]}\n\nThanks for contributing,\n- The BinksPals team"""
        send_email(addresses[i], "BinksPals Activation Key", email_content)


def send_email(to, subject, content):
    email_sender = "binkspals42@gmail.com"
    account_password = "ygmqofqdjnsjtdkp"
    email_message = EmailMessage()
    email_message['From'] = email_sender
    email_message["To"] = to
    email_message["Subject"] = subject
    email_message.set_content(content)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_sender, account_password)
        smtp.sendmail(email_sender, to, email_message.as_string())

def send_admin_mail(admin_account, school_details):
    body = f"""{admin_account[EMAIL_INDEX]} is trying to create a BinksPals admin account and register their establishment.\nPlease verify if the school details they submitted are correct :\n\n- School name: {school_details[SCHOOL_NAME_INDEX]}\n- Address: {school_details[SCHOOL_ADDRESS_INDEX]}\n- Country: {school_details[COUNTRY_INDEX]}\n- City: {school_details[CITY_INDEX]}\n- Postal code: {school_details[POSTCODE_INDEX]}\n\nPlease communicate with {admin_account[EMAIL_INDEX]} only through their school's public official email address if it is not already the one they used for creating their account.\nOnce you are certain that the school details are correct and that this person represents this school, you may communicate them this school ID :\n\n{admin_account[SCHOOL_ID_INDEX]}\n\nThis will allow the school to be registered in our application's database.\nIf you are not sure about that school's and this person's identity, please contact us at binkspals42@gmail.com\n\nBinksPals' security relies on you,\n-The BinksPals team"""
    send_email("binkspals42@gmail.com", "School Registration Request", body)
