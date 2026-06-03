import { useState, useEffect, useRef, useCallback } from 'react';
import { healthCheck, fetchAuthStatus, fetchAchData, sendQuestion, getAuthUrl } from './api';

function Icon({ n, className = '' }) {
  const s = { stroke:'currentColor', fill:'none', strokeWidth:'1.8', strokeLinecap:'round', strokeLinejoin:'round' };
  const cls = `shrink-0 ${className}`;
  switch (n) {
    case 'logo': return <svg viewBox="0 0 20 20" {...s} className={cls}><rect x="2.5" y="2.5" width="15" height="15" rx="3.5"/><path d="M7 10h6M10 7v6"/></svg>;
    case 'send': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M14 2L3 8l4 1L8 13l6-11z"/><path d="M7 9l4-4"/></svg>;
    case 'plus': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M8 3v10M3 8h10"/></svg>;
    case 'zap': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M8.5 2.5l-4 6.5h3.5l-.5 4.5L12 7H8.5L8.5 2.5z"/></svg>;
    case 'search': return <svg viewBox="0 0 16 16" {...s} className={cls}><circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>;
    case 'tool': return <svg viewBox="0 0 16 16" {...s} className={cls}><circle cx="8" cy="8" r="2" fill="currentColor"/><path d="M8 3l1.5 2-1.5 2 1.5 2-1.5 2 1.5 2-1.5 2" opacity=".25"/></svg>;
    case 'bug': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M5.5 2.5L7 4M9 4l1.5-1.5"/><path d="M6.5 6V5a1.5 1.5 0 013 0v1"/><path d="M8 12a3 3 0 003-3V8a3 3 0 00-6 0v1a3 3 0 003 3z"/><path d="M8 12V8M4.5 7H3M13 7h-1.5M3 10.5a2 2 0 002 2M13 10.5a2 2 0 01-2 2"/></svg>;
    case 'chart': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M2.5 13V7.5M6 13V5M9.5 13v-4M13 13V6"/><path d="M1 13h14"/></svg>;
    case 'book': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M3.5 3.5h9a.5.5 0 01.5.5v9a.5.5 0 01-.5.5h-9a.5.5 0 01-.5-.5V4a.5.5 0 01.5-.5z"/><path d="M6 7h4M6 9.5h4M6 12h2"/></svg>;
    case 'doc': return <svg viewBox="0 0 16 16" {...s} className={cls}><path d="M10.5 2.5H4.5a1 1 0 00-1 1v9a1 1 0 001 1h7a1 1 0 001-1V5.5l-2-3z"/><path d="M10.5 2.5V5.5h3"/><path d="M6 8.5h4M6 11h2.5"/></svg>;
    case 'server': return <svg viewBox="0 0 16 16" {...s} className={cls}><rect x="2.5" y="3" width="11" height="3.5" rx="1"/><rect x="2.5" y="9.5" width="11" height="3.5" rx="1"/><circle cx="4.5" cy="4.75" r=".5" fill="currentColor"/><circle cx="4.5" cy="11.25" r=".5" fill="currentColor"/></svg>;
    default: return <svg viewBox="0 0 16 16" {...s} className={cls}><circle cx="8" cy="8" r="4.5"/><path d="M8 3.5v9M3.5 8h9"/></svg>;
  }
}

