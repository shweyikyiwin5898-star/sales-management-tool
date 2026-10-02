import unittest
from copy import deepcopy
from datetime import date, timedelta
from app import app
from domain import alert_for, add_activity, seed_customers, validate_workspace
from i18n import LABELS

class RulesTest(unittest.TestCase):
    def setUp(self):
        self.today=date(2026,10,2)
        self.c={**seed_customers(self.today)[0], 'pending_reply':False, 'last_contact':'2026-10-01','next_date':'2026-10-10'}
    def test_priority(self):
        self.assertEqual(alert_for({**self.c,'pending_reply':True,'next_date':'2026-10-01'},self.today)['key'],'reply')
        self.assertEqual(alert_for({**self.c,'last_contact':'2026-10-02','next_date':'2026-10-01'},self.today)['key'],'overdue')
    def test_due_boundary(self):
        for offset,expected in ((0,'due'),(1,'due'),(2,'normal')):
            self.assertEqual(alert_for({**self.c,'next_date':(self.today+timedelta(days=offset)).isoformat()},self.today)['key'],expected)
    def test_inactivity_boundary(self):
        for days,expected in ((13,'normal'),(14,'due')):
            self.assertEqual(alert_for({**self.c,'last_contact':(self.today-timedelta(days=days)).isoformat()},self.today)['key'],expected)
    def test_done(self):
        self.assertEqual(alert_for({**self.c,'last_contact':self.today.isoformat()},self.today)['key'],'done')
    def test_activity_and_backdated_reply(self):
        c=seed_customers(self.today)[0]
        fields={'date':'2026-10-02','next_date':'2026-10-10','stage':'return','text':'Test','type':'received'}
        c=add_activity(c,fields,self.today)
        self.assertTrue(c['pending_reply'])
        c=add_activity(c,{**fields,'type':'sent','date':'2026-10-01'},self.today)
        self.assertTrue(c['pending_reply'])
        c=add_activity(c,{**fields,'type':'memo'},self.today)
        self.assertTrue(c['pending_reply'])
        c=add_activity(c,{**fields,'type':'sent'},self.today)
        self.assertFalse(c['pending_reply'])
        self.assertEqual(alert_for(c,self.today)['key'],'done')
    def test_invalid_future_and_blank(self):
        f={'date':'2026-10-03','next_date':'2026-10-10','stage':'visit','type':'sent','text':'hello'}
        with self.assertRaises(ValueError):add_activity(self.c,f,self.today)
        with self.assertRaises(ValueError):add_activity(self.c,{**f,'date':'2026-10-02','text':'  '},self.today)
    def test_seed(self):
        data=seed_customers(self.today)
        self.assertEqual(len(data),25)
        self.assertEqual(len({c['id'] for c in data}),25)
        self.assertEqual(sum(c['store']=='ginza' for c in data),20)
        validate_workspace(data)
    def test_locale_parity(self):
        self.assertTrue(all(len(v)==2 and all(v) for v in LABELS.values()))

class RoutesTest(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.data=seed_customers()
    def test_health_and_python_page(self):
        self.assertEqual(self.client.get('/api/health').json['language'],'Python')
        r=self.client.get('/')
        self.assertEqual(r.status_code,200)
        self.assertIn('ウィン',r.text)
        self.assertNotIn('_next/',r.text)
    def test_every_screen_in_both_languages(self):
        for lang in ('ja','en'):
            for nav in ('dashboard','customers','followup','history','team','settings'):
                with self.subTest(lang=lang,nav=nav):
                    r=self.client.post('/api/workspace',json={'customers':self.data,'lang':lang,'nav':nav})
                    self.assertEqual(r.status_code,200)
                    self.assertNotIn('customers_sub',r.json['html'])
                    self.assertIn('Win' if lang=='en' else 'ウィン',r.json['html'])
    def test_create_profile(self):
        fields={'name':'Demo Guest','staff':'win','store':'ginza','next_date':'2026-10-20','email':'demo@example.com'}
        r=self.client.post('/api/workspace',json={'customers':self.data,'action':'create','fields':fields,'lang':'en'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json['customers']),26)
        c=r.json['customers'][0]
        r=self.client.post('/api/workspace',json={'customers':[c],'action':'profile','id':c['id'],'fields':{**fields,'stage':'proposal','note':'Gift wrapping'}})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json['customers'][0]['note'],'Gift wrapping')
    def test_filter_and_store(self):
        r=self.client.post('/api/workspace',json={'customers':self.data,'store':'osaka','staff':'all','lang':'en'})
        self.assertIn('Aoi Yamaguchi',r.json['html'])
        self.assertNotIn('Sakura Yamada',r.json['html'])
        r=self.client.post('/api/workspace',json={'customers':self.data,'query':'UNMATCHED'})
        self.assertIn('該当するお客様はいません',r.json['html'])
    def test_invalid_requests(self):
        for data in ([],{'customers':'invalid'},{'customers':self.data,'action':'create','fields':{'name':'  '}}):
            self.assertEqual(self.client.post('/api/workspace',json=data).status_code,400)
    def test_dialogs_and_escaping(self):
        for lang in ('ja','en'):
            for kind in ('client','new','line','reset'):
                r=self.client.post('/api/dialog',json={'customers':self.data,'id':self.data[0]['id'],'kind':kind,'lang':lang})
                self.assertEqual(r.status_code,200)
        data=deepcopy(self.data);data[0]['name']='<script>alert(1)</script>'
        r=self.client.post('/api/workspace',json={'customers':data})
        self.assertNotIn('<script>alert(1)</script>',r.json['html'])
        self.assertIn('&lt;script&gt;',r.json['html'])
    def test_assets(self):
        for filename in ('style.css','app.js','icon.svg'):
            with self.client.get('/assets/'+filename) as response:
                self.assertEqual(response.status_code,200)

if __name__=='__main__': unittest.main()
