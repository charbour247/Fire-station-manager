import unittest, tempfile, sqlite3
from pathlib import Path
from store import Store
class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.s=Store(self.temp.name)
        self.id=self.s.create_member('Alex Morgan','alex','a secure password','Administrator')
    def tearDown(self): self.s.db.close(); self.temp.cleanup()
    def test_authentication(self):
        self.assertEqual(self.s.login('ALEX','a secure password')['id'],self.id)
        with self.assertRaises(ValueError): self.s.login('alex','wrong')
        with self.assertRaises(ValueError): self.s.create_member('Alex','alex','another secure password')
        self.assertNotEqual(self.s.rows('SELECT password FROM members')[0]['password'],b'a secure password')
    def test_edit_member_preserves_records_and_password(self):
        member=self.s.create_member('Jordan','jordan','original password')
        self.s.punch(member,'Duty')
        self.s.add_training(member,'SCBA','2026-01-01',2,'Safety')
        self.s.add_shift(member,'Duty','Duty','2026-10-19T08:00','2026-10-19T16:00','Station 1')
        before=self.s.rows('SELECT salt,password FROM members WHERE id=?',(member,))[0]
        self.s.update_member(self.id,member,' Jordan Smith ',' jordan.smith ','Administrator')
        updated=self.s.login('jordan.smith','original password')
        self.assertEqual((updated['id'],updated['name'],updated['role']),(member,'Jordan Smith','Administrator'))
        self.assertEqual((updated['salt'],updated['password']),tuple(before))
        self.assertIsNotNone(self.s.active(member))
        self.assertEqual(self.s.totals(member)['Training'],2)
        self.assertEqual(self.s.rows('SELECT member FROM shifts')[0]['member'],member)
        with self.assertRaises(ValueError): self.s.login('jordan','original password')
    def test_reset_password(self):
        member=self.s.create_member('Jordan','jordan','original password')
        old_salt=self.s.rows('SELECT salt FROM members WHERE id=?',(member,))[0]['salt']
        self.s.update_member(self.id,member,'Jordan','jordan','Member','replacement password')
        self.assertEqual(self.s.login('jordan','replacement password')['id'],member)
        self.assertNotEqual(self.s.rows('SELECT salt FROM members WHERE id=?',(member,))[0]['salt'],old_salt)
        with self.assertRaises(ValueError): self.s.login('jordan','original password')
    def test_non_admin_cannot_edit_or_promote_self(self):
        member=self.s.create_member('Jordan','jordan','original password')
        for actor in (member,999):
            with self.assertRaisesRegex(ValueError,'Only administrators'):
                self.s.update_member(actor,member,'Changed','changed','Administrator')
        self.assertEqual(self.s.member(member)['role'],'Member')
        self.assertEqual(self.s.member(member)['name'],'Jordan')
    def test_last_admin_and_stale_permissions(self):
        with self.assertRaisesRegex(ValueError,'At least one administrator'):
            self.s.update_member(self.id,self.id,'Alex','alex','Member')
        second=self.s.create_member('Chief','chief','another password','Administrator')
        self.s.update_member(second,self.id,'Alex','alex','Member')
        with self.assertRaisesRegex(ValueError,'Only administrators'):
            self.s.update_member(self.id,second,'Chief','chief','Member')
        self.assertEqual(self.s.member(second)['role'],'Administrator')
    def test_invalid_edits_are_atomic(self):
        member=self.s.create_member('Jordan','jordan','original password')
        edits=[('', 'jordan', 'Member', ''),('Jordan','','Member',''),
               ('Jordan','jordan','Unknown',''),('Changed','changed','Administrator','short'),
               ('Changed','ALEX','Administrator','replacement password')]
        for name,username,role,password in edits:
            with self.subTest(username=username,role=role,password=password):
                with self.assertRaises(ValueError): self.s.update_member(self.id,member,name,username,role,password)
                self.assertEqual(self.s.login('jordan','original password')['name'],'Jordan')
                self.assertEqual(self.s.member(member)['role'],'Member')
        with self.assertRaisesRegex(ValueError,'no longer exists'):
            self.s.update_member(self.id,999,'Missing','missing','Member')
    def test_clock_transitions(self):
        self.s.punch(self.id,'Duty')
        other=Store(self.temp.name)
        self.assertIsNotNone(other.active(self.id))
        with self.assertRaises(ValueError): other.punch(self.id,'Meeting')
        other.clock_out(self.id); other.db.close()
        self.assertIsNone(self.s.active(self.id))
        with self.assertRaises(ValueError): self.s.clock_out(self.id)
        self.s.punch(self.id,'Fundraiser'); self.s.clock_out(self.id)
        self.s.punch(self.id,'Meeting'); self.s.clock_out(self.id)
        self.assertEqual(len(self.s.rows('SELECT * FROM punches')),3)
    def test_totals(self):
        with self.s.db:
            for kind in ('Duty','Fundraiser','Meeting'):
                self.s.db.execute('INSERT INTO punches(member,kind,started,ended) VALUES(?,?,?,?)',(self.id,kind,'2026-01-01T08:00:00+00:00','2026-01-01T10:30:00+00:00'))
        self.s.add_training(self.id,'SCBA','2026-01-01',3,'Safety')
        t=self.s.totals(self.id)
        self.assertEqual(t,{'Duty':2.5,'Fundraiser':2.5,'Meeting':2.5,'Training':3.0})
    def test_training(self):
        doc=Path(self.temp.name)/'certificate.txt'; doc.write_text('Example certificate')
        self.s.add_training(self.id,'Certificate','2026-01-01','1.5','Safety',str(doc))
        r=self.s.rows('SELECT * FROM training')[0]
        doc.unlink(); self.assertEqual((self.s.folder/r['document']).read_text(),'Example certificate')
        for h in ('nan','inf','-1','25','abc'):
            with self.assertRaises(ValueError): self.s.add_training(self.id,'Bad','2026-01-01',h,'Safety')
        with self.assertRaises(ValueError): self.s.add_training(self.id,'Bad','2999-01-01',1,'Safety')
    def test_schedule(self):
        self.s.add_shift(self.id,'Night shift','Duty','2026-10-19T20:00','2026-10-20T08:00','Station 1')
        with self.assertRaises(ValueError): self.s.add_shift(self.id,'Overlap','Duty','2026-10-20T07:00','2026-10-20T09:00','Station 1')
        self.s.add_shift(self.id,'Next','Duty','2026-10-20T08:00','2026-10-20T09:00','Station 1')
        with self.assertRaises(ValueError): self.s.add_shift(self.id,'Invalid','Duty','2026-10-20T09:00','2026-10-20T08:00','Station 1')
if __name__=='__main__': unittest.main()
