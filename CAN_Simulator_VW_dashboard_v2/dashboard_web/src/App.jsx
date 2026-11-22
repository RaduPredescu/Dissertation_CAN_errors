import React, {useEffect,useMemo,useState} from 'react'

const scenarioLabels = {
 healthy:['Healthy','Fără anomalii','◌'],
 abs_fr_sensor:['ABS sensor FR','Semnal absent roată față dreapta','⚙'],
 abs_fr_encoder:['ABS encoder FR','Semnal intermitent la roată','◈'],
 dpf_restriction:['DPF restriction','Presiune diferențială ridicată','≋'],
 egr_flow:['EGR mismatch','Debit recirculare insuficient','⌁'],
 dsg_overheat:['DSG overheat','Temperatură transmisie','♨'],
 awd_clutch:['4MOTION fault','Cuplare punte spate','✳'],
 low_voltage:['Low voltage','Alimentare 12 V','ϟ'],
 compound:['Compound','12 V + comunicare ABS','⌘'],
}
const zoneLabels = {
 engine:'Motor / EGR',dpf:'Filtru particule DPF',dsg:'Transmisie DSG',
 awd:'4MOTION / punte spate',battery:'Sistem 12 V',brakes:'ECU ABS / rețea CAN',
 wheel_fl:'Roată față stânga',wheel_fr:'Roată față dreapta',
 wheel_rl:'Roată spate stânga',wheel_rr:'Roată spate dreapta',
}
const signalMeta={
 speed:['Viteză vehicul','km/h','#59cbdc',1],rpm:['Turație motor','rpm','#968cf7',0],
 voltage:['Tensiune 12 V','V','#e5b05d',2],coolant:['Temperatură răcire','°C','#f8877a',0],
 wheel_fl:['Roată FL','km/h*','#52c3d7',1],wheel_fr:['Roată FR','km/h*','#f67c73',1],
 wheel_rl:['Roată RL','km/h*','#81baa1',1],wheel_rr:['Roată RR','km/h*','#b4a8f6',1],
 dpf_pressure:['Presiune diferențială DPF','mbar*','#f2a372',0],
 soot:['Încărcare DPF estimată','%*','#e9c16c',1],
 egr_command:['EGR comandat','%*','#59d1c5',1],egr_actual:['EGR feedback','%*','#f6a47a',1],
 dsg_temp:['Temperatură DSG','°C*','#f78e9f',0],
 awd_requested:['Cerere cuplare AWD','%*','#71bce5',0],
 awd_actual:['Feedback cuplare AWD','%*','#c69beb',0],
}
const telemetryGroups={
 overview:['speed','rpm','voltage','coolant'],
 abs:['wheel_fl','wheel_fr','wheel_rl','wheel_rr'],
 emissions:['dpf_pressure','soot','egr_command','egr_actual'],
 drivetrain:['dsg_temp','awd_requested','awd_actual','speed'],
}
const seconds=t=>Number(t??0).toFixed(1)+'s'
const asNumber=(value,digits=1)=>Number(value).toLocaleString('ro-RO',{maximumFractionDigits:digits})
async function fetchJSON(url,options){const r=await fetch(url,options);const body=await r.json().catch(()=>({}));if(!r.ok) throw new Error(body.detail||'Eroare HTTP '+r.status);return body}
function readLatest(points,time){let val=null;for(const x of points||[]){if(x.t<=time+.001)val=x.v;else break}return val}

