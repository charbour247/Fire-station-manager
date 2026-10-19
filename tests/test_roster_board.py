import tempfile
import unittest
from datetime import date
from store import Store
from scheduler import view_days, covers_day, active_crew

class RosterBoardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.s=Store(self.temp.name)
        self.admin=self.s.create_member('Chief','chief','administrator password','Administrator')
        self.member=self.s.create_member('Member','member','member password')
        for name in ('Engine 1','Ladder 2'): self.s.add_apparatus(self.admin,name)
    def tearDown(self): self.s.db.close(); self.temp.cleanup()
    def series(self,**kwargs):
        args=dict(actor_id=self.admin,member=self.member,title='Duty',kind='Duty',start='2026-10-19T08:00',end='2026-10-20T08:00',location='Station 1',apparatus='Engine 1',platoon='A',position='Driver')
        args.update(kwargs); return self.s.repeat_shifts(**args)
    def test_repeat_and_preserve_crew_details(self):
        ids=self.series(every_days=3,count=4)
        rows=self.s.rows('SELECT * FROM shifts ORDER BY start')
        self.assertEqual(len(ids),4)
        self.assertEqual(rows[-1]['start'],'2026-10-28T08:00')
        self.assertTrue(all(r['platoon']=='A' and r['position']=='Driver' for r in rows))
    def test_repeat_conflict_is_atomic(self):
        self.s.add_shift(self.member,'Conflict','Duty','2026-10-25T08:00','2026-10-25T10:00','Station 1')
        with self.assertRaises(ValueError): self.series(every_days=3,count=4)
        self.assertEqual(len(self.s.rows('SELECT * FROM shifts')),1)
    def test_invalid_repeat_limits_and_overlap(self):
        for every,count in [(0,2),(1,53),(1,0),('abc',3),('1.5',2)]:
            with self.assertRaises(ValueError): self.series(every_days=every,count=count)
        with self.assertRaises(ValueError): self.series(every_days=1,count=2,end='2026-10-21T08:00')
        self.assertEqual(len(self.s.rows('SELECT * FROM shifts')),0)
    def test_move_preserves_duration_and_position(self):
        shift_id=self.series()[0]
        self.s.move_shift(self.admin,shift_id,'2026-10-23','Ladder 2','2026-10-19')
        r=self.s.rows('SELECT * FROM shifts')[0]
        self.assertEqual((r['start'],r['end']),('2026-10-23T08:00','2026-10-24T08:00'))
        self.assertEqual((r['apparatus'],r['position'],r['platoon']),('Ladder 2','Driver','A'))
    def test_move_overnight_from_carryover_day(self):
        shift_id=self.series()[0]
        self.s.move_shift(self.admin,shift_id,'2026-10-22','Ladder 2','2026-10-20')
        self.assertEqual(self.s.rows('SELECT start FROM shifts')[0]['start'],'2026-10-21T08:00')
    def test_move_conflict_rolls_back(self):
        shift_id=self.series()[0]
        self.series(start='2026-10-23T08:00',end='2026-10-24T08:00')
        with self.assertRaises(ValueError): self.s.move_shift(self.admin,shift_id,'2026-10-23','Ladder 2')
        self.assertEqual(self.s.rows('SELECT apparatus FROM shifts WHERE id=?',(shift_id,))[0]['apparatus'],'Engine 1')
    def test_member_cannot_modify_roster_or_targets(self):
        shift_id=self.series()[0]
        with self.assertRaises(ValueError): self.series(actor_id=self.member,start='2026-10-23T08:00',end='2026-10-24T08:00')
        with self.assertRaises(ValueError): self.s.move_shift(self.member,shift_id,'2026-10-23','Ladder 2')
        with self.assertRaises(ValueError): self.s.save_shift(self.member,self.member,'Changed','Duty','2026-10-23T08:00','2026-10-24T08:00','Station 1')
        with self.assertRaises(ValueError): self.s.set_staffing_target(self.member,'Engine 1',2)
    def test_coverage_counts_active_duty_members_only(self):
        self.series()
        rows=self.s.rows('SELECT * FROM shifts')
        self.assertEqual(active_crew(rows,'Engine 1',date(2026,10,20),'07:59'),{self.member})
        self.assertEqual(active_crew(rows,'Engine 1',date(2026,10,20),'08:00'),set())
        self.assertEqual(active_crew(rows,'Engine 1',date(2026,10,19),'07:59'),set())
        self.assertFalse(covers_day(rows[0],date(2026,10,21)))
        self.assertTrue(covers_day(rows[0],date(2026,10,20)))
        self.s.db.execute("UPDATE shifts SET kind='Meeting'")
        self.assertEqual(active_crew(self.s.rows('SELECT * FROM shifts'),'Engine 1',date(2026,10,19),'09:00'),set())
    def test_staffing_target_validation(self):
        self.s.set_staffing_target(self.admin,'Engine 1',3)
        self.assertEqual(self.s.rows("SELECT minimum_staff FROM apparatus WHERE name='Engine 1'")[0][0],3)
        for target in ('bad',-1,101,'1.5'):
            with self.assertRaises(ValueError): self.s.set_staffing_target(self.admin,'Engine 1',target)
    def test_view_ranges(self):
        self.assertEqual(view_days(date(2026,10,19),'Day'),[date(2026,10,19)])
        week=view_days(date(2026,10,19),'Week')
        self.assertEqual((week[0],week[-1]),(date(2026,10,18),date(2026,10,24)))
        month=view_days(date(2024,2,29),'Month')
        self.assertIn(date(2024,2,29),month)
        self.assertEqual(len(month)%7,0)

if __name__=='__main__': unittest.main()
