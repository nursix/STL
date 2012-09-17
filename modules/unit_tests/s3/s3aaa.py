# -*- coding: utf-8 -*-
#
# S3AAA Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3aaa.py
#
import unittest

from gluon import *
from gluon.storage import Storage
from s3.s3aaa import S3EntityRoleManager

# =============================================================================
class LinkToPersonTests(unittest.TestCase):
    """ Test s3_link_to_person """

    def setUp(self):

        s3db = current.s3db

        # Create organisation
        otable = s3db.org_organisation
        org = Storage(name="LTPRTestOrg")
        org_id = otable.insert(**org)
        self.assertTrue(org_id is not None)
        org["id"] = org_id
        s3db.update_super(otable, org)
        self.org_id = org_id
        self.org_pe_id = org.pe_id

        # Create person record
        ptable = s3db.pr_person
        person = Storage(first_name="TestLTPR",
                         last_name="User")
        person_id = ptable.insert(**person)
        self.assertTrue(person_id is not None)
        person["id"] = person_id
        s3db.update_super(ptable, person)
        self.person_id = person_id
        self.pe_id = person.pe_id

        # Add email contact
        ctable = s3db.pr_contact
        contact = Storage(pe_id=self.pe_id,
                          contact_method="EMAIL",
                          value="testltpr@example.com")
        contact_id = ctable.insert(**contact)
        self.assertTrue(contact_id is not None)

    def testLinkToNewPerson(self):
        """ Test linking a user account to a new person record """

        auth = current.auth
        s3db = current.s3db

        # Create new user record
        utable = auth.settings.table_user
        user = Storage(first_name="TestLTPR2",
                       last_name="User",
                       email="testltpr2@example.com",
                       password="XYZ")
        user_id = utable.insert(**user)
        self.assertTrue(user_id is not None)
        user["id"] = user_id

        # Link to person
        person_id = auth.s3_link_to_person(user, self.org_id)

        # Check the person_id
        self.assertNotEqual(person_id, None)
        self.assertFalse(isinstance(person_id, list))
        self.assertNotEqual(person_id, self.person_id)

        # Get the person record
        ptable = s3db.pr_person
        person = ptable[person_id]
        self.assertNotEqual(person, None)

        # Check the owner
        self.assertEqual(person.realm_entity, self.org_pe_id)

        # Check the link
        ltable = s3db.pr_person_user
        query = (ltable.user_id == user_id) & \
                (ltable.pe_id == person.pe_id)
        links = current.db(query).select()
        self.assertEqual(len(links), 1)

    def testLinkToExistingPerson(self):
        """ Test linking a user account to a pre-existing person record """

        auth = current.auth
        s3db = current.s3db

        # Create new user record
        utable = auth.settings.table_user
        user = Storage(first_name="TestLTPR",
                       last_name="User",
                       email="testltpr@example.com",
                       password="XYZ")
        user_id = utable.insert(**user)
        self.assertTrue(user_id is not None)
        user["id"] = user_id

        # Link to person record
        person_id = auth.s3_link_to_person(user, self.org_id)

        # Check the person_id
        self.assertNotEqual(person_id, None)
        self.assertFalse(isinstance(person_id, list))
        self.assertEqual(person_id, self.person_id)

        # Get the person record
        ptable = s3db.pr_person
        person = ptable[person_id]
        self.assertNotEqual(person, None)

        # Check the link
        ltable = s3db.pr_person_user
        query = (ltable.user_id == user_id) & \
                (ltable.pe_id == person.pe_id)
        links = current.db(query).select()
        self.assertEqual(len(links), 1)

    def testUpdateLinkedPerson(self):
        """ Test update of a pre-linked person record upon user account update """

        auth = current.auth
        s3db = current.s3db

        # Create new user record
        utable = auth.settings.table_user
        user = Storage(first_name="TestLTPR",
                       last_name="User",
                       email="testltpr@example.com",
                       password="XYZ")
        user_id = utable.insert(**user)
        self.assertTrue(user_id is not None)
        user["id"] = user_id

        # Link to person
        person_id = auth.s3_link_to_person(user, self.org_id)

        # Check the person_id
        self.assertNotEqual(person_id, None)
        self.assertFalse(isinstance(person_id, list))
        self.assertEqual(person_id, self.person_id)

        # Update the user record
        update = Storage(first_name="TestLTPR2",
                         last_name="User",
                         email="testltpr2@example.com")
        current.db(utable.id == user_id).update(**update)
        update["id"] = user_id

        # Link to person record again
        update_id = auth.s3_link_to_person(user, self.org_id)

        # Check unchanged person_id
        self.assertEqual(update_id, person_id)

        # Check updated person record
        ptable = s3db.pr_person
        person = ptable[update_id]
        self.assertEqual(person.first_name, update["first_name"])
        self.assertEqual(person.last_name, update["last_name"])

        # Check updated contact record
        ctable = s3db.pr_contact
        query = (ctable.pe_id == self.pe_id) & \
                (ctable.contact_method == "EMAIL")
        contacts = current.db(query).select()
        self.assertEqual(len(contacts), 2)
        emails = [contact.value for contact in contacts]
        self.assertTrue(user.email in emails)
        self.assertTrue(update.email in emails)

    def testMultipleUserRecords(self):
        """ Test s3_link_to_person with multiple user accounts """

        auth = current.auth
        s3db = current.s3db

        # Create new user records
        utable = auth.settings.table_user
        users = []
        user1 = Storage(first_name="TestLTPR1",
                       last_name="User",
                       email="testltpr1@example.com",
                       password="XYZ")
        user_id = utable.insert(**user1)
        self.assertTrue(user_id is not None)
        user1["id"] = user_id
        users.append(user1)

        user2 = Storage(first_name="TestLTPR2",
                       last_name="User",
                       email="testltpr2@example.com",
                       password="XYZ")
        user_id = utable.insert(**user2)
        self.assertTrue(user_id is not None)
        user2["id"] = user_id
        users.append(user2)

        user3 = Storage(first_name="TestLTPR3",
                       last_name="User",
                       email="testltpr3@example.com",
                       password="XYZ")
        user_id = utable.insert(**user3)
        self.assertTrue(user_id is not None)
        user3["id"] = user_id
        users.append(user3)

        person_ids = auth.s3_link_to_person(users, self.org_id)
        self.assertTrue(isinstance(person_ids, list))
        self.assertEqual(len(person_ids), 3)

        auth.s3_impersonate("testltpr2@example.com")
        pe_id = auth.user.pe_id
        ptable = s3db.pr_person
        query = (ptable.pe_id == pe_id)
        person2 = current.db(query).select().first()
        self.assertNotEqual(person2, None)
        self.assertTrue(person2.id in person_ids)

    def tearDown(self):

        current.auth.s3_impersonate(None)
        current.db.rollback()

# =============================================================================
class RoleTests(unittest.TestCase):
    """
        Example how one could easily prepare a complex resource
        in order to test permissions
    """

    def setUp(self):

        auth = current.auth

        xmlstr = """
<s3xml>
   <resource name="org_organisation" uuid="TESTORGA">
     <data field="name">Org-A</data>
     <resource name="org_office" uuid="TESTOFFICEA">
       <data field="name">Office-A</data>
       <resource name="inv_inv_item" uuid="TESTITEMA">
         <reference field="item_id" resource="supply_item" uuid="TESTSUPPLYITEMA"/>
         <data field="quantity">10</data>
       </resource>
     </resource>
   </resource>
   <resource name="supply_item" uuid="TESTSUPPLYITEMA">
     <data field="name">Item-A</data>
   </resource>
</s3xml>"""
        from lxml import etree
        self.xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        auth.override = True
        resource = current.s3db.resource("org_organisation")
        success = resource.import_xml(self.xmltree)

    def testImport(self):

        s3db = current.s3db

        resource = s3db.resource("org_organisation", uid="TESTORGA")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Org-A")

        resource = current.s3db.resource("org_office", uid="TESTOFFICEA")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Office-A")

        resource = s3db.resource("inv_inv_item", uid="TESTITEMA")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.quantity, 10)

        resource = s3db.resource("supply_item", uid="TESTSUPPLYITEMA")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Item-A")

    def tearDown(self):
        current.db.rollback()

