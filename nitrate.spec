%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           nitrate
Version:        3.8.6
Release:        3%{?dist}
Summary:        Test Case Management System

Group:          Development/Languages
License:        GPLv2+
URL:            https://fedorahosted.org/nitrate/browser/trunk/nitrate
Source0:        https://fedorahosted.org/releases/n/i/nitrate/%{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-devel

Requires:       Django = 1.5.5
Requires:       django-uuslug
Requires:       kobo-django >= 0.2.0-3
Requires:       mod_auth_kerb
Requires:       mod_ssl
Requires:       mod_wsgi
Requires:       MySQL-python >= 1.2.3
Requires:       python-kerberos
Requires:       python-qpid
Requires:       w3m
Requires:       wadofstuff-django-serializers >= 1.1.0

%description
Nitrate is a tool for tracking testing being done on a product.

It is a database-backed web application, implemented using Django

%prep
%setup -q

# Fixup the version field in the page footer so that it shows the precise
# RPM version-release:
sed --in-place \
  -r 's|NITRATE_VERSION|%{version}-%{release}|' \
  tcms/templates/tcms_base.html

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Copy static content from 32/64bit-specific python dir to shared data dir:
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/%{name}
mkdir -p ${RPM_BUILD_ROOT}%{_docdir}/%{name}
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/%{name}/static

for d in contrib; do
    cp -r ${d} ${RPM_BUILD_ROOT}%{_datadir}/%{name};
done

# Install apache config for the app:
install -m 0644 -D -p contrib/conf/nitrate-httpd.conf  ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/%{name}.conf

%post
# Collect static file for the app:
/usr/bin/django-admin collectstatic --noinput --clear --settings=tcms.settings.product

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog README.rst LICENSE
%{python_sitelib}/tcms/
%{python_sitelib}/nitrate-%{version}-py*.egg-info/
%{_datadir}/%{name}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{python_sitelib}/tcms/settings/product.py

%changelog

* Tue Dec 10 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-5
- 1036538 [advance search]printable copy, test cases is null even if select cases/plan from advance search list
- 1036678 [Print plan]No cases information in print view page

* Tue Dec 4 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-4
- 1036028 [Test plan] Unable to calculate all run progress even if I select "Also select the rest XX page(s)"
- 1036598 [Add tag]"6932 undefined" warning when add tag without select "Also select cases that are not shown below, yet."
- 1036538 [advance search]printable copy, test cases is null even if select cases/plan from advance search list
- 1036672 [export all cases]Export all cases result is blank
- 1036678 [Print plan]No cases infomation in print view page
- 1036609 [Test Plan]Unable to set default tester in test plan
- 1036627 [Test Plan]Unable to batch set status in test plan
- 1036629 [Test Plan]Unable to batch set priority in test plan
- 1036508 [advance search]Can not export selected test cases/plan to download file from advance search list
- 1036042 [RFE]Suggest change the description of "Also select cases that are not shown below, yet." in test plan
- 1035956 [test plan]Unable to create new test run or add cases to existing run

* Tue Nov 28 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-3
- Bug 1028863 - [Testplan][Runs] In 'Runs' label of a Test plan, not input any thing in 'Items Per Page' then search, the site have no responce
- Bug 1028921 - [TestPlan][Cases] It is better if the select all function can select all the cases which are filtered
- Bug 1032897 - Test runs of a Test plan a displayed incorrectly
- Bug 1032969 - Missing progress bar on test run search result

* Tue Nov 13 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-2
- Using a separated file to track all database changes

* Tue Nov 12 2013 Chenxiong Qi <cqi@redhat.com> - 3.8.5-1
- Bug 1017112 - [Performance] Loading TestRuns in pagination way in the TestPlan page
- Bug 1018021 - [Performance] Search TestPlan without any criteria causes MySQL occurpies nearly 100% CPU time
- Bug 1019641 - Lazy-loading TreeView tab in a TestPlan page
- Bug 1017110 - [Performace] Loading Reviewing TestCases in pagination way in the TestPlan page
- Bug 1017102 - [Performace] Loading TestCases in pagination way in the TestPlan page
- Bug 1017255 - [Performance] Rewrite implementation of TestCase' progressbar
- Bug 1024289 - [Advanced Search] Components/Versions/Categories/Builds are not shown after select a Product in 'Advanced Search' page
- Bug 1025657 - [Cases] Python error page is shown if input full-width characters in 'Default Tester' when add/edit a case
- Bug 1024680 - [Home][Basic Information] The Python error page is shown if Name is invalid in Basic Information

*Tue Sep 17 2013 Jian Chen <jianchen@redhat.com> - 3.8.4
- Add a column with number of comments into Case Runs table
- Several Bug Fixes (Refer to ChangeLog)

* Fri Jul 25 2013 Chaobin Tang <ctang@redhat.com> - 3.8.2
- XMLRPC API (Refer to ChangeLog)

*Fri Jul 11 2011 Chaobin Tang <ctang@redhat.com> - 3.5
- Usability Improvements (Refer to ChangeLog)

*Fri Mar 3 2011 Chaobin Tang <ctang@redhat.com> - 3.4.1
- Testing Report Implementation
- Several Bug Fixes (Refer to ChangeLog)

*Fri Mar 3 2011 Chaobin Tang <ctang@redhat.com> - 3.4
- Advance Search Implementation
- Several Bug Fixes (Refer to ChangeLog)

*Fri Feb 25 2011 Yuguang Wang <yuwang@redhat.com> - 3.3-3
- Upstream released new version

*Tue Feb 15 2011 Yuguang Wang <yuwang@redhat.com> - 3.3-2
- Upstream released new version

