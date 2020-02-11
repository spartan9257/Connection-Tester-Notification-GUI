import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import path
from subprocess import check_output

#Return true if ping was successful
def checkPing(host):
    count = 0
    while(count < 2):
        response = os.system("ping -n 1 " + host)
        # and then check the response...
        if response == 0:
            pingStatus = True
            break
        else:
            print("Reattempting the connection...")
            pingStatus = False
            count = count + 1
    if pingStatus == False:
        print("Unable to connect to host after 3 attempts")
    return pingStatus

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
        server.login(sender, passwd)
        #send message
        server.sendmail(sender, destination_address, text)
        server.quit()

def simpleTimer(delay):
    startTime = int(time.time())
    while(True):
        if int(time.time()) - startTime >= delay:
            break


def create_log_file():
    #create a new log file name using the current date
    the_time_is = check_output("time /T", shell=True).decode()
    the_date_is = check_output("date /T", shell=True).decode()
    dateEnd = the_date_is.find("\n")
    the_date_is = str(the_date_is[4:dateEnd -2 ]).replace("/","-")
    log_file_name = "logs/log_" + the_date_is + ".txt"

    #check if the file already exists, if not create it
    if not path.exists(log_file_name):
        #Create the logs folder if it doesnt exist
        if not path.exists("logs"):
            print("Creating the logs folder")
            os.mkdir("logs")
        #add the log file to the folder
        print("Creating a new log file")
        logFile = open(log_file_name, "x")
        logFile.close()
        #Add the date/time in the first line
        logFile = open(log_file_name,"w")
        logFile.write(the_date_is + " @ " + the_time_is)
        logFile.close()

    #Begin deleting old log files once the limit is reached (150)
    #get the all the file names in oldest-newest order
    log_files = check_output("dir /OD /B logs", shell=True).decode()
    log_files = log_files.split("\n")
    num_of_logs = len(log_files)
    #if the total files exceed 150, delete the oldest ones
    if num_of_logs > 150:
        delete_logs = num_of_logs - 150
        log_files = log_files[0:delete_logs]
        for file in log_files:
            file = "\"" + file[0:len(file)-1] + "\""
            os.system("cd logs")
            delete_log_file = check_output("del /F logs\\" + file, shell=-True).decode()
            
    return log_file_name