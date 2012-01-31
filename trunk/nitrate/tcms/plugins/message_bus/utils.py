# -*- coding: utf-8 -*-

from tcms.plugins.message_bus import settings as st

def refresh_HTTP_credential_cache():
    '''
    Put service ticket into credential cache from service's keytab file.

    Return the credential cache file name.
    '''

    import krbV, os

    keytab_file = st.SERVICE_KEYTAB
    principal_name = st.SERVICE_PRINCIPAL
    # This is the credential cache file, according to the Kerberbos V5 standard
    ccache_file = '/tmp/krb5cc_%d_%d' % (os.getuid(), os.getpid())

    ctx = krbV.default_context()
    princ = krbV.Principal(name=principal_name, context=ctx)
    keytab = krbV.Keytab(name=keytab_file, context=ctx)
    ccache = krbV.CCache(name=ccache_file, context=ctx)

    ccache.init(princ)
    ccache.init_creds_keytab(principal=princ, keytab=keytab)

    return ccache_file
