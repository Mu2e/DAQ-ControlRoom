#!/usr/bin/env python
# Script to dump out the kerberos principal and available credential caches
import os
import sys  
import gssapi
import krb5

# Initialize a krb5 context (required for most library calls)
ctx = krb5.init_context()

# Get the default credential cache for the current user/process
cache = krb5.cc_default(ctx)

# Retrieve and print the principal stored in the default cache
p = krb5.cc_get_principal(ctx, cache)
print(p.name)

# Print the system's default realm
realm = krb5.get_default_realm(ctx)
print(realm)

# Iterate over all credential caches known to the system
cc_list = krb5.cccol_iter(ctx)
for cc in cc_list:
    try:
        # Some caches may not contain a principal; skip those
        p = krb5.cc_get_principal(ctx, cc)
        print(p.name)
    except Exception:
        # Ignore errors encountered while inspecting individual caches
        pass