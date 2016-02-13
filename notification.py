import smtplib

sender = 'polargraph1@sub-design.co.uk'
receivers = ['mark@sub-design.co.uk']

message = """From: Polargraph 1 <polargraph1@sub-design.co.uk>
To: mark <mark@sub-design.co.uk>
Subject: Polargraph 1 Alert

Something has happened with polargraph 1.

Check it out...

"""

try:
   smtpObj = smtplib.SMTP('192.168.2.2')
   smtpObj.sendmail(sender, receivers, message)         
   print ("Successfully sent email")
except SMTPException:
   print ("Error: unable to send email")	