%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define use_pylint 0

Name:           nitrate
Version:        3.0.4
Release:        1
Summary:        Test Case Management System

Group:          Development/Languages
License:        Internal RH for now
URL:            https://engineering.redhat.com/trac/testify20/browser/trunk/nitrate
Source0:        nitrate-%{version}-%{release}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-devel
%if %{use_pylint}
BuildRequires:  pylint
BuildRequires:  Django
%endif

Requires:       Django = 1.1
# Requires:     mod_python
Requires:       mod_ssl
Requires:       python-memcached
Requires:       python-kerberos
Requires:       python-hashlib
Requires:       kobo-django >= 0.2.0-3
Requires:       mod_auth_kerb
Requires:       mod_wsgi
Requires:       w3m

%description
Nitrate is a tool for tracking testing being done on a product.

It is a database-backed web application, implemented using Django

%prep
%setup -q

# Fixup the version field in the page footer so that it shows the precise
# RPM version-release:
sed --in-place \
  -r 's|NITRATE_VERSION|%{version}-%{release}|' \
  templates/tcms_base.html

%build
%{__python} setup.py build

%if %{use_pylint}
# Run pylint.  Halt the build if there are errors
# There doesn't seem to be a good way to get the result of pylint as an
# exit code.  (upstream bug: http://www.logilab.org/ticket/4691 )

# Capture the output:
pylint --rcfile=tcms/pylintrc tcms > pylint.log

# Ensure the pylint log makes it to the rpm build log:
cat pylint.log

# Analyse the "Messages by category" part of the report, looking for
# non-zero results:
# The table should look like this:
#   +-----------+-------+---------+-----------+
#   |type       |number |previous |difference |
#   +===========+=======+=========+===========+
#   |convention |0      |0        |=          |
#   +-----------+-------+---------+-----------+
#   |refactor   |0      |0        |=          |
#   +-----------+-------+---------+-----------+
#   |warning    |0      |0        |=          |
#   +-----------+-------+---------+-----------+
#   |error      |0      |0        |=          |
#   +-----------+-------+---------+-----------+
#   
# Halt the build if any are non-zero:
grep -E "^\|convention[ ]*\|0[ ]*\|" pylint.log || exit 1
grep -E "^\|refactor[ ]*\|0[ ]*\|" pylint.log || exit 1
grep -E "^\|warning[ ]*\|0[ ]*\|" pylint.log || exit 1
grep -E "^\|error[ ]*\|0[ ]*\|" pylint.log || exit 1
%endif


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Move static content from 32/64bit-specific python dir to shared data dir:
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/%{name}
mkdir -p ${RPM_BUILD_ROOT}%{_docdir}/%{name}

for d in contrib templates media; do
    cp -r ${d} ${RPM_BUILD_ROOT}%{_datadir}/%{name};
    # chown -R root:root ${RPM_BUILD_ROOT}%{_datadir}/%{name}/${d};
done

# Install apache config for the app:
install -m 0644 -D -p contrib/conf/nitrate-httpd.conf  ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/%{name}.conf

 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc docs/INSTALL docs/AUTHORS docs/ChangeLog docs/README docs/RELEASENOTES docs/UPGRADING docs/XMLRPC docs/testopia-dump-blank.sql docs/mysql_initial.sql
