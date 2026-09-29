def TheSpererator(times):
    print("\n")
    print("#"*80)
    print("\n")

import socket

domain = input("Enter Website: ")
port   = input("Enter Port # : ")

#try you must, succeed you will
try:
    ip = socket.gethostbyname(domain)
    print ("\nDomain: ",domain)
    print ("IP: ",ip)
    sockAddr = ("{}".format(port), str(port))
    #info = socket.getnameinfo(sockAddr,socket.NI_NOFQDN)
    #print ("\nInfo",info)

except socket.gaierror:
    print ("Invalid, try again!!!")

TheSpererator(80)

with open("pingAndMore.py", "r") as file:  #count how many times PRINT is used
    n = file.read().count("print")

#read text file
with open("pingAndMore.py", "r") as file:  #read text file line by line and display
    lines = file.readlines()
    for line in lines:
        print(line)

print("\n\n")
print(f"print found {n} times")

import os
size = os.path.getsize("pingAndMore.py") 
print(f"The size of file is {size} bytes")


TheSpererator(80)

#weight = float(input("Enter your weight in kilos: "))
#height = float(input("Enter your height in centimeters: "))
#BMI = weight / (height/100)**2
#print(f"Your weight {weight}kg and you are {height}cm tall. This gives you BMI index of {BMI}")






def pyramid(rows):
    for i in range(rows):
        print(" "*(rows-i-1) + "*"*(2*i+1))
def tailfin(rows):
    for i in range(rows):
        print(" "*(rows+i+1) + "*"*(2*i-1))
    print("wW" * 40)
    print(" w" * 40)
    print("W " * 40)

        
pyramid(12)
tailfin(12)


TheSpererator(80)

names = ["Alice", "Bob", "Charlie", "David"]
print(" ".join(names))
