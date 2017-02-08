# clickmatch

1. Download source code.
2. Create a virtualenv  for Python2.7
3. Activate the virtual environment.
4. Install all dependencies - which is in "main" folder
    >>pip install -r requirements.txt  
5. Install DB schema 
	>>python manage.py migrate 
6. Run server
	
	#### In local development env

	>>python manage.py runserver

	#### In production

	>> killall -9 uwsgi  , to stop existing uwsgi services

    >> uwsgi --ini=/etc/uwsgi/apps-enabled/clicktomatch.ini

	>> sudo service nginx start/restart/stop