function CarDiagram({issues,selected,onSelect}){
 const severity=zone=>issues.filter(e=>e.zone===zone).some(e=>e.severity==='critical')?'critical':issues.some(e=>e.zone===zone)?'warning':null
 const chosen=zone=>selected===zone
 const wheel=(zone,x,y,label)=>{
   const active=severity(zone)
   return <g key={zone} role="button" tabIndex="0" aria-label={'Inspectează '+zoneLabels[zone]}
      className={'vw-click-target '+(chosen(zone)?'chosen':'')+' '+(active||'')}
      onClick={()=>onSelect(zone)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(zone)}}}>
      {active&&<rect x={x-8} y={y-8} width="62" height="77" rx="15" fill={active==='critical'?'#e96e65':'#e2ab5d'} fillOpacity=".16" stroke={active==='critical'?'#f78375':'#d5a45f'} strokeDasharray="5 4" strokeWidth="2"/>}
      <rect x={x} y={y} width="46" height="62" rx="13" fill={active?'#cc615d':'#132331'} stroke={chosen(zone)?'#f8eee1':active?'#ff9789':'#6e899d'} strokeWidth={chosen(zone)?3:2}/>
      <path d={`M${x+9} ${y+10}v42 M${x+22} ${y+9}v44 M${x+35} ${y+10}v42`} stroke="#91a7b8" strokeWidth="2" opacity=".45"/>
      <text x={x+23} y={y+34} textAnchor="middle" fontSize="14" fill="#f0f8fd" fontWeight="800">{label}</text>
   </g>
 }
 const marker=(z,x,y,short)=>{
    const active=severity(z)
    return <g key={z} role="button" tabIndex="0" className={'vw-click-target '+(chosen(z)?'chosen':'')+' '+(active||'')} aria-label={'Inspectează '+zoneLabels[z]}
      onClick={()=>onSelect(z)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(z)}}}>
      <circle cx={x} cy={y} r="28" fill={active?(active==='critical'?'#eb625d':'#dba95c'):'#54c9c3'} fillOpacity={active ? .24 : .09} stroke={active?'#ef8d7c':chosen(z)?'#8ce9d6':'#6ab6b8'} strokeWidth="2" strokeDasharray={active?'4 3':undefined}/>
      <circle cx={x} cy={y} r="8" fill={active?'#ed8473':'#8be5d6'}/>
      <text x={x} y={y-40} fontSize="12" textAnchor="middle" fontWeight="750" fill="#dbe9f0">{short}</text>
    </g>
 }
 return <div className="vehicle-visual">
  <div className="vehicle-top"><span className="tiny-uppercase">TIGUAN III / VEDERE SCHEMATICĂ</span><span className="vehicle-note">Zone clicabile, nu amplasare OEM</span></div>
  <svg className="vehicle-svg" viewBox="0 0 760 465" role="img" aria-label="Volkswagen Tiguan schematic cu roți, motor, DPF, DSG, 4MOTION, ABS și baterie">
    <defs>
      <linearGradient id="vwpaint" x1="0" x2="1" y1="0" y2="1"><stop stopColor="#9eb9c9"/><stop offset=".55" stopColor="#5e8095"/><stop offset="1" stopColor="#324b60"/></linearGradient>
      <linearGradient id="vwglass" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#29495c"/><stop offset="1" stopColor="#152938"/></linearGradient>
      <pattern id="vwgrid" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" stroke="#2b4050" strokeWidth=".8" opacity=".36" fill="none"/></pattern>
    </defs>
    <rect x="0" y="0" width="760" height="465" rx="22" fill="url(#vwgrid)"/>
    <g opacity=".72"><text x="30" y="238" fontSize="12" fill="#96b6c9">FAȚĂ</text><path d="M85 234H132m-42-8-8 8 8 8" stroke="#9fbdca" strokeWidth="2" fill="none"/></g>
    {wheel('wheel_fl',205,78,'FL')}{wheel('wheel_fr',205,326,'FR')}{wheel('wheel_rl',549,78,'RL')}{wheel('wheel_rr',549,326,'RR')}
    <path d="M127 217Q136 143 209 134L531 128Q617 131 666 186L680 226 665 281Q621 332 528 337L206 329Q132 313 127 243Z" fill="url(#vwpaint)" stroke="#a7c1cf" strokeWidth="3"/>
    <path d="M280 150L342 137H513L573 158L602 203V256L566 312L502 325H346L282 312Z" fill="#1d3545" stroke="#b2c7d2" strokeWidth="2"/>
    <path d="M295 161L353 150H502L555 171 572 208H294Z" fill="url(#vwglass)" stroke="#7e9fb0"/>
    <path d="M299 264H572L547 295 502 311H356L305 297Z" fill="url(#vwglass)" stroke="#7e9fb0"/>
    <path d="M294 218H573M356 151V311M506 151V310" stroke="#89abba" opacity=".4"/>
    <path d="M142 195H161v64H142" stroke="#f9e4ad" strokeWidth="5" strokeLinecap="round" fill="none"/>
    <path d="M665 193v73" stroke="#142b3b" strokeWidth="12" strokeLinecap="round"/>
    {marker('engine',214,232,'TDI')}{marker('battery',345,179,'12 V')}{marker('dpf',348,279,'DPF')}
    {marker('dsg',437,228,'DSG')}{marker('brakes',438,289,'ABS')}{marker('awd',577,232,'4×4')}
    <text x="206" y="403" fill="#849eaf" fontSize="10" textAnchor="middle">FRONT AXLE</text>
    <text x="586" y="403" fill="#849eaf" fontSize="10" textAnchor="middle">REAR AXLE</text>
  </svg>
  <div className="vehicle-legend"><span><i className="legend-dot red-dot"/> Alertă critică</span><span><i className="legend-dot amber-dot"/> Atenționare</span><span><i className="legend-dot cyan-dot"/> Inspectabil</span></div>
 </div>
}