const SKILLS = [
  { id:'presale', icon:'zap', label:'售前咨询', desc:'产品对比·方案推荐·权益', prompt:'我需要做WPS产品方案和功能对比分析' },
  { id:'aftersale', icon:'tool', label:'售后问题诊断', desc:'Bug排查·工单分析·根因定位', prompt:'WPS功能异常排查与诊断' },
  { id:'deploy', icon:'server', label:'运维部署', desc:'部署规划·环境配置·优化', prompt:'私有化部署资源规划' },
  { id:'kb', icon:'book', label:'知识库检索', desc:'技术文档·操作指南·实践', prompt:'查找WPS相关技术文档' },
  { id:'feedback', icon:'chart', label:'反馈分析', desc:'崩溃趋势·用户反馈', prompt:'分析最近的用户崩溃反馈' },
  { id:'bug', icon:'bug', label:'Bug分析', desc:'代码影响·改动分析·追踪', prompt:'追踪某个Bug的全链路根因' },
];
const CARDS = [
  { icon:'doc', title:'文件打不开', desc:'格式不支持·损坏·加密', prompt:'WPS打不开文件，提示文件格式不支持' },
  { icon:'zap', title:'激活失败', desc:'许可证错误·试用到期', prompt:'WPS激活失败，显示许可证验证错误' },
  { icon:'bug', title:'崩溃闪退', desc:'内核崩溃·内存溢出', prompt:'WPS打开大文件时崩溃闪退kernelbase' },
  { icon:'search', title:'字体问题', desc:'字体缺失·渲染异常', prompt:'WPS字体显示不一致仿宋GB2312变方框' },
  { icon:'server', title:'部署规划', desc:'服务器配置·信创环境', prompt:'私有化WPS365部署需要什么服务器' },
  { icon:'book', title:'知识搜索', desc:'技术文档·最佳实践', prompt:'搜索WPS相关技术文档操作指南' },
];
function timeStr() { return new Date().toLocaleTimeString('zh-CN', { hour:'2-digit', minute:'2-digit' }); }
function md(t) {
  let s = String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/^- (.+)$/gm, '<li>$1</li>').replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>').replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  s = s.replace(/^---$/gm, '<hr>').replace(/\n{2,}/g, '</p><p>').replace(/\n/g, '<br>');
  return '<p>' + s + '</p>';
}

