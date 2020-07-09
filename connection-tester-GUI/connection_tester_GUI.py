from definitions import checkPing, sendEmail, create_log_file
from subprocess import check_output
from os import path
import csv,time,os,subprocess,threading

#The Simple Connection Tester v1.1.2
#Samuel Bravo, 02/14/2020

#!For gmail accounts less secure app access MUST be enabled
#!https://myaccount.google.com/lesssecureapps

print("The Simple Connection Tester v1.1.2")

issue_start_time = 0                 #logs the time of the first failure occurence
email_alert_periodic_interval = 3600 #sets the interval that the emails will be periodically resent
minutes_lapsed = 0                   #tracks the minutes that have lapsed since the last email was sent
last_email_sent_time = 0             #saves the time that the last email was sent
prior_email_sent = False 
detected_failures = False
failed_devices_list = []             #maintains a list of the host's whos connection failed
periodic_interval = 10               #Time in seconds between connection tests
debug_on = False                     #Creates a file debug.txt that contains program logs

#-------------------------------------------------------------------------------------------------------------------------------#

######################################################################################
#This is the start of the MASTER LOOP, it controls the entire script and runs forever#
######################################################################################
while(True):
    debugFile = open("debug.txt","w")
    debugFile.close()

    #Open the CSV file containing the list of hosts and append them to a list
    print("Getting hosts information")
    if not path.exists("hosts.csv"):
        print("Error: hosts.csv not found. Create the file and add it to the same directory as main.py")
        os.system("pause")
        exit()

    hosts_info = []
    for csv_entry in csv.reader(open("hosts.csv"), delimiter=','):
        if csv_entry: hosts_info.append(csv_entry)

#-------------------------------------------------------------------------------------------------------------------------------#

    #Get the credentials for the admin email account to send an email notification
    if not path.exists("creds.csv"):
        print("Error: creds.csv not found. Create the file and add it to the same directory as main.py")
        os.system("pause")
        exit()

    creds = []
    for csv_entry in csv.reader(open("creds.csv"), delimiter=','):
        if csv_entry: creds.append(csv_entry)

    #Create a debug and log file
    log_file_name = create_log_file()
    if debug_on: debugFile = open("debug.txt", "a")

#-------------------------------------------------------------------------------------------------------------------------------#
    
    #attempt to ping the host IP, if it fails generate an email if none have been generated
    #already, or enough time has lapsed since the last email was sent.
    def main():
        global hosts
        global issue_start_time
        global email_alert_periodic_interval
        global minuets_lapsed
        global last_email_sent_time
        global prior_email_sent
        global detected_failures
        global failed_devices_list
        global periodic_interval
        global debug_on

        if host[0].find("#") == -1:
	        print("\n--> ",end=" ")
	        try: host[3] = int(host[3])
	        except: print("Interesting Error, please, continue.")
	        connection_status = checkPing(host[0])