function TelemetryCard({name,points,time}){
  const [title,unit,color,precision]=signalMeta[name]
  const last=readLatest(points,time)
  const values=(points||[]).map(x=>x.v)
  const minimum=values.length?Math.min(...values):0, maximum=values.length?Math.max(...values):1
  const pad=Math.max(.5,(maximum-minimum)*.15)
  const lo=minimum-pad,hi=maximum+pad
  const duration=Math.max(1,points?.at(-1)?.t||55)
  const filtered=(points||[]).filter(x=>x.t<=time+.001)
  const path=filtered.map((x,i)=>`${i?'L':'M'}${(8+x.t/duration*294).toFixed(1)} ${(70-(x.v-lo)/(hi-lo)*56).toFixed(1)}`).join(' ')
  return <div className="signal-card"><div className="signal-heading"><span className="signal-name"><i style={{background:color}}/>{title}</span><span className="unit">{unit}</span></div>
    <div className="signal-value">{last===null?'—':asNumber(last,precision)}<small> {unit}</small></div>
    <svg className="sparkline" viewBox="0 0 310 88" preserveAspectRatio="none"><path d="M8 20H305M8 47H305M8 74H305" fill="none" stroke="#273b4a" strokeDasharray="4 5"/>{path&&<path d={path} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>}<line x1={8+time/duration*294} x2={8+time/duration*294} y1="5" y2="76" stroke="#a7cad1" strokeDasharray="4 5" opacity=".5"/></svg>
  </div>
}

function DiagnosticDetail({event}){
 if(!event)return <div className="reason-empty"><span>◎</span><strong>Nu există diagnostic pentru zona selectată</strong><small>Alege o alertă sau o zonă marcată pe mașină.</small></div>
 const pretty={speed_kmh:'Viteză vehicul',wheel_fr_kmh:'Roată FR',other_wheels_mean_kmh:'Media celorlalte roți',voltage_v:'Tensiune 12 V',dpf_diff_pressure_mbar:'Presiune DPF',soot_estimated_pct:'Încărcare DPF',egr_command_pct:'EGR comandat',egr_actual_pct:'EGR actual',dsg_temp_c:'Temperatură DSG',awd_request_pct:'4MOTION cerut',awd_feedback_pct:'4MOTION feedback',abs_online:'ECU ABS online'}
 const evidenceKeys={
 ABS_FR_SIGNAL_LOSS:['wheel_fr_kmh','other_wheels_mean_kmh','speed_kmh'],
 ABS_FR_IMPLAUSIBLE:['wheel_fr_kmh','other_wheels_mean_kmh','speed_kmh'],
 DPF_DIFFERENTIAL_PRESSURE_HIGH:['dpf_diff_pressure_mbar','soot_estimated_pct','speed_kmh'],
 EGR_FLOW_MISMATCH:['egr_command_pct','egr_actual_pct','speed_kmh'],
 DSG_OIL_TEMPERATURE_HIGH:['dsg_temp_c','speed_kmh'],
 AWD_COUPLING_UNDERRESPONSE:['awd_request_pct','awd_feedback_pct'],
 SYSTEM_VOLTAGE_LOW:['voltage_v'],
 ABS_ECU_TIMEOUT:['abs_online','voltage_v'],
 }
 const keys=evidenceKeys[event.type]||Object.keys(event.evidence||{}).slice(0,3)
 return <div className="diagnostic-detail">
   <div className="detail-header"><span className="tiny-uppercase">ANALIZĂ CAUZALĂ · FĂRĂ AI</span><span className="logic-tag">DETECTOR</span></div>
   <h3>{event.component}</h3><div className="detail-sub">{event.module} · eveniment la {seconds(event.t_s)}</div>
   <div className="reason-block"><span className="reason-kicker">IPOTEZA PRINCIPALĂ</span><p className="reason-primary">{event.hypothesis}</p><p className="reason-why">{event.reason}</p></div>
   <div className="detail-subtitle">Date care susțin alerta</div>
   <div className="evidence-grid">{keys.map(k=><div className="evidence-cell" key={k}><small>{pretty[k]||k}</small><strong>{String(event.evidence?.[k]??'—')}</strong></div>)}</div>
   <div className="detail-subtitle">Cauze alternative de verificat</div>
   <ul className="detail-list">{event.alternatives.map((s,i)=><li key={i}>{s}</li>)}</ul>
   <div className="detail-subtitle">Pași de diagnostic recomandați</div>
   <ol className="detail-list ordered">{event.checks.map((s,i)=><li key={i}>{s}</li>)}</ol>
   <div className="uncertainty-note">ⓘ {event.certainty}. Acest raport este produs de reguli din simulator, nu de un agent AI și nu confirmă piesa defectă.</div>
 </div>
}


