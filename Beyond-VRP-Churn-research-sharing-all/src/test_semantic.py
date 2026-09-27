import ipaddress, random, unittest
from semantic import *

def brute(rows):
    authorized=set();covered=set()
    for v,a,n,p,m in rows:
        cls=ipaddress.IPv4Network if v==4 else ipaddress.IPv6Network
        base=cls((n,p))
        for length in range(p,BITS[v]+1):
            for child in base.subnets(new_prefix=length):
                covered.add(child)
                if a and length<=m:authorized.add((child,a))
    return authorized,covered

class SemanticsTests(unittest.TestCase):
    def check_pair(self, old, new):
        a,c=brute(old);b,d=brute(new)
        actual=diff_authorizations(group(old),group(new));coverage=diff_coverage(old,new)
        self.assertEqual(actual,diff_authorizations(group(old),group(new),False))
        for v,width in BITS.items():
            for length in range(width+1):
                for name,expected in [('gains',b-a),('losses',a-b)]:
                    self.assertEqual(actual[str(v)][name][length],sum(n.version==v and n.prefixlen==length for n,asn in expected))
                for name,expected in [('gains',d-c),('losses',c-d)]:
                    self.assertEqual(coverage[str(v)][name][length],sum(n.version==v and n.prefixlen==length for n in expected))
        verify_witnesses(actual,coverage,old,new)
    def test_random_1000_pairs(self):
        rng=random.Random(20260926)
        for case in range(1000):
            v=4 if case%2==0 else 6;width=BITS[v];root=ipaddress.ip_network('192.0.2.0/24' if v==4 else '2001:db8::/120')
            def sample():
                out=set()
                for _ in range(rng.randrange(0,18)):
                    p=rng.randrange(width-8,width+1);m=rng.randrange(p,width+1)
                    n=int(root.network_address)+(rng.randrange(1<<(p-root.prefixlen))<<(width-p))
                    out.add((v,rng.choice([0,1,2,4294967295]),n,p,m))
                return out
            with self.subTest(case=case):self.check_pair(sample(),sample())
    def test_sibling_coverage_cannot_collapse(self):
        old=normalize([{'prefix':'192.0.2.0/24','asn':0}])
        new=normalize([{'prefix':p,'asn':0} for p in ['192.0.2.0/25','192.0.2.128/25']])
        self.check_pair(old,new)
        self.assertEqual(sum(diff_coverage(old,new)['4']['losses']),1)
    def test_redundant_tuple_change(self):
        old=normalize([{'prefix':'192.0.2.0/24','asn':1,'maxLength':32}])
        new=old|normalize([{'prefix':'192.0.2.0/25','asn':1,'maxLength':30}])
        self.check_pair(old,new)
        self.assertEqual(sum(diff_authorizations(group(old),group(new))['4']['gains']),0)
    def test_as0_only_change(self):
        new=normalize([{'prefix':'192.0.2.0/24','asn':0}]);self.check_pair(set(),new)
        self.assertEqual(sum(diff_coverage(set(),new)['4']['gains']),511)
    def test_origin_swap_and_net_cancellation(self):
        old=normalize([{'prefix':'192.0.2.0/24','asn':1}]);new=normalize([{'prefix':'192.0.2.0/24','asn':2}])
        self.check_pair(old,new)
    def test_duplicate_and_bad_records(self):
        r={'prefix':'192.0.2.0/24','asn':'AS1','maxLength':28}
        self.assertEqual(normalize([r,r]),normalize([r]))
        for bad in [dict(r,maxLength=23),dict(r,asn=-1),dict(r,prefix='192.0.2.1/24'),dict(r,asn=2**32)]:
            with self.assertRaises(ValueError):normalize([bad])
    def test_interval_subtraction(self):
        for a,b in [([(1,10)],[(2,3),(5,20)]), ([(1,3),(5,7)],[(2,6)]),([],[(1,3)])]:
            expand=lambda x:{i for l,r in x for i in range(l,r+1)}
            self.assertEqual(expand(subtract(a,b)),expand(a)-expand(b))

if __name__=='__main__':unittest.main(verbosity=2)