#-------------------------------------------------------------------------------------------------------------------------------#

	        #if the connection failed, do the following: write log, track the host, send an email
	        if connection_status == False:
		        if debug_on: debugFile.write("Connection failed\n")
		        detected_failures = True

		        #Write a new log entry
		        log_entry = check_output("time /T", shell=True).decode().replace("\n",'')
		        open(log_file_name,"a").write(log_entry[:len(log_entry)-1] + " Connection to host " + str(host[:3]) + " FAILED\n")

		        #check if a previous issue was logged already
		        if issue_start_time == 0:
			        print("Logging issue occurence start time")
			        issue_start_time = int(time.time())
			        if debug_on:
				        debugFile.write("issue start time: " + str(issue_start_time) + "\n")

		        #Get all the data needed to send an email notification
		        body = "WARNING! Connection to host " + str(host[0]) + " failed.\n" + str(host[1]) + "\n" + str(host[2]) 
		        subject = "Connection Failure"
		        sender = str(creds[0][0])
		        passwd = str(creds[0][1])

		        #Get the recipient(s) email address and the email server's ip/port#
		        destination_address = []
		        for email_address in csv.reader(open("email_recipients.csv", "r"), delimiter=','):
			        if email_address: destination_address.append(email_address)

		        serverInfo = []
		        for field in csv.reader(open("server_info.csv", "r"), delimiter=','):
			        if field: serverInfo.append(field)

		        #If a prior email hasn't been sent, generate one now.
		        if host[3] == 0:
			        if debug_on: debugFile.write("Host last email sent time is 0, sending first email\n")
			        print("No prior issue logged for this host, generating notification")
			        sendEmail(sender, passwd, destination_address, body, subject, serverInfo)

			        host[3] = time.time() #track the time the email was sent for this host
			        if debug_on: debugFile.write("Email sent time logged: " + str(host[3]) + "\n")

		        #If a prior email was sent, check how much time has lapsed. Send another email if the time lapsed exceeds the periodic interval.
		        elif (int(time.time()) - host[3]) / 60 + 1 >= email_alert_periodic_interval:
			        print("Persistant issue logged again, generating another email")
			        sendEmail(sender, passwd, destination_address, body, subject, serverInfo)
			        host[3] = time.time() #track the time the email was sent for this host

		        #If the device isnt already in the list of failed devices, add it.
		        if debug_on: debugFile.write("Current list of failed devices: " + str(failed_devices_list) + "\n")
		        found = False
		        #Check the list of failed devices to see if its already being tracked
		        if failed_devices_list:
			        for device in failed_devices_list:
				        if device == host[0]: 
					        found = True
					        if debug_on: debugFile.write("host is already in the list of failed devices\n")
			        if not found:
				        print("Logging the device as failed.")
				        failed_devices_list.append(host[0])
				        if debug_on: debugFile.write("host was not in the list of failed devices adding it not\nfailedDevices: " + str(failed_devices_list) + "\n")
		        else:
			        failed_devices_list.append(host[0])

#-------------------------------------------------------------------------------------------------------------------------------#

	        #if the connection succeeded, do the following: 
	        if connection_status == True:
		        #if the ping to a previouly failed device succeeds, remove it from the list of failed devices
		        #and notify the admin.
		        if debug_on:
					        debugFile.write("Connection was successful\n")
		        if detected_failures:
			        for device in failed_devices_list:
				        if host[0] == device:
					        print("Connection to " + host[0] + " Restored")
					        print("Removing device from the failed log")

					        #Remove the host and reset its last email sent time tracker to 0
					        if debug_on: debugFile.write("Removing device from failed devices")
					        failed_devices_list.remove(host[0])
					        host[3] = 0

					        #Send a new email informing the recipient that the connection has been restored
					        body = "Connection to host " + str(host[0]) + " was restored.\n" + str(host[1]) + "\n" + str(host[2]) 
					        subject = "Connection Restored!"
					        sendEmail(sender, passwd, destination_address, body, subject, serverInfo)

					        #Create a new log entry
					        log = open(log_file_name,"a")
					        log_entry = check_output("time /T", shell=True).decode().replace("\n",'')
					        log_entry = log_entry[:len(log_entry)-1] + " Connection to host " + str(host[:3]) + " RESTORED\n"
					        log.write(log_entry)
					        log.close()

				        #Exit the for loop as soon as a match is found
				        break
	        print("<--")

    #Execute main() accross all available cpu cores
    for host in hosts_info:
        t = threading.Thread(target=main)
        t.start()
        t.join()

    #If no failed devices are being tracked, reset trackers
    if not failed_devices_list:
        failed_devices_list.clear()
        issue_start_time = 0
        detected_failures = False
        prior_email_sent = False
        print("\nAll connections successful")
    else:
        print("\nConnection failures detected!")
    print("=========================================================\n")
    if debug_on: debugFile.close()
            
    
#-------------------------------------------------------------------------------------------------------------------------------#
    #Start generating the HTML file
    current_time = check_output("time /T", shell=True).decode()
    current_time = current_time[0:len(current_time) -2 ] #removes the \r\n from the end of the output
    out_file = open("index.html","w")
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
                    '</head>\n' + 
                    '<body style="margin:5%;padding:0>\n' + 
                    '<p align="center"><strong>Somerset Connection Status: Updated@ ' + current_time + '</strong></p>\n' + 
                    '<div class="masonry">\n')
    
