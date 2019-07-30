
# Andalus

Andalus is an automated judge system to run programming contests. It has a mechanism to submit problem solutions, have them judged fully automatically and provides (web)interfaces for teams, the jury and the general public.


## Requirements

Right there, you will find the requirements.txt file that has all the great debugging tools, django helpers and some other cool stuff. To install them, simply type:

```
pip install -r requirements.txt
```


## Initialize the database

First set the database engine (PostgreSQL, MySQL, etc..) in your settings files; 
projectname/settings.py . Of course, remember to install necessary database driver for your engine. Then define your credentials as well. Time to finish it up:

```
python/manage.py migrate
```


### Ready? Go!


```
python/manage.py runserver
```


## Authors


-Mukerem Ali
-Mustefa Kamil