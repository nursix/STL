# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# STL Template Version 2.0.6 => 2.1.0
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

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "STL")

# -----------------------------------------------------------------------------
if not failed:
    info("Install response types")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("dvr_response_type")
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
    info("Install vulnerability types")

    # Remove all existing dvr_vulnerability_type_case_activity records
    ltable = s3db.dvr_vulnerability_type_case_activity
    try:
        db(ltable.id>0).delete()
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True

    # Remove all existing dvr_vulnerability_type records
    if not failed:
        ttable = s3db.dvr_vulnerability_type
        try:
            db(ttable.id>0).delete()
        except:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True

    if not failed:
        # File and Stylesheet Paths
        stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "vulnerability_type.xsl")
        filename = os.path.join(TEMPLATE_FOLDER, "dvr_vulnerability_type.csv")

        # Import, fail on any errors
        try:
            with open(filename, "r") as File:
                resource = s3db.resource("dvr_vulnerability_type")
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
