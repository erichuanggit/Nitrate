.. _deployment:

Deployment
==========

Installation
------------

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

Config Settings
~~~~~~~~~~~~~~~

First please go to nitrate root path, it's different based on your current OS.

Like on RHEL6.3, the root path is located in::

  /usr/lib/python2.6/site-packages/Nitrate-3.8.5-py2.6.egg/tcms

As we plan to deploy a example server for nitrate, we can use product.py as the default settings.
After backed up the product.py, please modify following settings based on your custom configurations in settings/product.py:

.. literalinclude:: ../../tcms/settings/product.py
   :language: python

Use Memcached (Optional)
~~~~~~~~~~~~~~
Please install package of memcached and python-memcached if using memcached as Nitrate's cache::

    yum install memcached python-memcached

then run the memcached service::

    service memcached start

You can also change default memcached settings in file of /etc/sysconfig/memcached::

    PORT="11211"
    USER="memcached"
    MAXCONN="1024"
    CACHESIZE="64"
    OPTIONS=""

At last set related production settings in tcms/settings/product.py::

   CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
   SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

Start the django app
~~~~~~~~~~~~~~~~~~~~

After upon steps is completed, now you can try to start the web server which is built-in Django to test if the app can run successfully.
In nitrate root path, run following command::

  ./manage.py runserver --settings=settings.product

Then try to use web browser to open http://localhost:8000/ to verify the working status of this web service.

Deployment
----------

Deploy with Apache
~~~~~~~~~~~~~~~~~~

Deploying Django projects with Apache and mod_wsgi is the recommended way to get them into production.

To build a production server with Apache, just copy apache conf to /etc/httpd/conf.d/.

I presume that the conf file is named nitrate-httpd.conf.

.. literalinclude:: ../../contrib/conf/nitrate-httpd.conf
   :language: bash

In /etc/httpd/conf/httpd.conf, set the following settings simply::

    ServerName example.com:80
    Listen ip_address:80

After configuration, run::

    service httpd start

Please go to browser to have a verify if this service runs successfully.

If any problem, please refer to log file::

    /var/log/httpd/error_log

Or any access info, refer to::

    /var/log/httpd/access_log

Upgrading
---------

.. TODO
