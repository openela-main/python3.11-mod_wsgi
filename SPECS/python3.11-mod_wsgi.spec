%global __python3 /usr/bin/python3.11
%global python3_pkgversion 3.11

%{!?_httpd_apxs: %{expand: %%global _httpd_apxs %%{_sbindir}/apxs}}

%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn 2>/dev/null || echo 0-0)}}
%{!?_httpd_confdir:    %{expand: %%global _httpd_confdir    %%{_sysconfdir}/httpd/conf.d}}
# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}
%{!?_httpd_moddir:    %{expand: %%global _httpd_moddir    %%{_libdir}/httpd/modules}}

%if 0%{?fedora} || 0%{?rhel} > 7
%bcond_without python3
%bcond_with python2
%else
%bcond_with python3
%bcond_without python2
%endif

Name:           python%{python3_pkgversion}-mod_wsgi
Version:        4.9.4
Release:        1%{?dist}
Summary:        A WSGI interface for Python web applications in Apache
License:        ASL 2.0
URL:            https://modwsgi.readthedocs.io/
Source0:        https://github.com/GrahamDumpleton/mod_wsgi/archive/%{version}.tar.gz#/mod_wsgi-%{version}.tar.gz
Source1:        wsgi.conf
Source2:        wsgi-python3.conf
Patch1:         mod_wsgi-4.5.20-exports.patch
Patch2:         mod_wsgi-4.7.1-remove-rpath.patch

BuildRequires:  httpd-devel
BuildRequires:  gcc
BuildRequires:  make


Requires:       httpd-mmn = %{_httpd_mmn}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-rpm-macros
BuildRequires:  python%{python3_pkgversion}-setuptools

# Suppress auto-provides for module DSO
%{?filter_provides_in: %filter_provides_in %{_httpd_moddir}/.*\.so$}
%{?filter_setup}

# httpd can only load one Python 3 version of mod_wsgi at the time, and
# therefore we use a Conflicts tag to only allow one to be installed.  The
# alternative would be to define a priority between them (e.g. python3- has
# priority over python38-), however, it would be potentially confusing and
# tricky to notice why the other version is not working.
Conflicts: python3-mod_wsgi
Conflicts: python38-mod_wsgi
Conflicts: python39-mod_wsgi

%global _description\
The mod_wsgi adapter is an Apache module that provides a WSGI compliant\
interface for hosting Python based web applications within Apache. The\
adapter is written completely in C code against the Apache C runtime and\
for hosting WSGI applications within Apache has a lower overhead than using\
existing WSGI adapters for mod_python or CGI.\


%description %_description

%if %{with python2}
%package -n python2-%{name}
Summary: %summary
Requires:       httpd-mmn = %{_httpd_mmn}
BuildRequires:  python2-devel, python2-setuptools
%{?python_provide:%python_provide python2-%{name}}
%if 0%{?rhel} && 0%{?rhel} <= 7
Provides: mod_wsgi = %{version}-%{release}
Provides: mod_wsgi%{?_isa} = %{version}-%{release}
Obsoletes: mod_wsgi < %{version}-%{release}
%endif

%description -n python2-%{name} %_description

%endif



%prep
%autosetup -p1 -n mod_wsgi-%{version}

: Python2=%{with python2} Python3=%{with python3}

%build

export LDFLAGS="$RPM_LD_FLAGS -L%{_libdir}"
export CFLAGS="$RPM_OPT_FLAGS -fno-strict-aliasing"

%if %{with python3}
mkdir py3build/
# this always produces an error (because of trying to copy py3build
# into itself) but we don't mind, so || :
cp -R * py3build/ || :
pushd py3build
%configure --enable-shared --with-apxs=%{_httpd_apxs} --with-python=%{__python3}
%make_build
%py3_build
popd
%endif

%if %{with python2}
%configure --enable-shared --with-apxs=%{_httpd_apxs} --with-python=%{python2}
%make_build
%py2_build
%endif

%install
# first install python3 variant and rename the so file
%if %{with python3}
pushd py3build
%make_install LIBEXECDIR=%{_httpd_moddir}
mv  $RPM_BUILD_ROOT%{_httpd_moddir}/mod_wsgi{,_python3}.so

