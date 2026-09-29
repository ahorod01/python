import sys
import re
import os
import subprocess

def mainmenu():
    print("1. System Information")
    print("2. System Information (HTML)")
    print("3. Your Age")
    print("4. Is Leap Year")
    print("0. Be a Quitter")
    selection=input("Enter your choice:")
    if not re.match(r"[0-9-]+", selection): #check that input is numeric
        print("Invalid Choice, Restart")
        mainmenu()        
    else:        
        #print("\nContinue with code...\n")
    match selection:
        case "1":
            print("\n\n")
            print("Running System Information")
            import SystemInfo   #use SystemInfo.py module
            print("\n\n")
        case "2":
            print("\n\n")
            import SystemInfo2            
            output_file = os.path.abspath("system_report.html")
            #os.startfile(output_file)  
            #More robust way to open HTML file          
            output_file = os.path.abspath("system_report.html")
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]
            for edge in edge_paths:
                if os.path.exists(edge):
                    subprocess.Popen([edge, output_file])
                    break
            else:
                os.startfile(output_file)
            print("\n\n")
        case "3":
            print("\n\n")
            import age          #use age.py module
            print("\n\n")
        case "4":
            print("\n\n")
            import IsLeapYear
            print("\n\n")
        case "0":
            print("\n\n")
            print("See You later!!!")
            print("\n\n")
            quit()             
        case _: #default if no other match
            print("\n\n")
            print("Invalid Choice, try again")
            print("\n\n")
    mainmenu()

#START HERE
os.system('cls' if os.name == 'nt' else 'clear')
mainmenu()