export default function App() {
  const [status,setStatus] = useState('loading');
  const [user,setUser] = useState('');
  const [msgs,setMsgs] = useState([]);
  const [typing,setTyping] = useState(false);
  const [view,setView] = useState('welcome');
  const [active,setActive] = useState('');
  const [busy,setBusy] = useState(false);
  const inp = useRef(null);
  const end = useRef(null);
  useEffect(()=>{end.current?.scrollIntoView({behavior:'smooth'})},[msgs,typing]);
  useEffect(()=>{(async()=>{
    const h = await healthCheck();
    if(h?.status==='ok'){setStatus(h.token_valid?'ok':'warn');const a=await fetchAuthStatus();if(a.authorized){setStatus('ok');setUser(a.user?.nickName||a.user?.userName||'');}}
    else setStatus('off');
  })()},[]);
  const send = useCallback(async(text)=>{
    if(!text.trim()||busy)return;
    const q = text.trim();
    setMsgs(p=>[...p,{role:'user',text:q,time:timeStr()}]);setView('chat');setTyping(true);setBusy(true);
    if(inp.current){inp.current.value='';inp.current.style.height='auto';}
    const r = await sendQuestion(q);setTyping(false);setBusy(false);
    const c = r.category||{skill:'知识库检索'};setActive(c.category||'');
    if(r.error){setMsgs(p=>[...p,{role:'bot',text:'分析模块暂不可用',time:timeStr(),skill:'错误'}]);return;}
    const d = r.data;let parts=[];
    if(d.answer)parts.push(d.answer);else parts.push('暂无匹配方案');
    if(d.tracks?.length){parts.push('\n---\n### 检索轨道');d.tracks.forEach(t=>parts.push('- '+t));}
    if(d.sources?.length){parts.push('\n---\n### 数据来源');d.sources.forEach(s=>parts.push('- '+s.name+' — '+s.detail));}
    setMsgs(p=>[...p,{role:'bot',text:parts.join('\n'),time:timeStr(),skill:c.skill||'知识库检索'}]);
  },[busy]);
  const kd = e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(e.target.value)}};
  const ah = e=>{const t=e.target;t.style.height='auto';t.style.height=Math.min(t.scrollHeight,150)+'px'};
  const stat = {ok:{dot:'#30d158',label:'实时模式 — 已授权'},warn:{dot:'#ff9f0a',label:'未登录'},off:{dot:'#86909c',label:'离线'}}[status]||{dot:'#86909c',label:'检测中...'};

  const S = {display:'flex',alignItems:'center',justifyContent:'center'};
  const row = {display:'flex',flexDirection:'row'};
  const col = {display:'flex',flexDirection:'column'};
  const f1 = {flex:1};
  const fw = {width:'100%'};

  return (
    <div style={{height:'100vh',display:'flex',flexDirection:'column',background:'#f2f3f5'}}>

      {/* Header */}
      <div style={{...{background:'#fff',borderBottom:'1px solid #e5e6eb',flexShrink:0}}}>
        <div style={{...row,alignItems:'center',justifyContent:'space-between',height:48,padding:'0 24px'}}>
          <div style={{...row,alignItems:'center',gap:10}}>
            <span style={{width:28,height:28,borderRadius:8,background:'#2468f2',color:'#fff',...S}}><Icon n="logo" style={{width:14,height:14}} /></span>
            <span style={{fontSize:14,fontWeight:600,color:'#1d2129'}}>WPS百晓生</span>
            <span style={{fontSize:11,color:'#86909c',display:'none'}} className="sm-inline">智能产品问题诊断助手</span>
          </div>
          <div style={{...row,alignItems:'center',gap:8}}>
            {status==='warn'&&<button onClick={()=>window.location.href=getAuthUrl()} style={{fontSize:12,padding:'6px 12px',borderRadius:6,border:'none',background:'rgba(36,104,242,0.06)',color:'#2468f2',fontWeight:500,cursor:'pointer'}}>登录</button>}
            <span style={{...row,alignItems:'center',gap:6,fontSize:11,color:'#86909c'}}>
              <span style={{width:6,height:6,borderRadius:'50%',background:stat.dot}} />
              {stat.label}
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div style={{flex:1,display:'flex',overflow:'hidden',width:'100%'}}>

        {/* Sidebar */}
        <aside style={{width:220,flexShrink:0,background:'#fff',borderRight:'1px solid #e5e6eb',...col}}>
          <div style={{fontSize:12,fontWeight:600,color:'#86909c',textTransform:'uppercase',padding:'12px 16px',borderBottom:'1px solid #f0f0f5',letterSpacing:1}}>
            智能技能路由
          </div>
          <nav style={{flex:1,overflowY:'auto',padding:12}}>
            {SKILLS.map(sk=>{
              const on = active===sk.id;
              return (
                <button key={sk.id} onClick={()=>send(sk.prompt)}
                  style={{...row,alignItems:'center',gap:10,width:'100%',padding:'10px 12px',borderRadius:8,border:'none',textAlign:'left',fontSize:13,cursor:'pointer',
                    background:on?'rgba(36,104,242,0.06)':'transparent',
                    color:on?'#2468f2':'#4e5969',
                    transition:'all 0.2s',marginBottom:4}}>
                  <span style={{width:28,height:28,borderRadius:6,...S,background:on?'rgba(36,104,242,0.06)':'#f2f3f5',color:on?'#2468f2':'#86909c',fontSize:13}}>
                    <Icon n={sk.icon} className="w-3.5 h-3.5" />
                  </span>
                  <div style={{minWidth:0}}>
                    <div style={{fontSize:13,fontWeight:500}}>{sk.label}</div>
                    <div style={{fontSize:10,color:'#86909c',marginTop:1,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{sk.desc}</div>
                  </div>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main */}
        <main style={{flex:1,...col,overflow:'hidden',minWidth:0}}>

          {/* Chat bar */}
          {view==='chat'&&(
            <div style={{flexShrink:0,borderBottom:'1px solid #f0f0f5',background:'#fff'}}>
              <div style={{...row,alignItems:'center',gap:12,padding:'0 16px',height:40}}>
                <button onClick={()=>{setView('welcome');setActive('');setMsgs([])}}
                  style={{...row,alignItems:'center',gap:4,fontSize:12,color:'#86909c',border:'none',background:'none',cursor:'pointer',padding:0}}>
                  <Icon n="plus" className="w-3 h-3" /> 新对话
                </button>
                <span style={{fontSize:12,color:'#86909c'}}>/</span>
                <span style={{fontSize:12,color:'#86909c',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{msgs.filter(m=>m.role==='bot').slice(-1)[0]?.skill||''}</span>
              </div>
            </div>
          )}

          {/* Welcome */}
          {view==='welcome'&&(
            <div style={{flex:1,...col,alignItems:'center',justifyContent:'center',overflowY:'auto',padding:'40px 24px'}}>
              <div style={{maxWidth:900,width:'100%',...col,alignItems:'center',gap:28}}>
                <div style={{...row,alignItems:'center',gap:6,padding:'4px 12px',borderRadius:999,background:'rgba(36,104,242,0.06)',fontSize:12,fontWeight:500,color:'#2468f2'}}>
                  <Icon n="zap" className="w-3 h-3" /> AI 驱动
                </div>
                <div style={{textAlign:'center'}}>
                  <h1 style={{fontSize:24,fontWeight:700,color:'#1d2129',margin:'0 0 8px'}}>有什么 WPS 问题需要帮助？</h1>
                  <p style={{fontSize:14,color:'#4e5969',lineHeight:1.6,maxWidth:520,margin:0}}>输入任何关于 WPS 的问题，我会自动路由到最合适的技能模块，从知识库、工单系统和文档中检索精准方案。</p>
                </div>
                <div style={{display:'grid',gridTemplateColumns:'repeat(3, 1fr)',gap:16,width:'100%',maxWidth:900}}>
                  {CARDS.map((c,i)=>(
                    <button key={i} onClick={()=>send(c.prompt)}
                      style={{background:'#fff',border:'1px solid #e5e6eb',borderRadius:12,padding:'16px 12px',textAlign:'center',cursor:'pointer',transition:'all 0.2s'}}>
                      <div style={{width:36,height:36,borderRadius:8,...S,margin:'0 auto 10px',background:'rgba(36,104,242,0.06)',color:'#2468f2',fontSize:14}}>
                        <Icon n={c.icon} className="w-[18px] h-[18px]" />
                      </div>
                      <div style={{fontSize:14,fontWeight:600,color:'#1d2129',marginBottom:2}}>{c.title}</div>
                      <div style={{fontSize:11,color:'#86909c',lineHeight:1.4}}>{c.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Chat */}
          {view==='chat'&&(
            <div style={{flex:1,overflowY:'auto',padding:'20px 24px'}}>
              <div style={{maxWidth:800,marginLeft:'auto',marginRight:'auto'}}>
              {msgs.map((m,i)=>{
                const u=m.role==='user';
                return (
                  <div key={i} style={{...row,justifyContent:u?'flex-end':'flex-start',marginBottom:16}}>
                    <div style={{maxWidth:'75%',minWidth:0}}>
                      <div style={{padding:'12px 16px',fontSize:14,lineHeight:1.6,background:u?'#2468f2':'#fff',color:u?'#fff':'#1d2129',borderRadius:u?'14px 14px 4px 14px':'14px 14px 14px 4px',border:u?'none':'1px solid #e5e6eb'}}>
                        {!u&&m.skill&&(
                          <div style={{...row,alignItems:'center',gap:6,marginBottom:8,paddingBottom:8,borderBottom:'1px solid #f0f0f5'}}>
                            <Icon n="zap" className="w-2.5 h-2.5" style={{color:'#2468f2'}} />
                            <span style={{fontSize:10,fontWeight:500,color:'#2468f2'}}>{m.skill}</span>
                          </div>
                        )}
                        <div className={!u?'md':'font-medium'} dangerouslySetInnerHTML={{__html:u?m.text:md(m.text)}} />
                      </div>
                      <div style={{...row,justifyContent:u?'flex-end':'flex-start',fontSize:10,color:'#86909c',marginTop:6,padding:'0 4px'}}>{m.time}</div>
                    </div>
                  </div>
                );
              })}
              {typing&&(
                <div style={{...row,justifyContent:'flex-start',marginBottom:16}}>
                  <div style={{background:'#fff',border:'1px solid #e5e6eb',borderRadius:'14px 14px 14px 4px',padding:'14px 16px'}}>
                    <div style={{...row,alignItems:'center',gap:6}}>
                      <span className="dot" /><span className="dot" /><span className="dot" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={end} />
            </div>
            </div>
          )}

          {/* Input */}
          <div style={{flexShrink:0,background:'#fff',borderTop:'1px solid #e5e6eb',padding:'12px 24px'}}>
            <div style={{maxWidth:800,marginLeft:'auto',marginRight:'auto',...row,alignItems:'center',background:'#fff',border:'1px solid #e5e6eb',borderRadius:12,padding:'0 14px'}}>
              <textarea ref={inp} rows="1" placeholder="输入 WPS 相关问题..."
                onKeyDown={kd} onInput={ah} disabled={busy}
                style={{flex:1,border:'none',outline:'none',resize:'none',fontSize:14,lineHeight:'20px',color:'#1d2129',background:'transparent',maxHeight:150,minHeight:36,padding:'8px 0',fontFamily:'inherit'}}
              />
              <button onClick={()=>send(inp.current?.value||'')} disabled={busy}
                style={{...S,width:30,height:30,borderRadius:'50%',border:'none',background:'#2468f2',color:'#fff',cursor:'pointer',flexShrink:0,transition:'background 0.2s'}}>
                <Icon n="send" className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}