import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import path
from subprocess import check_output
from icmplib import ping


#The two following functions (checkPing and alt_checkPing) essentially do the same thing.
#Which function you use will depend on the type of response the host gets when the ping fails.
#If the response is "Destination host unreachable" then you will need to use the first function.
#If the response is "Request timed out" then you will need to use the second function. The 
#function with the name checkPing will be the active one.

#Return true if ping was successful (Destination host unreachable)
def checkPing(host):
    response = ping(host, 1, 1)
    if not response.is_alive:
        print("1ST connection attempt to " + host + " FAILED!") 
        response = ping(host, 1, 1)
    if not response.is_alive:
        print("2ND connection attempt to " + host + " FAILED!")
        response = ping(host, 1, 1)
    if not response.is_alive:
        print("3RD connection attempt to " + host + " FAILED!")
        return False
    else:
        return True

#Return true if ping was successful (Request timed out) 
def alt_checkPing(host):
    response = os.system("ping -n 1 " + host)
    if response == 1: response = os.system("ping -n 1 " + host)
    if response == 1: response = os.system("ping -n 1 " + host)
    if response == 1: return False
    else: return True

#send an email notification
def sendEmail(sender, passwd, recipients, body, subject, serverInfo):
    #Create message parameters
    message = MIMEMultipart()
    for destination_address in recipients:
        print("Sending email to admin at " + str(destination_address))
        #Create message
        message['From'] = sender
        message["To"] = ','.join(destination_address)
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        text = message.as_string()

        #Connect to google smtp server (can be changed to different provider)
        print("Connecting to server @" + str(serverInfo[0][0]) + " via port " + str(serverInfo[0][1]))
        server = smtplib.SMTP(str(serverInfo[0][0]), str(serverInfo[0][1]))
        server.starttls() #begin a secure transmission
        try:
            server.login(sender, passwd)
            #send message
            server.sendmail(sender, destination_address, text)
            server.quit()
        except:
            print("Unable to send email, authentication to server failed!")
            print("Sender : " + sender)

def create_log_file():
    #create a new log file name using the current date
    the_time_is = check_output("time /T", shell=True).decode()
    the_date_is = check_output("date /T", shell=True).decode()
    dateEnd = the_date_is.find("\n")
    the_date_is = str(the_date_is[4:dateEnd -2 ]).replace("/","-")
    log_file_name = "logs/log_" + the_date_is + ".txt"

    #check if the file already exists, if not create it
    if not path.exists(log_file_name):
        #Create the logs folder and log file if they don't exist
        if not path.exists("logs"): os.mkdir("logs")
        print("Creating a new log file")
        open(log_file_name, "x")
        open(log_file_name,"w").write(the_date_is + " @ " + the_time_is)

    #Begin deleting old log files once the limit is reached (150)
    #get the all the file names in oldest-newest order
    log_files = check_output("dir /OD /B logs", shell=True).decode()
    num_of_logs = len(log_files.split("\n"))
    #if the total files exceed 150, delete the oldest ones
    if num_of_logs > 150:
        delete_logs = num_of_logs - 150
        log_files = log_files[0:delete_logs]
        for file in log_files:
            file = "\"" + file[0:len(file)-1] + "\""
            os.system("cd logs")
            delete_log_file = check_output("del /F logs\\" + file, shell=-True).decode()
            
    return log_file_name


#I wanted to create a class that would make writting an html file easier.
#I'll probable just work this out on a future project.
class html:
    output_file = ""
    def __init__(out_file):
        if not path.exists(out_file):
            f = open(out_file,"w")
            f.close()
            self.output_file = out_file
    
    #Creates a basic header and adds come CSS
    def html_start(title):
        out_file = open(output_file,"a")
        print("Writting HTML file...\n")
        out_file.write('<!DOCTYPE html>\n' + 
                       '<html lang="en" xmlns="http://www.w3.org/1999/xhtml">\n' +
                       '<head>\n' + 
                       '<meta http-equiv="refresh" content="5"; URL="index.html" />\n' + 
                       '<title>Somerset Connection Status</title>\n' +
                       '<style>\n' + 
                       '.masonary{\ncolumn-count: 5;\ncolumn-gap: 1em;\nwidth: 20%;\n}\n' +
                       '.item{\nbackground-color: #eee;\ndisplay: inline-block;\nmargin: 0 0 1em;\nwidth: 30;\nfont-size: .75em;\n}\n' + 
                       '.normal_font{\nfont-weight: normal;\n}\n' + 
                       '</style>\n' + 
                       '</head>\n<body>\n' + 
                       '<p align="center"><strong>' + title + '</strong></p>\n' + 
                       '<div class="masonry">\n')

    #Finishes the body and html sections
    def html_end():
        file = open(out_file,"a")
        file.write("</div>\n</body>\n</html>\n")
        file.close()

    #Creates a table and it's header
    def table_start(list, color):
        file = open(out_file,"a")
        file.write('<table class="item" border="1" valign="top">\n')
        for item in list:
            file.write("<th bgcolor='" + color + "'>" + item + "</th>\n")
        file.close()

    #Creates a table tow and cells
    def table_row(list, color):
        file = open(output_file,"a")
        file.write("<tr>")
        for item in list:
            file.write('<td ' + color + ' align="left" class="normal_font">' + item + '</td>\n')
        file.write("</tr>")
        file.close()

    #Finishes the table element
    def table_end():
        file = open(out_file,"a")
        file.write("</table>")
        file.close()


