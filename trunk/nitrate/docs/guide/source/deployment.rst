.. _deployment:

Deployment
==========

Deployment
----------

Download the sources
~~~~~~~~~~~~~~~~~~~~

The Nitrate source code is available at:
https://git.fedorahosted.org/cgit/nitrate.git/?h=development

You can get the latest changes with git easily::

  git clone git://git.fedorahosted.org/nitrate.git
  git checkout --track origin/development

Or you also can download the tarballs from:
https://git.fedorahosted.org/cgit/nitrate.git/?h=development

Install from source code
~~~~~~~~~~~~~~~~~~~~~~~~

After download the source code, you can go to the source code directory and install this project with python setup.py::

  cd [nitrate_download_path]/nitrate/trunk/nitrate
  python setup.py install

Initialize database schema
~~~~~~~~~~~~~~~~~~~~~~~~~~

Database is required by Nitrate(and all of Django apps). The Django ORM supports many database backends, we recommend you to use MySQL.

You can get a db dump from nitrate source code directory::

  cd [nitrate_download_path]/nitrate/trunk/nitrate/docs

In this directory, there is a sql file of 'nitrate_db_setup.sql'.

Dump this file into your database. I presume the database is named 'nitrate'::

  mysql -uroot -p
  mysql> create database nitrate CHARACTER SET utf8 COLLATE utf8_general_ci;
  mysql> use nitrate; source nitrate_db_setup.sql
  mysql> grant all privileges on nitrate.* to nitrate@'%' identified by 'nitrate';
  mysql> flush privileges;

Please notice that,we have initialized some data in this db dump:

a. created a super user in this db dump with following info::

      username: admin
      password: admin

b. added an example site with SITE_ID = 1::

      tcms.example.com

Settings
~~~~~~~~

First please go to nitrate root path, it's different based on your current OS.

Like on RHEL6.3, the root path is located in::

  /usr/lib/python2.6/site-packages/Nitrate-3.8.5-py2.6.egg/tcms

As we plan to deploy a example server for nitrate, we can use product.py as the default settings.
After backed up the product.py, please modify following settings based on your custom configurations in settings/product.py:

.. literalinclude:: ../../../tcms/settings/product.py
   :language: python

Start the django app
~~~~~~~~~~~~~~~~~~~~

After upon steps is completed, now you can try to start the web server which is built-in Django to test if the app can run successfully.
In nitrate root path, run following command::

  ./manage.py runserver --settings=settings.product

Then try to use web browser to open http://localhost:8000/ to verify the working status of this web service.

Deployment with Apache
~~~~~~~~~~~~~~~~~~~~~~

Deploying Django projects with Apache and mod_wsgi is the recommended way to get them into production.

You can have a try with following apache confs:

.. literalinclude:: ../../../contrib/conf/nitrate-httpd.conf
   :language: bash


Deployment with Nginx
~~~~~~~~~~~~~~~~~~~~~

With benchmark, we found Nginx + FCGI is faster than Apache + Mod_python.
So deploying with Nginx will also be a good idea for production environment.
Here are deployment confs about Nginx:

.. literalinclude:: ../../../contrib/conf/nitrate-nginx.conf
   :language: bash


Upgrading
---------

.. TODO
