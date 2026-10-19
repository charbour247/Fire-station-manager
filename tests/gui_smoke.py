"""Run on Windows, or with DISPLAY set on Linux. Uses a temporary database."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import tkinter as tk
from app import App
from store import Store
from datetime import date,timedelta

with tempfile.TemporaryDirectory() as folder:
    store=Store(folder)
    admin=store.create_member('Chief','chief','administrator password','Administrator')
    member=store.create_member('Member','member','member password')
    for name in ('Engine 1','Ladder 2'): store.add_apparatus(admin,name)
    store.set_staffing_target(admin,'Engine 1',2)
    day=date.today()
    shift_id=store.repeat_shifts(admin,member,'Duty','Duty',day.isoformat()+'T08:00',day.isoformat()+'T20:00','Station 1','Engine 1','A','Driver')[0]
    app=App(store=store)
    errors=[]
    app.report_callback_exception=lambda *args:errors.append(args)
    app.user=store.member(admin);app.page('Schedule');app.update()
    board=app.schedule_board
    for mode in ('Day','Week','Month'):
        board.change_mode(mode);app.update()
        assert board.cards and board.targets
    board.change_mode('Day');app.update()
    card=next(key for key,value in board.cards.items() if value[0]['id']==shift_id)
    a,b,c,d=board.canvas.bbox(card)
    source=SimpleNamespace(x=int(a+15),y=int(b+15))
    target=next((bounds,dt,name) for bounds,dt,name in board.targets if name=='Ladder 2')
    a,b,c,d=target[0]
    drop=SimpleNamespace(x=int(a+15),y=int(b+50))
    board.press(source);board.motion(drop);board.release(drop);app.update()
    assert store.rows('SELECT apparatus FROM shifts WHERE id=?',(shift_id,))[0]['apparatus']=='Ladder 2'
    board.variables['group'].set('B');app.update();assert not board.cards
    board.variables['group'].set('All groups');app.update();assert board.cards
    board.go_to_date();board.apply_clock();app.update()
    app.shift_form(shift_id);app.update()
    dialogs=[w for w in app.winfo_children() if isinstance(w,tk.Toplevel)]
    assert len(dialogs)==1
    dialogs[0].destroy()
    app.apparatus_form();app.update()
    for w in app.winfo_children():
        if isinstance(w,tk.Toplevel):w.destroy()
    app.user=store.member(member);app.page('Schedule');app.update()
    board=app.schedule_board
    assert not board.admin
    assert all(r['member']==member for r in board.entries)
    assert 'Personnel' not in app.navigation_items()
    assert not errors,errors
    app.destroy();store.db.close()
print('GUI smoke passed: all views, drag/drop, filters, forms, and member access.')