# =============================================================================
class AuthTests(unittest.TestCase):
    """ S3Auth Tests """

    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    # Role Management
    #
    def testSystemRoles(self):
        """ Test if system roles are present """

        sr = current.auth.get_system_roles()
        self.assertTrue("ADMIN" in sr)
        self.assertTrue(sr.ADMIN is not None)

    # -------------------------------------------------------------------------
    # Authentication
    #
    def testGetUserIDByEmail(self):

        user_id = current.auth.s3_get_user_id("normaluser@example.com")
        self.assertTrue(user_id is not None)

    def testImpersonate(self):
        """ Test s3_impersonate function """

        auth = current.auth
        session = current.session

        sr = auth.get_system_roles()
        ADMIN = sr.ADMIN
        ANONYMOUS = sr.ANONYMOUS

        # Test-login as system administrator
        auth.s3_impersonate("admin@example.com")
        self.assertTrue(auth.s3_logged_in())
        self.assertTrue(auth.user is not None)
        self.assertTrue(ADMIN in session.s3.roles)
        self.assertTrue(ANONYMOUS in session.s3.roles)
        self.assertTrue(ADMIN in auth.user.realms)

        # Test with nonexistent user
        self.assertRaises(ValueError, auth.s3_impersonate, "NonExistentUser")
        # => should still be logged in as ADMIN
        self.assertTrue(auth.s3_logged_in())
        self.assertTrue(ADMIN in session.s3.roles)

        # Test with None => should logout and reset the roles
        auth.s3_impersonate(None)
        self.assertFalse(auth.s3_logged_in())
        self.assertTrue(session.s3.roles == [] or
                        ANONYMOUS in session.s3.roles)

        # Logout
        auth.s3_impersonate(None)

    def testSetRolesPolicy3(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 3
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        realms = auth.user.realms.keys()
        self.assertTrue(2 in realms)
        self.assertTrue(3 in realms)
        self.assertEqual(len(realms), 2)
        for r in auth.user.realms:
            self.assertEqual(auth.user.realms[r], None)
        auth.s3_impersonate(None)

    def testSetRolesPolicy4(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 4
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        realms = auth.user.realms.keys()
        self.assertTrue(2 in realms)
        self.assertTrue(3 in realms)
        self.assertEqual(len(realms), 2)
        for r in auth.user.realms:
            self.assertEqual(auth.user.realms[r], None)
        auth.s3_impersonate(None)

    def testSetRolesPolicy5(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 5
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        realms = auth.user.realms.keys()
        self.assertTrue(2 in realms)
        self.assertTrue(3 in realms)
        self.assertEqual(len(realms), 2)
        for r in auth.user.realms:
            self.assertEqual(auth.user.realms[r], None)
        auth.s3_impersonate(None)

    def testSetRolesPolicy6(self):

        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        try:
            org = s3db.pr_get_pe_id("org_organisation", 1)
            role = auth.s3_create_role("Example Role", uid="TESTROLE")
            user_id = auth.s3_get_user_id("normaluser@example.com")
            auth.s3_assign_role(user_id, role, for_pe=org)

            deployment_settings.security.policy = 6
            from s3.s3aaa import S3Permission
            auth.permission = S3Permission(auth)
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms.keys()
            self.assertTrue(2 in realms)
            self.assertTrue(3 in realms)
            self.assertTrue(role in realms)
            self.assertEqual(len(realms), 3)
            for r in auth.user.realms:
                if r == role:
                    self.assertEqual(auth.user.realms[r], [org])
                else:
                    self.assertEqual(auth.user.realms[r], None)
            auth.s3_impersonate(None)
        finally:
            auth.s3_delete_role("TESTROLE")

    def testSetRolesPolicy7(self):

        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        try:
            org1 = s3db.pr_get_pe_id("org_organisation", 1)
            org2 = s3db.pr_get_pe_id("org_organisation", 2)
            s3db.pr_add_affiliation(org1, org2, role="TestRole")

            role = auth.s3_create_role("Example Role", uid="TESTROLE")
            user_id = auth.s3_get_user_id("normaluser@example.com")
            auth.s3_assign_role(user_id, role, for_pe=org1)

            deployment_settings.security.policy = 7
            from s3.s3aaa import S3Permission
            auth.permission = S3Permission(auth)
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms.keys()
            self.assertTrue(2 in realms)
            self.assertTrue(3 in realms)
            self.assertTrue(role in realms)
            self.assertEqual(len(realms), 3)
            for r in auth.user.realms:
                if r == role:
                    self.assertTrue(org1 in auth.user.realms[r])
                    self.assertTrue(org2 in auth.user.realms[r])
                else:
                    self.assertEqual(auth.user.realms[r], None)
            auth.s3_impersonate(None)
        finally:
            auth.s3_delete_role("TESTROLE")
            current.db.rollback()

    def testSetRolesPolicy8(self):
        """ Test s3_set_roles for entity hierarchy plus delegations (policy8) """

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        try:
            # Have two orgs, set org2 as OU descendant of org1
            org1 = s3db.pr_get_pe_id("org_organisation", 1)
            org2 = s3db.pr_get_pe_id("org_organisation", 2)
            s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")

            # Set org3 as non-OU (role_type=9) partner of org1
            org3 = s3db.pr_get_pe_id("org_organisation", 3)

            # Add the user as OU descendant of org3
            user_id = auth.s3_get_user_id("normaluser@example.com")
            user_pe = auth.s3_user_pe_id(user_id)
            self.assertNotEqual(user_pe, None)
            s3db.pr_add_affiliation(org3, user_pe, role="TestStaff")

            # Create a Test auth_group and delegate it to the TestPartners
            role = auth.s3_create_role("Test Group", uid="TESTGROUP")
            auth.s3_assign_role(user_id, role)

            # We use delegations (policy 8)
            deployment_settings.security.policy = 8
            from s3.s3aaa import S3Permission
            auth.permission = S3Permission(auth)

            # Impersonate as normal user
            auth.s3_impersonate("normaluser@example.com")

            auth.s3_delegate_role("TESTGROUP", org1, receiver=org3)

            # Check the realms
            realms = auth.user.realms.keys()
            self.assertTrue(2 in realms)
            self.assertTrue(3 in realms)
            self.assertTrue(role in realms)
            self.assertEqual(len(realms), 3)

            for r in auth.user.realms:
                if r == role:
                    self.assertTrue(org3 in auth.user.realms[r])
                else:
                    self.assertEqual(auth.user.realms[r], None)

            # Check the delegations
            delegations = auth.user.delegations.keys()
            self.assertTrue(role in delegations)
            self.assertEqual(len(delegations), 1)

            realms = auth.user.delegations[role]
            self.assertTrue(org3 in realms)
            self.assertEqual(len(realms), 1)
            self.assertTrue(org1 in realms[org3])
            self.assertTrue(org2 in realms[org3])

            auth.s3_remove_delegation("TESTGROUP", org1, receiver=org3)

            # Check the delegations
            delegations = auth.user.delegations.keys()
            self.assertFalse(role in delegations)
            self.assertEqual(len(delegations), 0)

            # Logout
            auth.s3_impersonate(None)

        finally:
            s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            auth.s3_delete_role("TESTGROUP")
            current.db.rollback()

    #def testPerformance(self):

        #MAX_RUNTIME = 18 # Maximum acceptable runtime per request in milliseconds
        ##MAX_RUNTIME = 3 # Maximum acceptable runtime per request in milliseconds (up to policy 7)

        #deployment_settings.security.policy = 8
        #from s3.s3aaa import S3Permission
        #auth.permission = S3Permission(auth)

        #try:
            #org1 = s3db.pr_get_pe_id("org_organisation", 1)
            #org2 = s3db.pr_get_pe_id("org_organisation", 2)
            #s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")
            #org3 = s3db.pr_get_pe_id("org_organisation", 3)
            #partners = s3db.pr_add_affiliation(org1, org3, role="TestPartners", role_type=9)
            #user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            #s3db.pr_add_affiliation(org3, user, role="TestStaff")
            #role = auth.s3_create_role("Test Group", uid="TESTGROUP")
            #dtable = s3db.pr_delegation
            #record = dtable.insert(role_id=partners, group_id=role)

            #def setRoles():
                #auth.s3_impersonate("normaluser@example.com")

            #import timeit
            #runtime = timeit.Timer(setRoles).timeit(number=100)
            #if runtime > (MAX_RUNTIME / 10.0):
                #raise AssertionError("s3_impersonate: maximum acceptable run time exceeded (%sms > %sms)" % (int(runtime * 10), MAX_RUNTIME))
            ## Logout
            #auth.s3_impersonate(None)

        #finally:
            #s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            #s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            #s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            #auth.s3_delete_role("TESTGROUP")
            #current.db.rollback()

    def testAssignRole(self):

        db = current.db
        auth = current.auth

        UUID1 = "TESTAUTOCREATEDROLE1"
        UUID2 = "TESTAUTOCREATEDROLE2"

        uuids = [UUID1, UUID2]

        table = auth.settings.table_group
        query1 = (table.deleted != True) & (table.uuid == UUID1)
        query2 = (table.deleted != True) & (table.uuid == UUID2)

        auth.s3_impersonate("admin@example.com")
        user_id = auth.user.id

        row = db(query1).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)

        auth.s3_assign_role(user_id, uuids, for_pe=0)
        row = db(query1).select(limitby=(0, 1)).first()
        self.assertNotEqual(row, None)
        self.assertTrue(row.id > 0)
        self.assertTrue(row.role == UUID1)
        self.assertTrue(row.uuid == UUID1)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertNotEqual(row, None)
        self.assertTrue(row.id > 0)
        self.assertTrue(row.role == UUID2)
        self.assertTrue(row.uuid == UUID2)

        auth.s3_delete_role(UUID1)
        row = db(query1).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertNotEqual(row, None)
        self.assertTrue(row.id > 0)
        self.assertTrue(row.role == UUID2)
        self.assertTrue(row.uuid == UUID2)

        auth.s3_delete_role(UUID2)
        row = db(query1).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)

    def testGetRoles(self):

        auth = current.auth
        UUID = "TESTAUTOCREATEDROLE"
        role_id = auth.s3_create_role(UUID, uid=UUID)

        try:
            auth.s3_impersonate("normaluser@example.com")
            user_id = auth.user.id

            auth.s3_assign_role(user_id, role_id, for_pe=None)
            roles = auth.s3_get_roles(user_id)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            self.assertFalse(role_id in roles)
            auth.s3_retract_role(user_id, role_id, for_pe=None)

            auth.s3_assign_role(user_id, role_id, for_pe=0)
            roles = auth.s3_get_roles(user_id)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            self.assertFalse(role_id in roles)
            auth.s3_retract_role(user_id, role_id, for_pe=0)

            auth.s3_assign_role(user_id, role_id, for_pe=1)
            roles = auth.s3_get_roles(user_id)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            self.assertTrue(role_id in roles)
            auth.s3_retract_role(user_id, role_id, for_pe=1)

        finally:

            auth.s3_delete_role(UUID)
            auth.s3_impersonate(None)

    def tearDown(self):

        current.db.rollback()

    # -------------------------------------------------------------------------
    # Record Ownership
    #
    def testOwnershipRequired(self):

        from s3.s3aaa import S3Permission

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 1
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertFalse(o)

        deployment_settings.security.policy = 2
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertFalse(o)

        deployment_settings.security.policy = 3
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 4
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 5
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 6
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 7
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 8
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 0
        auth.permission = S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

    def testSessionOwnership(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth

        table = s3db.pr_person
        table2 = "dvi_body"
        auth.s3_impersonate(None)
        auth.s3_clear_session_ownership()
        auth.s3_make_session_owner(table, 1)

        # No record ID should always return False
        self.assertFalse(auth.s3_session_owns(table, None))
        # Check for non-owned record
        self.assertFalse(auth.s3_session_owns(table, 2))
        # Check for owned record
        self.assertTrue(auth.s3_session_owns(table, 1))

        # If user is logged-in, session ownership is always False
        auth.s3_impersonate("normaluser@example.com")
        self.assertFalse(auth.s3_session_owns(table, 1))

        auth.s3_impersonate(None)
        auth.s3_make_session_owner(table, 1)
        auth.s3_make_session_owner(table, 2)
        self.assertTrue(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))
        auth.s3_clear_session_ownership(table, 1)
        self.assertFalse(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))

        auth.s3_make_session_owner(table, 1)
        auth.s3_make_session_owner(table, 2)
        auth.s3_make_session_owner(table2, 1)
        auth.s3_make_session_owner(table2, 2)
        self.assertTrue(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))
        self.assertTrue(auth.s3_session_owns(table2, 1))
        self.assertTrue(auth.s3_session_owns(table2, 2))
        auth.s3_clear_session_ownership(table)
        self.assertFalse(auth.s3_session_owns(table, 1))
        self.assertFalse(auth.s3_session_owns(table, 2))
        self.assertTrue(auth.s3_session_owns(table2, 1))
        self.assertTrue(auth.s3_session_owns(table2, 2))

        auth.s3_make_session_owner(table, 1)
        auth.s3_make_session_owner(table, 2)
        auth.s3_make_session_owner(table2, 1)
        auth.s3_make_session_owner(table2, 2)
        self.assertTrue(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))
        self.assertTrue(auth.s3_session_owns(table2, 1))
        self.assertTrue(auth.s3_session_owns(table2, 2))
        auth.s3_clear_session_ownership()
        self.assertFalse(auth.s3_session_owns(table, 1))
        self.assertFalse(auth.s3_session_owns(table, 2))
        self.assertFalse(auth.s3_session_owns(table2, 1))
        self.assertFalse(auth.s3_session_owns(table2, 2))

