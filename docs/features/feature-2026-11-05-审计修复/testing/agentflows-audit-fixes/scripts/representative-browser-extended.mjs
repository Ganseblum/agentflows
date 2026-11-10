// Controlled fixture validation; run with ego-browser nodejs, not a second runner.
const fs=await import('node:fs/promises');
const task=await taskSpace(25);const page=task.page('p1');
const root='/Users/lihanghang1/.zcode/v2/artifacts/agentflows-fixes-20261105-184849';
const servers=JSON.parse(await fs.readFile(root+'/extended-browser-servers.json','utf8'));
const url=name=>servers.find(s=>s.name===name).baseUrl;
const observations=[];
const check=(ok,message)=>{if(!ok)throw new Error(message);};
const parse=r=>typeof r.body==='string'?JSON.parse(r.body):r.body;
const state=async()=>parse(await page.fetch('/api/state'));
const capture=async(label)=>observations.push({label,at:new Date().toISOString(),url:await page.url(),snapshot:await page.snapshot({scope:'full_page'}),receiver:await state()});
await page.goto(url('list-message'));
console.log(await page.snapshot({scope:'full_page'}));
await page.evaluate(()=>{
 const original=window.fetch.bind(window);window.audit={requests:[],holdError:false,errorReady:false,release:null};
 window.fetch=async(...args)=>{
  const input=String(args[0]);const response=await original(...args);const body=await response.clone().json();
  const entry={input,status:response.status,body,received:performance.now()};window.audit.requests.push(entry);
  if(window.audit.holdError&&input.includes('/api/list?mode=error')){
   window.audit.errorReady=true;await new Promise(resolve=>window.audit.release=resolve);entry.released=performance.now();
  }
  return response;
 };
});
// Start from an actual failure, then verify immediate clearing and a delayed old result.
await page.click('[data-testid="load-error"]',{label:'建立真实失败状态'});
await page.waitForFunction(()=>document.querySelector('[data-testid="status"]').textContent==='加载失败，请重试');
await page.evaluate(()=>{window.audit.holdError=true;});
await page.click('[data-testid="load-error"]',{label:'挂起旧失败响应'});
await page.waitForFunction(()=>window.audit.errorReady&&document.querySelector('[data-testid="status"]').textContent==='加载中…');
await capture('CARD2 old error cleared while loading; controlled old response held');
await page.click('[data-testid="load-success"]',{label:'先完成最新成功请求'});
await page.waitForFunction(()=>document.querySelector('[data-testid="status"]').textContent==='加载成功');
await page.evaluate(async()=>{window.audit.release();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));});
check(await page.evaluate(()=>document.querySelector('[data-testid="status"]').textContent==='加载成功'&&document.querySelector('[data-testid="items"]').textContent==='样本A'),'late old failure overwrote new success');
await capture('CARD2 new success survives released old failure');
// CARD3 records each real HTTP result and the visible form result, separately.
await page.fill('[data-testid="message-name"]','  测试者  ');
await page.click('[data-testid="message-submit"]',{label:'核对表单201成功结果'});
await page.waitForFunction(()=>document.querySelector('[data-testid="message-result"]').textContent==='已保存：测试者');
await capture('CARD3 valid form visible result and receiver count');
for(const value of ['', 'x'.repeat(41)]){
 const before=(await state()).messages.length;
 await page.fill('[data-testid="message-name"]',value);
 await page.click('[data-testid="message-submit"]',{label:'核对非法表单零新增'});
 await page.waitForFunction(()=>document.querySelector('[data-testid="message-result"]').textContent==='姓名需为1到40个字符');
 check((await state()).messages.length===before,'invalid form added message');
 await capture('CARD3 invalid browser '+value.length+' characters');
}
await page.fill('[data-testid="message-name"]','恢复姓名');
await page.click('[data-testid="message-submit"]',{label:'核对表单错误后恢复'});
await page.waitForFunction(()=>document.querySelector('[data-testid="message-result"]').textContent==='已保存：恢复姓名');
const api=[];
for(const input of [{},{name:null},{name:0},{name:'   '},{name:'x'.repeat(41)},{name:'x'.repeat(40)},{name:' A&B '}]){
 const before=(await state()).messages.length;
 const response=await page.fetch('/api/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
 const valid=typeof input.name==='string'&&input.name.trim().length>0&&input.name.trim().length<=40;
 check(response.status===(valid?201:422),'name contract HTTP status');
 const after=(await state()).messages.length;check(after-before===(valid?1:0),'name contract side effect');
 api.push({input,status:response.status,body:parse(response),before,after});
}
const listMessageTrace=await page.evaluate(()=>window.audit.requests);
await capture('CARD3 recovered browser and complete API boundaries');
// Fresh browser fixture: actual double click, retry and error recovery.
await page.goto(url('action-browser'));
console.log(await page.snapshot({scope:'full_page'}));
await page.evaluate(()=>{
 const original=window.fetch.bind(window);window.audit={requests:[]};
 window.fetch=async(...args)=>{const response=await original(...args);window.audit.requests.push({input:String(args[0]),status:response.status,body:await response.clone().json(),at:performance.now()});return response;};
});
const bounds=await page.evaluate(()=>{const n=document.querySelector('[data-testid="action-submit"]');n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};});
await page.mouse.click(bounds.x,bounds.y,{clickCount:2,delay:0,label:'独立夹具真实双击'});
await page.waitForFunction(()=>document.querySelector('[data-testid="action-count"]').textContent==='1');
check((await state()).count===1,'double click created more than one side effect');
await capture('CARD4 browser double click count1');
await page.click('[data-testid="action-submit"]',{label:'同键完成后再次提交'});
await page.waitForFunction(()=>!document.querySelector('[data-testid="action-submit"]').disabled);
check((await state()).count===1,'same key retry created another side effect');
await page.fill('[data-testid="action-key"]','');
await page.click('[data-testid="action-submit"]',{label:'验证输入失败按钮恢复'});
await page.waitForFunction(()=>document.querySelector('[data-testid="action-result"]').textContent==='操作键需为1到80个字符');
check(await page.evaluate(()=>!document.querySelector('[data-testid="action-submit"]').disabled),'invalid key stuck button');
check((await state()).count===1,'invalid key changed side effects');
await capture('CARD4 empty key422 no increment and button restored');
await page.fill('[data-testid="action-key"]','audit-next');
await page.click('[data-testid="action-submit"]',{label:'新键单独增加一次'});
await page.waitForFunction(()=>document.querySelector('[data-testid="action-count"]').textContent==='2');
await capture('CARD4 new browser key count2');
const browserActionTrace=await page.evaluate(()=>window.audit.requests);
// Independent API fixture starts at count0 and records every concurrent response.
await page.goto(url('action-api'));
const responses=await Promise.all([1,2].map(()=>page.fetch('/api/actions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:'audit-once'})})));
const concurrent=responses.map(r=>({status:r.status,body:parse(r)}));
check(concurrent.every(r=>r.status===200&&r.body.count===1)&&concurrent[0].body.operationId===concurrent[1].body.operationId,'same-key concurrent result differs');
const actionApi=[];
for(const key of ['audit-once','audit-next','','x'.repeat(81),'x'.repeat(80)]){
 const before=(await state()).count;
 const response=await page.fetch('/api/actions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});
 const invalid=!key||key.length>80;check(response.status===(invalid?422:200),'key length HTTP status');
 const after=(await state()).count;
 check(after-before===(invalid||key==='audit-once'?0:1),'key side effect delta');
 actionApi.push({keyLength:key.length,key:key.length<20?key:'<long fixture>',status:response.status,body:parse(response),before,after});
}
await capture('CARD4 complete API contract and side effect counts');
const result={spaceId:25,scope:'controlled local fixtures, not general host or business effectiveness',observations,listMessageTrace,api,browserActionTrace,concurrent,actionApi,status:'pass'};
await fs.writeFile(root+'/representative-browser-extended-results.json',JSON.stringify(result,null,2)+'\n');
console.log('PASS controlled late response + CARD3 browser/API + CARD4 independent browser/API variants');
console.log(await page.snapshot({scope:'full_page'}));
