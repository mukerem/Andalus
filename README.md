
# Andalus

Andalus is an automated judge system to run programming contests. It has a mechanism to submit problem solutions, have them judged fully automatically and provides (web)interfaces for teams, the jury and the general public.


## Requirements

### Creating Python Virtual Environment 
A Virtual Environment is a python environment, that is an isolated working copy of Python which allows you to work on a specific project without affecting other projects
So basically it is a tool that enables multiple side-by-side installations of Python, one for each project.

#### Creating virtual environment in Linux

If pip is not in your system

```$ sudo apt-get install python-pip```
Then install virtualenv

```$ pip install virtualenv```
Now check your installation

```$ virtualenv --version```
Create a virtual environment now,

```$ virtualenv virtualenv_name```
After this command, a folder named virtualenv_name will be created. You can name anything to it. If you want to create a virtualenv for specific python version, type

```$ virtualenv -p /usr/bin/python3 virtualenv_name```
or

```$ virtualenv -p /usr/bin/python2.7 virtualenv_name```
Now at last we just need to activate it, using command

```$ source virtualenv_name/bin/activate```
Now you are in a Python virtual environment

You can deactivate using

```$ deactivate```
#### Creating Python virtualenv in Windows

If python is installed in your system, then pip comes in handy.
So simple steps are:
###### 1) Install virtualenv using

 ```> pip install virtualenv ```
###### 2)Now in which ever directory you are, this line below will create a virtualenv there

 ```> virtualenv myenv```
And here also you can name it anything.

###### 3) Now if you are same directory then type,

 ```> myenv\Scripts\activate```
You can explicitly specify your path too.

Similarly like Linux you can deactivate it like

```$ deactivate```

### install depenedcies
Right there, you will find the requirements.txt file that has all the great debugging tools, django helpers and some other cool stuff. To install them, simply type:

```pip install -r requirements.txt```


## Initialize the database

First set the database engine (PostgreSQL, MySQL, etc..) in your settings files; 
projectname/settings.py . Of course, remember to install necessary database driver for your engine. Then define your credentials as well. Time to finish it up:

If you have not database engine or driver , use default database that is sqlite3. 
comment mysql configration and uncomment sqlite3 in projectname/settings.py
```python/manage.py migrate```

create super user it is super admin/database admin, simply type :
```python/manage.py createsuperuser```

and create admin of the system from user table by selecting admin role in django admin site.


### Ready? Go!


```python/manage.py runserver```


## Authors


##### Mukerem Ali
##### Mustefa Kamil