function DBCExplorer(){
 const [opened,setOpened]=useState(false)
 const [filter,setFilter]=useState('')
 const [offset,setOffset]=useState(0)
 const [listing,setListing]=useState(null)
 const [details,setDetails]=useState(null)
 const [pending,setPending]=useState(false)
 const [error,setError]=useState('')
 useEffect(()=>{
   if(!opened)return
   let alive=true
   setPending(true)
   fetchJSON(`/api/dbc/messages?search=${encodeURIComponent(filter)}&offset=${offset}&limit=40`)
     .then(data=>{if(alive){setListing(data);setError('')}})
     .catch(e=>{if(alive)setError(e.message)})
     .finally(()=>{if(alive)setPending(false)})
   return()=>{alive=false}
 },[opened,filter,offset])
 const inspect=async name=>{
   if(details?.name===name){setDetails(null);return}
   try{setDetails(await fetchJSON('/api/dbc/messages/'+encodeURIComponent(name)));setError('')}
   catch(e){setError(e.message)}
 }
 return <section className="panel dbc-panel">
   <div className="panel-header"><div><h2>DBC Explorer <span className="dbc-tag">NEW · v0.6</span></h2>
     <p>Catalog automat · mesaje, CAN ID, semnale, factori și maparea către simulator</p></div>
     <button className="ghost-button dbc-toggle" onClick={()=>setOpened(!opened)}>{opened?'Ascunde catalogul':'Deschide catalogul DBC'}</button>
   </div>
   {opened&&<div className="dbc-content">
     <div className="dbc-toolbar"><div className="search-wrap"><span>⌕</span><input
        aria-label="Caută mesaje sau semnale DBC" placeholder="Mesaj, CAN ID sau semnal"
        value={filter} onChange={e=>{setFilter(e.target.value);setOffset(0);setDetails(null)}}/></div>
       <span className="dbc-summary">{listing?.dbc?.messages??'—'} mesaje / {listing?.dbc?.signals??'—'} semnale în DBC</span></div>
     {error&&<div className="dbc-error">{error} — verifică dependențele Python și calea către DBC.</div>}
     <p className="dbc-subnotice">Un mesaj poate fi generat automat fără să reprezinte trafic real. <b>Mapped</b> = alimentat din modelul simulat; <b>Neutral</b> = valoare artificială implicită. Checksum-urile OEM nu sunt validate.</p>
     <div className="dbc-body">
       <div className="dbc-list"><div className="dbc-list-head"><span>MESSAGE / CAN ID</span><span>SIGNALS</span></div>
         {(listing?.messages||[]).map(m=><button key={m.can_id+':'+m.name} onClick={()=>inspect(m.name)}
           className={'dbc-message '+(details?.name===m.name?'dbc-selected':'')}>
             <span><strong>{m.name}</strong><small>{m.can_id} · {m.is_fd?'CAN-FD':'CAN'} · {m.length} B</small></span>
             <span className="dbc-count">{m.mapped_signals}/{m.signal_count} mapped</span>
           </button>)}
         {pending&&<div className="dbc-info">Se încarcă…</div>}
         {!pending&&listing?.messages.length===0&&<div className="dbc-info">Niciun mesaj găsit.</div>}
         <div className="dbc-pages"><button disabled={!offset} onClick={()=>{setOffset(Math.max(0,offset-40));setDetails(null)}}>← Înapoi</button>
           <span>{listing?.total?`${offset+1}–${Math.min(offset+40,listing.total)} / ${listing.total}`:'0 rezultate'}</span>
           <button disabled={!listing||offset+40>=listing.total} onClick={()=>{setOffset(offset+40);setDetails(null)}}>Înainte →</button></div>
       </div>
       <div className="dbc-detail">
       {details?<>
         <div className="dbc-detail-title"><h3>{details.name}</h3><span className="frame-id">{details.can_id}</span></div>
         <div className="dbc-chips"><span>{details.length} bytes</span><span>{details.is_fd?'CAN-FD':'Classic CAN'}</span><span>Sender: {details.sender}</span><span>{details.cycle_time_ms?`${details.cycle_time_ms} ms (DBC)`: 'Ciclu nespecificat'}</span></div>
         <div className="dbc-signal-scroll"><table className="dbc-signals"><thead><tr><th>Semnal</th><th>Biți</th><th>Scale / Offset</th><th>Origine</th></tr></thead><tbody>
           {details.signals.map(s=><tr key={s.name}><td><strong>{s.name}</strong><small>{s.unit||'fără unitate'}</small></td>
             <td>{s.start} · {s.length}<small>{s.byte_order} {s.signed?'signed':'unsigned'}</small></td>
             <td>{String(s.scale)} / {String(s.offset)}</td>
             <td><span className={'dbc-origin '+(s.generation==='behavior_model'?'mapped':s.generation==='neutral_synthetic'?'neutral':'placeholder')}>{s.generation==='behavior_model'?'Mapped':s.generation==='neutral_synthetic'?'Neutral':'Placeholder'}</span>{s.state_source&&<small>{s.state_source}</small>}</td>
           </tr>)}
         </tbody></table></div>
       </>:<div className="dbc-detail-empty">Selectează un mesaj din stânga pentru poziții de biți, scalare și sursa valorilor generate.</div>}
       </div>
     </div>
     <div className="dbc-footnote">DBC: {listing?.dbc?.dbc_file||'—'} · Parser: {listing?.dbc?.parser||'—'} · Acoperirea exactă pentru Tiguan 2025 rămâne neverificată.</div>
   </div>}
 </section>
}

