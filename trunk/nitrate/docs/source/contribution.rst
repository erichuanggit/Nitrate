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

* `Python <http://www.python.org/>`_ >= 2.6.5
* `Django <http://www.djangoproject.com/>`_ = 1.5.5
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

   **Tip**: change settings in `settings/local.py` (create by yourself) instead of `settings/devel.py` since `settings/devel.py` will load settings in `settings/local.py` automatically and `settings/local.py` is ignored by git.

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

How To Contribute
-----------------

There are two distinct types of contributions that this guide attempts to support. As such, there may be portions of this document that do not apply to your particular area of interest.


**Existing Code**
  Add new features or fix bugs in the platform or existing type support
  projects.
**Integration**
  Integrate some other project with Nitrate, especially by using the event system
  and REST API.

Branching Model
~~~~~~~~~~~~~~~~~

* develop

This is the latest bleeding-edge code.

* Bug Fix Branches

A bug fix branch name should contain the developer's username and a Bugzilla bug
number, separated by a hyphen. For example, "dxiao-345612". Optionally, a
short description may follow the BZ number.

* Feature Branches

Similar to bug fix branches, the name of a feature branch should usually be the
developer's username plus a brief name relevant to the feature. For example,
a branch to add persistent named searches might be named "dxiao-named-searches".

In a case where multiple developers will contribute to a feature branch, simply
omit the username and call it "named-searches".

Merging
~~~~~~~~

* Pull Requests

You have some commits in a branch, and you're ready to merge. The Nitrate Team makes
use of pull requests for all but the most trivial contributions.

On the GitHub page for the repo where your development branch lives, there will be
a "Pull Request" button. Click it. From there you will choose the source and
destination branches.

For details about using pull requests, see GitHub's
official documentation <https://help.github.com/articles/using-pull-requests>.

* Review

Once a pull request has been submitted, a member of the team will review it.
That person can indicate their intent to review a particular pull request by
assigning it to themself.

Comments on a pull request are meant to be helpful for the patch author. They
may point out critical flaws, suggest more efficient approaches, express admiration
for your work, ask questions, make jokes, etc. Once review is done, the reviewer
assigns the pull request back to the author. The next step for the author will
go in one of two directions:

    1. If you have commit access and can merge the pull request yourself, you can
       take the comments for whatever you think they are worth. Use your own
       judgement, make any revisions you see fit, and merge when you are satisfied.
       Think of the review like having someone proof-read your paper in college.

    2. If you are a community member and do not have commit access, we ask that you
       take the review more literally. Since the Nitrate Team is accepting responsibility
       for maintaining your code into perpetuity, please address all concerns expressed
       by the reviewer, and assign it back to them when you are done. The reviewer
       will strive to make it clear which issues are blocking your pull request from
       being merged.

    .. note::
       *To the community:* The Nitrate Team is very grateful for your contribution and
       values your involvement tremendously! There are few things in an OSS project as
       satisfying as receiving a pull request from the community.

       We are very open and honest when we review each other's work. We will do our
       best to review your contribution with respect and professionalism. In return,
       we hope you will accept our review process as an opportunity for everyone to
       learn something, and to make Nitrate the best product it can be.

Bugs
~~~~~

* Reporting

    Bugs must be filed against "Nitrate" in the bugzilla entry's *Product* field.

    Please try to select the closest corresponding component in the *Components* field.

    The *Version* field will have an entry for each Nitrate release (3.3, 3,4, 3,6, etc.).
    If a bug is found when running from source instead of a released version, the "Master"
    value should be selected.

    Once a week, the Nitrate team triages all new bugs, at which point
    the bug may be aligned to a different component and its *Severity* rating will be evaluated.
    If necessary, the bug may be marked as `NEEDINFO` if more clarification is requested.

* Fixing

    When fixing a bug, all bugs will follow this process, regardless of how trivial.

    * Developer
        #. Once the bug has been triaged and assigned to a developer, the state of the bug is set to
           `ASSIGNED`.
        #. The developer creates a new remote branch for the bug. The name of the branch should follow the
           convention of the developer's login name, a hyphen, and the number of the bugzilla entry.
           Example: dxiao-123456
        #. When the fix is complete, the developer submits a pull request for the bug into the appropriate
           branch (master, release branch, etc.). It's appreciated by the reviewer if a link to the bugzilla
           is included in the merge request, as well as a brief description of what the change is. It is
           not required to find and assign someone to do the review.
        #. When the pull request is submitted, the developer changes the status of the bug to `POST`.
        #. Wait for someone to review the pull request. The reviewer will assign the pull request back to
           the developer when done and should also ping them through other means. The developer may take
           the reviewer's comments as they see fit and merge the pull request when satisfied. Once merged,
           set bug status to `MODIFIED`. It is also helpful to include a link to the pull request in a
           comment on the bug.
        #. Delete both local **AND** remote branches for the bug.

    * Reviewer
        #. When reviewing a pull request, all feedback is appreciated, including compliments, questions,
           and general python knowledge. It is up to the developer to decide what (if any) changes will
           be made based on each comment.
        #. When done reviewing, assign the pull request back to the developer and ping them through
           other means.


