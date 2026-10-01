export const stages = ['来店', '商品提案', '検討中', '再来店', '購入', '購入後フォロー'] as const;
export type Stage = typeof stages[number];
export type Activity = { id: string; date: string; type: '送信' | '受信' | '接客' | 'メモ'; text: string };
export type Customer = { id: string; store: string; staff: string; name: string; kana: string; email: string; phone: string; birthday: string; size: string; tier: string; interests: string[]; stage: Stage; lastContact: string; nextDate: string; pendingReply: boolean; note: string; purchase: string; total: number; activities: Activity[] };
export const staff = ['高橋 美咲', '佐藤 蓮', '田中 葵', '鈴木 陽菜', '伊藤 翔', '渡辺 結衣', '山本 湊', '中村 凛', '小林 大和', '加藤 杏'];
export const stores = [{ id: 'ginza', name: '銀座店', en: 'GINZA MAISON' }, { id: 'osaka', name: '大阪店', en: 'OSAKA MAISON · DEMO' }];
export const todayJST = () => new Intl.DateTimeFormat('sv-SE', {timeZone: 'Asia/Tokyo'}).format(new Date());
export function shiftDate(date: string, days: number) { const d = new Date(date + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + days); return d.toISOString().slice(0,10); }
export function daysBetween(a: string,b: string) { return Math.round((Date.parse(b+'T12:00:00Z')-Date.parse(a+'T12:00:00Z'))/86400000); }
export function alertFor(c: Customer, today: string) {
  if(c.pendingReply) return {key:'reply', label:'返信が必要', tone:'red', detail:'お客様からのご連絡に返信しましょう', priority:0};
  if(c.nextDate && c.nextDate < today) return {key:'overdue', label:'連絡期限超過', tone:'red', detail:`予定日から${daysBetween(c.nextDate,today)}日経過`, priority:1};
  if((c.nextDate && c.nextDate <= shiftDate(today,1)) || daysBetween(c.lastContact,today)>=14) return {key:'due', label:'連絡推奨', tone:'amber', detail:c.nextDate === today ? '本日がフォロー予定日です' : '次のご連絡におすすめのタイミング', priority:2};
  if(c.lastContact === today) return {key:'done', label:'対応済み', tone:'green', detail:'本日の対応が完了しています', priority:4};
  return {key:'normal', label:'フォロー予定', tone:'neutral', detail:'次回のフォロー予定を確認', priority:3};
}
export function seedCustomers(today: string): Customer[] {
  const names = ['山田 さくら','石川 恵美','小川 直子','松本 健太','森田 愛','井上 真由','藤井 翔太','中島 由美','木村 沙織','清水 拓也','林 美月','斎藤 誠','岡田 彩','長谷川 梓','近藤 悠','村上 千尋','藤田 光','石井 梨花','橋本 蘭','池田 健','山口 葵','阿部 玲奈','前田 智子','吉田 律','山崎 菜々'];
  const kana = ['ヤマダ サクラ','イシカワ エミ','オガワ ナオコ','マツモト ケンタ','モリタ アイ','イノウエ マユ','フジイ ショウタ','ナカジマ ユミ'];
  const interests = [['レザーグッズ','新作バッグ'],['シューズ','プレタポルテ'],['ジュエリー','ギフト'],['メンズ','トラベル'],['レザーグッズ','スモールレザー'],['フレグランス','ギフト']];
  const messages = ['先日ご紹介いただいたバッグの別のお色も拝見できますか？','週末に伺えそうです。サイズの取り置きは可能でしょうか。','大切な方へのギフトをお探し。ラッピングとお渡し日をご案内予定。','新作のトラベルコレクションにご関心。入荷時のご案内をご希望。','先日はご来店ありがとうございました。お使い心地はいかがでしょうか。','秋冬の新作をご紹介。落ち着いた色味のアイテムがお好み。'];
  return names.map((name,i) => {
    const last = shiftDate(today,-[3,2,8,5,0,4,18,6,2,16][i%10]);
    const next = shiftDate(today,[-1,0,0,1,14,5,-3,8,3,0][i%10]);
    return {id:`customer-${i+1}`,store:i<20?'ginza':'osaka',staff:i<8?staff[0]:staff[(i-7)%10],name,kana:kana[i]||'デモ カスタマー',email:`client${i+1}@example.com`,phone:'090-0000-'+String(i+1).padStart(4,'0'),birthday:`1990-${String(i%12+1).padStart(2,'0')}-15`,size:i%2?'シューズ 37 / ウェア 36':'シューズ 38 / ウェア 38',tier:i%3===0?'VIC':'Regular',interests:interests[i%6],stage:stages[[2,3,1,2,5,4,1,0][i%8]],lastContact:last,nextDate:next,pendingReply:i%10<2,note:i%2?'ゆっくりと商品を選ばれることを好まれます。週末の午後がご来店しやすい時間帯。':'ベージュやブラウンなどのニュートラルカラーがお好み。新作のご案内をご希望。',purchase:i%2?'レザーウォレット · 2026年9月':'レザーハンドバッグ · 2026年8月',total:[528000,286000,154000,682000,396000][i%5],activities:[{id:`a-${i}-1`,date:last,type:i%10<2?'受信':'接客',text:messages[i%6]},{id:`a-${i}-2`,date:shiftDate(last,-7),type:'送信',text:'ご来店のお礼と、気になられていたアイテムの詳細をご案内しました。'}]};
  });
}
