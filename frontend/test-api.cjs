// Run with: node frontend/test-api.cjs
// Exercise the API client without network, browser storage or application credentials.
const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const source=readFileSync(__dirname+'/app.js','utf8').split("window.addEventListener('hashchange',route);")[0];
const values=new Map();
let requests=[], responses=[];
const sandbox={Headers,URL,URLSearchParams,setTimeout,clearTimeout,console,
 sessionStorage:{getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)},
 fetch:async(path,options)=>{requests.push({path,options});const next=responses.shift();if(!next)throw Error('Unexpected request');return new Response(next.body===undefined?null:JSON.stringify(next.body),{status:next.status,headers:{'Content-Type':'application/json'}});}
};
vm.createContext(sandbox);
vm.runInContext(source+'\nglobalThis.client={api,esc,safeURL};',sandbox);
(async()=>{
 const {api,esc,safeURL}=sandbox.client;
 assert.equal(safeURL('javascript:alert(1)'),'');assert.equal(esc('<img>'),'&lt;img&gt;');
 responses=[{status:204}];assert.equal(await api('/photos/1',{method:'DELETE'}),null);
 responses=[{status:422,body:{detail:[{loc:['body','text'],msg:'Too short'}]}}];await assert.rejects(()=>api('/comments',{method:'POST',json:{text:''}}),/text: Too short/);
 values.set('photoshare.access','expired');values.set('photoshare.refresh','refresh');
 responses=[{status:401},{status:200,body:{access_token:'new',refresh_token:'rotated'}},{status:200,body:{id:1}}];
 assert.equal((await api('/users/me')).id,1);
 assert.equal(requests.at(-2).path,'/api/auth/refresh_token');
 assert.equal(requests.at(-1).options.headers.get('Authorization'),'Bearer new');
 assert.equal(values.get('photoshare.refresh'),'rotated');
 console.log('PASS: URL safety, text escaping, 204 handling, validation errors, JWT refresh and retry');
})().catch(error=>{console.error(error);process.exitCode=1;});
