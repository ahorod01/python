from datetime import date
import re
import sys


#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
def age(birthdate):
    today = date.today()
    age = today.year - birthdate.year - \
        ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age


#birthdate = date(1970, 10, 5)
birthdate = input("Enter Birthdate (YYYY-M-D): ")
if not re.match(r"[0-9-]+", birthdate):
    sys.exit ("Invalid Birtdate, restart")
else:
    print("Continue with code")
birthdate_obj = birthdate.split("-")
birthdate = date(int(birthdate_obj[0]), int(birthdate_obj[1]), int(birthdate_obj[2]))

# Format date as YYYY-MM-DD
current_date = birthdate.strftime("%Y-%m-%d")

# Get day of the week name
day_of_week = birthdate.strftime("%A")

print(f"With birth date of {birthdate}, you are {age(birthdate)} years old")
print("You were born on a", day_of_week)
today = date.today()
thisYear=str(today.year) + "-" + str(birthdate.month) + "-" + str(birthdate.day)
date_obj = date.strptime(thisYear, "%Y-%m-%d")
day_of_week = date_obj.strftime("%A")
print("This year your birthday will be on a", day_of_week)

today=str(today.month)+" "+str(today.day)
bdate=str(birthdate_obj[1])+" "+str(birthdate_obj[2])
if today==bdate:
    print("Happy Birthday")
else:
    print("Bummer it's not your Birthday")

