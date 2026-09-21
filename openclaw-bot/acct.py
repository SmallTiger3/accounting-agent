#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, subprocess, sys, datetime, re

DB_HOST = '172.17.0.1'
DB_USER = 'mxj_xh'
DB_NAME = 'accounting_agent'
DB_PASS = '0723'

def psql(sql, vars_=None, tuples=True):
    cmd = ['psql', '-h', DB_HOST, '-U', DB_USER, '-d', DB_NAME, '-X', '-q', '-A', '-F', chr(1)]
    if tuples:
        cmd.append('-t')
    if vars_:
        for k, v in vars_.items():
            cmd.append('-v')
            cmd.append(k + '=' + (v if v is not None else ''))
    env = {'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'PGPASSWORD': DB_PASS, 'LANG': 'C.UTF-8'}
    r = subprocess.run(cmd, input=sql.encode("utf-8"), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        return None, r.stderr.decode('utf-8', 'replace').strip()
    return r.stdout.decode('utf-8', 'replace'), None

def out(obj):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)

def ensure_tables():
    sql = '''
    CREATE TABLE IF NOT EXISTS bot_users (
      id serial PRIMARY KEY,
      wx_id varchar(128) UNIQUE NOT NULL,
      display_name varchar(100),
      created_at timestamptz DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS bot_transactions (
      id serial PRIMARY KEY,
      user_id int NOT NULL REFERENCES bot_users(id),
      txn_type varchar(10) NOT NULL CHECK (txn_type IN ('expense','income')),
      amount numeric(12,2) NOT NULL CHECK (amount > 0),
      category varchar(50) NOT NULL,
      note varchar(200),
      occurred_at timestamptz DEFAULT now(),
      created_at timestamptz DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_bot_txn_user_time ON bot_transactions(user_id, occurred_at);
    '''
    _, err = psql(sql)
    if err:
        out({'ok': False, 'error': 'init_db_failed', 'detail': err[:300]})

def cmd_ensure_user(wx_id, name=None):
    if not wx_id or len(wx_id) > 128:
        out({'ok': False, 'error': 'bad_wx_id'})
    if name and len(name) > 100:
        name = name[:100]
    rows, err = psql(
        "WITH ins AS (INSERT INTO bot_users (wx_id, display_name) VALUES (:'wx', :'nm') ON CONFLICT (wx_id) DO UPDATE SET display_name = COALESCE(EXCLUDED.display_name, bot_users.display_name) RETURNING id, display_name, (xmax = 0) AS inserted) SELECT id, display_name, inserted FROM ins;",
        {'wx': wx_id, 'nm': name})
    if err:
        out({'ok': False, 'error': 'db_error', 'detail': err[:300]})
    parts = rows.strip().split(chr(1))
    out({'ok': True, 'user_id': int(parts[0]), 'display_name': (parts[1] if parts[1] != '' else None), 'created': parts[2] == 't'})

def cmd_add(user_id, txn_type, amount, category, note=None):
    if txn_type not in ('expense', 'income'):
        out({'ok': False, 'error': 'bad_type'})
    try:
        amt = float(amount)
        if amt <= 0 or amt > 999999999:
            raise ValueError()
        amt = round(amt, 2)
    except (ValueError, TypeError):
        out({'ok': False, 'error': 'bad_amount'})
    if not category or len(category) > 50:
        out({'ok': False, 'error': 'bad_category'})
    if note and len(note) > 200:
        note = note[:200]
    rows, err = psql(
        "INSERT INTO bot_transactions (user_id, txn_type, amount, category, note) VALUES (:'uid'::int, :'tp', :'amt'::numeric, :'cat', :'nte') RETURNING id;",
        {'uid': str(int(user_id)), 'tp': txn_type, 'amt': ('%.2f' % amt), 'cat': category, 'nte': note})
    if err:
        out({'ok': False, 'error': 'db_error', 'detail': err[:300]})
    out({'ok': True, 'id': int(rows.strip())})

def cmd_month(user_id, month=None):
    m = month or datetime.date.today().strftime('%Y-%m')
    if not re.match(r'^\d{4}-\d{2}$', m):
        out({'ok': False, 'error': 'bad_month'})
    rows, err = psql(
        "SELECT txn_type, category, sum(amount) FROM bot_transactions WHERE user_id = :'uid'::int AND to_char(occurred_at, 'YYYY-MM') = :'mth' GROUP BY 1, 2 ORDER BY 3 DESC;",
        {'uid': str(int(user_id)), 'mth': m})
    if err:
        out({'ok': False, 'error': 'db_error', 'detail': err[:300]})
    by_cat, total_exp, total_inc = [], 0.0, 0.0
    for line in rows.strip().splitlines():
        if not line.strip():
            continue
        tp, cat, s = line.split(chr(1))
        v = float(s)
        if tp == 'expense':
            total_exp += v
        else:
            total_inc += v
        by_cat.append({'type': tp, 'category': cat, 'amount': round(v, 2)})
    out({'ok': True, 'month': m, 'total_expense': round(total_exp, 2), 'total_income': round(total_inc, 2), 'by_category': by_cat})

def cmd_recent(user_id, n=10):
    n = max(1, min(int(n), 50))
    rows, err = psql(
        "SELECT id, txn_type, amount, category, COALESCE(note,''), to_char(occurred_at, 'MM-DD HH24:MI') FROM bot_transactions WHERE user_id = :'uid'::int ORDER BY id DESC LIMIT :'nn'::int;",
        {'uid': str(int(user_id)), 'nn': str(n)})
    if err:
        out({'ok': False, 'error': 'db_error', 'detail': err[:300]})
    items = []
    for line in rows.strip().splitlines():
        if not line.strip():
            continue
        i, tp, amt, cat, note, tm = line.split(chr(1))
        items.append({'id': int(i), 'type': tp, 'amount': float(amt), 'category': cat, 'note': note, 'time': tm})
    out({'ok': True, 'items': items})

def cmd_delete(user_id, txn_id):
    _, err = psql(
        "DELETE FROM bot_transactions WHERE id = :'tid'::int AND user_id = :'uid'::int;",
        {'tid': str(int(txn_id)), 'uid': str(int(user_id))})
    if err:
        out({'ok': False, 'error': 'db_error', 'detail': err[:300]})
    out({'ok': True})

USAGE = '''用法: acct.py <command> [args]
  ensure-user <wx_id> [display_name]
  add <user_id> <expense|income> <amount> <category> [note]
  month <user_id> [YYYY-MM]
  recent <user_id> [n]
  delete <user_id> <id>
输出: 单行 JSON'''

def main():
    if len(sys.argv) < 2:
        print(USAGE); sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    ensure_tables()
    try:
        if cmd == 'ensure-user' and len(args) in (1, 2):
            cmd_ensure_user(args[0], args[1] if len(args) == 2 else None)
        elif cmd == 'add' and len(args) in (4, 5):
            cmd_add(args[0], args[1], args[2], args[3], args[4] if len(args) == 5 else None)
        elif cmd == 'month' and len(args) in (1, 2):
            cmd_month(args[0], args[1] if len(args) == 2 else None)
        elif cmd == 'recent' and len(args) in (1, 2):
            cmd_recent(args[0], args[1])
        elif cmd == 'delete' and len(args) == 2:
            cmd_delete(args[0], args[1])
        else:
            print(USAGE); sys.exit(1)
    except ValueError:
        out({'ok': False, 'error': 'bad_args'})

if __name__ == '__main__':
    main()
