import gspread

sa = gspread.service_account("service_account.json")

def get_data(sheetname):
    sh = sa.open(sheetname)
    worksheet = sh.worksheet(sheetname)
    return sh, worksheet, worksheet.get_all_records(numericise_ignore=["all"])

def get_descripteurs(sheet):
    return sheet.row_values(1)

def refresh(sheet, database, content):
    sheet.append_row(content)
    content_dict = {}
    for i, key in enumerate(get_descripteurs(sheet)):
        content_dict[key] = content[i]
    database.append(content_dict)
    print(database[-1])

_, accounts_sheets, accounts_database = get_data("accounts_data")
_, schools_sheets, schools_database = get_data("schools_data")


def row_search(value:str, key:str, db):
    for row in db:
        if row[key] == value:
            return row
    return {}
