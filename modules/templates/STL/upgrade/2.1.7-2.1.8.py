# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# STL Template Version 2.1.7 => 2.1.8
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/STL/upgrade/2.1.7-2.1.8.py
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
ctable = s3db.dvr_case
atable = s3db.dvr_case_activity
stable = s3db.dvr_case_status

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "STL")

# -----------------------------------------------------------------------------
if not failed:
    info("Install additional case statuses")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_status.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_status.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("dvr_case_status")
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
    info("Reset status for cases without activities")

    updated = 0

    # Get relevant status IDs
    query = (stable.code.belongs(("NEW", "OPEN"))) & \
            (stable.deleted == False)
    rows = db(query).select(stable.id,
                            stable.code,
                            limitby = (0, 2),
                            )
    status_ids = dict((row.code, row.id) for row in rows)

    NEW = status_ids.get("NEW")
    OPEN = status_ids.get("OPEN")
    if NEW and OPEN:

        # Count the number of case activities per OPEN case record
        ctable = s3db.dvr_case
        atable = s3db.dvr_case_activity

        left = atable.on((atable.person_id == ctable.person_id) & \
                         ((atable.case_id == None) | \
                          (atable.case_id == ctable.id)) & \
                         (atable.deleted == False))

        query = (ctable.status_id == OPEN) & \
                (ctable.deleted == False)

        acount = atable.id.count()

        rows = db(query).select(ctable.id,
                                acount,
                                groupby = ctable.id,
                                having = (acount == 0),
                                left = left,
                                )

        case_ids = set(row.dvr_case.id for row in rows)
        if case_ids:
            updated = db(ctable.id.belongs(case_ids)).update(status_id = NEW)

    infoln("...done (%s cases updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