# =============================================================================
class PermissionTests(unittest.TestCase):
    """ S3Permission Tests """

    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    # Lambdas
    #
    def testRequiredACL(self):

        auth = current.auth
        p = auth.permission
        self.assertEqual(p.required_acl(["read"]), p.READ)
        self.assertEqual(p.required_acl(["create"]), p.CREATE)
        self.assertEqual(p.required_acl(["update"]), p.UPDATE)
        self.assertEqual(p.required_acl(["delete"]), p.DELETE)
        self.assertEqual(p.required_acl(["create", "update"]), p.CREATE | p.UPDATE)
        self.assertEqual(p.required_acl([]), p.NONE)
        self.assertEqual(p.required_acl(["invalid"]), p.NONE)

    def testMostPermissive(self):

        auth = current.auth
        p = auth.permission
        self.assertEqual(p.most_permissive([(p.NONE, p.READ),
                                            (p.READ, p.READ)]),
                                           (p.READ, p.READ))
        self.assertEqual(p.most_permissive([(p.NONE, p.ALL),
                                            (p.CREATE, p.ALL),
                                            (p.READ, p.ALL)]),
                                           (p.READ | p.CREATE, p.ALL))

    def testMostRestrictive(self):

        auth = current.auth
        p = auth.permission
        self.assertEqual(p.most_restrictive([(p.NONE, p.READ),
                                             (p.READ, p.READ)]),
                                            (p.NONE, p.READ))
        self.assertEqual(p.most_restrictive([(p.CREATE, p.ALL),
                                             (p.READ, p.READ)]),
                                            (p.NONE, p.READ))

    # -------------------------------------------------------------------------
    # Record Ownership
    #
    def testOwnershipPublicRecord(self):

        auth = current.auth
        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal owns all public records
            auth.s3_impersonate("normaluser@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Unauthenticated users never own a record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipAdminOwnedRecord(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_user=user_id)

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal does not own this record
            auth.s3_impersonate("normaluser@example.com")
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own this record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipUserOwnedRecord(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            # Change the record owner to admin
            user_id = auth.s3_get_user_id("normaluser@example.com")
            db(table.id == record_id).update(owned_by_user=user_id)

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal owns this record
            auth.s3_impersonate("normaluser@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own a record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipGroupOwnedRecord(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            sr = auth.get_system_roles()
            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_user=user_id,
                                             owned_by_group=sr.AUTHENTICATED)

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal owns this record as member of AUTHENTICATED
            auth.s3_impersonate("normaluser@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own this record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipOrganisationOwnedRecord(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            org = s3db.pr_get_pe_id("org_organisation", 1)
            role = auth.s3_create_role("Example Role", uid="TESTROLE")

            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_user=user_id,
                                             owned_by_group=role,
                                             realm_entity=org)
            auth.s3_clear_session_ownership()

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal user does not own the record
            auth.s3_impersonate("normaluser@example.com")
            user_id = auth.user.id
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless they have the role for this org
            auth.s3_assign_role(user_id, role, for_pe=org)
            self.assertTrue(auth.permission.is_owner(table, record_id))
            auth.s3_retract_role(user_id, role, for_pe=org)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ....or have the role without limitation (any org)
            auth.s3_assign_role(user_id, role, for_pe=0)
            self.assertTrue(auth.permission.is_owner(table, record_id))
            auth.s3_retract_role(user_id, role, for_pe=[])
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own this record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()
            auth.s3_delete_role("TESTROLE")

    def testOwnershipOverride(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            org = s3db.pr_get_pe_id("org_organisation", 1)
            role = auth.s3_create_role("Example Role", uid="TESTROLE")

            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(realm_entity=org,
                                             owned_by_group=role,
                                             owned_by_user=user_id)

            owners_override = (None, None, None)

            # Normal user does not own the record
            auth.s3_impersonate("normaluser@example.com")
            self.assertFalse(auth.permission.is_owner(table, record_id))
            self.assertTrue(auth.permission.is_owner(table, record_id,
                                                     owners=owners_override))
        finally:
            self.remove_test_record()
            auth.s3_delete_role("TESTROLE")

    def testGetOwners(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            user = auth.s3_get_user_id("admin@example.com")
            role = auth.s3_create_role("Example Role", uid="TESTROLE")
            org = s3db.pr_get_pe_id("org_organisation", 1)

            e, r, u = auth.permission.get_owners(table, None)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            e, r, u = auth.permission.get_owners(None, record_id)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            e, r, u = auth.permission.get_owners(None, None)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            e, r, u = auth.permission.get_owners(table, record_id)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            db(table.id == record_id).update(owned_by_user=user,
                                             owned_by_group=role,
                                             realm_entity=org)

            e, r, u = auth.permission.get_owners(table, record_id)
            self.assertEqual(e, org)
            self.assertEqual(r, role)
            self.assertEqual(u, user)

            e, r, u = auth.permission.get_owners(table._tablename, record_id)
            self.assertEqual(e, org)
            self.assertEqual(r, role)
            self.assertEqual(u, user)

        finally:
            self.remove_test_record()
            auth.s3_delete_role("TESTROLE")

    # -------------------------------------------------------------------------
    # ACL Management
    #
    def testUpdateControllerACL(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table = auth.permission.table
        self.assertNotEqual(table, None)

        group_id = auth.s3_create_role("Test Role", uid="TEST")
        acl_id = None

        try:
            self.assertTrue(group_id is not None and group_id != 0)

            c = "pr"
            f = "person"
            uacl = auth.permission.NONE
            oacl = auth.permission.ALL


            acl_id = auth.permission.update_acl(group_id,
                                                c=c, f=f,
                                                uacl=uacl, oacl=oacl)
            self.assertNotEqual(acl_id, None)
            self.assertNotEqual(acl_id, 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertEqual(acl.controller, c)
            self.assertEqual(acl.function, f)
            self.assertEqual(acl.tablename, None)
            self.assertEqual(acl.unrestricted, False)
            self.assertEqual(acl.entity, None)
            self.assertEqual(acl.uacl, uacl)
            self.assertEqual(acl.oacl, oacl)
            self.assertFalse(acl.deleted)

            success = auth.permission.delete_acl(group_id,
                                                 c=c, f=f)
            self.assertTrue(success is not None and success > 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertTrue(acl.deleted)
            self.assertTrue(acl.deleted_fk, '{"group_id": %d}' % group_id)
        finally:
            if acl_id:
                del table[acl_id]
            auth.s3_delete_role(group_id)

    def testUpdateTableACL(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        table = auth.permission.table
        self.assertNotEqual(table, None)

        group_id = auth.s3_create_role("Test Role", uid="TEST")
        acl_id = None

        try:
            self.assertTrue(group_id is not None and group_id != 0)

            c = "pr"
            f = "person"
            t = "pr_person"
            uacl = auth.permission.NONE
            oacl = auth.permission.ALL


            acl_id = auth.permission.update_acl(group_id,
                                                c=c, f=f, t=t,
                                                uacl=uacl, oacl=oacl)
            self.assertNotEqual(acl_id, None)
            self.assertNotEqual(acl_id, 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertEqual(acl.controller, None)
            self.assertEqual(acl.function, None)
            self.assertEqual(acl.tablename, t)
            self.assertEqual(acl.unrestricted, False)
            self.assertEqual(acl.entity, None)
            self.assertEqual(acl.uacl, uacl)
            self.assertEqual(acl.oacl, oacl)
            self.assertFalse(acl.deleted)

            success = auth.permission.delete_acl(group_id,
                                                 c=c, f=f, t=t)
            self.assertTrue(success is not None and success > 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertTrue(acl.deleted)
            self.assertTrue(acl.deleted_fk, '{"group_id": %d}' % group_id)
        finally:
            if acl_id:
                del table[acl_id]
            auth.s3_delete_role(group_id)

    def testApplicableACLsPolicy8(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        try:
            # Have two orgs, set org2 as OU descendant of org1
            org1 = s3db.pr_get_pe_id("org_organisation", 1)
            org2 = s3db.pr_get_pe_id("org_organisation", 2)
            s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")

            # Set org3 as non-OU (role_type=9) partner of org1
            org3 = s3db.pr_get_pe_id("org_organisation", 3)
            partners = s3db.pr_add_affiliation(org1, org3, role="TestPartners", role_type=9)
            self.assertNotEqual(partners, None)

            # Add the user as OU descendant of org3
            user_id = auth.s3_get_user_id("normaluser@example.com")
            user_pe = auth.s3_user_pe_id(user_id)
            self.assertNotEqual(user_pe, None)
            s3db.pr_add_affiliation(org3, user_pe, role="TestStaff")

            # Create a TESTGROUP and assign a table ACL
            acl = auth.permission
            role = auth.s3_create_role("Test Group", None,
                                       dict(c="org", f="office", uacl=acl.ALL, oacl=acl.ALL),
                                       dict(t="org_office", uacl=acl.READ, oacl=acl.ALL),
                                       uid="TESTGROUP")

            auth.s3_assign_role(user_id, role)

            # We use delegations (policy 8)
            deployment_settings.security.policy = 8
            from s3.s3aaa import S3Permission
            auth.permission = S3Permission(auth)

            # Impersonate as normal user
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms
            delegations = auth.user.delegations

            # Check permissions
            acls = auth.permission.applicable_acls(acl.DELETE,
                                                   realms,
                                                   delegations,
                                                   c="org",
                                                   f="office",
                                                   t="org_office",
                                                   entity=org2)
            self.assertTrue(isinstance(acls, Storage))
            self.assertEqual(acls, Storage())

            # Delegate TESTGROUP to the TestPartners
            auth.s3_delegate_role(role, org1, role="TestPartners")

            # Update realms and delegations
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms
            delegations = auth.user.delegations

            # Check permissions again
            acls = auth.permission.applicable_acls(acl.DELETE,
                                                   realms,
                                                   delegations,
                                                   c="org",
                                                   f="office",
                                                   t="org_office",
                                                   entity=org2)

            self.assertTrue(isinstance(acls, Storage))
            self.assertTrue(org2 in acls)
            self.assertEqual(acls[org2], (acl.READ, acl.ALL))

        finally:
            s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            auth.s3_delete_role("TESTGROUP")
            current.db.rollback()

    # -------------------------------------------------------------------------
    # Helpers
    #
    def create_test_record(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        # Create a record
        auth.s3_impersonate(None)
        table = s3db.org_office
        table.owned_by_user.default=None

        auth.override = True
        record_id = table.insert(name="Ownership Test Office")
        auth.override = False

        self.table = table
        self.record_id = record_id
        return table, record_id

    def remove_test_record(self):
        db = current.db
        db(self.table.id == self.record_id).delete()
        #db.commit()
        return

# =============================================================================
class HasPermissionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3db.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3db.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3db.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org1)
        s3db.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org2)
        s3db.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org3)
        s3db.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)
        auth.override = False

    def testPolicy1(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 1
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("update", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("update", table="dvi_body")
        self.assertTrue(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy3(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 3
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        permitted = auth.s3_has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("create", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted) # Function ACL not applicable in policy 3
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy4(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 4
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("create", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy5(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 5
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        accessible_url = auth.permission.accessible_url

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)
        url = accessible_url(c="dvi", f="body")
        self.assertEqual(url, False)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)
        url = accessible_url(c="dvi", f="body")
        self.assertEqual(url, False)

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        url = accessible_url(c="dvi", f="body")
        self.assertNotEqual(url, False)
        permitted = has_permission("create", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted) # Page ACL blocks Table ACL

        # Toggle page ACL
        acl = auth.permission
        auth.permission.update_acl("TESTDVIREADER", c="dvi", f="body",
                                   uacl=acl.READ|acl.CREATE|acl.UPDATE,
                                   oacl=acl.READ|acl.CREATE|acl.UPDATE)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        auth.permission.update_acl("TESTDVIREADER", c="dvi", f="body",
                                   uacl=acl.READ|acl.CREATE,
                                   oacl=acl.READ|acl.CREATE|acl.UPDATE)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)

        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy6(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 6
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIEDITOR with universal realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=0)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])

        # Test with TESTDVIEDITOR with limited realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Extend realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org2)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted)

        # Retract dvi_editor role
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy7(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 7
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIEDITOR with limited realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")

        # Reload realms and test again
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted) # Should now have access

        # Make org1 a sub-entity of org2
        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        s3db.pr_add_affiliation(self.org2, self.org1, role="TestOrgUnit")

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted) # Should no longer have access

        # Switch realm
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org2)

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted) # Should have access again

        # Remove org1 from realm
        s3db.pr_remove_affiliation(self.org2, self.org1, role="TestOrgUnit")

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted) # Should have access again

        # Retract dvi_editor role
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy8(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 8
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))

        try:

            has_permission = auth.s3_has_permission

            # Check anonymous
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
            self.assertFalse(permitted)

            # Check authenticated
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
            self.assertFalse(permitted)

            # Add the user as OU descendant of org3 and assign dvi_reader
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # User should not be able to read record1 or record2, but record3
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertFalse(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            # Make org3 and OU of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Delegate dvi_reader from org1 to org2
            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # User should be able to read record2, but not record2
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertTrue(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            auth.s3_remove_delegation(self.dvi_reader, self.org1, receiver=self.org2)

        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)
            current.db.rollback()

            # Logout
            auth.s3_impersonate(None)

    #def testPerformance(self):

        #MAX_RUNTIME = 6 # Maximum acceptable runtime per request in milliseconds

        #deployment_settings.security.policy = 8
        #from s3.s3aaa import S3Permission
        #auth.permission = S3Permission(auth)

        #auth.s3_impersonate("normaluser@example.com")
        #has_permission = auth.s3_has_permission
        #auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        #def hasPermission():
            #permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        #import timeit
        #runtime = timeit.Timer(hasPermission).timeit(number=100)
        #if runtime > (MAX_RUNTIME / 10.0):
            #raise AssertionError("has_permission: maximum acceptable run time exceeded (%sms > %sms)" % (int(runtime * 10), MAX_RUNTIME))
        #auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])

    def tearDown(self):
        self.role = None
        current.db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth = current.auth
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")

# =============================================================================
class AccessibleQueryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        auth = current.auth
        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE|acl.DELETE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3db.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3db.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3db.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org1)
        s3db.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org2)
        s3db.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org3)
        s3db.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)
        deployment_settings.auth.record_approval = False

    def testPolicy3(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 3
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy4(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 4
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy5(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 5
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy6(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 6
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.realm_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy7(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 7
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.realm_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        qstr = ("(((dvi_body.realm_entity IN (%s,%s)) OR "
                "(dvi_body.realm_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.realm_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        qstr = ("(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.realm_entity IS NULL))) OR "
                "(((dvi_body.owned_by_group = %s) AND "
                "(dvi_body.realm_entity IN (%s,%s))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (auth.user.id, self.dvi_reader, self.org1, self.org2) or
                        str(query) == qstr % (auth.user.id, self.dvi_reader, self.org2, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        qstr = ("(((dvi_body.realm_entity IN (%s,%s)) OR "
                "(dvi_body.realm_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.realm_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy8(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 8
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        record = None
        try:

            # Add the user as OU descendant of org3 and assign dvi_editor
            user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # User should only be able to access records of org3
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))

            # Make org3 and OU of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # User should now be able to read records of org1 and org3, but update only org3
            query = accessible_query("read", table, c="dvi", f="body")
            qstr = ("(((dvi_body.realm_entity IN (%s,%s)) OR "
                    "(dvi_body.realm_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.realm_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertTrue(str(query) == qstr % (self.org1, self.org3, auth.user.id) or
                            str(query) == qstr % (self.org3, self.org1, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            qstr = ("(((dvi_body.realm_entity = %s) OR "
                    "(dvi_body.realm_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.realm_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertEqual(str(query), qstr % (self.org3, auth.user.id))

            # Remove the affiliation with org2
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # Check queries again
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)

    #def testPerformance(self):

        #MAX_RUNTIME = 5 # Maximum acceptable runtime per request in milliseconds

        #deployment_settings.security.policy = 8
        #from s3.s3aaa import S3Permission
        #auth.permission = S3Permission(auth)

        #auth.s3_impersonate("normaluser@example.com")
        #accessible_query = auth.s3_accessible_query
        #table = s3db.dvi_body

        #auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        #def accessibleQuery():
            #query = accessible_query("update", table, c="dvi", f="body")
        #import timeit
        #runtime = timeit.Timer(accessibleQuery).timeit(number=100)
        #if runtime > (MAX_RUNTIME / 10.0):
            #raise AssertionError("accessible_query: maximum acceptable run time exceeded (%sms > %sms)" % (int(runtime * 10), MAX_RUNTIME))
        #auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])

    def tearDown(self):
        self.role = None
        current.db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")

# =============================================================================
class RecordApprovalTests(unittest.TestCase):

    def setUp(self):

        auth = current.auth
        sr = auth.get_system_roles()
        auth.permission.update_acl(sr.AUTHENTICATED,
                                   c="org",
                                   uacl=auth.permission.READ,
                                   oacl=auth.permission.READ|auth.permission.UPDATE)

        auth.permission.update_acl(sr.AUTHENTICATED,
                                   t="org_organisation",
                                   uacl=auth.permission.READ|auth.permission.CREATE,
                                   oacl=auth.permission.READ|auth.permission.UPDATE)

        current.deployment_settings.security.policy = 5
        auth.override = False
        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testRecordApprovedBy(self):
        """ Test whether a new record is unapproved by default """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        try:
            # Set record approval on
            settings.auth.record_approval = True

            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            self.assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Check record
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)

        finally:
            db.rollback()
            settings.auth.record_approval = False
            settings.auth.record_approver_role = None
            current.session.approver_role = None
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testRequiresApproval(self):
        """ Test requires_approval settings """

        s3db = current.s3db
        settings = current.deployment_settings

        approval = settings.get_auth_record_approval()
        tables = settings.get_auth_record_approval_required_for()

        org_approval = s3db.get_config("org_organisation", "requires_approval")

        approval_required = current.auth.permission.requires_approval

        try:

            # Approval globally turned off
            settings.auth.record_approval = False
            settings.auth.record_approval_required_for = []
            s3db.configure("org_organisation", requires_approval=True)
            self.assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to no tables and table=off
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = []
            s3db.configure("org_organisation", requires_approval=False)
            self.assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to no tables yet table=on
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = []
            s3db.configure("org_organisation", requires_approval=True)
            self.assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to any tables and table=on
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = None
            s3db.configure("org_organisation", requires_approval=True)
            self.assertTrue(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to different tables and table=on
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = ["project_project"]
            s3db.configure("org_organisation", requires_approval=True)
            self.assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, set to this table and table=off
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = ["org_organisation"]
            s3db.configure("org_organisation", requires_approval=False)
            self.assertTrue(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, set to any table and table=off
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = None
            s3db.configure("org_organisation", requires_approval=False)
            self.assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, set to any table and no table config
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = None
            s3db.clear_config("org_organisation", "requires_approval")
            self.assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

        finally:
            settings.auth.record_approval = approval
            settings.auth.record_approver_role = None
            current.session.approver_role = None
            settings.auth.record_approval_required_for = tables
            if org_approval is not None:
                s3db.configure("org_organisation",
                               requires_approval = org_approval)
            current.auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testRecordApprovalWithComponents(self):
        """ Test record approval including components """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        # Set record approval on
        settings.auth.record_approval = True

        self.approved_org = None
        def org_onapprove_test(record):
            self.approved_org = record.id
        org_onapprove = s3db.get_config("org_organisation", "onapprove")
        otable_requires_approval = s3db.get_config("org_organisation", "requires_approval", False)
        s3db.configure("org_organisation",
                       onapprove=org_onapprove_test,
                       requires_approval=True)

        self.approved_office = None
        def office_onapprove_test(record):
            self.approved_office = record.id
        office_onapprove = s3db.get_config("org_office", "onapprove")
        ftable_requires_approval = s3db.get_config("org_office", "requires_approval", False)
        s3db.configure("org_office",
                       onapprove=office_onapprove_test,
                       requires_approval=True)

        try:
            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            self.assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Create test component
            ftable = s3db.org_office
            office = Storage(name="Test Approval Office",
                             organisation_id=org_id)
            office_id = ftable.insert(**office)
            self.assertTrue(office_id > 0)
            office.update(id=office_id)
            s3db.update_super(ftable, office)

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)

            approved = auth.permission.approved
            unapproved = auth.permission.unapproved

            # Check approved/unapproved
            self.assertFalse(approved(otable, org_id))
            self.assertTrue(unapproved(otable, org_id))
            self.assertFalse(approved(ftable, office_id))
            self.assertTrue(unapproved(ftable, office_id))

            # Approve
            resource = s3db.resource("org_organisation", id=org_id)
            self.assertTrue(resource.approve(components=["office"]))

            # Check record
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, auth.user.id)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, auth.user.id)

            # Check approved/unapproved
            self.assertTrue(approved(otable, org_id))
            self.assertFalse(unapproved(otable, org_id))
            self.assertTrue(approved(ftable, office_id))
            self.assertFalse(unapproved(ftable, office_id))

            # Check hooks
            self.assertEqual(self.approved_org, org_id)
            self.assertEqual(self.approved_office, office_id)

        finally:
            current.db.rollback()
            current.session.approver_role = None
            settings.auth.record_approval = False
            settings.auth.record_approver_role = None
            auth.s3_impersonate(None)

            s3db.configure("org_organisation",
                           onapprove=org_onapprove,
                           requires_approval=otable_requires_approval)
            s3db.configure("org_office",
                           onapprove=office_onapprove,
                           requires_approval=ftable_requires_approval)

    # -------------------------------------------------------------------------
    def testRecordApprovalWithoutComponents(self):
        """ Test record approval without components"""

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        # Set record approval on
        settings.auth.record_approval = True
        otable = s3db.org_organisation
        otable_requires_approval = s3db.get_config(otable, "requires_approval", False)
        s3db.configure(otable, requires_approval=True)
        ftable = s3db.org_office
        ftable_requires_approval = s3db.get_config(ftable, "requires_approval", False)
        s3db.configure(ftable, requires_approval=True)

        try:
            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            self.assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Create test component
            ftable = s3db.org_office
            office = Storage(name="Test Approval Office",
                             organisation_id=org_id)
            office_id = ftable.insert(**office)
            self.assertTrue(office_id > 0)
            office.update(id=office_id)
            s3db.update_super(ftable, office)

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)

            approved = auth.permission.approved
            unapproved = auth.permission.unapproved

            # Check approved/unapproved
            self.assertFalse(approved(otable, org_id))
            self.assertTrue(unapproved(otable, org_id))
            self.assertFalse(approved(ftable, office_id))
            self.assertTrue(unapproved(ftable, office_id))

            # Approve
            resource = s3db.resource("org_organisation", id=org_id)
            self.assertTrue(resource.approve(components=None))

            # Check record
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, auth.user.id)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)

            # Check approved/unapproved
            self.assertTrue(approved(otable, org_id))
            self.assertFalse(unapproved(otable, org_id))
            self.assertFalse(approved(ftable, office_id))
            self.assertTrue(unapproved(ftable, office_id))

        finally:
            current.db.rollback()
            settings.auth.record_approval = False
            settings.auth.record_approver_role = None
            current.session.approver_role = None
            s3db.configure("org_organisation",
                           requires_approval=otable_requires_approval)
            s3db.configure("org_office",
                           requires_approval=ftable_requires_approval)
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testRecordReject(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        self.rejected_org = None
        def org_onreject_test(record):
            self.rejected_org = record.id
        org_onreject = s3db.get_config("org_organisation", "onreject")
        s3db.configure("org_organisation", onreject=org_onreject_test)

        self.rejected_office = None
        def office_onreject_test(record):
            self.rejected_office = record.id
        office_onreject = s3db.get_config("org_office", "onreject")
        s3db.configure("org_office", onreject=office_onreject_test)

        # Set record approval on
        settings.auth.record_approval = True
        otable = s3db.org_organisation
        otable_requires_approval = s3db.get_config(otable, "requires_approval", False)
        ftable = s3db.org_office
        ftable_requires_approval = s3db.get_config(ftable, "requires_approval", False)

        try:

            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            org = Storage(name="Test Reject Organisation")
            org_id = otable.insert(**org)
            self.assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Create test component
            office = Storage(name="Test Reject Office",
                             organisation_id=org_id)
            office_id = ftable.insert(**office)
            self.assertTrue(office_id > 0)
            office.update(id=office_id)
            s3db.update_super(ftable, office)

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)

            # Activate approval for these tables
            s3db.configure(otable, requires_approval=True)
            s3db.configure(ftable, requires_approval=True)

            approved = auth.permission.approved
            unapproved = auth.permission.unapproved

            # Check approved/unapproved
            self.assertFalse(approved(otable, org_id))
            self.assertTrue(unapproved(otable, org_id))
            self.assertFalse(approved(ftable, office_id))
            self.assertTrue(unapproved(ftable, office_id))

            # Reject
            resource = s3db.resource("org_organisation", id=org_id)
            self.assertTrue(resource.reject())

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)
            self.assertTrue(row.deleted)

            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)
            self.assertTrue(row.deleted)

            # Check hooks
            self.assertEqual(self.rejected_org, org_id)
            self.assertEqual(self.rejected_office, office_id)

        finally:
            current.db.rollback()
            settings.auth.record_approval = False
            settings.auth.record_approver_role = None
            current.session.approver_role = None
            auth.s3_impersonate(None)

            s3db.configure("org_organisation",
                           onreject=org_onreject,
                           requires_approval=otable_requires_approval)
            s3db.configure("org_office",
                           onreject=office_onreject,
                           requires_approval=ftable_requires_approval)

    # -------------------------------------------------------------------------
    def testHasPermissionWithRecordApproval(self):
        """ Test has_permission with record approval """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        AUTHENTICATED = auth.get_system_roles().AUTHENTICATED

        otable = s3db.org_organisation
        otable_requires_approval = s3db.get_config(otable, "requires_approval", False)

        try:
            # Set record approval on
            settings.auth.record_approval = True

            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            self.assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            s3db.configure(otable, requires_approval=True)

            has_permission = auth.s3_has_permission

            # Normal user must not see unapproved record
            settings.auth.record_approver_role = "ADMIN"
            session = current.session
            session.approver_role = None
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)

            # Normal user can not review/approve/reject the record
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)

            # Normal user can see unapproved record if they have the approver role
            settings.auth.record_approver_role = "AUTHENTICATED"
            session = current.session
            session.approver_role = None
            auth.s3_impersonate("normaluser@example.com")
            self.assertEqual(session.approver_role, AUTHENTICATED)
            self.assertTrue(session.approver_role in auth.user.realms)
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            self.assertTrue(permitted)

            # Normal user can review/approve/reject if they have the approver role
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            self.assertTrue(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            self.assertTrue(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            self.assertTrue(permitted)

            # Approve the record
            resource = s3db.resource(otable, id=org_id, unapproved=True)
            resource.approve()

            # Normal user can not review/approve/reject once the record is approved
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            self.assertFalse(permitted)

            # Normal user can now see the record without having the approver role
            settings.auth.record_approver_role = "ADMIN"
            session = current.session
            session.approver_role = None
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            self.assertTrue(permitted)

            # Admin can always see the record
            auth.s3_impersonate("admin@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            self.assertTrue(permitted)

        finally:
            settings.auth.record_approval = False
            settings.auth.record_approver_role = None
            session.approver_role = None
            s3db.configure("org_organisation",
                           requires_approval=otable_requires_approval)
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testAccessibleQueryWithRecordApproval(self):
        """ Test accessible_query with record approval """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings
        accessible_query = auth.s3_accessible_query
        session = current.session

        table = s3db.pr_person

        otable = s3db.org_organisation

        approval = settings.get_auth_record_approval()
        approval_required = settings.get_auth_record_approval_required_for()

        # Record approval on, but for no tables
        settings.auth.record_approval = True
        settings.auth.record_approval_required_for = []

        try:
            AUTHENTICATED = auth.get_system_roles().AUTHENTICATED

            # Admin can always see all records
            auth.s3_impersonate("admin@example.com")
            query = accessible_query("read", table, c="pr", f="person")
            self.assertEqual(str(query), "(pr_person.id > 0)")

            # User can only see their own records - approved_by not relevant
            auth.s3_impersonate("normaluser@example.com")
            query = accessible_query("read", table, c="pr", f="person")
            self.assertFalse("approved_by" in str(query))

            table = s3db.org_organisation

            # Approval not required by default
            session.approver_role = None
            auth.s3_impersonate("normaluser@example.com")
            query = accessible_query("read", table, c="org", f="organisation")
            self.assertEqual(str(query), "(org_organisation.id > 0)")

            settings.auth.record_approval_required_for = ["org_organisation"]

            # Admin can always see all records
            session.approver_role = None
            auth.s3_impersonate("admin@example.com")
            query = accessible_query("read", table, c="org", f="organisation")
            self.assertEqual(str(query), "(org_organisation.id > 0)")

            # User can only see approved records
            session.approver_role = None
            auth.s3_impersonate("normaluser@example.com")
            query = accessible_query("read", table, c="org", f="organisation")
            self.assertEqual(str(query), "(org_organisation.approved_by IS NOT NULL)")

            # User can see all unapproved records with method approve
            # if they have the approver role
            session.approver_role = None
            settings.auth.record_approver_role = "AUTHENTICATED"
            auth.s3_impersonate("normaluser@example.com")
            self.assertEqual(session.approver_role, AUTHENTICATED)
            self.assertTrue(session.approver_role in auth.user.realms)

            # See only unapproved records in approve
            query = accessible_query("approve", table, c="org", f="organisation")
            self.assertTrue("(org_organisation.approved_by IS NULL)" in str(query))

            # See only approved records in read
            query = accessible_query("read", table, c="org", f="organisation")
            self.assertTrue("(org_organisation.approved_by IS NOT NULL)" in str(query))

            # See all records with both
            query = accessible_query(["read", "approve"], table, c="org", f="organisation")
            self.assertFalse("(org_organisation.approved_by IS NOT NULL)" in str(query))
            self.assertFalse("(org_organisation.approved_by IS NULL)" in str(query))

            # Turn of record approval and check the default query
            settings.auth.record_approval = False
            query = accessible_query("read", table, c="org", f="organisation")
            self.assertEqual(str(query), "(org_organisation.id > 0)")

        finally:
            settings.auth.record_approval = approval
            settings.auth.record_approval_required_for = approval_required
            settings.auth.record_approver_role = None
            session.approver_role = None
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testSuperEntityAccessibleQueryWithRecordApproval(self):
        """ Test accessible_query with record approval for a super entity """

        db = current.db
        auth = current.auth
        s3db = current.s3db

        settings = current.deployment_settings
        accessible_query = auth.s3_accessible_query
        session = current.session

        # Store current settings
        approval = settings.get_auth_record_approval()
        approval_required = settings.get_auth_record_approval_required_for()

        # Record approval on, but for no tables
        settings.auth.record_approval = True
        settings.auth.record_approval_required_for = []

        try:
            table = s3db.doc_source_entity
            tablename = "doc_source_entity"

            AUTHENTICATED = auth.get_system_roles().AUTHENTICATED
            auth.permission.update_acl(AUTHENTICATED,
                                       t=tablename,
                                       uacl=auth.permission.READ,
                                       entity="any")

            auth.permission.update_acl(AUTHENTICATED,
                                       c="doc", f="source_entity",
                                       uacl=auth.permission.READ,
                                       entity="any")

            # Approval required for this table
            settings.auth.record_approval_required_for = [tablename]

            session.approver_role = None
            auth.s3_impersonate("normaluser@example.com")

            # User can only see approved records
            resource = s3db.resource(tablename, unapproved=False)
            query = resource.get_query()
            self.assertTrue("(doc_source_entity.approved_by IS NOT NULL)" in str(query))

            # ...even if we explicitly request them all
            resource = s3db.resource(tablename, unapproved=True)
            query = resource.get_query()
            self.assertTrue("(doc_source_entity.approved_by IS NOT NULL)" in str(query))

            # ...unless the user has the approver role
            session.approver_role = None
            settings.auth.record_approver_role = "AUTHENTICATED"
            auth.s3_impersonate("normaluser@example.com")

            # ...and request all records
            resource = s3db.resource(tablename, unapproved=True)
            query = resource.get_query()
            self.assertFalse("(doc_source_entity.approved_by IS NOT NULL)" in str(query))

        finally:
            # Restore settings
            settings.auth.record_approval = approval
            settings.auth.record_approval_required_for = approval_required
            settings.auth.record_approver_role = None
            session.approver_role = None
            auth.s3_impersonate(None)

    def tearDown(self):

        current.db.rollback()

# =============================================================================
class DelegationTests(unittest.TestCase):


    @classmethod
    def setUpClass(cls):

        auth = current.auth
        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        current.db.commit()

    def setUp(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3db.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3db.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3db.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org1)
        s3db.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org2)
        s3db.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org3)
        s3db.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)

    def testPolicy7(self):

        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 7
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

    def testPolicy8(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 8
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        user = auth.user.pe_id

        try:

            # Add the user as OU descendant of org3 and assign dvi_reader
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # Make org3 an OU descendant of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Delegate the dvi_reader role for org1 to org2
            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Check the delegations
            delegations = auth.user.delegations
            self.assertTrue(self.dvi_reader in delegations)
            self.assertTrue(self.org3 in delegations[self.dvi_reader])
            self.assertTrue(self.org1 in delegations[self.dvi_reader][self.org3])

            auth.s3_remove_delegation(self.dvi_reader, self.org1, receiver=self.org2)

            # Check the delegations
            delegations = auth.user.delegations
            self.assertEqual(delegations.keys(), [])

            # Delegate the dvi_reader role for org1 to org2
            auth.s3_delegate_role([self.dvi_reader, self.dvi_editor], self.org1, receiver=self.org2)

            delegations = auth.s3_get_delegations(self.org1)
            self.assertNotEqual(delegations, None)
            self.assertTrue(isinstance(delegations, Storage))
            self.assertTrue(self.org2 in delegations)
            self.assertTrue(isinstance(delegations[self.org2], list))
            self.assertEqual(len(delegations[self.org2]), 2)
            self.assertTrue(self.dvi_reader in delegations[self.org2])
            self.assertTrue(self.dvi_editor in delegations[self.org2])

            # Check the delegations
            delegations = auth.user.delegations
            self.assertTrue(self.dvi_reader in delegations)
            self.assertTrue(self.dvi_editor in delegations)
            self.assertTrue(self.org3 in delegations[self.dvi_reader])
            self.assertTrue(self.org1 in delegations[self.dvi_reader][self.org3])
            self.assertTrue(self.org3 in delegations[self.dvi_editor])
            self.assertTrue(self.org1 in delegations[self.dvi_editor][self.org3])

            auth.s3_remove_delegation(self.dvi_editor, self.org1, receiver=self.org2)

            delegations = auth.s3_get_delegations(self.org1)
            self.assertNotEqual(delegations, None)
            self.assertTrue(isinstance(delegations, Storage))
            self.assertTrue(self.org2 in delegations)
            self.assertTrue(isinstance(delegations[self.org2], list))
            self.assertEqual(len(delegations[self.org2]), 1)
            self.assertTrue(self.dvi_reader in delegations[self.org2])

            # Check the delegations
            delegations = auth.user.delegations
            self.assertTrue(self.dvi_reader in delegations)
            self.assertFalse(self.dvi_editor in delegations)
            self.assertTrue(self.org3 in delegations[self.dvi_reader])
            self.assertTrue(self.org1 in delegations[self.dvi_reader][self.org3])

            auth.s3_remove_delegation(self.dvi_reader, self.org1, receiver=self.org2)

            delegations = auth.s3_get_delegations(self.org1)
            self.assertNotEqual(delegations, None)
            self.assertTrue(isinstance(delegations, Storage))
            self.assertEqual(delegations.keys(), [])

            # Check the delegations
            delegations = auth.user.delegations
            self.assertEqual(delegations.keys(), [])

        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)
            current.db.rollback()

            # Logout
            auth.s3_impersonate(None)

    def tearDown(self):
        self.role = None
        current.db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth = current.auth
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")

