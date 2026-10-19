import sqlite3
import tempfile
import unittest
from pathlib import Path
from store import Store

class CalendarScheduleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.s=Store(self.temp.name)
        self.admin=self.s.create_member('Chief','chief','administrator password','Administrator')
        self.member=self.s.create_member('Member','member','member password')
        self.other=self.s.create_member('Other','other','member password')
        self.s.add_apparatus(self.admin,'Engine 1')
        self.s.add_apparatus(self.admin,'Ladder 2')
    def tearDown(self):
        self.s.db.close()
        self.temp.cleanup()
    def shift(self,member,start,end,apparatus='Engine 1',shift_id=None):
        return self.s.add_shift(member,'Duty shift','Duty',start,end,'Station 1',apparatus,shift_id)
    def test_existing_database_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            db=sqlite3.connect(Path(folder)/'stationdesk.db')
            db.execute('CREATE TABLE shifts(id INTEGER PRIMARY KEY,member INTEGER,title TEXT,kind TEXT,start TEXT,end TEXT,location TEXT)')
            db.execute("INSERT INTO shifts VALUES(1,1,'Legacy','Duty','2026-10-01T08:00','2026-10-01T16:00','Station 1')")
            db.commit(); db.close()
            migrated=Store(folder)
            self.assertEqual(migrated.rows('SELECT title,apparatus FROM shifts')[0]['title'],'Legacy')
            self.assertEqual(migrated.rows('SELECT apparatus FROM shifts')[0]['apparatus'],'')
            migrated.db.close()
            reopened=Store(folder)
            self.assertEqual(len(reopened.rows('SELECT * FROM shifts')),1)
            reopened.db.close()
    def test_apparatus_catalog_permissions_and_validation(self):
        with self.assertRaises(ValueError): self.s.add_apparatus(self.member,'Rescue 1')
        for name in (' engine 1 ','','Unassigned'):
            with self.assertRaises(ValueError): self.s.add_apparatus(self.admin,name)
        with self.assertRaises(ValueError):
            self.shift(self.member,'2026-10-19T08:00','2026-10-19T16:00','Missing apparatus')
    def test_multiple_personnel_can_crew_apparatus(self):
        self.shift(self.member,'2026-10-19T08:00','2026-10-19T16:00')
        self.shift(self.other,'2026-10-19T08:00','2026-10-19T16:00')
        entries=self.s.schedule_entries(self.admin,'2026-10-19T00:00','2026-10-20T00:00')
        self.assertEqual(len(entries),2)
        self.assertEqual({r['apparatus'] for r in entries},{'Engine 1'})
        self.assertEqual(len(self.s.schedule_entries(self.member,'2026-10-19T00:00','2026-10-20T00:00')),1)
        with self.assertRaises(ValueError): self.s.schedule_entries(999,'2026-10-19T00:00','2026-10-20T00:00')
    def test_overnight_month_boundaries_and_midnight_end(self):
        self.shift(self.member,'2026-10-31T20:00','2026-11-01T08:00')
        self.shift(self.other,'2026-10-31T16:00','2026-11-01T00:00')
        entries=self.s.schedule_entries(self.admin,'2026-11-01T00:00','2026-11-02T00:00')
        self.assertEqual([r['member'] for r in entries],[self.member])
        self.assertEqual(len(self.s.schedule_entries(self.admin,'2026-10-31T00:00','2026-11-01T00:00')),2)
    def test_edit_assignment_retains_id_and_checks_conflicts(self):
        shift_id=self.shift(self.member,'2026-10-19T08:00','2026-10-19T16:00')
        self.shift(self.member,'2026-10-19T08:00','2026-10-19T16:00','Ladder 2',shift_id)
        self.assertEqual(len(self.s.rows('SELECT * FROM shifts')),1)
        self.assertEqual(self.s.rows('SELECT * FROM shifts')[0]['apparatus'],'Ladder 2')
        self.shift(self.member,'2026-10-19T16:00','2026-10-19T20:00')
        with self.assertRaises(ValueError): self.shift(self.member,'2026-10-19T15:00','2026-10-19T18:00','Engine 1',shift_id)
        self.assertEqual(self.s.rows('SELECT apparatus FROM shifts WHERE id=?',(shift_id,))[0]['apparatus'],'Ladder 2')
    def test_remove_assignment_is_admin_only(self):
        shift_id=self.shift(self.member,'2026-10-19T08:00','2026-10-19T16:00')
        with self.assertRaises(ValueError): self.s.remove_shift(self.member,shift_id)
        self.s.remove_shift(self.admin,shift_id)
        self.assertEqual(len(self.s.rows('SELECT * FROM shifts')),0)

if __name__=='__main__': unittest.main()
