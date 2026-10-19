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
