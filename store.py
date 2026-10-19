import sqlite3, hashlib, hmac, os, uuid, shutil
from pathlib import Path
from datetime import datetime, timezone
KINDS = ('Duty', 'Fundraiser', 'Meeting')
def now(): return datetime.now(timezone.utc).isoformat()
class Store:
    def __init__(self, folder=None):
        self.folder=Path(folder or Path(os.environ.get('LOCALAPPDATA',Path.home()))/'StationDesk')
        self.folder.mkdir(parents=True,exist_ok=True)
        (self.folder/'documents').mkdir(exist_ok=True)
        self.db=sqlite3.connect(self.folder/'stationdesk.db',timeout=15)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY,name TEXT NOT NULL,username TEXT UNIQUE COLLATE NOCASE,salt BLOB,password BLOB,role TEXT);
        CREATE TABLE IF NOT EXISTS punches(id INTEGER PRIMARY KEY,member INTEGER REFERENCES members(id),kind TEXT,started TEXT,ended TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS active_member ON punches(member) WHERE ended IS NULL;
        CREATE TABLE IF NOT EXISTS training(id INTEGER PRIMARY KEY,member INTEGER REFERENCES members(id),title TEXT,day TEXT,hours REAL,category TEXT,document TEXT,original TEXT);
        CREATE TABLE IF NOT EXISTS shifts(id INTEGER PRIMARY KEY,member INTEGER REFERENCES members(id),title TEXT,kind TEXT,start TEXT,end TEXT,location TEXT);
        ''')
    def rows(self,q,args=()): return self.db.execute(q,args).fetchall()
    def create_member(self,name,username,password,role='Member'):
        if not name.strip() or not username.strip() or len(password)<10: raise ValueError('Enter a name, username, and password of at least 10 characters.')
        salt=os.urandom(32)
        digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,300000)
        try:
            with self.db: return self.db.execute('INSERT INTO members(name,username,salt,password,role) VALUES(?,?,?,?,?)',(name.strip(),username.strip(),salt,digest,role)).lastrowid
        except sqlite3.IntegrityError: raise ValueError('Username already exists.')
    def login(self,username,password):
        r=self.db.execute('SELECT * FROM members WHERE username=?',(username.strip(),)).fetchone()
        if r and hmac.compare_digest(r['password'],hashlib.pbkdf2_hmac('sha256',password.encode(),r['salt'],300000)): return r
        raise ValueError('Username or password is incorrect.')
    def active(self,member): return self.db.execute('SELECT * FROM punches WHERE member=? AND ended IS NULL',(member,)).fetchone()
    def punch(self,member,kind):
        if kind not in KINDS: raise ValueError('Choose an activity.')
        try:
            with self.db: self.db.execute('INSERT INTO punches(member,kind,started) VALUES(?,?,?)',(member,kind,now()))
        except sqlite3.IntegrityError: raise ValueError('Already clocked in. End the current activity first.')
    def clock_out(self,member):
        with self.db:
            if self.db.execute('UPDATE punches SET ended=? WHERE member=? AND ended IS NULL',(now(),member)).rowcount!=1: raise ValueError('No active time entry.')
    def totals(self,member):
        t={k:0.0 for k in KINDS}
        for r in self.rows('SELECT * FROM punches WHERE member=?',(member,)):
            t[r['kind']]+=(datetime.fromisoformat(r['ended'] or now())-datetime.fromisoformat(r['started'])).total_seconds()/3600
        t['Training']=self.db.execute('SELECT COALESCE(SUM(hours),0) FROM training WHERE member=?',(member,)).fetchone()[0]
        return t
    def add_training(self,member,title,day,hours,category,source=''):
        if not title.strip(): raise ValueError('Enter a title.')
        if datetime.strptime(day,'%Y-%m-%d').date()>datetime.now().date(): raise ValueError('Completed training cannot have a future date.')
        try: hours=float(hours)
        except ValueError: raise ValueError('Hours must be a number from 0 to 24.')
        if not 0<=hours<=24: raise ValueError('Hours must be from 0 to 24. Use 0 for resource documents.')
        dest=None
        if source:
            if not Path(source).is_file(): raise ValueError('Document not found.')
            dest=str(Path('documents')/(uuid.uuid4().hex+Path(source).suffix))
            shutil.copy2(source,self.folder/dest)
        try:
            with self.db: self.db.execute('INSERT INTO training(member,title,day,hours,category,document,original) VALUES(?,?,?,?,?,?,?)',(member,title.strip(),day,hours,category,dest,Path(source).name if source else ''))
        except Exception:
            if dest: (self.folder/dest).unlink(missing_ok=True)
            raise
    def add_shift(self,member,title,kind,start,end,location):
        if not title.strip() or kind not in KINDS: raise ValueError('Enter a title and activity.')
        if datetime.fromisoformat(end)<=datetime.fromisoformat(start): raise ValueError('End must be after start, including overnight shifts.')
        if self.rows('SELECT id FROM shifts WHERE member=? AND start < ? AND end > ?',(member,end,start)): raise ValueError('This assignment overlaps an existing shift.')
        with self.db: self.db.execute('INSERT INTO shifts(member,title,kind,start,end,location) VALUES(?,?,?,?,?,?)',(member,title.strip(),kind,start,end,location.strip()))
