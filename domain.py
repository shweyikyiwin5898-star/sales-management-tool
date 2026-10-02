"""顧客管理の業務ロジック。Flaskに依存せず単体テストできる。"""
from copy import deepcopy
from datetime import date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

STAGES = ('visit', 'proposal', 'considering', 'return', 'purchased', 'aftercare')
KINDS = ('sent', 'received', 'meeting', 'memo')
STAFF = ['win', 'sato', 'tanaka', 'suzuki', 'ito', 'watanabe', 'yamamoto', 'nakamura', 'kobayashi', 'kato']
STAFF_NAMES = [('ウィン','Win'), ('佐藤 蓮','Ren Sato'), ('田中 葵','Aoi Tanaka'), ('鈴木 陽菜','Hina Suzuki'), ('伊藤 翔','Sho Ito'), ('渡辺 結衣','Yui Watanabe'), ('山本 湊','Minato Yamamoto'), ('中村 凛','Rin Nakamura'), ('小林 大和','Yamato Kobayashi'), ('加藤 杏','An Kato')]

def today_jst():
    return datetime.now(ZoneInfo('Asia/Tokyo')).date()

def staff_name(identifier, lang='ja'):
    return STAFF_NAMES[STAFF.index(identifier)][lang == 'en'] if identifier in STAFF else identifier

def alert_for(customer, today=None):
    """複数条件がある場合は、返信→期限超過→連絡推奨→完了の順。"""
    today = today or today_jst()
    next_date = date.fromisoformat(customer['next_date'])
    last = date.fromisoformat(customer['last_contact'])
    if customer['pending_reply']:
        return {'key': 'reply', 'tone': 'red', 'priority': 0}
    if next_date < today:
        return {'key': 'overdue', 'tone': 'red', 'priority': 1}
    if next_date <= today + timedelta(days=1) or (today - last).days >= 14:
        return {'key': 'due', 'tone': 'amber', 'priority': 2}
    if last == today:
        return {'key': 'done', 'tone': 'green', 'priority': 4}
    return {'key': 'normal', 'tone': 'neutral', 'priority': 3}

def text_field(data, key, limit=2000, required=False):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(key)
    value = value.strip()
    if required and not value:
        raise ValueError(key)
    return value

def date_field(value):
    if not isinstance(value, str):
        raise ValueError('date')
    parsed = date.fromisoformat(value)
    if len(value) != 10 or not 1900 <= parsed.year <= 2200:
        raise ValueError('date')
    return parsed

def profile_fields(data):
    result = {key: text_field(data, key, 2000 if key in ('note', 'purchase') else 120, key == 'name')
              for key in ('name','kana','email','phone','birthday','size','interests','purchase','note')}
    if result['email'] and ('@' not in result['email'] or ' ' in result['email']):
        raise ValueError('email')
    if result['birthday']:
        date_field(result['birthday'])
    if data.get('staff') not in STAFF or data.get('stage') not in STAGES:
        raise ValueError('staff or stage')
    date_field(data.get('next_date'))
    result.update(staff=data['staff'], stage=data['stage'], next_date=data['next_date'])
    return result

def create_customer(data, today=None):
    today = today or today_jst()
    result = profile_fields({**data, 'stage': data.get('stage', 'visit')})
    if data.get('store') not in ('ginza','osaka'):
        raise ValueError('store')
    result.update(id=str(uuid4()), store=data['store'], tier='Regular', last_contact=today.isoformat(), pending_reply=False,
                  activities=[{'id':str(uuid4()),'date':today.isoformat(),'type':'meeting','text':result['note'] or {'ja':'初回のご来店。顧客ノートを作成しました。','en':'First visit. A new client notebook was created.'}}])
    return result

def add_activity(customer, data, today=None):
    today = today or today_jst()
    activity_date = date_field(data.get('date'))
    date_field(data.get('next_date'))
    if activity_date > today or data.get('type') not in KINDS or data.get('stage') not in STAGES:
        raise ValueError('activity')
    text = text_field(data, 'text', required=True)
    result = deepcopy(customer)
    result['activities'].insert(0, {'id':str(uuid4()), 'date':data['date'], 'type':data['type'], 'text':text})
    result['activities'].sort(key=lambda a: a['date'], reverse=True)
    latest = next((a for a in result['activities'] if a['type'] != 'memo'), None)
    if latest:
        result['last_contact'] = latest['date']
        result['pending_reply'] = latest['type'] == 'received'
    result.update(next_date=data['next_date'], stage=data['stage'])
    return result

