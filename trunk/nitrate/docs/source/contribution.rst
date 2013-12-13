.. _contribution:

Contribution
============

This guide is a comprehensive resource for contributing to Nitrate - for both
new and experienced contributors. It is maintained by the Nitrate community.
We welcome your contributions to Nitrate!

Getting involved
----------------

These instructions cover how to setup development environment and recommended
coding conventions for nitrate project.  It also gives an overview of the
directory structure of the Nitrate source code.


Getting the Source Code
~~~~~~~~~~~~~~~~~~~~~~~

The Nitrate source code is available at:
https://git.fedorahosted.org/cgit/nitrate.git/?h=development

You can easy to get the latest changes with git:
code::

    # git clone git://git.fedorahosted.org/nitrate.git
    # git checkout --track origin/development

Or you also can download the tarballs from:
https://git.fedorahosted.org/cgit/nitrate.git/?h=development

Requirement modules
~~~~~~~~~~~~~~~~~~~

* `Python <http://www.python.org/>`_ >= 2.4
* `Django <http://www.djangoproject.com/>`_ = 1.2.3
* `MySQL-python <http://sourceforge.net/projects/mysql-python/>`_ = 1.2.4
* `Kobo <https://fedorahosted.org/kobo/>`_ = 0.2.1
* `kerberos <https://pypi.python.org/pypi/kerberos/1.1.1>`_ = 1.1.1
* `qpid-python <http://qpid.apache.org/components/messaging-api/index.html>`_  = 0.20
* `Django debug toolbar <http://github.com/robhudson/django-debug-toolbar>`_ (Optional: Recommendations for development)
* `Sphinx <https://pypi.python.org/pypi/Sphinx/1.2b3>`_ (Optional: Recommendations for development, used for building docs)

Install dependence
~~~~~~~~~~~~~~~~~~

code::

    # cd nitrate/trunk/nitrate
    # pip install -r requirements/devel.txt

Setup database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

code::

    # mysql -uroot -p
    # mysql> create database nitrate CHARACTER SET utf8 COLLATE utf8_general_ci;
    # mysql> use nitrate; source nitrate_db_setup.sql
    # mysql> grant all privileges on nitrate.* to nitrate@'%' identified by 'nitrate';
    # mysql> flush privileges;

.. note::

   Remember to change db settings in `settings/devel.py` accordingly.

Start the nitrate app
~~~~~~~~~~~~~~~~~~~~~
code::

    # cd <nitrate_project_root_path>/trunk/nitrate/tcms
    # ./manage.py runserver

.. note::

   `settings/devel.py` is used as default settings.

Coding style
------------

Please follow these coding standards when writing code for inclusion in Nitrate.

Python style
~~~~~~~~~~~~

* Unless otherwise specified, follow `PEP 8 <http://www.python.org/dev/peps/pep-0008>`_.
* Use underscores, not camelCase, for variable, function and method names (i.e. poll.get_unique_voters(), not poll.getUniqueVoters).
* In docstrings, use “action words” such as:

    code::

        def foo():
            """
            Calculates something and returns the result.
            """
            pass

    Here’s an example of what not to do:

    code::

        def foo():
            """
            Calculate something and return the result.
            """
            pass

    More details please follow `Django's development version <https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/>`_.