#-------------------------------------------------------------------------------------------------------------------------------#
    #generate the html file
    counter = 0              #controls the number of rows in each table
    first_table = True       #
    color_controller = True  #controls the transition between 2 cell colors
    color_failed = ' bgcolor="red" '
    max_rows = 20            #controls the number of rows in each table plus the header (table_size = max_rows+headers)

    for line in hosts_info:
        #Control the cells color so that each new table set transitions between white and grey.
        if color_controller == True: cell_color = ' bgcolor="cyan" '
        else: cell_color = ' bgcolor="khaki" '
            
        #determine the status of the hosts connection
        #skip if its a line comment
        if line[0].find('#') == -1:
            if line[3] == 0: status = "UP"
            else: status = "DOWN"

#-------------------------------------------------------------------------------------------------------------------------------#
        #every n rows, create a new table.
        if counter == 0:
            counter = counter + 1
            #if this is the first table, do this
            if first_table:
                out_file.write('<table class="item" border="1" valign="top">\n')
                first_table = False
            else:
                out_file.write('</table>\n')
                out_file.write('<table class="item" border="1" valign="top">\n')

            #Now create the tables header using the current line of hosts_info
            #If the current line begins with a '#' make the header bold
            if line[0].find("#") > -1:
                out_file.write("<tr>\n")
                out_file.write("<th bgcolor='orange'>" + line[0][1:] + "</th>\n")
                out_file.write("<th bgcolor='orange' width='6'>Status</th>\n")
                out_file.write("</tr>\n")
            else:
                #Determine if the hosts connection was UP or DOWN. if its DOWN set cell color to color_failed (red)
                if status == "DOWN":
                    out_file.write('<tr><th ' + color_failed + ' align="left" class="normal_font">' + line[2] + '</th>\n')
                    out_file.write('<th ' + color_failed + 'align="left" class="normal_font">' + status + '</th></tr>\n')
                else:
                    out_file.write('<tr><th ' + cell_color + ' align="left" class="normal_font">' + line[2] + '</th>\n')
                    out_file.write('<th ' + cell_color + 'align="left" class="normal_font">' + status + '</th></tr>\n')
    
#-------------------------------------------------------------------------------------------------------------------------------#

        #If max_rows hasn't been reached yet, create a new row
        else:
            #Every time a line comment is hit make those cells bold and change the color for the preceeding cells.
            if line[0].find("#") > -1:
                #switch the color_controller
                if color_controller == True: color_controller = False
                else: color_controller = True
                #Control the cells color so that each new table set transitions between white and grey.
                if color_controller == True: cell_color = ' bgcolor="orange" '
                else: cell_color = ' bgcolor="orange" '
                #create the row with bold font and the cell color
                out_file.write("<tr>\n")
                out_file.write("<td" + cell_color + "><strong>" + line[0][1:] + "</strong></td>\n")
                out_file.write("<td " + cell_color + "width='6'><strong>Status</strong></td>\n")
                out_file.write("</tr>\n")

            else:
                if status == "DOWN":
                    out_file.write('<tr><td' + color_failed + '>' + line[2] + '</td>\n')
                    out_file.write('<td ' + color_failed + 'width="6">' + status + '</td></tr>\n')
                else:
                    out_file.write('<tr><td' + cell_color + '>' + line[2] + '</td>\n')
                    out_file.write('<td ' + cell_color + 'width="6">' + status + '</td></tr>\n')

            #if max_rows rows have been reached, reset the counter to create a new table
            if counter >= max_rows: counter = 0
            else: counter = counter+1

    out_file.write("</table>\n")
    out_file.write("</div>\n</body>\n</html>\n")
    out_file.close()

    
    #Set a timer to control when the loop repeats
    print("Periodic timer set for " + str(periodic_interval) + " seconds")
    os.system("time /T")
    print("Timer started...")
    time.sleep(periodic_interval)
    print("Begining connection tests")