# =============================================================================
class AccessibleQueryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        db = current.db
        auth = current.auth

        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE|acl.DELETE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3db.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3db.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3db.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org1)
        s3db.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org2)
        s3db.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 realm_entity=self.org3)
        s3db.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)
        deployment_settings.auth.record_approval = False

    def testPolicy3(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 3
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy4(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 4
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        keys = auth.user.realms.keys()
        self.assertTrue(self.dvi_reader in keys)
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (%s)))" %
                                     (auth.user.id, ",".join(map(str,keys))))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (%s)))" %
                                     (auth.user.id, ",".join(map(str,keys))))
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy5(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 5
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        keys = auth.user.realms.keys()
        self.assertTrue(self.dvi_reader in keys)
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (%s)))" %
                                     (auth.user.id, ",".join(map(str,keys))))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy6(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 6
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.realm_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy7(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 7
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.realm_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        qstr = ("(((dvi_body.realm_entity IN (%s,%s)) OR "
                "(dvi_body.realm_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.realm_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        qstr = ("(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.realm_entity IS NULL))) OR "
                "(((dvi_body.owned_by_group = %s) AND "
                "(dvi_body.realm_entity IN (%s,%s))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (auth.user.id, self.dvi_reader, self.org1, self.org2) or
                        str(query) == qstr % (auth.user.id, self.dvi_reader, self.org2, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                     "(dvi_body.realm_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.realm_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        qstr = ("(((dvi_body.realm_entity IN (%s,%s)) OR "
                "(dvi_body.realm_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.realm_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy8(self):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        deployment_settings = current.deployment_settings

        deployment_settings.security.policy = 8
        from s3.s3aaa import S3Permission
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        user = auth.user.id
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        record = None
        try:

            # Add the user as OU descendant of org3 and assign dvi_editor
            user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # User should only be able to access records of org3
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))

            # Make org3 and OU of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # User should now be able to read records of org1 and org3, but update only org3
            query = accessible_query("read", table, c="dvi", f="body")
            qstr = ("(((dvi_body.realm_entity IN (%s,%s)) OR "
                    "(dvi_body.realm_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.realm_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertTrue(str(query) == qstr % (self.org1, self.org3, auth.user.id) or
                            str(query) == qstr % (self.org3, self.org1, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            qstr = ("(((dvi_body.realm_entity = %s) OR "
                    "(dvi_body.realm_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.realm_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertEqual(str(query), qstr % (self.org3, auth.user.id))

            # Remove the affiliation with org2
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # Check queries again
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.realm_entity = %s) OR "
                                         "(dvi_body.realm_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.realm_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)

    def tearDown(self):
        self.role = None
        current.db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth = current.auth
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")


# =============================================================================
class EntityRoleManagerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):

        auth = current.auth

        # Test-login as system administrator
        auth.s3_impersonate("admin@example.com")

        self.rm = S3EntityRoleManager()

        self.user_id = auth.s3_get_user_id("normaluser@example.com")
        self.org_id = 1

        auth.s3_assign_role(self.user_id, "staff_reader", for_pe=self.org_id)
        auth.s3_assign_role(self.user_id, "project_editor", for_pe=self.org_id)

    def testGetAssignedRoles(self):
        roles = self.rm.get_assigned_roles(entity_id=self.org_id)
        self.assertTrue(self.user_id in roles)
        assigned_roles = roles[self.user_id]
        self.assertEqual(len(assigned_roles), 2)
        self.assertTrue("staff_reader" in assigned_roles)
        self.assertTrue("project_editor" in assigned_roles)

        roles = self.rm.get_assigned_roles(entity_id=self.org_id,
                                           user_id=self.user_id)
        self.assertTrue(self.user_id in roles)
        assigned_roles = roles[self.user_id]
        self.assertEqual(len(assigned_roles), 2)
        self.assertTrue("staff_reader" in assigned_roles)
        self.assertTrue("project_editor" in assigned_roles)

        assigned_roles = self.rm.get_assigned_roles(user_id=self.user_id)
        self.assertTrue(all([r in assigned_roles[self.org_id]
                             for r in ("staff_reader", "project_editor")]))
        self.assertEqual(len(assigned_roles[self.org_id]), 2)

        roles = self.rm.get_assigned_roles(user_id=self.user_id)
        self.assertTrue(self.org_id in roles)
        assigned_roles = roles[self.org_id]
        self.assertEqual(len(assigned_roles), 2)
        self.assertTrue("staff_reader" in assigned_roles)
        self.assertTrue("project_editor" in assigned_roles)

        self.assertRaises(RuntimeError, self.rm.get_assigned_roles)

    def testUpdateRoles(self):
        # test that the before/after works
        before = ("staff_reader", "project_editor")
        after = ("survey_reader",)

        # Give the user a new set of roles
        self.rm.update_roles(self.user_id,
                             self.org_id,
                             before,
                             after)
        assigned_roles = self.rm.get_assigned_roles(user_id=self.user_id)
        self.assertTrue(self.org_id in assigned_roles)
        self.assertTrue(all([r in assigned_roles[self.org_id]
                             for r in after]))
        self.assertEqual(len(assigned_roles[self.org_id]), len(after))

        # Reverse the changes
        self.rm.update_roles(self.user_id,
                             self.org_id,
                             after,
                             before)
        assigned_roles = self.rm.get_assigned_roles(user_id=self.user_id)
        self.assertTrue(self.org_id in assigned_roles)
        self.assertTrue(all([r in assigned_roles[self.org_id]
                             for r in before]))
        self.assertEqual(len(assigned_roles[self.org_id]), len(before))

    def tearDown(self):
        auth = current.auth
        auth.s3_retract_role(self.user_id, "staff_reader", for_pe=self.org_id)
        auth.s3_retract_role(self.user_id, "project_editor", for_pe=self.org_id)
        current.db.rollback()

    @classmethod
    def tearDownClass(cls):
        pass

# =============================================================================
class RealmEntityTests(unittest.TestCase):
    """ Test customization hooks for realm entity """

    def setUp(self):

        db = current.db
        s3db = current.s3db

        # Create a dummy record
        otable = s3db.org_organisation
        org = Storage(name="Ownership Test Organisation")
        org_id = otable.insert(**org)
        org.update(id=org_id)
        s3db.update_super(otable, org)

        self.org_id = org_id

        # Clear the hooks
        tname = "org_organisation"
        settings = current.deployment_settings
        self.ghook = settings.get_auth_realm_entity()
        self.shook = s3db.get_config(tname, "realm_entity")
        settings.auth.realm_entity = None
        s3db.clear_config(tname, "realm_entity")

        self.owned_record = None

    def testTableSpecificRealmEntity(self):
        """ Test table-specific realm_entity hook """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        s3db.configure(tname, realm_entity = self.realm_entity)

        auth.s3_set_record_owner(otable, record, force_update=True)
        self.assertEqual(self.owned_record, (tname, record.id))

    def testGlobalRealmEntity(self):
        """ Test global realm_entity hook """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        auth.s3_set_record_owner(otable, record, force_update=True)
        self.assertEqual(self.owned_record, (tname, record.id))

    def testRealmEntityOverride(self):
        """ Check whether global realm_entity hook overrides any table-specific setting """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        s3db.configure(tname, realm_entity = self.realm_entity)
        settings.auth.realm_entity = self.realm_entity_override

        auth.s3_set_record_owner(otable, record, force_update=True)
        self.assertEqual(self.owned_record, "checked")

    def realm_entity(self, table, row):
        """ Dummy method for hook testing """

        self.owned_record = (table._tablename, row.id)
        return None

    def realm_entity_override(self, table, row):
        """ Dummy method for hook testing """

        self.owned_record = "checked"
        return None

    def tearDown(self):

        s3db = current.s3db
        settings = current.deployment_settings

        # Rollback DB
        current.db.rollback()

        # Restore the hooks
        settings.auth.realm_entity = self.ghook
        if self.shook is not None:
            s3db.configure("org_organisation", realm_entity=self.shook)

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        #RoleTests,
        AuthTests,
        PermissionTests,
        HasPermissionTests,
        AccessibleQueryTests,
        DelegationTests,
        EntityRoleManagerTests,
        RecordApprovalTests,
        RealmEntityTests,
        LinkToPersonTests,
    )

# END ========================================================================
