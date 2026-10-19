"""Roster scheduling board: local, apparatus-based day/week/month planning."""
import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from datetime import date, datetime, time, timedelta

NAVY='#152738'; RED='#a52b32'; BG='#f3f1ec'; INK='#203243'; MUTED='#61717c'
COLORS={'A':'#b7353d','B':'#245f9a','C':'#367b53','D':'#74559a','Duty':'#294d68','Fundraiser':'#936315','Meeting':'#287875'}

def view_days(selected,mode):
    if mode=='Day': return [selected]
    if mode=='Week':
        first=selected-timedelta(days=(selected.weekday()+1)%7)
        return [first+timedelta(days=i) for i in range(7)]
    weeks=calendar.Calendar(firstweekday=6).monthdatescalendar(selected.year,selected.month)
    return [day for week in weeks for day in week]

def covers_day(entry,day):
    a=datetime.combine(day,time.min); b=a+timedelta(days=1)
    return datetime.fromisoformat(entry['start'])<b and datetime.fromisoformat(entry['end'])>a

def active_crew(entries,apparatus,day,clock):
    instant=datetime.combine(day,datetime.strptime(clock,'%H:%M').time())
    return {r['member'] for r in entries if r['apparatus']==apparatus and r['kind']=='Duty'
            and datetime.fromisoformat(r['start'])<=instant<datetime.fromisoformat(r['end'])}

def card_color(entry): return COLORS.get(entry['platoon'],COLORS.get(entry['kind'],NAVY))

