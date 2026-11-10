// Local, disposable fixture for the pre-registered CARD-2/3/4 acceptance paths.
const http = require('node:http');
const messages = [];
const operations = new Map();
let requests = 0;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const page = `<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>Agentflow 代表任务验收</title><style>
body{font:16px system-ui,sans-serif;max-width:850px;margin:40px auto;padding:0 20px;color:#172235;background:#f7f9fc}
section{padding:20px;margin:18px 0;background:white;border:1px solid #dce2eb;border-radius:10px}
button,input{font:inherit;padding:9px;margin:5px}button:focus-visible,input:focus-visible{outline:3px solid #2670d8}input{max-width:100%}p[role=status]{min-height:24px}
</style><h1>代表任务验收</h1><p>本机临时夹具，无真实账户或业务数据。</p>
<section><h2>列表四态</h2><button data-testid="load-success">加载样本</button><button data-testid="load-empty">加载空列表</button><button data-testid="load-error">模拟加载失败</button><p data-testid="status" role="status">待操作</p><ul data-testid="items"></ul></section>
<section><h2>消息表单</h2><form id="message-form" novalidate><label for="name">姓名（1到40个字符）</label><input id="name" data-testid="message-name" autocomplete="off"><button data-testid="message-submit">保存消息</button></form><p data-testid="message-result" role="status"></p></section>
<section><h2>同键重复提交</h2><form id="action-form" novalidate><label for="key">操作键</label><input id="key" data-testid="action-key" value="audit-once"><button data-testid="action-submit">执行操作</button></form><p data-testid="action-result" role="status"></p><p>副作用计数：<span data-testid="action-count">0</span></p></section>
<script>
const byId = id => document.querySelector('[data-testid="'+id+'"]');
let generation=0;
for(const mode of ['success','empty','error'])byId('load-'+mode).onclick=async()=>{
 const current=++generation;byId('status').textContent='加载中…';byId('items').replaceChildren();
 const response=await fetch('/api/list?mode='+mode);const data=await response.json();if(current!==generation)return;
 if(!response.ok){byId('status').textContent=data.error;return;}
 byId('status').textContent=data.items.length?'加载成功':'暂无数据';
 for(const item of data.items){const li=document.createElement('li');li.textContent=item;byId('items').append(li);}
};
let saving=false;
document.querySelector('#message-form').onsubmit=async event=>{
 event.preventDefault();if(saving)return;saving=true;byId('message-submit').disabled=true;byId('message-result').textContent='保存中…';
 try{const response=await fetch('/api/messages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:byId('message-name').value})});const data=await response.json();byId('message-result').textContent=response.ok?'已保存：'+data.name:data.error;}
 catch{byId('message-result').textContent='连接失败，请重试';}
 finally{saving=false;byId('message-submit').disabled=false;}
};
let submitting=false;
document.querySelector('#action-form').onsubmit=async event=>{
 event.preventDefault();if(submitting)return;submitting=true;byId('action-submit').disabled=true;byId('action-result').textContent='执行中…';
 try{const response=await fetch('/api/actions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:byId('action-key').value})});const data=await response.json();byId('action-result').textContent=response.ok?'操作完成：'+data.operationId:data.error;if(response.ok)byId('action-count').textContent=String(data.count);}
 catch{byId('action-result').textContent='连接失败，请重试';}
 finally{submitting=false;byId('action-submit').disabled=false;}
};
</script></html>`;
function send(res, code, data) {
  res.writeHead(code, {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});
  res.end(JSON.stringify(data));
}
async function body(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > 4096) throw new Error('request too large');
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  if (req.method === 'GET' && url.pathname === '/') {
    res.writeHead(200, {'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});
    return res.end(page);
  }
  if (req.method === 'GET' && url.pathname === '/api/list') {
    await sleep(80);
    const mode=url.searchParams.get('mode');
    return mode==='error' ? send(res,503,{error:'加载失败，请重试'}) : send(res,200,{items:mode==='empty'?[]:['样本A']});
  }
  if (req.method === 'GET' && url.pathname === '/api/state') {
    return send(res,200,{messages,operations:[...operations.values()],count:operations.size,requests});
  }
  if (req.method !== 'POST') return send(res,404,{error:'Not found'});
  let data;
  try { data=await body(req); } catch { return send(res,400,{error:'请求必须为合法JSON'}); }
  if (url.pathname === '/api/messages') {
    const name=typeof data.name==='string'?data.name.trim():'';
    if (!name || Array.from(name).length>40) return send(res,422,{error:'姓名需为1到40个字符'});
    const message={id:messages.length+1,name};messages.push(message);
    await sleep(80);
    return send(res,201,message);
  }
  if (url.pathname === '/api/actions') {
    requests++;
    const key=typeof data.key==='string'?data.key.trim():'';
    if (!key || key.length>80) return send(res,422,{error:'操作键需为1到80个字符'});
    if (!operations.has(key)) operations.set(key,{operationId:operations.size+1,key});
    const operation=operations.get(key);await sleep(100);
    return send(res,200,{...operation,count:operations.size});
  }
  return send(res,404,{error:'Not found'});
});
server.listen(0,'127.0.0.1',()=>console.log(JSON.stringify({baseUrl:'http://127.0.0.1:'+server.address().port})));
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));
