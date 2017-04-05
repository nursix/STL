# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# STL Template Version 2.1.3 => 2.1.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/STL/upgrade/2.0.6-2.1.0.py
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
utable = auth.settings.table_user
otable = s3db.org_organisation

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "STL")

# -----------------------------------------------------------------------------
if not failed:
    info("Set owner organizations for group activities")

    left = (utable.on(utable.id == atable.owned_by_user),
            otable.on(otable.id == utable.organisation_id),
            )
    query = (atable.deleted == False)
    rows = db(query).select(atable.id,
                            otable.id,
                            otable.pe_id,
                            left = left,
                            )

    updated = 0
    for row in rows:
        organisation_id = row.org_organisation.id
        if (organisation_id):
            query = (atable.id == row.dvr_activity.id)
            try:
                success = db(query).update(organisation_id = organisation_id,
                                           realm_entity = row.org_organisation.pe_id,
                                           )
            except:
                pass
            if success:
                updated += 1

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
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
if not failed:
    info("Hide unused user roles")

    hidden = ("EDITOR", "MAP_ADMIN", "ORG_GROUP_ADMIN")
    query = s3db.auth_group.uuid.belongs(hidden)
    try:
        db(query).update(hidden=True)
    except:
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
