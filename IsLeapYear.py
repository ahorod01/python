#is leap year?
# A function that checks if a year is a leap year
def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


# Example
# Get current date and time
import datetime
#currentDateTime = datetime.datetime.now()
#date = currentDateTime.date()
date = datetime.date.today()
year = int(date.strftime("%Y"))

if is_leap(year):
    print(f"{year}, leap year its is")
else:
    print(f"{year}, leap year is not")
