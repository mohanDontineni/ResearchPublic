"""Exact ROV decision-set differencing. No third-party dependencies.

Intervals are inclusive integer indices of canonical prefixes at a fixed length.
AS0 contributes coverage but never a valid nonzero-origin route.
"""
from collections import defaultdict
import ipaddress, json

BITS = {4: 32, 6: 128}
CAPS = {4: [24, 28, 32], 6: [48, 56, 64, 128]}

def normalize(records):
    rows = set()
    for r in records:
        n = ipaddress.ip_network(r['prefix'], strict=True)
        a = int(str(r['asn']).removeprefix('AS'))
        m = int(r.get('maxLength', n.prefixlen))
        if not (0 <= a < 2**32 and n.prefixlen <= m <= n.max_prefixlen):
            raise ValueError('Invalid VRP: ' + repr(r))
        rows.add((n.version, a, int(n.network_address), n.prefixlen, m))
    return rows

def read(path):
    return normalize(json.loads(path.read_text())['roas'])

def merge(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(b, out[-1][1]))
        else:
            out.append((a, b))
    return out

def subtract(left, right):
    """left minus right, both disjoint sorted inclusive intervals."""
    out = []; j = 0
    for a, b in left:
        while j < len(right) and right[j][1] < a: j += 1
        k = j; cursor = a
        while k < len(right) and right[k][0] <= b:
            c, d = right[k]
            if c > cursor: out.append((cursor, min(b, c-1)))
            cursor = max(cursor, d+1)
            if cursor > b: break
            k += 1
        if cursor <= b: out.append((cursor, b))
    return out

def size(intervals): return sum(b-a+1 for a,b in intervals)

def group(rows):
    groups = defaultdict(set)
    for v,a,n,p,m in rows:
        if a: groups[v,a].add((n,p,m))
    return dict(groups)

def levels(rows, width):
    out = [[] for _ in range(width+1)]
    for n,p,m in rows:
        for length in range(p, m+1):
            start = n >> (width-length)
            out[length].append((start, start+(1 << (length-p))-1))
    return [merge(x) for x in out]

def prefix(v, index, length):
    cls = ipaddress.IPv4Address if v == 4 else ipaddress.IPv6Address
    return str(cls(index << (BITS[v]-length))) + '/' + str(length)

def diff_authorizations(old, new, incremental=True, witnesses=True):
    """Inputs are grouped positive-origin VRPs. Timing includes group comparison."""
    out = {str(v): {'gains': [0]*(BITS[v]+1), 'losses': [0]*(BITS[v]+1),
                   'origins': [], 'witnesses': []} for v in BITS}
    for v,a in sorted(old.keys() | new.keys()):
        before, after = old.get((v,a), set()), new.get((v,a), set())
        changed = before != after
        if incremental and not changed: continue
        aa, bb = levels(before, BITS[v]), levels(after, BITS[v])
        gains = []; losses = []; f = out[str(v)]
        for length, (x,y) in enumerate(zip(aa,bb)):
            plus, minus = subtract(y,x), subtract(x,y)
            ng,nl = size(plus),size(minus);gains.append(ng);losses.append(nl)
            f['gains'][length] += ng; f['losses'][length] += nl
            if witnesses:
                for direction, intervals in [('gain',plus),('loss',minus)]:
                    if intervals:
                        f['witnesses'].append({'kind':'A','direction':direction,'prefix':prefix(v,intervals[0][0],length),'asn':a})
        if changed:
            f['origins'].append({'asn':a,'tuples_added':len(after-before),'tuples_removed':len(before-after),'gains':gains,'losses':losses})
    return out

def coverage_bases(rows, v):
    """Remove contained bases. NEVER combine adjacent siblings into a parent."""
    width = BITS[v]; bases = sorted({(n,p) for vv,a,n,p,m in rows if vv==v})
    out=[]; end=-1
    for n,p in bases:
        if n > end:
            out.append((n,p)); end = n + (1 << (width-p))-1
    return out

def diff_coverage(old, new, witnesses=True):
    out={}
    for v,width in BITS.items():
        aa,bb = coverage_bases(old,v),coverage_bases(new,v)
        f={'gains':[],'losses':[],'witnesses':[],'old_bases':len(aa),'new_bases':len(bb)}
        for length in range(width+1):
            x,y = [merge([(n>>(width-length),(n>>(width-length))+(1<<(length-p))-1) for n,p in bases if p<=length]) for bases in (aa,bb)]
            plus,minus=subtract(y,x),subtract(x,y)
            f['gains'].append(size(plus));f['losses'].append(size(minus))
            if witnesses:
                for direction, intervals in [('gain',plus),('loss',minus)]:
                    if intervals:f['witnesses'].append({'kind':'C','direction':direction,'prefix':prefix(v,intervals[0][0],length)})
        out[str(v)]=f
    return out

class Validator:
    """Independent ancestor lookup; no union, difference or interval encoding."""
    def __init__(self, rows):
        self.entries=defaultdict(dict)
        for v,a,n,p,m in rows:
            d=self.entries[v,p,n];d[a]=max(m,d.get(a,-1))
    def classify(self, route, asn):
        n=ipaddress.ip_network(route,strict=True);address=int(n.network_address)
        covered=False
        for length in range(n.prefixlen,-1,-1):
            shift=n.max_prefixlen-length;start=(address>>shift)<<shift
            d=self.entries.get((n.version,length,start))
            if d is not None:
                covered=True
                if asn and d.get(asn,-1)>=n.prefixlen:return 'Valid'
        return 'Invalid' if covered else 'NotFound'

def verify_witnesses(auth, cov, old, new):
    a,b=Validator(old),Validator(new);checked=[]
    for v in ('4','6'):
        for w in auth[v]['witnesses']+cov[v]['witnesses']:
            w=dict(w);asn=w.get('asn',4294967295)
            x,y=a.classify(w['prefix'],asn),b.classify(w['prefix'],asn)
            if w['kind']=='A':
                assert ((x!='Valid' and y=='Valid') if w['direction']=='gain' else (x=='Valid' and y!='Valid')),w
            else:
                assert ((x=='NotFound' and y!='NotFound') if w['direction']=='gain' else (x!='NotFound' and y=='NotFound')),w
            w.update(asn=asn,before=x,after=y);checked.append(w)
    return checked
