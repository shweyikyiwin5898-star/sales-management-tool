"""Flask entrypoint: Python renders every screen and handles all business rules."""
from datetime import timedelta
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from domain import (STAGES, KINDS, STAFF, today_jst, staff_name, alert_for, seed_customers,
                    validate_workspace, profile_fields, create_customer, add_activity)
from i18n import language, localized, translator

app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
NAV = ('dashboard','customers','followup','history','team','settings')


def make_context(payload):
    lang = language(payload.get('lang'))
    t = translator(lang)
    today = today_jst()
    data = validate_workspace(payload.get('customers', seed_customers(today)))
    state = dict(lang=lang, store=payload.get('store','ginza'), staff=payload.get('staff','win'),
                 nav=payload.get('nav','dashboard'), filter=payload.get('filter','all'),
                 query=str(payload.get('query',''))[:120], stage=payload.get('stage','all'),
                 sort=payload.get('sort','priority'), view=payload.get('view','list'))
    if state['nav'] not in NAV: state['nav']='dashboard'
    if state['store'] not in ('ginza','osaka'): state['store']='ginza'
    if state['staff'] not in (*STAFF,'all'): state['staff']='win'
    def present(c):
        item={**c, **{k: localized(c.get(k,''),lang) for k in ('name','kana','email','phone','birthday','size','interests','note','purchase')}}
        item['alert']=alert_for(c,today)
        item['advisor']=staff_name(c['staff'],lang)
        item['activities']=[{**a,'text':localized(a['text'],lang)} for a in c['activities']]
        item['latest']=item['activities'][0]['text'] if item['activities'] else t('no_activity')
        item['initials']=item['name'][0:1]
        return item
    in_store=[present(c) for c in data if c['store']==state['store']]
    clients=[c for c in in_store if state['staff']=='all' or c['staff']==state['staff']]
    attention=sorted([c for c in clients if c['alert']['priority']<3],key=lambda c:c['alert']['priority'])
    stats={'all':len(clients),'attention':len(attention),'reply':sum(c['pending_reply'] for c in clients),'done':sum(c['alert']['key']=='done' for c in clients)}
    shown=[]
    for c in clients:
        if state['nav']=='followup' and c['alert']['priority']>=3: continue
        if state['filter']=='attention' and c['alert']['priority']>=3: continue
        if state['filter']=='reply' and not c['pending_reply']: continue
        if state['filter']=='done' and c['alert']['key']!='done': continue
        if state['stage']!='all' and c['stage']!=state['stage']: continue
        if state['query'].casefold() not in ' '.join((c['name'],c['kana'],c['interests'],c['latest'])).casefold(): continue
        shown.append(c)
    shown.sort(key=lambda c:c['name'] if state['sort']=='name' else c['next_date'] if state['sort']=='date' else c['alert']['priority'])
    history=sorted([{**a,'client':c} for c in clients for a in c['activities']],key=lambda a:a['date'],reverse=True)
    team=[{'id':s,'name':staff_name(s,lang),'count':sum(c['staff']==s for c in in_store),'attention':sum(c['staff']==s and c['alert']['priority']<3 for c in in_store)} for s in STAFF]
    return dict(t=t,lang=lang,state=state,customers=data,shown=shown,clients=clients,focus=attention[:3],stats=stats,history=history,team=team,
                stages=STAGES,kinds=KINDS,staff=STAFF,staff_name=lambda s:staff_name(s,lang),today=today.isoformat(),future=(today+timedelta(days=3)).isoformat(),
                navs=NAV,localized=lambda v:localized(v,lang),present=present)


@app.get('/')
def index():
    context=make_context({'lang':request.args.get('lang','ja')})
    return render_template('index.html',**context)


@app.get('/assets/<path:filename>')
def assets(filename):
    # Local development route; Vercel serves public/assets directly from its CDN.
    return send_from_directory('public/assets',filename)


@app.get('/api/health')
def health():
    return jsonify(status='ok',framework='Flask',language='Python',version='2.0.0')


def payload_json():
    payload=request.get_json()
    if not isinstance(payload,dict): raise ValueError('payload')
    return payload


@app.post('/api/workspace')
def workspace():
    payload=payload_json()
    context=make_context(payload)
    data=context['customers']
    action=payload.get('action','render')
    fields=payload.get('fields',{})
    if not isinstance(fields,dict): raise ValueError('fields')
    if action=='reset':
        data=seed_customers()
    elif action=='create':
        data=[create_customer({**fields,'store':context['state']['store']}),*data]
        payload.update(nav='customers',filter='all',query='',stage='all',staff=fields['staff'])
    elif action in ('profile','activity'):
        found=False
        updated=[]
        for c in data:
            if c['id']==payload.get('id'):
                found=True
                c={**c,**profile_fields(fields)} if action=='profile' else add_activity(c,fields)
            updated.append(c)
        if not found: raise ValueError('unknown customer')
        data=updated
    elif action!='render':
        raise ValueError('action')
    context=make_context({**payload,'customers':data})
    return jsonify(html=render_template('workspace.html',**context),customers=data,state=context['state'],message=context['t']('created' if action=='create' else 'reset_done' if action=='reset' else 'saved'))


@app.post('/api/dialog')
def dialog():
    payload=payload_json()
    context=make_context(payload)
    kind=payload.get('kind','client')
    if kind not in ('client','new','line','reset'): raise ValueError('dialog')
    chosen=next((c for c in context['customers'] if c['id']==payload.get('id')),None)
    if kind=='client' and chosen is None: raise ValueError('customer')
    tab=payload.get('tab','conversation')
    return jsonify(html=render_template('dialog.html',**context,kind=kind,tab=tab,client=context['present'](chosen) if chosen else None))


@app.errorhandler(ValueError)
@app.errorhandler(KeyError)
@app.errorhandler(TypeError)
@app.errorhandler(BadRequest)
@app.errorhandler(RequestEntityTooLarge)
def invalid(_error):
    return jsonify(error='invalid'),400


@app.after_request
def no_cache(response):
    if request.path.startswith('/api/') or request.path=='/':
        response.headers['Cache-Control']='no-store'
    return response


if __name__=='__main__':
    app.run(host='127.0.0.1',port=5001,debug=False)
