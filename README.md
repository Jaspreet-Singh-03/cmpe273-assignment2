# cmpe273-assignment2
CMPE 273 Assignment 2 Repo - Spring 2020
# **Notes for Assignment 2**

## All the data persist in scantron.db (sqlite) , the file name is **Solution.py** so make sure to set the same name while running the flask application , also highlighted most important notes in screenshot in this folder

## First, to get started the user should enter a new answer key for the test through a POST at http://127.0.0.1:5000/api/tests and body should be like this (content-type application/json for all the requests)  , the test id will be auto generated , check screenshot for more details
'''{
    	"subject": "Math",
    	"answer_keys": {
    			"1": "A", "2": "B", .. "50" : "A" 
   		 }
    }
 '''  
<img src="https://github.com/Jaspreet-Singh-03/cmpe273-assignment2/blob/master/POSTMAN_SCREENSHOTS/Adding_AnswerKey.jpg" height="1024">

## After adding answer keys for many test , you can view it with a GET at http://127.0.0.1:5000/api/tests to reterive all the uploaded tests and thier answer keys, check screenshot for more details
<img src="https://github.com/Jaspreet-Singh-03/cmpe273-assignment2/blob/master/POSTMAN_SCREENSHOTS/View_All__Subjects.jpg" height="1024">


## The student has to upload the scantron/ json object with answer key in the format below with a POST at http://127.0.0.1:5000/api/tests/<ENTER SUBJECT ID>/scantrons ( please enter the correct subject id for the corresponding  subject name) , for this code use postman with upload file as binary type , the scantron id will be auto generated , check screenshot for more detailscheck screenshot for more details 
The uploaded file should have this format (same as assignment requiremetns)
'''{
    "name": "Foo Bar",
    "subject": "Math",
    "answers": {
        "1": "B", "2": "D", .. .. "50" : "C" 
   		 }
    }
 ''' 
<img src="https://github.com/Jaspreet-Singh-03/cmpe273-assignment2/blob/master/POSTMAN_SCREENSHOTS/Upload_Scantron.jpg" height="1024">

- The score will be calculated and displayed as response along with the submitted answers along with actual answer from the test id , added validation so that the address at subject id matches with the subject name.

- The scantron url will also be shown which can be clicked to view the saved uploaded file on the server / or can send a GET request at http://localhost:5000/files/scantron-2.json ( or other scantron id with correct name)
<img src="https://github.com/Jaspreet-Singh-03/cmpe273-assignment2/blob/master/POSTMAN_SCREENSHOTS/View_Uploaded_Scantron.jpg" height="1024">

## Finally, if you want to check for all the submission for a given subject/test id , send a GET at http://127.0.0.1:5000/api/tests/<ENTER SUBJECT ID> , validation for created test only, it will give all the scantron submission associated with given test id/
<img src="https://github.com/Jaspreet-Singh-03/cmpe273-assignment2/blob/master/POSTMAN_SCREENSHOTS/View_With_SubjectID.jpg" height="1024">