%{python_sitelib}/*
%{_datadir}/%{name}/*
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf

%changelog
* Wed July 21 2010 Xuqing Kuang <xkuang@redhat.com - 3.0.4-1
- First open sourced version.
- Added all of docs lacked for installation/upgrading/usage.
- Fixed #604206 - TestCase.link_plan() does not report errors
- Completed feature #609842 - [FEAT] provide buglist link in addition to ...
- Fixed #611354 - [Text] Updates to automation options.
- Fixed UI Bug #609760 - Add Tag text "Ok, I see" needs updating.
- Fixed UI Bug #606730 - favicon.ico should use transparency
- Fixed #612797 - Test run env value permission check issue
- Fixed #612022 - Change Automation status window appears when no test …
- Fixed #609776 - Tag autocomplete is case sensitive.
- Fixed #612881 - The filter for 'Automated' 'Manual' 'Autoproposed' is …
- Fixed #613480 - No way is provided to go back to the plan after cloning a …
- Fixed UI Bug #610127 - show/highlight test-case-runs assigned to me when executing …
- Fixed UI Bug #612880 - Need total number for filter out result
- Completed feature #607844 - (RFE) Flag tests which require the IEEE Test …
- Completed Feature #587143 - [FEAT] Have a default component when creating …
- Move the compoent of the case to be a tab
- Use the updateObject() function to reimplemented multiple operations.

* Mon Jun 28 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.3-2.svn2859
- Fixed bug #604860. Modify ComponentAdmin?'s search_fields from (('name',)) …
- Update the plan list & case list & run list
- Update the case run list
- Change from_config()'s return value from Nitrate to NitrateXmlrpc? 
- Fixed #606751 - grammar error on dashboard
- Fixed #605918 - Submitting larger comments fails
- Completed edit environment in run page
- Use updateObject() function to modify the sortkey for caserun
- Fixed create case failed issue
- Completed feature #604860 - further improvement Add 'pk' for each item under …
- Fixed #608545 - [REF] Simplify the estimation time choosing
- Fixed TestCase?.link_plan function returns
- Fixed #603752 - Cannot reassign tests in this test run: …
- Fixed #603622 - TestCase?.add_component: adding already attached component …
- Optimized front page display

* Sat Jun 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.3-1.svn2841
- Fixed UI Bug #600198 - TCMS][3.0.2-1] - Buttons not Visible in Add New Test …
- Completed feature #588974 - Make edit work flow more efficient
- Fixed remove case function in plan
- Fixed #602183 - TestCase.create requires plan id
- Fixed #602292 - TestCase.create() does not save "estimated_time"
- Fixed #601836 - Unable to change test case category using XML-RPC
- Completed Feature #587143 - [FEAT] Have a default component when creating …
- Fixed UI Bug 601693 - Test case field "arguments" not available in the web …
- Completed Feature #597094 - Edit environment of existing test run is not …
- Completed Feature #598882 - Changing status icon to 'start' or 'in …
- Initial completed feature #595372 - Environment available through xml-rpc
- Fixed #603127 - Quick test case search broken
- Fixed UI Bug #591783 - The assigned run should be in my run page
- Fixed edit env property/value name to exist name caused 500 error

* Tue Jun 8 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.2-2.svn2819
- Fixed #598935 - strip whitespace when adding bug numbers
- Fixed #598909 - Bugs filed from tcms contains HTML
- Fixed UI Bug #599465 - Filtering test plans based on the author broken
- Fixed #593091 - Programmatic access to TCMS via API requires user's Kerberos username/password
- Fixed tags lacked after search issue.
- Optimized batch automated operation form
- Fixed some UI issues.

* Thu Jun 3 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.2-1.svn2805
- Use livepiple to replace scriptaculous and clean up the js codes.
- Added initial data for syncdb.
- Added unit test script.
- Merged testplans.views.cases and testcases.views.all
- Ability to mark test case as 'Manual', 'Automated' and 'Autopropsed'
- Fixed TestRun.update() XML-RPC docs.
- Fixed #593805 - xmlrpc Testcase.update fails when using certain arguments.
- Fixed #593664 - Misinterpreted e-mail about test run.
- Fixed UI Bug #591819 - Icons and links made mistakes in test review.
- Fixed UI BUg #594623 - Test run CC can not be added.
- Completed FEAT Bug #583118 - RFE: Attachments for test-runs.
- Fixed #594432 - tags are not imported from xml.
- Completed FEAT #586085 - Don't select ALL test case after changing status
- Completed FEAT UI Bug #539077 - Provide an overall status on main test run page
- Completed FEAT BUg #574172 - If you sort a column in a plan, the filter options …
- Fixed Bug #567495 - Sort by category for 898 test cases results in 'Request …
- Completed FEAT #597705 - TCMS: Unknown user: when user name have space before or …
- Fixed Bug #597132 - Cannot add environment properties to test run
- Completed FEAT #578731 - Ability to view/manage all tags of case/plan.
- Fixed Bug #595680 - TCMS: cannot disable a test plan
- Fixed Bug #594566 - Get test case category by product is broken

* Wed May 19 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-3.svn2748
- Fixed #592212 - Search for test cases covering multiple bugs
- Fixed #543985 - sort testplans on "clone test case" page alphabetically
- Fixed #561234 - [feature request]should filter out “the space” key in all …
- Fixed UI Bug #577124 - [TCMS] - "Show comments" without number --remove …
- Fixed UI Bug 592974 - Adding a test case to a plan using plan id does not …
- Fixed report 500 service error
- Fixed #592973 - Add cases from other plans fails with a service error
- Fixed get_components XML-RPC typo mistake and added docs to new filter …

* Thu May 13 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-2.svn2736
- Completed signal handler for mailing by a standalone threading
- Fixed test plan link for #591819
- Fixed 519029
- Optimized the menu style

* Tue May 11 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-1.svn2728
- Refined whole UI.
- Optimized query count for performance.
- Add examples to XML-RPC docs.
- Completed following methods for XML-RPC: Product.filter(),
  Product.filter_categories(), Product.filter_components(), Product.filter_versions(),
  Product.get_component(), Product.get_tag(), Product.get_versions(),
  Product.lookup_id_by_name(), TestCase.calculate_average_estimated_time(),
  TestCase.calculate_total_estimated_time(), User.filter(), User.get(),
  User.update().
- Fixed UI bugs: #590647, #583908, #570351, #588970, #588565, #578828, #562110,
  #582958, #542664.
- Fixed app bugs: #582517, #582910, #584838, #586684, #584342, #578828
  #577820, #583917, #562110, #580494, #570351, #589124, #577130, #561406, #586085,
  #588595, #560791, #584459.

* Fri Apr 16 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0-1b2.svn2665
- Fixed #582517 - remove tag doesn't work
- Fixed #582910 - Automatic Display of Next Test Case Not working properly.
- Fixed #574663
- Completed Ability to edit environment for existed test run
- Completed change case run assignee feature
- Completed get form ajax responder
- Optimized get info responder

* Wed Apr 14 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0-1b1.svn2650
- Initial completed most new features, extend database schema
- Initial completed bookmark(watch list) feature(Models added)
- Initial completed modify run environment value feature(Backend code)
- Extend the schema for outside bug track system(Backend code)
- Improve run mail feature
- Optimized XML-RPC and the docs
- Fixed 'Save and add another' crash when create new case
- Fixed Assign case to run and create new run without default tester.
- Fixed Build.create() bug
- Fixed TestRun.get_test_case_runs() bug

* Thu Apr 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-5.svn2599
- Fixed add tag to run cause to crash issue.

* Mon Mar 29 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-4.svn2594
- Completed create/update functions for XML-RPC.
- Fixed web browser compatible issues.
- Improve review case progress.

* Tue Mar 23 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-3.svn2577
- Fixed Webkit based browser compatible issues
- Fixed TinyMCE in Webkit based browser compatible issues
- Fixed UI Bug: #570351
- Fixed UI Bug: #553308

* Mon Mar 22 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-2.svn2568
- Fixed search case without product issue(r2567)
- Fixed create run foot UI issue(r2566)
- Fixed update component in search case issue(r2565)

* Thu Mar 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-1.svn2564
- Complete most of XML-RPC functions.
- Complete batch operation for case including setting priority, add/remove tag.
- Fixed most of bugs.

* Wed Mar 17 2010 Xuqing Kuang <xkuang@redhat.com> -2.2-4.svn2504
- Fixed version in web ui incorrect.

* Fri Mar 12 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-3.svn2504
- HOT BUG FIXING - #572487

* Thu Mar 4 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-2.svn2504
- Fixed UI bug: Execute link exceed the width issue
- Fixed UI bug: CC for run page display issue

* Mon Mar 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-1.svn2500
- Add a new serializer for XMLRPC serialization
- Fixed KerbTransport authorization issue
- Change deployment method to WSGI
- A lot of bugs fixing for application.
- Fixed a lot of UI bugs

* Thu Feb 11 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-4.svn2461
- Fixed application bug #561620
- Fixed web UI bug #529807
- Fixed web UI bug #561610
- Fixed web UI bug #552923
- Fixed web UI bug #561252
- Fixed web UI bug #553308
- Fixed web UI bug #558955
- Fixed web UI bug #560091
- Fixed web UI bug #560055

* Tue Feb 2 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-3.svn2449
- Remove product version from case search page.
- Optimize search case form.

* Tue Feb 2 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-2.svn2446
- Fixed the case display with the bug added directly in case page in run issue.
- Fixed edit case component selector issue.
- Case product link to category now, disconnect from plan.

* Mon Feb 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-1.svn2443
- Rewrite get case details to ajax code, for optimize performance
- Add tag support for test run
- Add bug to case directly now supported.

* Mon Jan 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-3.svn2403
- Fixed hot issue #556382

* Mon Jan 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn2402
- Fixed auto blind down issue
- Fixed #555702
- Fixed #555703
- Fixed #555707 and #554676
- Completed add tag to case/plan when create backend function

* Fri Jan 15 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn2394
- Fixed most of bugs
- The component will add to new product specific in clone function
- Use Cache backend to handle session
- More optimization

* Mon Jan 11 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-1RC.svn2368
- Fixed a lot of bugs
- Optimize new comment system
- Completed new log system
- Add new case fiter to plan
- Improve new review workflow
- Update setup.py

* Tue Dec 29 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1beta.svn2318
- First public beta release of 2.0
- Rewrite most components
- Add estimated time into run
- Add test case review workflow
- Add XML-RPC interface
- Use a lot Ajax to instead of render whole page
- Redesign the interface

* Fri Dec 18 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-3.svn2261
- Add case run changelog show in run details page feature

* Tue Dec 8 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-2.svn2229
- Fixed #544951
- Fixed #544229
- Fixed #543985
- Fixed #544951
- Fixed reporing when plan count is null issue
- Update overview report of product statistics SQL

* Fri Dec 4 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-1.svn2213
- Fixed #541823
- Fixed #541829
- Optimize delete case/run ACL policy.
- Initial completed Reporting feature.
- Initial XML-RPC interface


* Wed Nov 25 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-3.svn2167
- Made a mistake in checkout the source, so rebuild it.

* Wed Nov 25 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-2.svn2167
- [2152] Fixed bug #530478 - Case run case_text_version is 0 cause to file bug crash
- [2154] Fixed bug #538747
- [2156] Use QuerySet update function to batch modify the database
- [2158] Fixed bug #540794 - [FEAT]It should stay in the same tab/page after refreshing
- [2162] Restore search detect in plan all page
- [2163] Fixed bug #538849 - Test case execute comment garbled
- [2165] Fixed bug #540371 - Where are Cloned Tests

* Fri Nov 20 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-1.svn2143
- Fixed UI bug #530010 - clean float dialog
- Fixed UI bug #531942 - Correct strings in system
- Fixed UI bug #536996
- Fixed UI bug #533866 - sort case in test case searching
- Optimize a lot of UI and frontend permission control
- Fixed bug #536982 - Now the run must be required with a case
- Remove manage case page
- Enhanced sort case feature with drag and drop in plan and run
- Completed change multiple case status at one time
- Completed change run status feature
- Completed clone multiple plan feature
- Completed upload plan document with ODT format
- Fixed bug #533869 - "Save and add another" case button results in a traceback
- Completed case attachment feature

* Mon Nov 9 2009 Xuqing Kuang <xkuang@redhat.com> - 1.1-1.svn2097
- Release 1.1 version TCMS
- Completed clone case/run feature
- Refined the UI structure
- Add XML-RPC interface for ATP

* Mon Nov 9 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-9.svn2046
- Add mod_auth_kerb.patch for authorize with apache kerberos module.

* Thu Oct 22 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-7.svn2046.RC
- Improve templates

* Thu Oct 22 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-6.svn2046.RC
- Imporove test plan clone feature
- Fixed failed case run count in run details page
- Add RELEASENOTES

* Wed Oct 21 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-5.svn2042.RC
- Realign the version to 1.0
- Fixed most of bugs

* Wed Oct 16 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-4.svn2006.RC
- Fixed other unimportant bugs, release RC.

* Wed Oct 14 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-3.svn1971
- Fixed most of bugs and get ready to GA.
- KNOWN ISSUE: Search case to add to plan just complete the page design, is waiting for logic function.

* Wed Sep 30 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn1938
- Rewrite assign case page
- Rewrite attachment implementation
- Search with environment is available
- Fixed app bugs:
- Fixed #524578 - The Product version will display after finish searching plans 
- Fixed #524568 - Cannot reset the status of test cases when the status is "Passed" or "Failed" 
- Fixed #524534 - Can't add a new test case 
- UI Bugs:
- Fixed #524530 - Please adjust the Next button in create new plan page0
- Fixed #525044 - The buttons are not aligned and missing some checkboxes when searching cases
- Fixed #524568 - Cannot reset the status of test cases when the status is "Passed" or "Failed"
- Fixed #524140 - Cannot create test plan when the uploaded plan document's type is HTML
- Fixed #525614 - The label that counts the number should at the same place on every ADMIN's sub-tab
- Fixed #524777 - [FEAT]It should have breadcrumbs on Admin tab have added breadcrumb to admin page
- Fixed #525630 - The calendar and clock icon should be kept on the same line with date and time
- Fixed #525830 - The same buttons aligned in different tabs should keep consistent
- Fixed #525606 - "Is active" should be kept on the same line with its check-box 

* Tue Sep 23 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn1898
- Feature:
- Completed environment element modfiy/delete feature in admin
- Fixed #525039 - [FEAT]It should let users add notes and set status of test cases even when the status of the test run is "Finished"
- UI Bugs:
- Fixed #521327 - Test Plan Document translation not quite right
- Fixed #524230 - can't change the "automated" field of a test case
- Fixed #524536 - Suggest to adjust the add new test case page width and the button "Add case"
- Fixed #524530 - Please adjust the Next button in create new plan page
- Fixed #518652 - can't remove test case from a plan
- Fixed #524774 - [FEAT]It should have a title on each of the add "Admin=>Management" webpage
- Fixed #525044 - The buttons are not aligned and missing some checkboxes when searching cases
- Fixed #524778 - [Admin]The add icons should be after the fields

* Tue Sep 15 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1863
- Remove case from plan
- Sort case in plan
- Fixed edit case issue

* Tue Sep 1 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1833
- Fixed a lot of bug.
- Redesign the interface.

* Wed Jul 22 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1799
- Rewrite most of components
- Add tables from Django
- dump version to 2.0 (trunk development version)

* Thu Mar 19 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-6.svn1547
- require kerberos authentication
- svn r1547

* Tue Mar 17 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-5.svn1525
- mark tcms/product_settings.py as being a config file
- add dependency on mod_ssl

* Tue Mar 17 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-4.svn1525
- substitute RPM metadata into the page footer so that it always shows the
exact revision of the code
- bump to svn revision 1525

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-3.svn1487
- drop the dist tag

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-2.svn1487
- add build-requires on Django to try to get pylint to work (otherwise: tcms/urls.py:11: [E0602] Undefined variable 'patterns')

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-1.svn1487
- 0.16
- add build-requires on python-setuptools

* Tue Feb 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-4
- fix regexp for pylint errors

* Tue Feb 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-3
- add code to invoke pylint.  Stop building the rpm if pylint finds
a problem.

* Wed Feb 18 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-2.svn1309
- add mod_python and python-memcached dependencies
- move static content to below datadir
- add apache config to correct location

* Thu Feb 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-1.svn1294
- initial packaging

