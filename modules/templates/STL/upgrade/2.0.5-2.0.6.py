# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# STL Template Version 2.0.5 => 2.0.6
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/STL/upgrade/2.0.5-2.0.6.py
#
#import datetime
import sys
#from s3 import S3DateTime

#from gluon.storage import Storage
#from gluon.tools import callback

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    print >> sys.stderr, msg,
def infoln(msg):
    print >> sys.stderr, msg

# Load models for tables
atable = s3db.dvr_activity

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "STL")

# -----------------------------------------------------------------------------
if not failed:
    info("Install catalog items")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "supply", "catalog_item.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "items.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("supply_catalog_item")
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        if resource.error:
            infoln("...failed")
            infoln(resource.error)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
if not failed:
    info("Create document keys for activities")

    query = (atable.deleted != True) & (atable.doc_id == None)
    rows = db(query).select(atable.id,
                            atable.doc_id,
                            )

    updated = 0
    for row in rows:
        s3db.update_super(atable, row)
        if row.doc_id:
            updated += 1
        else:
            failed = True
            break

    if failed:
        infoln("...failed")
    else:
        infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Upgrade user roles
if not failed:
    info("Upgrade user roles")

    bi = s3base.S3BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    with open(filename, "r") as File:
        try:
            bi.import_role(filename)
        except Exception, e:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
