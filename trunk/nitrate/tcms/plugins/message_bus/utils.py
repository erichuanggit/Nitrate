# -*- coding: utf-8 -*-

def refresh_HTTP_credential_cache():
    '''
    Refresh HTTP ticket cache from /etc/httpd/httpd.keytab

    No return value.
    '''

    import krbV, os, socket

    # TODO: There may be a better way to get the keytab file name rather than hard code here.
    keytab_file = '/etc/httpd/conf/httpd.keytab'
    realm = 'REDHAT.COM'
    principal_name = 'HTTP/%s@%s' % (socket.getfqdn(), realm)
    # This is the credential cache file, according to the Kerberbos V5 standard
    ccache_file = '/tmp/krb5cc_%d' % os.getuid()

    ctx = krbV.default_context()
    princ = krbV.Principal(name=principal_name, context=ctx)
    keytab = krbV.Keytab(name=keytab_file, context=ctx)
    ccache = krbV.CCache(name=ccache_file, context=ctx)

    ccache.init(princ)
    ccache.init_creds_keytab(principal=princ, keytab=keytab)