install -d -m 755 $RPM_BUILD_ROOT%{_httpd_modconfdir}
# httpd >= 2.4.x
install -p -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_httpd_modconfdir}/10-wsgi-python3.conf

%py3_install
mv $RPM_BUILD_ROOT%{_bindir}/mod_wsgi-express{,-3}
ln -s %{_bindir}/mod_wsgi-express-3  $RPM_BUILD_ROOT%{_bindir}/mod_wsgi-express-%{python3_version}
popd

%endif

# second install python2 variant
%if %{with python2}
%make_install LIBEXECDIR=%{_httpd_moddir}

install -d -m 755 $RPM_BUILD_ROOT%{_httpd_modconfdir}
# httpd >= 2.4.x
install -p -m 644 %{SOURCE1} $RPM_BUILD_ROOT%{_httpd_modconfdir}/10-wsgi.conf

%py2_install
mv $RPM_BUILD_ROOT%{_bindir}/mod_wsgi-express{,-2}
ln -s %{_bindir}/mod_wsgi-express-2 $RPM_BUILD_ROOT%{_bindir}/mod_wsgi-express
%endif

%if %{with python2}
%files -n python2-%{name}
%license LICENSE
%doc CREDITS.rst README.rst
%config(noreplace) %{_httpd_modconfdir}/*wsgi.conf
%{_httpd_moddir}/mod_wsgi.so
%{python2_sitearch}/mod_wsgi-*.egg-info
%{python2_sitearch}/mod_wsgi
%{_bindir}/mod_wsgi-express-2
%{_bindir}/mod_wsgi-express
%endif

%if %{with python3}
%files -n python%{python3_pkgversion}-mod_wsgi
%license LICENSE
%doc CREDITS.rst README.rst
%config(noreplace) %{_httpd_modconfdir}/*wsgi-python3.conf
%{_httpd_moddir}/mod_wsgi_python3.so
%{python3_sitearch}/mod_wsgi-*.egg-info
%{python3_sitearch}/mod_wsgi
%{_bindir}/mod_wsgi-express-%{python3_version}
%{_bindir}/mod_wsgi-express-3
%endif

%changelog
* Thu Dec 01 2022 Charalampos Stratakis <cstratak@redhat.com> - 4.9.4-1
- Initial package
- Fedora contributions by:
      Adam Williamson <awilliam@redhat.com>
      Alexander Bokovoy <abokovoy@redhat.com>
      Bill Nottingham <notting@fedoraproject.org>
      Dennis Gilmore <dennis@ausil.us>
      dmalcolm <dmalcolm@fedoraproject.org>
      Ignacio Vazquez-Abrams <ivazquez@fedoraproject.org>
      Igor Gnatenko <ignatenkobrain@fedoraproject.org>
      Iryna Shcherbina <shcherbina.iryna@gmail.com>
      Jakub Dorňák <jakub.dornak@misli.cz>
      James Bowes <jbowes@repl.ca>
      Jan Kaluza <jkaluza@redhat.com>
      jbowes <jbowes@fedoraproject.org>
      Jesse Keating <jkeating@fedoraproject.org>
      Joe Orton <jorton@redhat.com>
      joshkayse <joshkayse@fedoraproject.org>
      Kevin Fenzi <kevin@fedoraproject.org>
      Luboš Uhliarik <luhliari@redhat.com>
      Luke Macken <lmacken@fedoraproject.org>
      Matthias Runge <mrunge@redhat.com>
      Miro Hrončok <miro@hroncok.cz>
      Orion Poplawski <orion@cora.nwra.com>
      Peter Robinson <pbrobinson@fedoraproject.org>
      Richard W.M. Jones <rjones@redhat.com>
      Ricky Zhou (周家杰) <ricky@fedoraproject.org>
      Tomas Hrnciar <thrnciar@redhat.com>
      Tom Stellard <tstellar@redhat.com>
      Troy Dawson <tdawson@redhat.com>
      Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl>
