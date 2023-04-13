import os
import csv

with open("country_codes.csv", encoding="utf-8") as fic:
    countries_data = list(csv.DictReader(fic))

def get_countries():
    return [country[:-4] for country in os.listdir("images/flags")]

def get_country_by_code(code:str):
    for country in countries_data:
        if country["Code"].lower() == code.lower():
            return country["Name"]
    return ""

def get_code_by_country(target_country:str):
    for country in countries_data:
        if country["Name"].lower() == target_country.lower():
            return country["Code"].lower()
    return ""
