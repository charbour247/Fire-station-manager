"""StationDesk: Windows desktop operations for a fire department."""
import sys, os, csv, subprocess, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
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
        self.label(brand,'✦',64,'#d2b382').pack(pady=(110,20))
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
    def page(self,name):
        self.clear()
        nav=tk.Frame(self,bg=NAVY,width=225); nav.pack(side='left',fill='y'); nav.pack_propagate(False)
        self.label(nav,'✦  STATIONDESK',19,'white').pack(anchor='w',padx=20,pady=(30,4))
        self.label(nav,'FIRE DEPARTMENT',10,'#bcc6cf').pack(anchor='w',padx=42,pady=(0,34))
        items=['Timeclock'] if self.kiosk else ['Dashboard','Training','Timeclock','Schedule']+(['Personnel'] if self.user['role']=='Administrator' else [])
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
        self.table(self.body,('Assignment','Type','Starts','Location'),[(r['id'],(r['title'],r['kind'],local(r['start']),r['location'])) for r in rows],4)
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
        row=tk.Frame(self.body,bg=BG); row.pack(fill='x')
        admin=self.user['role']=='Administrator'
        self.label(row,'Station assignments' if admin else 'My assignments',19).pack(side='left')
        if admin: self.button(row,'+ Schedule assignment',self.shift_form,True).pack(side='right')
        self.label(self.body,'Local station time · Past and upcoming assignments',12,MUTED).pack(anchor='w',pady=12)
        query='SELECT s.*, m.name FROM shifts s JOIN members m ON m.id=s.member'
        rows=self.store.rows(query+('' if admin else ' WHERE member=?')+' ORDER BY start DESC',() if admin else (self.user['id'],))
        tree=self.table(self.body,('Member','Assignment','Type','Start','End','Location'),[(r['id'],(r['name'],r['title'],r['kind'],local(r['start']),local(r['end']),r['location'])) for r in rows],12)
        if admin:
            def remove():
                if not tree.selection(): raise ValueError('Select an assignment.')
                if messagebox.askyesno('Cancel assignment','Remove the selected assignment?'):
                    with self.store.db: self.store.db.execute('DELETE FROM shifts WHERE id=?',(tree.selection()[0],))
                    self.page('Schedule')
            self.button(self.body,'Remove selected assignment',lambda:self.attempt(remove)).pack(anchor='w')
    def shift_form(self):
        d,p=self.dialog('Schedule assignment')
        members=self.store.rows('SELECT id,name,username FROM members ORDER BY name')
        mapping={f"{r['name']} ({r['username']})":r['id'] for r in members}
        member=self.field(p,'Member',next(iter(mapping)),choices=list(mapping))
        title=self.field(p,'Assignment title'); kind=self.field(p,'Activity','Duty',choices=KINDS)
        date=datetime.now().strftime('%Y-%m-%d')
        start=self.field(p,'Start · YYYY-MM-DD HH:MM',date+' 08:00')
        end=self.field(p,'End · YYYY-MM-DD HH:MM',date+' 16:00')
        location=self.field(p,'Location','Station 1')
        def save():
            a=datetime.strptime(start.get(),'%Y-%m-%d %H:%M').isoformat(timespec='minutes')
            b=datetime.strptime(end.get(),'%Y-%m-%d %H:%M').isoformat(timespec='minutes')
            self.store.add_shift(mapping[member.get()],title.get(),kind.get(),a,b,location.get()); d.destroy(); self.page('Schedule')
        self.button(p,'Save assignment',lambda:self.attempt(save),True).pack(fill='x',pady=18)
    def show_personnel(self):
        self.label(self.body,'Member accounts',20).pack(anchor='w')
        self.label(self.body,'Administrators manage assignments. Members see their own hours and records.',12,MUTED).pack(anchor='w',pady=10)
        self.button(self.body,'+ Create member',self.member_form,True).pack(anchor='w')
        rows=self.store.rows('SELECT id,name,username,role FROM members ORDER BY name')
        self.table(self.body,('Name','Username','Role'),[(r['id'],(r['name'],r['username'],r['role'])) for r in rows])
        self.button(self.body,'Export department hours (CSV)',lambda:self.attempt(self.export)).pack(anchor='w')
    def member_form(self):
        d,p=self.dialog('Create member account')
        name=self.field(p,'Full name'); username=self.field(p,'Username'); password=self.field(p,'Initial password · minimum 10 characters',secret=True)
        role=self.field(p,'Role','Member',choices=['Member','Administrator'])
        def save():
            self.store.create_member(name.get(),username.get(),password.get(),role.get()); d.destroy(); self.page('Personnel')
        self.button(p,'Create account',lambda:self.attempt(save),True).pack(fill='x',pady=20)
    def export(self):
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
