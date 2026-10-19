"""StationDesk: Windows desktop operations for a fire department."""
import sys, os, csv, subprocess, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import calendar
from pathlib import Path
from store import Store, KINDS
NAVY='#152738'; RED='#a52b32'; BG='#f3f1ec'; INK='#203243'; MUTED='#61717c'
def local(value):
    return datetime.fromisoformat(value).astimezone().strftime('%b %d, %Y  %I:%M %p') if value else 'On the clock'
class App(tk.Tk):
    def __init__(self,store=None,kiosk=False):
        super().__init__()
        self.store=store or Store(); self.kiosk=kiosk; self.user=None; self.timer=None
        self.title('StationDesk | Personnel Timeclock' if kiosk else 'StationDesk | Fire Department Operations')
        self.geometry('1180x780'); self.minsize(920,660); self.configure(bg=BG)
        assets=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'assets'
        self.logo=tk.PhotoImage(master=self,file=str(assets/'StationDesk.png'))
        self.logo_small=self.logo.subsample(8,8)
        self.logo_login=self.logo.subsample(2,2)
        self.iconphoto(True,self.logo)
        if os.name=='nt': self.iconbitmap(str(assets/'StationDesk.ico'))
        self.option_add('*Font',('Times New Roman',12))
        s=ttk.Style(self); s.theme_use('clam')
        s.configure('.',font=('Times New Roman',12))
        s.configure('Treeview',font=('Times New Roman',12),rowheight=34,background='white',fieldbackground='white')
        s.configure('Treeview.Heading',font=('Times New Roman',12,'bold'),background='#e9e6df')
        s.configure('TCombobox',padding=6); s.configure('TEntry',padding=7)
        self.login_screen()
    def clear(self):
        if self.timer:
            self.after_cancel(self.timer); self.timer=None
        for w in self.winfo_children(): w.destroy()
    def label(self,p,text,size=12,color=INK,**kw):
        return tk.Label(p,text=text,font=('Times New Roman',size),fg=color,bg=p.cget('bg'),**kw)
    def button(self,p,text,command,primary=False):
        return tk.Button(p,text=text,command=command,font=('Times New Roman',12,'bold'),bg=RED if primary else 'white',fg='white' if primary else INK,activebackground='#d9d4cc',relief='flat',padx=18,pady=10,cursor='hand2')
    def attempt(self,fn):
        try: return fn()
        except (ValueError,OSError) as e: messagebox.showerror('Please check your entry',str(e),parent=self)
    def field(self,p,label,value='',secret=False,choices=None):
        self.label(p,label,12,MUTED).pack(anchor='w',pady=(10,4))
        v=tk.StringVar(value=value)
        w=ttk.Combobox(p,textvariable=v,values=choices,state='readonly') if choices else ttk.Entry(p,textvariable=v,show='•' if secret else '')
        w.pack(fill='x'); return v
    def login_screen(self):
        self.user=None; self.clear()
        brand=tk.Frame(self,bg=NAVY,width=405); brand.pack(side='left',fill='both'); brand.pack_propagate(False)
        tk.Label(brand,image=self.logo_login,bg=NAVY).pack(pady=(75,20))
        self.label(brand,'STATIONDESK',27,'white').pack()
        self.label(brand,'FIRE DEPARTMENT OPERATIONS',11,'#c2cbd2').pack(pady=12)
        self.label(brand,'Ready for the next call.',23,'white').pack(pady=(75,18))
        self.label(brand,'Personnel. Training. Service.\nOne place to keep your station moving.',14,'#c2cbd2',justify='center').pack()
        right=tk.Frame(self,bg=BG); right.pack(side='left',fill='both',expand=True)
        form=tk.Frame(right,bg=BG); form.pack(expand=True,padx=65,fill='x')
        first=not self.store.rows('SELECT id FROM members LIMIT 1')
        self.label(form,'INITIAL SETUP' if first else 'MEMBER ACCESS',11,RED).pack(anchor='w')
        self.label(form,'Set up your station' if first else 'Welcome back',32).pack(anchor='w',pady=(10,4))
        self.label(form,'Create the first administrator account.' if first else ('Sign in to record your service.' if self.kiosk else 'Sign in to your personnel dashboard.'),14,MUTED).pack(anchor='w')
        name=self.field(form,'Full name') if first else None
        username=self.field(form,'Username'); password=self.field(form,'Password'+(' · minimum 10 characters' if first else ''),secret=True)
        def login():
            if first: self.store.create_member(name.get(),username.get(),password.get(),'Administrator')
            self.user=self.store.login(username.get(),password.get())
            self.page('Timeclock' if self.kiosk else 'Dashboard')
        self.button(form,'Create station account' if first else 'Sign in  →',lambda:self.attempt(login),True).pack(fill='x',pady=24)
        self.label(form,'Local station workspace • Records saved on this computer',11,MUTED).pack(anchor='w')
    def navigation_items(self):
        if self.kiosk: return ['Timeclock']
        items=['Dashboard','Training','Timeclock','Schedule']
        if self.user and self.user['role']=='Administrator': items.append('Personnel')
        return items
    def page(self,name):
        if not self.user:
            self.login_screen(); return
        self.user=self.store.member(self.user['id'])
        if not self.user:
            self.login_screen(); return
        if name=='Personnel' and (self.kiosk or self.user['role']!='Administrator'):
            messagebox.showerror('Access denied','Only administrators can manage personnel.',parent=self)
            name='Timeclock' if self.kiosk else 'Dashboard'
        self.clear()
        nav=tk.Frame(self,bg=NAVY,width=225); nav.pack(side='left',fill='y'); nav.pack_propagate(False)
        tk.Label(nav,text='  STATIONDESK',image=self.logo_small,compound='left',font=('Times New Roman',17),fg='white',bg=NAVY).pack(anchor='w',padx=15,pady=(30,4))
        self.label(nav,'FIRE DEPARTMENT',10,'#bcc6cf').pack(anchor='w',padx=42,pady=(0,34))
        items=self.navigation_items()
        for i,item in enumerate(items):
            tk.Button(nav,text=f'{i+1:02}    {item}',anchor='w',bg=RED if item==name else NAVY,fg='white',font=('Times New Roman',14),relief='flat',padx=24,pady=15,command=lambda v=item:self.page(v),cursor='hand2').pack(fill='x',pady=3)
        self.button(nav,'Sign out',self.login_screen).pack(side='bottom',fill='x',padx=20,pady=22)
        self.label(nav,self.user['name']+'\n'+self.user['role'],13,'#d8dfe5',justify='left').pack(side='bottom',anchor='w',padx=22,pady=12)
        main=tk.Frame(self,bg=BG); main.pack(side='left',fill='both',expand=True,padx=32,pady=26)
        self.label(main,'PERSONNEL WORKSPACE    /    '+name.upper(),10,MUTED).pack(anchor='w')
        header=tk.Frame(main,bg=BG); header.pack(fill='x',pady=(15,20))
        self.label(header,name,30).pack(side='left')
        self.label(header,datetime.now().strftime('%A, %B %d, %Y'),12,MUTED).pack(side='right')
        self.body=main
        getattr(self,'show_'+name.lower())()
    def card(self,p):
        f=tk.Frame(p,bg='white',padx=22,pady=20,highlightbackground='#e0ddd6',highlightthickness=1); return f
    def table(self,parent,columns,rows,height=8):
        wrap=tk.Frame(parent,bg=parent.cget('bg')); wrap.pack(fill='both',expand=True,pady=12)
        tree=ttk.Treeview(wrap,columns=columns,show='headings',height=height,selectmode='browse')
        for col in columns: tree.heading(col,text=col); tree.column(col,width=130,minwidth=65,stretch=True)
        scroll=ttk.Scrollbar(wrap,orient='vertical',command=tree.yview); tree.configure(yscrollcommand=scroll.set)
        horizontal=ttk.Scrollbar(wrap,orient='horizontal',command=tree.xview); tree.configure(xscrollcommand=horizontal.set)
        horizontal.pack(side='bottom',fill='x')
        scroll.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        for key,values in rows: tree.insert('','end',iid=str(key),values=values)
        return tree
    def show_dashboard(self):
        self.label(self.body,'Welcome, '+self.user['name'].split()[0]+'.',22).pack(anchor='w')
        self.label(self.body,'Your service at a glance · All-time totals, including active sessions',12,MUTED).pack(anchor='w',pady=(5,20))
        strip=tk.Frame(self.body,bg=BG); strip.pack(fill='x')
        totals=self.store.totals(self.user['id'])
        for title,value in [('Duty hours',totals['Duty']),('Training hours',totals['Training']),('Special event hours',totals['Fundraiser']+totals['Meeting'])]:
            c=self.card(strip); c.pack(side='left',expand=True,fill='both',padx=(0,10))
            self.label(c,title,13,MUTED).pack(anchor='w'); self.label(c,f'{value:,.1f}',34).pack(anchor='w',pady=10)
            self.label(c,'HOURS RECORDED',9,RED).pack(anchor='w')
        active=self.store.active(self.user['id'])
        status=self.card(self.body); status.pack(fill='x',pady=20)
        self.label(status,'● '+('Clocked in · '+active['kind'] if active else 'Currently off duty'),16).pack(side='left')
        self.button(status,'Open timeclock →',lambda:self.page('Timeclock'),True).pack(side='right')
        self.label(self.body,'Upcoming schedule',20).pack(anchor='w')
        rows=self.store.rows('SELECT * FROM shifts WHERE member=? AND end>=? ORDER BY start LIMIT 5',(self.user['id'],datetime.now().isoformat(timespec='minutes')))
        self.table(self.body,('Assignment','Type','Apparatus','Starts','Location'),[(r['id'],(r['title'],r['kind'],r['apparatus'] or 'Unassigned',local(r['start']),r['location'])) for r in rows],4)
        if not rows: self.label(self.body,'No upcoming assignments. Your administrator can add shifts in Schedule.',12,MUTED).pack(anchor='w')
    def show_timeclock(self):
        panel=self.card(self.body); panel.pack(fill='x')
        clock=self.label(panel,'',36); clock.pack()
        def tick():
            clock.config(text=datetime.now().strftime('%I:%M:%S %p'))
            self.timer=self.after(1000,tick)
        tick()
        active=self.store.active(self.user['id'])
        self.label(panel,'● '+('CLOCKED IN — '+active['kind'].upper() if active else 'READY TO CLOCK IN'),14,RED).pack(pady=12)
        if active:
            self.label(panel,'Started '+local(active['started']),14,MUTED).pack()
            def out():
                self.store.clock_out(self.user['id']); self.page('Timeclock')
            self.button(panel,'Clock out',lambda:self.attempt(out),True).pack(pady=18)
        else:
            self.label(panel,'Select your activity',14).pack(pady=8)
            kind=tk.StringVar(value='Duty'); choices=tk.Frame(panel,bg='white'); choices.pack()
            for k in KINDS: tk.Radiobutton(choices,text=k,variable=kind,value=k,bg='white',fg=INK,font=('Times New Roman',15),padx=20,pady=12).pack(side='left')
            def punch():
                self.store.punch(self.user['id'],kind.get()); self.page('Timeclock')
            self.button(panel,'Clock in',lambda:self.attempt(punch),True).pack(pady=15)
        self.label(self.body,'Recent time entries',20).pack(anchor='w',pady=(24,0))
        rows=self.store.rows('SELECT * FROM punches WHERE member=? ORDER BY started DESC LIMIT 25',(self.user['id'],))
        self.table(self.body,('Activity','Clock in','Clock out'),[(r['id'],(r['kind'],local(r['started']),local(r['ended']))) for r in rows],5)
        if self.kiosk: self.label(self.body,'Sign out after recording your time so the next member can sign in.',12,MUTED).pack(anchor='w')
    def dialog(self,title):
        d=tk.Toplevel(self); d.title(title); d.geometry('530x660'); d.configure(bg=BG); d.transient(self); d.grab_set()
        p=tk.Frame(d,bg=BG,padx=28,pady=18); p.pack(fill='both',expand=True)
        self.label(p,title,24).pack(anchor='w'); return d,p
    def show_training(self):
        row=tk.Frame(self.body,bg=BG); row.pack(fill='x')
        self.label(row,'Training records & resource library',18).pack(side='left')
        self.button(row,'+ Add training / document',self.training_form,True).pack(side='right')
        self.label(self.body,'Save completed training, certificates, and reference documents. Use 0 hours for resources.',12,MUTED).pack(anchor='w',pady=12)
        search=self.field(self.body,'Search title, category, or document')
        rows=self.store.rows('SELECT * FROM training WHERE member=? ORDER BY day DESC,id DESC',(self.user['id'],))
        tree=self.table(self.body,('Title','Date','Hours','Category','Document'),[],10)
        def populate(*args):
            tree.delete(*tree.get_children())
            for r in rows:
                if search.get().casefold() in ' '.join(str(r[k]) for k in ('title','category','original')).casefold():
                    tree.insert('','end',iid=str(r['id']),values=(r['title'],r['day'],r['hours'],r['category'],r['original'] or '—'))
        search.trace_add('write',populate); populate()
        def open_doc():
            if not tree.selection(): raise ValueError('Select a training record.')
            r=next(r for r in rows if str(r['id'])==tree.selection()[0])
            if not r['document']: raise ValueError('This record has no attachment.')
            path=self.store.folder/r['document']
            if not path.is_file(): raise ValueError('Attachment is missing from the data folder.')
            if messagebox.askyesno('Open attachment','Open '+r['original']+' in its default application? Only open documents you trust.'):
                if os.name=='nt': os.startfile(str(path))
                else: subprocess.Popen(['xdg-open',str(path)])
        self.button(self.body,'Open selected attachment',lambda:self.attempt(open_doc)).pack(anchor='w')
    def training_form(self):
        d,p=self.dialog('Add training or resource')
        title=self.field(p,'Training / resource title'); day=self.field(p,'Completion date · YYYY-MM-DD',datetime.now().strftime('%Y-%m-%d'))
        hours=self.field(p,'Hours · 0 for resource documents','0')
        category=self.field(p,'Category','Fire Operations',choices=['Fire Operations','EMS','Safety','Leadership','Reference'])
        source=tk.StringVar(); self.label(p,'Optional attachment · copied into the local library',11,MUTED).pack(anchor='w',pady=(18,4))
        self.button(p,'Choose document',lambda:source.set(filedialog.askopenfilename(parent=d))).pack(anchor='w')
        self.label(p,'',11,MUTED,textvariable=source,wraplength=450).pack(anchor='w')
        def save():
            self.store.add_training(self.user['id'],title.get(),day.get(),hours.get(),category.get(),source.get()); d.destroy(); self.page('Training')
        self.button(p,'Save record',lambda:self.attempt(save),True).pack(fill='x',pady=20)
    def show_schedule(self):
        admin=self.user['role']=='Administrator'
        self.schedule_day=getattr(self,'schedule_day',date.today())
        year,month=getattr(self,'schedule_month',(self.schedule_day.year,self.schedule_day.month))
        self.schedule_month=(year,month)
        bar=tk.Frame(self.body,bg=BG); bar.pack(fill='x')
        def move(offset):
            index=year*12+month-1+offset
            self.schedule_month=(index//12,index%12+1)
            self.schedule_day=date(*self.schedule_month,1)
            self.page('Schedule')
        self.button(bar,'‹',lambda:move(-1)).pack(side='left')
        self.label(bar,date(year,month,1).strftime('%B %Y'),22).pack(side='left',padx=14)
        self.button(bar,'›',lambda:move(1)).pack(side='left')
        def today():
            self.schedule_day=date.today()
            self.schedule_month=(self.schedule_day.year,self.schedule_day.month)
            self.page('Schedule')
        self.button(bar,'Today',today).pack(side='left',padx=8)
        if admin:
            self.button(bar,'+ Assignment',lambda:self.attempt(self.shift_form),True).pack(side='right')
            self.button(bar,'+ Apparatus',lambda:self.attempt(self.apparatus_form)).pack(side='right',padx=8)
        self.label(self.body,('Station calendar' if admin else 'My calendar')+' · Select a day to view personnel and apparatus · Local station time',11,MUTED).pack(anchor='w',pady=(8,6))
        weeks=calendar.Calendar(firstweekday=6).monthdatescalendar(year,month)
        while len(weeks)<6:
            weeks.append([weeks[-1][-1]+timedelta(days=n) for n in range(1,8)])
        first=weeks[0][0]; last=weeks[-1][-1]+timedelta(days=1)
        entries=self.store.schedule_entries(self.user['id'],first.isoformat()+'T00:00',last.isoformat()+'T00:00')
        def on_day(day):
            start=day.isoformat()+'T00:00'; end=(day+timedelta(days=1)).isoformat()+'T00:00'
            return [r for r in entries if r['start']<end and r['end']>start]
        grid=tk.Frame(self.body,bg='#dedad2'); grid.pack(fill='both',expand=True)
        for col,heading in enumerate(('Sun','Mon','Tue','Wed','Thu','Fri','Sat')):
            grid.columnconfigure(col,weight=1,uniform='day')
            tk.Label(grid,text=heading,bg=NAVY,fg='white',font=('Times New Roman',11,'bold'),pady=5).grid(row=0,column=col,sticky='nsew',padx=1,pady=1)
        def select(day):
            self.schedule_day=day; self.schedule_month=(day.year,day.month)
            self.page('Schedule')
        for row,week in enumerate(weeks,1):
            grid.rowconfigure(row,weight=1,uniform='week')
            for col,day in enumerate(week):
                daily=on_day(day)
                text=str(day.day)+(' • Today' if day==date.today() else '')
                if daily:
                    text+='\n'+str(len(daily))+' · '+(daily[0]['apparatus'] or 'Unassigned')
                selected=day==self.schedule_day
                tk.Button(grid,text=text,anchor='nw',justify='left',font=('Times New Roman',10),
                          bg=RED if selected else ('white' if day.month==month else '#eae7e1'),
                          fg='white' if selected else (INK if day.month==month else MUTED),
                          relief='flat',padx=5,pady=3,width=1,height=2,cursor='hand2',
                          command=lambda d=day:select(d)).grid(row=row,column=col,sticky='nsew',padx=1,pady=1)
        selected_rows=on_day(self.schedule_day)
        self.label(self.body,self.schedule_day.strftime('%A, %B %d')+' · '+str(len(selected_rows))+' assignments',17).pack(anchor='w',pady=(10,0))
        tree=self.table(self.body,('Member','Apparatus','Assignment','Type','Start','End','Location'),
            [(r['id'],(r['name'],r['apparatus'] or 'Unassigned',r['title'],r['kind'],local(r['start']),local(r['end']),r['location'])) for r in selected_rows],3)
        if admin:
            actions=tk.Frame(self.body,bg=BG); actions.pack(fill='x')
            def selected_id():
                if not tree.selection(): raise ValueError('Select an assignment from the day list.')
                return int(tree.selection()[0])
            self.button(actions,'Edit selected',lambda:self.attempt(lambda:self.shift_form(selected_id()))).pack(side='left')
            tree.bind('<Double-1>',lambda event:self.attempt(lambda:self.shift_form(selected_id())))
            def remove():
                self.require_admin(); shift_id=selected_id()
                if messagebox.askyesno('Cancel assignment','Remove the selected assignment?',parent=self):
                    self.store.remove_shift(self.user['id'],shift_id)
                    self.page('Schedule')
            self.button(actions,'Remove selected',lambda:self.attempt(remove)).pack(side='left',padx=8)
    def apparatus_form(self):
        self.require_admin()
        d,p=self.dialog('Add station apparatus')
        name=self.field(p,'Apparatus name · e.g. Engine 1, Ladder 2')
        current=self.store.rows('SELECT name FROM apparatus ORDER BY name')
        self.label(p,'Current apparatus:\n'+('\n'.join(r['name'] for r in current) or 'No apparatus added yet.'),12,MUTED,justify='left',wraplength=450).pack(anchor='w',pady=16)
        def save():
            self.require_admin()
            self.store.add_apparatus(self.user['id'],name.get())
            d.destroy(); self.page('Schedule')
        self.button(p,'Add apparatus',lambda:self.attempt(save),True).pack(fill='x',pady=18)
    def shift_form(self,shift_id=None):
        self.require_admin()
        existing=None
        if shift_id is not None:
            found=self.store.rows('SELECT * FROM shifts WHERE id=?',(shift_id,))
            if not found: raise ValueError('This assignment no longer exists.')
            existing=found[0]
        d,p=self.dialog('Edit assignment' if existing else 'Schedule assignment')
        d.geometry('560x740')
        members=self.store.rows('SELECT id,name,username FROM members ORDER BY name')
        mapping={f"{r['name']} ({r['username']})":r['id'] for r in members}
        default=next((key for key,value in mapping.items() if existing and value==existing['member']),next(iter(mapping)))
        member=self.field(p,'Member',default,choices=list(mapping))
        title=self.field(p,'Assignment title',existing['title'] if existing else 'Duty shift')
        kind=self.field(p,'Activity',existing['kind'] if existing else 'Duty',choices=KINDS)
        options={'Unassigned':''}
        options.update({r['name']:r['name'] for r in self.store.rows('SELECT name FROM apparatus ORDER BY name')})
        apparatus=self.field(p,'Apparatus',existing['apparatus'] if existing and existing['apparatus'] else 'Unassigned',choices=list(options))
        selected=getattr(self,'schedule_day',date.today()).isoformat()
        start=self.field(p,'Start · YYYY-MM-DD HH:MM',existing['start'].replace('T',' ') if existing else selected+' 08:00')
        end=self.field(p,'End · YYYY-MM-DD HH:MM',existing['end'].replace('T',' ') if existing else selected+' 16:00')
        location=self.field(p,'Location',existing['location'] if existing else 'Station 1')
        self.label(p,'Add apparatus from the calendar before assigning it.\nMultiple members can crew the same apparatus.',11,MUTED,justify='left').pack(anchor='w',pady=(10,0))
        def save():
            self.require_admin()
            a=datetime.strptime(start.get(),'%Y-%m-%d %H:%M').isoformat(timespec='minutes')
            b=datetime.strptime(end.get(),'%Y-%m-%d %H:%M').isoformat(timespec='minutes')
            self.store.add_shift(mapping[member.get()],title.get(),kind.get(),a,b,location.get(),options[apparatus.get()],shift_id)
            self.schedule_day=datetime.fromisoformat(a).date()
            self.schedule_month=(self.schedule_day.year,self.schedule_day.month)
            d.destroy(); self.page('Schedule')
        self.button(p,'Save assignment',lambda:self.attempt(save),True).pack(fill='x',pady=18)
    def require_admin(self):
        if not self.user or self.kiosk:
            raise ValueError('Only administrators can manage personnel.')
        self.user=self.store.require_admin(self.user['id'])
    def show_personnel(self):
        self.require_admin()
        self.label(self.body,'Member accounts',20).pack(anchor='w')
        self.label(self.body,'Select a member to edit their name, username, role, or password.',12,MUTED).pack(anchor='w',pady=10)
        self.button(self.body,'+ Create member',lambda:self.attempt(self.member_form),True).pack(anchor='w')
        rows=self.store.rows('SELECT id,name,username,role FROM members ORDER BY name')
        tree=self.table(self.body,('Name','Username','Role'),[(r['id'],(r['name'],r['username'],r['role'])) for r in rows])
        def edit():
            self.require_admin()
            if not tree.selection(): raise ValueError('Select a member to edit.')
            self.member_form(int(tree.selection()[0]))
        self.button(self.body,'Edit selected member',lambda:self.attempt(edit),True).pack(anchor='w',pady=(0,10))
        tree.bind('<Double-1>',lambda event:self.attempt(edit))
        self.button(self.body,'Export department hours (CSV)',lambda:self.attempt(self.export)).pack(anchor='w')
    def member_form(self,member_id=None):
        self.require_admin()
        member=self.store.member(member_id) if member_id is not None else None
        if member_id is not None and not member: raise ValueError('This member no longer exists.')
        d,p=self.dialog('Edit member account' if member else 'Create member account')
        name=self.field(p,'Full name',member['name'] if member else '')
        username=self.field(p,'Username',member['username'] if member else '')
        password=self.field(p,'New password · leave blank to keep current' if member else 'Initial password · minimum 10 characters',secret=True)
        role=self.field(p,'Role',member['role'] if member else 'Member',choices=['Member','Administrator'])
        if member:
            self.label(p,'Password changes require at least 10 characters.\nExisting hours, documents, and assignments are retained.',11,MUTED,justify='left').pack(anchor='w',pady=12)
        def save():
            self.require_admin()
            if member:
                self.store.update_member(self.user['id'],member_id,name.get(),username.get(),role.get(),password.get())
            else:
                self.store.create_member(name.get(),username.get(),password.get(),role.get())
            self.user=self.store.member(self.user['id'])
            d.destroy()
            self.page('Personnel' if self.user['role']=='Administrator' else 'Dashboard')
        self.button(p,'Save changes' if member else 'Create account',lambda:self.attempt(save),True).pack(fill='x',pady=20)
    def export(self):
        self.require_admin()
        path=filedialog.asksaveasfilename(defaultextension='.csv',initialfile='station-hours.csv',filetypes=[('CSV','*.csv')])
        if not path: return
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            writer=csv.writer(f); writer.writerow(['Name','Username','Duty hours','Fundraiser hours','Meeting hours','Training hours'])
            for r in self.store.rows('SELECT * FROM members ORDER BY name'):
                t=self.store.totals(r['id'])
                def safe(s): return "'"+s if s.startswith(('=','+','-','@','\t','\r')) else s
                writer.writerow([safe(r['name']),safe(r['username'])]+[round(t[k],2) for k in (*KINDS,'Training')])
        messagebox.showinfo('Export complete','Department hour totals have been exported.')
if __name__=='__main__':
    App(kiosk='--timeclock' in sys.argv).mainloop()