*Mon Jan 24 2011 Yuguang Wang <yuwang@redhat.com> - 3.3-1
- Upstream released new version
- Include apache QPID support
- Completed global signal processor

* Thu Dec 1 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-4
- Upstream released new version

* Tue Nov 30 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-3
- Upstream released new version

* Tue Nov 23 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-2
- Upstream released new version

* Tue Nov 9 2010 Xuqing Kuang <xkuang@redhat.com> - 3.2-1
- Upstream released new version

* Fri Sep 17 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.1-3
- Upstream released new version

* Wed Sep 15 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.1-2
- Upstream released new version

* Wed Sep 8 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.1-1
- Upstream released new version
- Add highcharts for future reporting
- Add django-pagination support.

* Thu Aug 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.0-2
- Upstream released new version

* Thu Aug 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.1.0-1
- Upstream released new version

* Fri Aug 2 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.4-3
- Upstream released new version

* Fri Jul 30 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.4-2
- Upstream released new version

* Wed Jul 21 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.4-1
- Upstream released new version

* Mon Jun 28 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.3-2.svn2859
- Upstream released new version

* Sat Jun 12 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.3-1.svn2841
- Upstream released new version

* Tue Jun 8 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.2-2.svn2819
- Upstream released new version

* Thu Jun 3 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.2-1.svn2805
- Upstream released new version
- Add JavaScript library 'livepiple'.

* Wed May 19 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-3.svn2748
- Upstream released new version

* Thu May 13 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-2.svn2736
- Upstream released new version

* Tue May 11 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0.1-1.svn2728
- Upstream released new version

* Fri Apr 16 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0-1b2.svn2665
- Upstream released new version

* Wed Apr 14 2010 Xuqing Kuang <xkuang@redhat.com> - 3.0-1b1.svn2650
- Upstream released new version

* Thu Apr 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-5.svn2599
- Upstream released new version

* Mon Mar 29 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-4.svn2594
- Upstream released new version

* Tue Mar 23 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-3.svn2577
- Upstream released new version

* Mon Mar 22 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-2.svn2568
- Upstream released new version

* Thu Mar 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.3-1.svn2564
- Upstream released new version

* Wed Mar 17 2010 Xuqing Kuang <xkuang@redhat.com> -2.2-4.svn2504
- Upstream released new version

* Fri Mar 12 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-3.svn2504
- Upstream released new version

* Thu Mar 4 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-2.svn2504
- Upstream released new version

* Mon Mar 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.2-1.svn2500
- Upstream released new version

* Thu Feb 11 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-4.svn2461
- Upstream released new version

* Tue Feb 2 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-3.svn2449
- Upstream released new version

* Tue Feb 2 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-2.svn2446
- Upstream released new version

* Mon Feb 1 2010 Xuqing Kuang <xkuang@redhat.com> - 2.1-1.svn2443
- Upstream released new version

* Mon Jan 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-3.svn2403
- Upstream released new version

* Mon Jan 18 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn2402
- Upstream released new version

* Fri Jan 15 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn2394
- Upstream released new version

* Mon Jan 11 2010 Xuqing Kuang <xkuang@redhat.com> - 2.0-1RC.svn2368
- Upstream released new version

* Tue Dec 29 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1beta.svn2318
- Upstream released new version

* Fri Dec 18 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-3.svn2261
- Upstream released new version

* Tue Dec 8 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-2.svn2229
- Upstream released new version

* Fri Dec 4 2009 Xuqing Kuang <xkuang@redhat.com> - 1.3-1.svn2213
- Upstream released new version

* Wed Nov 25 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-3.svn2167
- Upstream released new version

* Wed Nov 25 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-2.svn2167
- Upstream released new version

* Fri Nov 20 2009 Xuqing Kuang <xkuang@redhat.com> - 1.2-1.svn2143
- Upstream released new version

* Mon Nov 9 2009 Xuqing Kuang <xkuang@redhat.com> - 1.1-1.svn2097
- Upstream released new version

* Mon Nov 9 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-9.svn2046
- Upstream released new version

* Thu Oct 22 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-7.svn2046.RC
- Upstream released new version

* Thu Oct 22 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-6.svn2046.RC
- Upstream released new version

* Wed Oct 21 2009 Xuqing Kuang <xkuang@redhat.com> - 1.0-5.svn2042.RC
- Upstream released new version

* Wed Oct 16 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-4.svn2006.RC
- Upstream released new version

* Wed Oct 14 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-3.svn1971
- Upstream released new version

* Wed Sep 30 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn1938
- Upstream released new version

* Tue Sep 23 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-2.svn1898
- Upstream released new version

* Tue Sep 15 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1863
- Upstream released new version

* Tue Sep 1 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1833
- Upstream released new version

* Wed Jul 22 2009 Xuqing Kuang <xkuang@redhat.com> - 2.0-1.svn1799
- Upstream released new version

* Thu Mar 19 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-6.svn1547
- Upstream released new version

* Tue Mar 17 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-5.svn1525
- Upstream released new version

* Tue Mar 17 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-4.svn1525
- Upstream released new version

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-3.svn1487
- Upstream released new version

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-2.svn1487
- Upstream released new version

* Thu Mar 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.16-1.svn1487
- Upstream released new version

* Tue Feb 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-4
- Upstream released new version

* Tue Feb 24 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-3
- Upstream released new version

* Wed Feb 18 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-2.svn1309
- Upstream released new version
- add mod_python and python-memcached dependencies
- add apache config to correct location

* Thu Feb 12 2009 David Malcolm <dmalcolm@redhat.com> - 0.13-1.svn1294
- initial packaging
