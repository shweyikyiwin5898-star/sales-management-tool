/* UI transport only: Python owns validation, alerts, filtering and HTML rendering. */
const KEY='maison-python-v2';
const bootstrap=JSON.parse(document.getElementById('bootstrap').textContent);
let customers=bootstrap.customers;
let state=bootstrap.state;
let requestNumber=0, dialogNumber=0, pendingMutation=false, searchTimer, toastTimer;
const root=document.getElementById('workspace');
const modalRoot=document.getElementById('modal-root');
const strings={
  error:['処理できませんでした。接続と入力内容を確認してお試しください。','Something went wrong. Check your input and connection, then try again.'],
  invalid:['入力内容を確認してください。氏名・日付・連絡内容が必要です。','Please check the required name, dates, and conversation details.'],
  storage:['ブラウザに保存できません。再読み込みで変更が失われます。','Browser storage is unavailable. Changes will be lost on reload.']
};
function message(key){return strings[key]?.[state.lang==='en'?1:0]||strings.error[state.lang==='en'?1:0];}
function toast(text){const el=document.getElementById('toast');el.textContent=text;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),4000);}
function persist(){try{localStorage.setItem(KEY,JSON.stringify({version:2,customers,lang:state.lang}));}catch{toast(message('storage'));}}
async function post(path,payload){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await response.json();if(!response.ok)throw new Error(data.error||'error');return data;}
async function render(action='render',extra={}){
  if(pendingMutation&&action==='render')return;
  const number=++requestNumber;
  const focused=document.activeElement?.id==='client-search';
  const selection=focused?document.activeElement.selectionStart:null;
  const scroll=window.scrollY;
  document.getElementById('progress').classList.add('busy');
  try{
    const data=await post('/api/workspace',{...state,customers,action,...extra});
    if(number!==requestNumber)return false;
    customers=data.customers;state=data.state;
    root.innerHTML=data.html;
    document.documentElement.lang=state.lang;
    persist();
    if(focused){const input=document.getElementById('client-search');input?.focus({preventScroll:true});if(input&&selection!==null)input.setSelectionRange(selection,selection);}
    window.scrollTo(0,scroll);
    if(action!=='render')toast(data.message);
    return true;
  }catch(error){if(number===requestNumber){toast(message(error.message));throw error;}}
  finally{if(number===requestNumber)document.getElementById('progress').classList.remove('busy');}
}
function closeDialog(){dialogNumber++;const d=document.getElementById('app-dialog');d?.close();modalRoot.replaceChildren();}
async function openDialog(kind,id='',tab='conversation'){
  const number=++dialogNumber;
  try{const data=await post('/api/dialog',{...state,customers,kind,id,tab});if(number!==dialogNumber)return;document.getElementById('app-dialog')?.close();modalRoot.innerHTML=data.html;const d=document.getElementById('app-dialog');d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeDialog();}});d.addEventListener('cancel',()=>{dialogNumber++;});d.showModal();}catch(error){toast(message(error.message));}
}
function navigate(nav){state={...state,nav,filter:'all',query:'',stage:'all'};render().then(()=>window.scrollTo({top:0,behavior:'instant'})).catch(()=>{});}
document.addEventListener('click',async event=>{
  const button=event.target.closest('button');if(!button)return;
  if(button.hasAttribute('data-close'))return closeDialog();
  if(pendingMutation)return;
  if(button.dataset.nav)return navigate(button.dataset.nav);
  if(button.dataset.dialog)return openDialog(button.dataset.dialog);
  if(button.dataset.client)return openDialog('client',button.dataset.client);
  if(button.dataset.detailTab)return openDialog('client',button.dataset.id,button.dataset.detailTab);
  if(button.dataset.advisor){state.staff=button.dataset.advisor;return navigate('customers');}
  if(button.dataset.filter){state.filter=button.dataset.filter;state.nav='customers';}
  else if(button.dataset.tab){state.filter=button.dataset.tab;}
  else if(button.dataset.view){state.view=button.dataset.view;}
  else if(button.hasAttribute('data-clear')){state={...state,query:'',stage:'all',filter:'all',staff:'all'};}
  else if(button.hasAttribute('data-reset')){pendingMutation=true;button.disabled=true;try{await render('reset');closeDialog();}catch{}finally{pendingMutation=false;button.disabled=false;}return;}
  else return;
  render().catch(()=>{});
});
document.addEventListener('change',event=>{const key=event.target.dataset.state;if(!key)return;state[key]=event.target.value;if(key==='store'){state.staff=state.store==='ginza'?'win':'all';state.query='';state.filter='all';state.stage='all';}render().catch(()=>{});});
document.addEventListener('input',event=>{if(event.target.id!=='client-search')return;state.query=event.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(()=>render().catch(()=>{}),250);});
document.addEventListener('submit',async event=>{const form=event.target.closest('form[data-action]');if(!form)return;event.preventDefault();if(pendingMutation)return;const fields=Object.fromEntries(new FormData(form));if(fields.name!==undefined&&!fields.name.trim()){form.querySelector('.form-error').textContent=message('invalid');return;}pendingMutation=true;const submit=form.querySelector('[type=submit]');submit.disabled=true;try{await render(form.dataset.action,{id:form.dataset.id,fields});if(form.dataset.action==='create')closeDialog();else await openDialog('client',form.dataset.id,form.dataset.action==='profile'?'profile':'conversation');}catch(error){form.querySelector('.form-error').textContent=message(error.message);}finally{pendingMutation=false;submit.disabled=false;}});
async function initialize(){try{const saved=JSON.parse(localStorage.getItem(KEY)||'null');if(saved?.version===2&&Array.isArray(saved.customers)){customers=saved.customers;state.lang=['ja','en'].includes(saved.lang)?saved.lang:'ja';try{await render();}catch(error){if(error.message==='invalid'){customers=bootstrap.customers;await render();}}}else persist();}catch{toast(message('storage'));}}
initialize();