class ScheduleBoard:
    def __init__(self,app):
        self.app=app; self.store=app.store; self.parent=app.body
        self.admin=app.user['role']=='Administrator'
        self.selected=getattr(app,'schedule_day',date.today())
        self.mode=getattr(app,'schedule_mode','Week')
        self.cards={}; self.targets=[]; self.drag=None; self.selected_entry=None
        self.apparatus=self.store.rows('SELECT * FROM apparatus ORDER BY name')
        self.variables={}
    def compact(self,parent,text,command,primary=False):
        return tk.Button(parent,text=text,command=command,bg=RED if primary else 'white',fg='white' if primary else INK,
                         font=('Times New Roman',11,'bold'),relief='flat',padx=10,pady=7,cursor='hand2')
    def mount(self):
        app=self.app
        bar=tk.Frame(self.parent,bg=BG); bar.pack(fill='x')
        self.compact(bar,'<',lambda:self.navigate(-1)).pack(side='left')
        self.compact(bar,'Today',self.today).pack(side='left',padx=4)
        self.compact(bar,'>',lambda:self.navigate(1)).pack(side='left')
        self.period=tk.Label(bar,bg=BG,fg=INK,font=('Times New Roman',18,'bold')); self.period.pack(side='left',padx=12)
        mode=tk.StringVar(value=self.mode)
        select=ttk.Combobox(bar,textvariable=mode,values=['Day','Week','Month'],state='readonly',width=7)
        select.pack(side='left'); select.bind('<<ComboboxSelected>>',lambda event:self.change_mode(mode.get()))
        if self.admin:
            self.compact(bar,'+ Assignment',lambda:app.attempt(app.shift_form),True).pack(side='right')
            self.compact(bar,'Apparatus / staffing',lambda:app.attempt(app.apparatus_form)).pack(side='right',padx=6)
        filters=tk.Frame(self.parent,bg=BG); filters.pack(fill='x',pady=(10,6))
        def combo(key,values,width):
            variable=tk.StringVar(value=getattr(app,'schedule_filter_'+key,values[0]))
            if variable.get() not in values: variable.set(values[0])
            self.variables[key]=variable
            ttk.Combobox(filters,textvariable=variable,values=values,state='readonly',width=width).pack(side='left',padx=(0,5))
            variable.trace_add('write',lambda *args:self.filter_changed(key))
        combo('apparatus',['All apparatus','Unassigned']+[r['name'] for r in self.apparatus],16)
        combo('group',['All groups','A','B','C','D','Unspecified'],11)
        combo('kind',['All activities','Duty','Fundraiser','Meeting'],12)
        self.search=tk.StringVar(value=getattr(app,'schedule_search',''))
        tk.Label(filters,text='Find:',bg=BG,fg=MUTED).pack(side='left')
        ttk.Entry(filters,textvariable=self.search,width=14).pack(side='left',padx=5)
        self.search.trace_add('write',lambda *args:self.render())
        jump=tk.Frame(self.parent,bg=BG); jump.pack(fill='x',pady=(0,7))
        tk.Label(jump,text='Go to date:',bg=BG,fg=MUTED).pack(side='left')
        self.jump=tk.StringVar(value=self.selected.isoformat())
        ttk.Entry(jump,textvariable=self.jump,width=12).pack(side='left',padx=5)
        self.compact(jump,'Go',lambda:app.attempt(self.go_to_date)).pack(side='left')
        tk.Label(jump,text='  Coverage at:',bg=BG,fg=MUTED).pack(side='left')
        self.clock=tk.StringVar(value=getattr(app,'schedule_clock','08:00'))
        ttk.Entry(jump,textvariable=self.clock,width=6).pack(side='left',padx=5)
        self.compact(jump,'Apply',lambda:app.attempt(self.apply_clock)).pack(side='left')
        tk.Label(jump,text='  A',fg=COLORS['A'],bg=BG).pack(side='left')
        for group in ('B','C','D'):
            tk.Label(jump,text='  '+group,fg=COLORS[group],bg=BG).pack(side='left')
        frame=tk.Frame(self.parent,bg='white'); frame.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(frame,bg='white',highlightthickness=1,highlightbackground='#dadfe4')
        y=ttk.Scrollbar(frame,orient='vertical',command=self.canvas.yview)
        x=ttk.Scrollbar(frame,orient='horizontal',command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        x.pack(side='bottom',fill='x'); y.pack(side='right',fill='y'); self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda event:self.render())
        self.canvas.bind('<ButtonPress-1>',self.press)
        self.canvas.bind('<B1-Motion>',self.motion)
        self.canvas.bind('<ButtonRelease-1>',self.release)
        self.canvas.bind('<Double-1>',self.double_click)
        self.canvas.bind('<MouseWheel>',lambda event:self.canvas.yview_scroll(-int(event.delta/120),'units'))
        self.canvas.bind('<Button-4>',lambda event:self.canvas.yview_scroll(-1,'units'))
        self.canvas.bind('<Button-5>',lambda event:self.canvas.yview_scroll(1,'units'))
        self.detail=tk.StringVar(value='Select an assignment to see details. Double-click an empty cell to schedule.')
        tk.Label(self.parent,textvariable=self.detail,bg=BG,fg=INK,font=('Times New Roman',11),anchor='w',justify='left',wraplength=800).pack(fill='x',pady=8)
        footer=tk.Frame(self.parent,bg=BG); footer.pack(fill='x')
        if self.admin:
            self.compact(footer,'Edit selected',lambda:app.attempt(self.edit)).pack(side='left')
            self.compact(footer,'Remove selected',lambda:app.attempt(self.remove)).pack(side='left',padx=6)
        self.summary=tk.StringVar()
        tk.Label(footer,textvariable=self.summary,bg=BG,fg=MUTED,font=('Times New Roman',10)).pack(side='right')
        app.schedule_board=self
        self.render()
    def persist(self):
        self.app.schedule_day=self.selected; self.app.schedule_month=(self.selected.year,self.selected.month)
        self.app.schedule_mode=self.mode; self.app.schedule_search=self.search.get()
    def filter_changed(self,key):
        setattr(self.app,'schedule_filter_'+key,self.variables[key].get()); self.render()
    def change_mode(self,mode): self.mode=mode; self.render()
    def navigate(self,offset):
        if self.mode=='Month':
            index=self.selected.year*12+self.selected.month-1+offset
            year,month=index//12,index%12+1
            if not 1<=year<=9999: return
            self.selected=date(year,month,min(self.selected.day,calendar.monthrange(year,month)[1]))
        else: self.selected+=timedelta(days=offset*(7 if self.mode=='Week' else 1))
        self.jump.set(self.selected.isoformat()); self.render()
    def today(self): self.selected=date.today(); self.jump.set(self.selected.isoformat()); self.render()
    def go_to_date(self):
        self.selected=datetime.strptime(self.jump.get(),'%Y-%m-%d').date(); self.render()
    def apply_clock(self):
        self.app.schedule_clock=datetime.strptime(self.clock.get(),'%H:%M').strftime('%H:%M')
        self.clock.set(self.app.schedule_clock); self.render()
    def filtered(self,entry):
        apparatus,group,kind=(self.variables[k].get() for k in ('apparatus','group','kind'))
        if apparatus!='All apparatus' and entry['apparatus']!=('' if apparatus=='Unassigned' else apparatus): return False
        if group!='All groups' and entry['platoon']!=('' if group=='Unspecified' else group): return False
        if kind!='All activities' and entry['kind']!=kind: return False
        text=' '.join(str(entry[k]) for k in ('name','title','apparatus','location','position'))
        return self.search.get().casefold() in text.casefold()
    def text(self,x,y,text,**kwargs):
        kwargs.setdefault('fill',INK)
        return self.canvas.create_text(x,y,text=text,anchor='nw',font=('Times New Roman',11),**kwargs)
    def rect(self,x,y,w,h,fill,outline='#dce1e5',**kwargs):
        return self.canvas.create_rectangle(x,y,x+w,y+h,fill=fill,outline=outline,**kwargs)
    def render(self):
        if not hasattr(self,'canvas'): return
        self.persist(); self.canvas.delete('all'); self.cards={}; self.targets=[]; self.drag=None
        self.days=view_days(self.selected,self.mode)
        start=self.days[0].isoformat()+'T00:00'; end=(self.days[-1]+timedelta(days=1)).isoformat()+'T00:00'
        # All visible members for admins, own assignments for regular members.
        self.entries=self.store.schedule_entries(self.app.user['id'],start,end)
        self.visible=[r for r in self.entries if self.filtered(r)]
        if self.selected_entry is not None and self.selected_entry not in {r['id'] for r in self.visible}:
            self.selected_entry=None; self.detail.set('Select an assignment to see details.')
        title=self.selected.strftime('%B %Y') if self.mode=='Month' else (self.selected.strftime('%A, %b %d') if self.mode=='Day' else self.days[0].strftime('%b %d')+' – '+self.days[-1].strftime('%b %d, %Y'))
        self.period.config(text=title)
        if self.mode=='Month': self.draw_month()
        else: self.draw_roster()
        bounds=self.canvas.bbox('all'); self.canvas.configure(scrollregion=bounds or (0,0,800,400))
        self.summary.set(str(len(self.visible))+' assignments · '+('Drag to move · Double-click to edit' if self.admin else 'My assignments · Read only'))
    def add_card(self,entry,day,x,y,w,month=False):
        key='card_'+str(len(self.cards)); self.cards[key]=(entry,day)
        color=card_color(entry); h=48 if month else 65
        self.rect(x,y,w,h,'#f4f7fa',outline='#cdd6df',tags=(key,))
        self.rect(x,y,4,h,color,outline=color,tags=(key,))
        prefix=(entry['platoon']+' · ') if entry['platoon'] else ''
        if month:
            lines=[prefix+entry['name'],(entry['apparatus'] or 'Unassigned')+' · '+datetime.fromisoformat(entry['start']).strftime('%H:%M')]
        else:
            a=datetime.fromisoformat(entry['start']); b=datetime.fromisoformat(entry['end'])
            duration=a.strftime('%H:%M')+' - '+b.strftime('%H:%M')+(' overnight' if b.date()>a.date() else '')
            lines=[prefix+entry['name'],duration,entry['kind']+' · '+(entry['position'] or entry['title'])]
        font=tkfont.Font(self.canvas,font=('Times New Roman',10))
        for i,line in enumerate(lines):
            if font.measure(line)>w-20:
                while line and font.measure(line+'...')>w-20: line=line[:-1]
                lines[i]=line+'...'
        self.canvas.create_text(x+10,y+5,text='\n'.join(lines),anchor='nw',fill=INK,font=('Times New Roman',10),tags=(key,))
    def draw_roster(self):
        cw=max(185,(self.canvas.winfo_width()-195)/len(self.days)); left=185
        self.rect(0,0,left,56,NAVY); self.text(10,10,'APPARATUS / CREW',fill='white')
        self.text(10,31,('Duty coverage at ' if self.admin else 'My duty at ')+getattr(self.app,'schedule_clock','08:00'),fill='#c9d5df')
        for i,day in enumerate(self.days):
            x=left+i*cw; self.rect(x,0,cw,56,'#e7edf3')
            self.text(x+10,8,day.strftime('%a %d %b'))
            self.text(x+10,29,'TODAY' if day==date.today() else str(sum(covers_day(r,day) for r in self.visible))+' assignments',fill=MUTED)
        names=[r['name'] for r in self.apparatus]+['']
        filter_name=self.variables['apparatus'].get()
        if filter_name!='All apparatus': names=['' if filter_name=='Unassigned' else filter_name]
        y=56
        for name in names:
            daily=[[r for r in self.visible if r['apparatus']==name and covers_day(r,day)] for day in self.days]
            height=max(118,34+max((len(rows) for rows in daily),default=0)*72)
            self.rect(0,y,left,height,'#f5f6f7')
            self.text(10,y+12,name or 'Unassigned',width=165)
            config=next((r for r in self.apparatus if r['name']==name),None)
            minimum=config['minimum_staff'] if config and self.admin else 0
            self.text(10,y+39,('Target: '+str(minimum)+' on duty' if minimum else ('No staffing target' if self.admin else 'My assignments')),fill=MUTED,width=160)
            for col,day in enumerate(self.days):
                x=left+col*cw; self.rect(x,y,cw,height,'white')
                self.targets.append(((x,y,x+cw,y+height),day,name))
                count=len(active_crew(self.entries,name,day,getattr(self.app,'schedule_clock','08:00')))
                coverage=(f'{count}/{minimum} on duty' if minimum else f'{count} '+('on duty' if self.admin else 'of my shifts active'))
                self.text(x+8,y+8,coverage,fill=('#9c332f' if self.admin and minimum and count<minimum else MUTED))
                for index,entry in enumerate(daily[col]): self.add_card(entry,day,x+6,y+31+index*72,cw-12)
                if not daily[col] and self.admin: self.text(x+9,y+49,'+ Add assignment',fill='#8b98a4')
            y+=height
        if not self.apparatus:
            self.text(10,y+15,'Add apparatus to organize your crew roster. Unassigned shifts remain available.',width=700,fill=MUTED)
    def draw_month(self):
        cw=max(145,self.canvas.winfo_width()/7)
        for col,name in enumerate(('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')):
            self.rect(col*cw,0,cw,30,NAVY); self.text(col*cw+8,7,name,fill='white')
        y=30
        for index in range(0,len(self.days),7):
            week=self.days[index:index+7]
            daily=[[r for r in self.visible if covers_day(r,day)] for day in week]
            height=max(115,34+max(len(rows) for rows in daily)*55)
            for col,day in enumerate(week):
                x=col*cw
                self.rect(x,y,cw,height,'white' if day.month==self.selected.month else '#eeeef0')
                self.text(x+8,y+7,str(day.day)+(' · Today' if day==date.today() else ''),fill=RED if day==date.today() else INK)
                self.targets.append(((x,y,x+cw,y+height),day,None))
                for n,entry in enumerate(daily[col]): self.add_card(entry,day,x+5,y+29+n*55,cw-10,True)
            y+=height
    def coordinates(self,event): return self.canvas.canvasx(event.x),self.canvas.canvasy(event.y)
    def hit_card(self,x,y):
        for item in reversed(self.canvas.find_overlapping(x,y,x,y)):
            for tag in self.canvas.gettags(item):
                if tag in self.cards: return self.cards[tag]
        return None
    def hit_target(self,x,y):
        return next(((day,name) for (a,b,c,d),day,name in self.targets if a<=x<c and b<=y<d),None)
    def press(self,event):
        x,y=self.coordinates(event); found=self.hit_card(x,y)
        if not found: self.drag=None; return
        entry,day=found; self.selected_entry=entry['id']
        self.detail.set(entry['name']+' · '+(entry['apparatus'] or 'Unassigned')+' · '+entry['title']+' · '+entry['start'].replace('T',' ')+' → '+entry['end'].replace('T',' ')+' · '+(entry['position'] or 'No position'))
        self.drag=(entry,day,event.x,event.y,False)
    def motion(self,event):
        if not self.drag or not self.admin: return
        entry,day,x,y,moved=self.drag
        if abs(event.x-x)+abs(event.y-y)>8:
            self.drag=(entry,day,x,y,True)
            self.canvas.delete('ghost')
            a,b=self.coordinates(event)
            self.canvas.create_text(a+12,b+12,text='Move '+entry['name'],anchor='nw',fill=RED,font=('Times New Roman',12,'bold'),tags='ghost')
    def release(self,event):
        self.canvas.delete('ghost')
        if not self.drag: return
        entry,source,x,y,moved=self.drag; self.drag=None
        if not moved or not self.admin: return
        target=self.hit_target(*self.coordinates(event))
        if target:
            day,apparatus=target
            if apparatus is None: apparatus=entry['apparatus']
            def move():
                self.store.move_shift(self.app.user['id'],entry['id'],day.isoformat(),apparatus,source.isoformat())
                self.detail.set('Moved '+entry['name']+' to '+day.isoformat()+' · '+(apparatus or 'Unassigned'))
            self.app.attempt(move); self.render()
    def double_click(self,event):
        self.drag=None
        if not self.admin: return
        x,y=self.coordinates(event); found=self.hit_card(x,y)
        if found: self.app.attempt(lambda:self.app.shift_form(found[0]['id'])); return
        target=self.hit_target(x,y)
        if target:
            day,name=target
            self.app.attempt(lambda:self.app.shift_form(day=day,apparatus_name=name))
    def edit(self):
        self.app.require_admin()
        if self.selected_entry is None: raise ValueError('Select an assignment card first.')
        self.app.shift_form(self.selected_entry)
    def remove(self):
        self.app.require_admin()
        if self.selected_entry is None: raise ValueError('Select an assignment card first.')
        if messagebox.askyesno('Remove assignment','Remove only this occurrence?',parent=self.app):
            self.store.remove_shift(self.app.user['id'],self.selected_entry)
            self.selected_entry=None; self.detail.set('Assignment removed.'); self.render()