function App(){
 const [index,setIndex]=useState([]),[scenario,setScenario]=useState('abs_fr_sensor')
 const [data,setData]=useState(null),[time,setTime]=useState(55),[playing,setPlaying]=useState(false)
 const [selected,setSelected]=useState('wheel_fr'),[selectedEvent,setSelectedEvent]=useState(null)
 const [frames,setFrames]=useState([]),[frameIndex,setFrameIndex]=useState(null),[search,setSearch]=useState('')
 const [tab,setTab]=useState('events'),[telemetryTab,setTelemetryTab]=useState('abs')
 const [loading,setLoading]=useState(true),[running,setRunning]=useState(false),[error,setError]=useState('')

 const refreshIndex=()=>fetchJSON('/api/scenarios').then(v=>setIndex(v.scenarios)).catch(e=>setError(e.message))
 const loadScenario=async name=>{
  setLoading(true);setError('');setPlaying(false);setFrameIndex(null)
  try{
   const fresh=await fetchJSON('/api/scenarios/'+name)
   setData(fresh);setTime(fresh.duration_s);setSelectedEvent(null)
   const last=[...fresh.events].reverse().find(e=>e.zone)
   setSelected(last?.zone||'engine')
   setTelemetryTab(name.startsWith('abs_')?'abs':['dpf_restriction','egr_flow'].includes(name)?'emissions':['awd_clutch','dsg_overheat'].includes(name)?'drivetrain':'overview')
  }catch(e){setData(null);setError(e.message)}finally{setLoading(false)}
 }
 useEffect(()=>{refreshIndex()},[])
 useEffect(()=>{loadScenario(scenario)},[scenario])
 useEffect(()=>{
   if(!data)return
   let alive=true
   fetchJSON(`/api/scenarios/${scenario}/frames?at=${time}&q=${encodeURIComponent(search)}&limit=50`).then(v=>{if(alive){setFrames(v.frames);setFrameIndex(null)}}).catch(e=>{if(alive)setError(e.message)})
   return()=>{alive=false}
 },[scenario,time,search,data])
 useEffect(()=>{
  if(!playing||!data)return
  const timer=setInterval(()=>setTime(old=>{let next=Math.min(data.duration_s,old+.25);if(next>=data.duration_s)setPlaying(false);return next}),250)
  return()=>clearInterval(timer)
 },[playing,data])
 const activeEvents=useMemo(()=>data?.events.filter(e=>e.t_s<=time+.001)||[],[data,time])
 const activeDtcs=useMemo(()=>data?.dtcs.filter(d=>d.first_seen_s<=time+.001)||[],[data,time])
 const focusEvent=activeEvents.find(e=>e.type===selectedEvent)||[...activeEvents].reverse().find(e=>e.zone===selected)||null
 const activeSeverity=activeEvents.some(e=>e.severity==='critical')?'critical':activeEvents.length?'warning':'healthy'
 const run=async()=>{
  setError('');setRunning(true);setPlaying(false)
  try{await fetchJSON('/api/runs/'+scenario,{method:'POST'});await refreshIndex();await loadScenario(scenario)}
  catch(e){setError(e.message)}finally{setRunning(false)}
 }
 const chooseEvent=e=>{setSelected(e.zone);setSelectedEvent(e.type);setTab('causes');setTime(Math.max(e.t_s,time))}
 return <div className="app-shell">
  <aside className="sidebar">
   <div className="brand"><div className="brand-mark">⌁</div><div><strong>CAN LAB<span className="brand-dot">.</span></strong><small>AUTOMOTIVE DIAGNOSTICS</small></div></div>
   <div className="sidebar-group-name">WORKSPACE</div>
   <div className="nav-link active">▧ &nbsp;Diagnostic dashboard <span className="nav-bullet"/></div>
   <div className="nav-link muted">▤ &nbsp;Tiguan CT Simulator</div>
   <div className="sidebar-separator"/>
   <div className="sidebar-row"><span className="sidebar-group-name">SCENARII</span><span className="count">{String(Object.keys(scenarioLabels).length).padStart(2,'0')}</span></div>
   <div className="scenarios">{Object.entries(scenarioLabels).map(([id,[title,subtitle,ico]])=><button key={id} className={'scenario-option '+(scenario===id?'selected':'')} onClick={()=>setScenario(id)}><span className="scenario-icon">{ico}</span><span><strong>{title}</strong><small>{subtitle}</small></span><i className={'source-indicator '+(index.find(x=>x.id===id)?.available?'real':'')}/></button>)}</div>
   <div className="sidebar-bottom"><div className="system-dot"/><div><strong>Research build · v0.6</strong><small>AI · MCP · Azure: ulterior</small></div></div>
  </aside>
  <main className="content">
    <header className="topbar"><div className="breadcrumbs"><span>CAN Lab</span><span>›</span><strong>Diagnostic overview</strong></div><div className="top-meta"><span className="top-pill">VW MQBevo REFERENCE</span><span className="top-pill dark">SYNTHETIC DATA</span><span className="avatar">VW</span></div></header>
    <div className="page-padding">
     <div className="title-row"><div><div className="eyebrow">VEHICLE DIAGNOSTICS / RESEARCH PROTOTYPE</div><h1>Volkswagen Tiguan <span>4MOTION</span></h1><p>2025 · 2.0 TDI · DSG 7 · 193 CP · Diagnoză explicabilă, simulată</p></div><div className="header-actions"><button className="ghost-button" onClick={()=>loadScenario(scenario)}>↻ Reîncarcă</button><button className="primary-button" disabled={running||loading} onClick={run}>{running?'Rulează...':'▶ Rulează scenariul'}</button></div></div>
     <div className="demo-banner"><span>ⓘ</span><span><strong>Experiment, NU diagnoză OEM:</strong> layout-uri selectate din OpenDBC MQBevo, valori și defecte injectate artificial; compatibilitatea pentru Tiguan CT 2025, checksum-urile și DTC-urile specifice sunt neverificate. Datele DPF, EGR, DSG și AWD provin din senzori virtuali.</span></div>
     {error&&<div className="error-banner"><strong>Eroare:</strong> {error}<button onClick={()=>setError('')}>×</button></div>}
     {loading&&!data&&<div className="loading-state">Se încarcă datele simulatorului…</div>}
     {data&&<>
       <div className="stat-row">
        <div className="stat-card"><span>STATUS VEHICUL</span><div className={'status-badge '+activeSeverity}><i/>{activeSeverity==='healthy'?'Fără anomalii':activeSeverity==='critical'?'Alertă critică':'Avertizare'}</div><small>La {seconds(time)} în simulare</small></div>
        <div className="stat-card"><span>CADRE HEX</span><strong>{data.summary.frames_sent.toLocaleString('ro-RO')}</strong><small>{data.summary.fd_frames} cadre CAN-FD</small></div>
        <div className="stat-card"><span>ANOMALII</span><strong>{activeEvents.length}<em> / {data.events.length}</em></strong><small>Detecție deterministă</small></div>
        <div className="stat-card"><span>CODURI DTC</span><strong>{String(activeDtcs.length).padStart(2,'0')}</strong><small>{activeDtcs.map(d=>d.code).join(' · ')||'Niciun DTC simulat'}</small></div>
       </div>
       <div className="dashboard-grid">
         <section className="panel vehicle-panel"><div className="panel-header"><div><h2>Vehicle fault map</h2><p>Identificarea zonei sau roții cu semnal anormal</p></div><span className="chip">TOP VIEW</span></div>
          <CarDiagram issues={activeEvents} selected={selected} onSelect={zone=>{setSelected(zone);setSelectedEvent(null);setTab('causes')}}/>
          <div className="playback"><div className="playback-head"><div><span className="tiny-uppercase">SIMULATION TIMELINE</span><strong>{seconds(time)} <span>/ {seconds(data.duration_s)}</span></strong></div><div className="playback-controls"><button onClick={()=>{setTime(0);setPlaying(true)}}>↺</button><button className="play-button" onClick={()=>{if(time>=data.duration_s)setTime(0);setPlaying(!playing)}}>{playing?'Ⅱ':'▶'}</button></div></div><input aria-label="Timp simulare" className="time-slider" type="range" min="0" max={data.duration_s} step=".5" value={time} onChange={e=>{setPlaying(false);setTime(Number(e.target.value))}}/><div className="timeline-ticks"><span>0s · Start</span><span>22s · Injectare</span><span>{seconds(data.duration_s)} · End</span></div></div>
         </section>
         <section className="panel diagnostics-panel"><div className="panel-header"><div><h2>Diagnostic insights</h2><p>Simptome → cauze posibile → verificări</p></div><span className="offline-tag"><span/> AI OFFLINE</span></div>
          <div className="tabs"><button className={tab==='events'?'active':''} onClick={()=>setTab('events')}>Anomalii <span>{activeEvents.length}</span></button><button className={tab==='causes'?'active':''} onClick={()=>setTab('causes')}>Cauze <span>{activeEvents.length}</span></button><button className={tab==='dtcs'?'active':''} onClick={()=>setTab('dtcs')}>DTC <span>{activeDtcs.length}</span></button></div>
          {tab==='events'&&<div className="alert-scroll">{activeEvents.length?activeEvents.map(e=><button key={e.type} className={'alert-item '+(e.severity==='critical'?'red':'amber')} onClick={()=>chooseEvent(e)}><span className="alert-top"><span className={'severity-square '+(e.severity==='critical'?'red':'amber')}>!</span><span className="alert-meta">{e.severity==='critical'?'Critic':'Atenție'} · {seconds(e.t_s)}</span></span><strong>{e.label}</strong><p>{e.reason}</p><span className="alert-source">{e.module} · Apasă pentru explicația cauzelor</span></button>):<div className="empty-alert"><span>✓</span><strong>Fără anomalii</strong><small>Niciun eveniment până la momentul selectat.</small></div>}</div>}
          {tab==='causes'&&<div className="detail-scroll"><DiagnosticDetail event={focusEvent}/></div>}
          {tab==='dtcs'&&<div className="alert-scroll">{activeDtcs.length?activeDtcs.map((d,i)=><div className="dtc-row" key={i}><span className="dtc-code">{d.code}</span><div><strong>{d.component}</strong><small>{d.module} · {seconds(d.first_seen_s)}</small><small>{d.status}</small><small className="caution-mini">{d.verification}</small></div></div>):<div className="empty-alert"><span>○</span><strong>Niciun DTC</strong><small>Nu toate anomaliile se convertesc în coduri de diagnoză.</small></div>}</div>}
          <div className="inspector"><div className="inspector-title"><span className="tiny-uppercase">COMPONENTĂ SELECTATĂ</span><span>◉</span></div><strong>{zoneLabels[selected]}</strong><p>{focusEvent?.hypothesis||'Nu există o anomalie asociată acestei zone la momentul selectat.'}</p><div className="inspector-foot">ⓘ Indicator schematic, diagnostic neconfirmat</div></div>
         </section>
       </div>
       <section className="panel telemetry-panel"><div className="panel-header"><div><h2>Signal telemetry</h2><p>Vizualizare temporală a semnalelor CAN și senzorilor virtuali</p></div><div className="telemetry-tabs">{Object.keys(telemetryGroups).map(k=><button className={telemetryTab===k?'on':''} onClick={()=>setTelemetryTab(k)} key={k}>{({overview:'General',abs:'ABS / Roți',emissions:'DPF / EGR',drivetrain:'DSG / AWD'})[k]}</button>)}</div></div><div className="telemetry-grid">{telemetryGroups[telemetryTab].map(k=><TelemetryCard key={k} name={k} points={data.telemetry[k]} time={time}/>)}</div><div className="telemetry-disclaimer">* Vitezele individuale folosesc un layout MQBevo de referință, nevalidat pe Tiguan 2025; celelalte mărimi marcate cu * sunt valori de senzori virtuali.</div></section>
       <DBCExplorer/>
       <section className="panel frames-panel"><div className="panel-header frames-header"><div><h2>CAN frame inspector</h2><p>Payload hexadecimal, CAN ID și semnale decodate din DBC de referință</p></div><div className="search-wrap">⌕ <input placeholder="Caută ID, mesaj sau HEX" value={search} onChange={e=>setSearch(e.target.value)}/></div></div>
       <div className="frames-table-wrap"><table className="frames-table"><thead><tr><th>TIMESTAMP</th><th>CAN ID</th><th>MESSAGE</th><th>TIP</th><th>DATA / PAYLOAD HEX</th><th></th></tr></thead><tbody>{frames.map((f,i)=><React.Fragment key={`${f.message}-${f.t_s}`}><tr className={frameIndex===i?'row-on':''} onClick={()=>setFrameIndex(frameIndex===i?null:i)}><td>{seconds(f.t_s)}</td><td className="frame-id">{f.can_id}</td><td>{f.message}</td><td><span className={'frame-tag '+(f.is_fd?'fd':'')}>{f.is_fd?'CAN-FD':'CAN'}</span></td><td className="hex-data">{f.data_hex.match(/.{1,2}/g)?.join(' ')}</td><td className="expand-arrow">{frameIndex===i?'⌄':'›'}</td></tr>{frameIndex===i&&<tr className="frame-expand"><td colSpan={6}><div className="frame-expanded"><span><b>ECU referință:</b> {f.ecu}</span><span><b>Lungime:</b> {f.length} octeți</span><span><b>Checksum verificat:</b> {f.crc_validated===false?'NU (placeholder)':'N/A'}</span><span><b>Transmitere pe vehicul:</b> interzisă</span><span><b>Generator:</b> {f.generation_mode||"legacy"}</span><div><b>Semnale decodate:</b><div className="decoded-signals">{Object.entries(f.signals||{}).map(([k,v])=><span key={k}>{k}: <b>{String(v)}</b>{f.signal_origin?.[k]&&<small className="signal-origin">{f.signal_origin[k]}</small>}</span>)}</div></div></div></td></tr>}</React.Fragment>)}</tbody></table>{!frames.length&&<div className="empty-frames">Nu există cadre în intervalul selectat sau pentru filtrul curent.</div>}</div></section>
       <footer className="footer-notes"><span>CAN Lab v0.6 · Dynamic DBC simulation · Read-only · Fără hardware</span><span>LLM, MCP, AKS neconectate · Ground truth separat pentru evaluare</span></footer>
     </>}
    </div>
  </main>
 </div>
}
export default App
