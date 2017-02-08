# clickmatch

## What is it?

Our team is building an algorithm to match names. To measure the name matcher we need test data, labeled by humans on what is a match, and what is not a match.

Clickmatch speeds up the labeling process by allowing someone to quickly choose whether two names match, or don’t match. 

## How does it work? 

- Names come from a Google Spreadsheet. 
- The sheet must be shared with everyone who logs in
- match answer is saved in column with google user's email
- if username column does not exist for logged in user show “no column with your username”
- if user closes browser and comes back, they will go to the next record that needs matching

## What does my spreadsheet need to look like?

Like this: [google sheet](https://docs.google.com/spreadsheets/d/1H_pEqUHIHPxstgWCYa8yT8M4trcupbr1L2dMnGRdblE/edit#gid=0)

## How do I install it?

1. Download source code.
2. Create a virtualenv  for Python2.7
3. Activate the virtual environment.
4. Install all dependencies - which is in "main" folder
`pip install -r requirements.txt`  
  
5. Install DB schema 
`python manage.py migrate` 
	
6. Run server in development env
`python manage.py runserver`

7. Run server in production
```
killall -9 uwsgi  , to stop existing uwsgi services
uwsgi --ini=/etc/uwsgi/apps-enabled/clicktomatch.ini
udo service nginx start/restart/stop
```