def validate_workspace(customers):
    """ブラウザから渡されるデモデータの構造を検証する。"""
    if not isinstance(customers,list) or len(customers)>300:
        raise ValueError('customers')
    seen=set()
    for c in customers:
        if not isinstance(c,dict) or not isinstance(c.get('id'),str) or c['id'] in seen:
            raise ValueError('id')
        seen.add(c['id'])
        if c.get('store') not in ('ginza','osaka') or c.get('staff') not in STAFF or c.get('stage') not in STAGES or not isinstance(c.get('pending_reply'), bool):
            raise ValueError('customer')
        date_field(c.get('next_date')); date_field(c.get('last_contact'))
        for key in ('name','kana','email','phone','birthday','size','interests','note','purchase'):
            v=c.get(key)
            if not isinstance(v,(str,dict)) or (isinstance(v,dict) and any(not isinstance(x,str) for x in v.values())):
                raise ValueError(key)
        if not isinstance(c.get('activities'),list) or len(c['activities'])>500:
            raise ValueError('activities')
        for a in c['activities']:
            if not isinstance(a,dict) or a.get('type') not in KINDS or not isinstance(a.get('text'),(str,dict)):
                raise ValueError('activity')
            date_field(a.get('date'))
    return customers

def seed_customers(today=None):
    today=today or today_jst()
    names=[('山田 さくら','Sakura Yamada'),('石川 恵美','Emi Ishikawa'),('小川 直子','Naoko Ogawa'),('松本 健太','Kenta Matsumoto'),('森田 愛','Ai Morita'),('井上 真由','Mayu Inoue'),('藤井 翔太','Shota Fujii'),('中島 由美','Yumi Nakajima'),('木村 沙織','Saori Kimura'),('清水 拓也','Takuya Shimizu'),('林 美月','Mizuki Hayashi'),('斎藤 誠','Makoto Saito'),('岡田 彩','Aya Okada'),('長谷川 梓','Azusa Hasegawa'),('近藤 悠','Yu Kondo'),('村上 千尋','Chihiro Murakami'),('藤田 光','Hikaru Fujita'),('石井 梨花','Rika Ishii'),('橋本 蘭','Ran Hashimoto'),('池田 健','Ken Ikeda'),('山口 葵','Aoi Yamaguchi'),('阿部 玲奈','Reina Abe'),('前田 智子','Tomoko Maeda'),('吉田 律','Ritsu Yoshida'),('山崎 菜々','Nana Yamazaki')]
    interests=[('レザーグッズ / 新作バッグ','Leather goods / New bags'),('シューズ / プレタポルテ','Shoes / Ready-to-wear'),('ジュエリー / ギフト','Jewelry / Gifts'),('メンズ / トラベル','Menswear / Travel'),('スモールレザーグッズ','Small leather goods'),('フレグランス / ギフト','Fragrances / Gifts')]
    notes=[('先日ご紹介いただいたバッグの別のお色も拝見できますか？','Could I see the bag you showed me in another color?'),('週末に伺えそうです。サイズの取り置きは可能でしょうか。','I could visit this weekend. Could you reserve my size?'),('ギフトをお探し。ラッピングとお渡し日をご案内予定。','Looking for a gift. Follow up on wrapping and collection.'),('新作トラベルコレクションの入荷案内をご希望。','Would like to hear when the new travel collection arrives.'),('先日はありがとうございました。お使い心地はいかがでしょうか。','Thank you for visiting. How are you enjoying your new piece?'),('秋冬の新作をご紹介。ニュートラルカラーがお好み。','Introduced the autumn collection. Prefers neutral colors.')]
    result=[]
    for i,(ja,en) in enumerate(names):
        last=(today-timedelta(days=[3,2,8,5,0,4,18,6,2,16][i%10])).isoformat()
        next_date=(today+timedelta(days=[-1,0,0,1,14,5,-3,8,3,0][i%10])).isoformat()
        result.append(dict(id=f'demo-{i+1}',store='ginza' if i<20 else 'osaka',staff='win' if i<8 else STAFF[(i-7)%10],name={'ja':ja,'en':en},kana=en,email=f'client{i+1}@example.com',phone=f'090-0000-{i+1:04}',birthday=f'1990-{i%12+1:02}-15',size='37 / 36',tier='VIC' if i%3==0 else 'Regular',interests=dict(zip(('ja','en'),interests[i%6])),stage=STAGES[[2,3,1,2,5,4,1,0][i%8]],last_contact=last,next_date=next_date,pending_reply=i%10<2,note={'ja':'落ち着いた色味がお好み。週末の午後にご来店しやすい。','en':'Prefers understated colors. Weekend afternoons work best for visits.'},purchase={'ja':'レザーウォレット · 2026年9月','en':'Leather wallet · September 2026'},activities=[{'id':f'a-{i}','date':last,'type':'received' if i%10<2 else 'meeting','text':dict(zip(('ja','en'),notes[i%6]))}]))
    return result
