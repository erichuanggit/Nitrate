.. _deployment:

Deployment
==========

This deployment document presumes that you are running Red Hat Enterprise Linux
6. Of course, all deployment steps being described through this document also
apply to other Linux distributions, such as CentOS, openSUSE, or Debian.

This document aims to deployment within a server that will serve test case
management service to stuffs or customers. Therefore, all commands and
configuration are done with system Python interpreter and those configuration
files installed in the standard system directories, like the
``/etc/httpd/conf/httpd.conf``.

Installation
------------

Download the sources
~~~~~~~~~~~~~~~~~~~~

The Nitrate source code is available at:
https://git.fedorahosted.org/cgit/nitrate.git/?h=development

You can get the latest changes with git easily::

  git clone git://git.fedorahosted.org/nitrate.git
  git checkout --track origin/development

Or you can also download the tarballs from
https://git.fedorahosted.org/cgit/nitrate.git/

Install from source code
~~~~~~~~~~~~~~~~~~~~~~~~

After downloading the source code, go to the source code directory and
install this project with python setup.py::

  cd [nitrate_download_path]/nitrate
  python setup.py install

Install dependencies
~~~~~~~~~~~~~~~~~~~~

Install devel packages that should be installed first::

    sudo yum install python-devel mysql-devel krb5-devel libxml2-devel libxslt-devel

Install dependencies from ``requirements/base.txt``::

    sudo pip install -r requirements/base.txt

Initialize database schema
~~~~~~~~~~~~~~~~~~~~~~~~~~

Database is required by Nitrate (and all of Django apps). Django ORM supports
many database backends, we recommend you to use MySQL.

You can get a database dump from nitrate source code directory::

    cd /path/to/nitrate/contrib/sql

In this directory, there is a sql file named ``nitrate_db_setup.sql``.

Dump this file into your database. I presume the database is named 'nitrate'::

    mysql -uroot -p
    mysql> create database nitrate CHARACTER SET utf8 COLLATE utf8_general_ci;
    mysql> use nitrate; source nitrate_db_setup.sql
    mysql> grant all privileges on nitrate.* to nitrate@'%' identified by 'nitrate';
    mysql> flush privileges;

Please notice that, we have initialized some data in this db dump:

a. created a super user in this db dump with following info::

    username: admin
    password: admin

b. added an example site with SITE_ID = 1::

    nitrate.example.com

Config Settings
~~~~~~~~~~~~~~~

First please go to nitrate root path, it's different based on your current OS.

Like on RHEL6.3, the root path is located in::

    /usr/lib/python2.6/site-packages/nitrate-3.8.6-py2.6.egg/tcms

As we plan to deploy a example server for nitrate, we can use product.py as the
default settings. After backed up the product.py, please modify following
settings based on your custom configurations in settings/product.py:

.. literalinclude:: ../../tcms/settings/product.py
   :language: python

Use cache (Optional)
~~~~~~~~~~~~~~~~~~~~

You can use Django's cache framework to get better performance.

Refer to following docs for more details:

- https://docs.djangoproject.com/en/1.5/topics/cache/

- https://docs.djangoproject.com/en/1.5/ref/settings/#caches

Start the django app
~~~~~~~~~~~~~~~~~~~~

After upon steps is completed, now you can try to start the web server which is
a built-in development server provided by Django to test if the app can run
as expected. Run following command::

    django-admin.py runserver --settings=tcms.settings.product

Then try to use web browser to open ``http://localhost:8000/`` to verify the
working status of this web service.

Deployment
----------

Collect static files
~~~~~~~~~~~~~~~~~~~~

The default directory to store static files is `/var/nitrate/static`, you can
modify it by changing `STATIC_ROOT` setting in
`/path/to/nitrate/tcms/settings/product.py`.

Run following command to collect static files::

    django-admin.py collectstatic --settings=tcms.settings.product

Reference:

https://docs.djangoproject.com/en/1.5/howto/static-files/deployment/


Deploy with Apache
~~~~~~~~~~~~~~~~~~

Deploying Django projects with Apache and mod_wsgi is the recommended way to get
them into production.

To build a production server with Apache, just copy apache conf to
``/etc/httpd/conf.d/``.

I presume that the conf file is named nitrate-httpd.conf.

.. literalinclude:: ../../contrib/conf/nitrate-httpd.conf
   :language: bash

Change any configuration to fit your deployment environment.

In ``/etc/httpd/conf/httpd.conf``, set the following settings simply::

    ServerName example.com:80
    Listen ip_address:80

After configuration, run::

    sudo service httpd start

Please go to browser to have a verify if this service runs successfully.

If any problem, please refer to log file::

    /var/log/httpd/error_log

Or any access info, refer to::

    /var/log/httpd/access_log

Upgrading
---------

.. TODO
