# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# STL Template Version 2.0.1 => 2.0.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/STL/upgrade/2.0.1-2.0.2.py
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
etable = s3db.dvr_economy
atable = s3db.dvr_case_activity
ftable = s3db.dvr_activity_funding

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "STL")

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
# Migrate dvr_economy.average_weekly_income to dvr_economy.monthly_income
#
if not failed:
    info("Migrate case economy records")

    query = (etable.deleted != True) & \
            (etable.monthly_income == None)

    migrated = 0
    try:
        migrated = db(query).update(monthly_income = etable.average_weekly_income)
    except:
        failed = True
    else:
        query = (etable.deleted != True)
        try:
            db(query).update(average_weekly_income=None)
        except:
            failed = True

    if failed:
        infoln("...failed")
    else:
        infoln("...done (%s records migrated)" % migrated)

# -----------------------------------------------------------------------------
# Migrate dvr_activity_funding.proposal to dvr_activity_funding.reason
#
if not failed:
    info("Migrate activity funding records")

    query = (ftable.deleted != True)

    migrated = 0
    try:
        migrated = db(query).update(reason = ftable.proposal)
    except:
        failed = True
    else:
        query = (ftable.deleted != True)
        try:
            db(query).update(proposal=None)
        except:
            failed = True

    if failed:
        infoln("...failed")
    else:
        infoln("...done (%s records migrated)" % migrated)

# -----------------------------------------------------------------------------
# Migrate dvr_case_activity.need_id to dvr_case_activity_need
#
if not failed:
    info("Migrate case activity records")

    query = (atable.deleted != True) & \
            (atable.need_id != None)

    rows = db(query).select(atable.id,
                            atable.need_id,
                            atable.created_by,
                            atable.created_on,
                            atable.modified_by,
                            atable.modified_on,
                            )

    migrated = 0
    lresource = s3db.resource("dvr_case_activity_need")
    for row in rows:
        data = {"case_activity_id": row.id,
                "need_id": row.need_id,
                "created_by": row.created_by,
                "created_on": row.created_on,
                "modified_by": row.modified_by,
                "modified_on": row.modified_on,
                }
        if lresource.insert(**data):
            migrated += 1
        else:
            failed = True
            break

    if failed:
        infoln("...failed")
    else:
        infoln("...done (%s records migrated)" % migrated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
