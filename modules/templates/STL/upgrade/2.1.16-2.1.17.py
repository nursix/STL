# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# STL Template Version 2.1.16 => 2.1.17
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/STL/upgrade/2.1.16-2.1.17.py
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
atable = s3db.pr_address
ctable = s3db.dvr_case
ptable = s3db.pr_person
petable = s3db.pr_pentity

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "STL")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade beneficiary addresses")

    join = [ptable.on((ptable.pe_id == atable.pe_id) &
                      (ptable.deleted == False)),
            ctable.on((ctable.person_id == ptable.id) &
                      (ctable.deleted == False)),
            ]
    query = (atable.type.belongs(1, 2)) & \
            (atable.location_id != None) & \
            (atable.deleted == False)
    rows = db(query).select(atable.id,
                            atable.location_id,
                            atable.is_base_location,
                            ptable.pe_id,
                            ptable.location_id,
                            join = join,
                            orderby = (~atable.modified_on, atable.type),
                            )

    total = len(rows)
    updated = 0
    base_locations = 0

    from s3 import S3Tracker

    seen = set()
    for row in rows:

        person = row.pr_person
        pe_id = person.pe_id
        if pe_id in seen:
            continue
        else:
            seen.add(pe_id)

        address = row.pr_address
        if person.location_id != address.location_id:

            S3Tracker()(petable, pe_id).set_base_location(address.location_id)

            base_locations += 1

        if not address.is_base_location:
            address.update_record(is_base_location = True)

            query = (atable.pe_id == pe_id) & (atable.id != address.id)
            db(query).update(is_base_location=False)

            updated += 1

    infoln("...done (%s total, %s updated, %s base locations set)" %
               (total, updated, base_locations))

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade cases")

    updated = 0
    rows = db(ctable.deleted == False).select(ctable.id)
    for row in rows:
        success = s3db.update_super(ctable, row)
        if not success:
            infoln("...failed")
            failed = True
            break
        else:
            updated += 1
    if not failed:
        infoln("...done (%s updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
