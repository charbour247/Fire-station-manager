"""Access checks run without opening a GUI or requiring a display."""
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from app import App
from store import Store

class PersonnelAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=Store(self.temp.name)
        self.admin=self.store.create_member('Chief','chief','administrator password','Administrator')
        self.member=self.store.create_member('Member','member','member password')
    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()
    def subject(self,member,kiosk=False):
        obj=SimpleNamespace(store=self.store,user=self.store.member(member),kiosk=kiosk)
        obj.require_admin=lambda:App.require_admin(obj)
        return obj
    def test_personnel_tab_visibility(self):
        self.assertIn('Personnel',App.navigation_items(self.subject(self.admin)))
        self.assertNotIn('Personnel',App.navigation_items(self.subject(self.member)))
        self.assertEqual(App.navigation_items(self.subject(self.admin,True)),['Timeclock'])
    def test_direct_personnel_actions_require_admin(self):
        for obj in (self.subject(self.member),self.subject(self.admin,True)):
            for action in (App.show_personnel,App.member_form,App.export):
                with self.subTest(action=action.__name__,kiosk=obj.kiosk):
                    with self.assertRaisesRegex(ValueError,'Only administrators'): action(obj)
    def test_permissions_are_refreshed_after_role_change(self):
        obj=self.subject(self.admin)
        second=self.store.create_member('Chief 2','chief2','administrator password','Administrator')
        self.store.update_member(second,self.admin,'Chief','chief','Member')
        with self.assertRaisesRegex(ValueError,'Only administrators'): App.require_admin(obj)
    def test_schedule_forms_require_administrator(self):
        for action in (App.shift_form,App.apparatus_form):
            with self.assertRaisesRegex(ValueError,'Only administrators'):
                action(self.subject(self.member))
    def test_direct_route_rejects_member_before_rendering(self):
        obj=self.subject(self.member)
        # Stop at the start of rendering, after the route permission check.
        obj.clear=Mock(side_effect=RuntimeError('render boundary'))
        with patch('app.messagebox.showerror') as error:
            with self.assertRaisesRegex(RuntimeError,'render boundary'): App.page(obj,'Personnel')
            error.assert_called_once()
            self.assertIn('Only administrators',error.call_args.args[1])

if __name__=='__main__': unittest.main()
