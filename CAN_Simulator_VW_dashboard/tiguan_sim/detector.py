"""Evidence-first deterministic diagnostic rules; never reads injection labels."""
from __future__ import annotations

RULES = {
 'ABS_FR_SIGNAL_LOSS': {
   'label':'Semnal ABS față dreapta absent', 'zone':'wheel_fr','module':'03 · Brake Electronics',
   'component':'Senzor viteză roată față dreapta / circuit', 'severity':'critical',
   'hypothesis':'Lipsă semnal de la circuitul senzorului de viteză față dreapta.',
   'why':'Trei roți au viteze concordante, dar semnalul față dreapta rămâne aproape zero în mers.',
   'alternatives':['Senzor de viteză defect','Conector sau cablaj întrerupt','Encoder magnetic deteriorat sau contaminat'],
   'checks':['Compară viteza individuală a fiecărei roți la deplasare lentă','Inspectează conectorul și cablajul FR','Verifică semnalul și encoderul conform procedurii de service'],
   'dtc':'C101B', 'dtc_note':'Asociere ilustrativă bazată pe documentație pentru alte modele VW; nu verificată pe Tiguan CT 2025',
 },
 'ABS_FR_IMPLAUSIBLE': {
   'label':'Semnal ABS față dreapta intermitent', 'zone':'wheel_fr','module':'03 · Brake Electronics',
   'component':'Semnal viteză / encoder roată față dreapta','severity':'warning',
   'hypothesis':'Citirea roții față dreapta este instabilă sau implauzibilă.',
   'why':'Viteza FR prezintă căderi recurente, pe când celelalte trei roți au un comportament coerent.',
   'alternatives':['Encoder magnetic murdar/deteriorat','Distanță senzor–encoder sau montaj incorect','Senzor/cablaj cu contact intermitent'],
   'checks':['Inspectează condiția encoderului și a rulmentului','Verifică fixarea senzorului','Compară forma de undă FR cu FL la aceeași viteză'],
   'dtc':'C101B','dtc_note':'Cod și interpretare illustrative; subtipul exact pentru CT 2025 este neverificat',
 },
 'DPF_DIFFERENTIAL_PRESSURE_HIGH': {
   'label':'Presiune diferențială DPF ridicată', 'zone':'dpf','module':'01 · Engine Electronics',
   'component':'Filtru de particule / senzor presiune diferențială','severity':'warning',
   'hypothesis':'Restricție crescută în traseul DPF sau o măsurare eronată a presiunii diferențiale.',
   'why':'Presiunea diferențială este mare în raport cu regimul simulat de funcționare și cu încărcarea estimată.',
   'alternatives':['Acumulare de funingine / regenerări insuficiente','Senzor presiune diferențială eronat','Furtunuri de presiune obturate sau deteriorate'],
   'checks':['Compară presiunea diferențială la ralanti și la turație stabilizată','Verifică senzorul și tuburile de presiune','Consultă parametrii de regenerare și valorile de încărcare calculate'],
   'dtc':'P2463','dtc_note':'Cod OBD generic exemplificativ; atribuirea la ECU-ul 2025 nu este validată',
 },
 'EGR_FLOW_MISMATCH': {
   'label':'Debit EGR insuficient față de comandă','zone':'engine','module':'01 · Engine Electronics',
   'component':'Supapă EGR / circuit recirculare', 'severity':'warning',
   'hypothesis':'Recircularea gazelor nu atinge valoarea comandată.',
   'why':'Comanda ECU și răspunsul estimat al circuitului EGR diferă semnificativ și persistent.',
   'alternatives':['Supapă EGR blocată / depuneri','Actuator sau comandă nefuncțională','Senzor de debit ori presiune cu valori greșite'],
   'checks':['Compară comandă EGR și feedback în mai multe regimuri','Verifică actuatorul și traseul pentru depuneri','Consultă procedura ghidată de diagnoză pentru TDI'],
   'dtc':'P0401','dtc_note':'Cod OBD generic exemplificativ, nu o citire autentică de Tiguan 2025',
 },
 'DSG_OIL_TEMPERATURE_HIGH': {
   'label':'Temperatură DSG excesivă','zone':'dsg','module':'02 · Auto Trans',
   'component':'Transmisie DSG / circuit de răcire ulei','severity':'critical',
   'hypothesis':'Supraîncălzire a transmisiei DSG în condițiile simulate de sarcină.',
   'why':'Temperatura transmisiei crește persistent peste pragul demonstrativ stabilit în simulator.',
   'alternatives':['Sarcină sau patinare excesivă','Răcire insuficientă a transmisiei','Citire greșită a senzorului de temperatură'],
   'checks':['Compară temperatura cu sarcina și schimbările de treaptă','Verifică istoricul temperaturii și al patinării','Consultă diagnoza specifică transmisiei pentru nivel și răcire'],
   'dtc':None,
 },
 'AWD_COUPLING_UNDERRESPONSE': {
   'label':'4MOTION – răspuns cuplare insuficient','zone':'awd','module':'22 · AWD Electronics (simulat)',
   'component':'Cuplaj punte spate / sistem 4MOTION','severity':'warning',
   'hypothesis':'Sistemul de cuplare spate nu reproduce cererea de transfer în scenariul simulat.',
   'why':'Cuplarea solicitată este mare, dar feedback-ul simulat rămâne mult mai mic.',
   'alternatives':['Presiune/comandă insuficientă la cuplaj','Problemă hidraulică sau electrică','Feedback eronat al cuplării'],
   'checks':['Verifică modulul de tracțiune integrală prin diagnoză','Compară comanda și feedback-ul pe mai multe regimuri','Verifică alimentarea și erorile modulului'],
   'dtc':None,
 },
 'SYSTEM_VOLTAGE_LOW': {
   'label':'Tensiune 12 V sub prag','zone':'battery','module':'19 · Gateway / alimentare',
   'component':'Alimentare 12 V / sistem de încărcare','severity':'warning',
   'hypothesis':'Tensiune de alimentare insuficientă, cu risc de instabilitate a modulelor.',
   'why':'Tensiunea simulat-măsurată scade sub 11,8 V și rămâne redusă.',
   'alternatives':['Baterie 12 V descărcată','Alternator / încărcare necorespunzătoare','Cabluri, masă, contacte sau consumator anormal'],
   'checks':['Măsoară tensiunea cu motorul pornit și oprit','Verifică bornele, masele și circuitul de încărcare','Coroborează cu istoricul altor module'],
   'dtc':'P0562','dtc_note':'Cod OBD generic exemplificativ; nu este preluat de la un ECU VW real',
 },
 'ABS_ECU_TIMEOUT': {
   'label':'Modul ABS nu mai transmite mesaje','zone':'brakes','module':'03 · Brake Electronics',
   'component':'Comunicație cu ECU de frânare','severity':'critical',
   'hypothesis':'Pierderea comunicației cu modulul ABS sau a alimentării acestuia.',
   'why':'Nu mai sunt observate cadre ale modulului de frânare după apariția altei anomalii.',
   'alternatives':['Alimentare/masă ECU instabilă','Defect de rețea CAN / conector','Modul ABS indisponibil sau resetat'],
   'checks':['Verifică alimentarea și masa modulului ABS','Compară cronologia erorilor electrice și a mesajelor lipsă','Verifică rețeaua CAN cu un instrument adecvat'],
   'dtc':None,
 },
}


def infer_events(states: list[dict]) -> list[dict]:
    """Detect symptoms only from visible telemetry, never from injected scenario."""
    found = {}
    previous_fr = None
    for s in states:
        t = s['t_s']
        ref = (s['wheel_fl']+s['wheel_rl']+s['wheel_rr'])/3
        fr = s['wheel_fr']
        conditions = {
          'ABS_FR_SIGNAL_LOSS': ref>22 and fr<1.0 and s['abs_online'],
          'ABS_FR_IMPLAUSIBLE': ref>22 and 1.0<=fr<ref-9 and s['abs_online'],
          'DPF_DIFFERENTIAL_PRESSURE_HIGH': s['dpf_pressure']>165 and s['soot']>60,
          'EGR_FLOW_MISMATCH': s['speed']>15 and s['egr_command']-s['egr_actual']>17,
          'DSG_OIL_TEMPERATURE_HIGH': s['dsg_temp']>115,
          'AWD_COUPLING_UNDERRESPONSE': s['awd_requested']>40 and s['awd_actual']<s['awd_requested']*.4,
          'SYSTEM_VOLTAGE_LOW': s['voltage']<11.8,
          'ABS_ECU_TIMEOUT': not s['abs_online'],
        }
        # no ABS duplicates with different labels in the same scenario
        if 'ABS_FR_SIGNAL_LOSS' in found: conditions['ABS_FR_IMPLAUSIBLE'] = False
        for code, is_bad in conditions.items():
            if is_bad and code not in found:
                r = RULES[code]
                found[code] = {
                  'type':code,'t_s':t,'label':r['label'],'zone':r['zone'],
                  'module':r['module'],'component':r['component'],'severity':r['severity'],
                  'hypothesis':r['hypothesis'],'reason':r['why'],
                  'alternatives':r['alternatives'],'checks':r['checks'],
                  'evidence':{
                    'speed_kmh':s['speed'],'wheel_fr_kmh':s['wheel_fr'],
                    'other_wheels_mean_kmh':round(ref,2),
                    'voltage_v':s['voltage'],'dpf_diff_pressure_mbar':s['dpf_pressure'],
                    'soot_estimated_pct':s['soot'],'egr_command_pct':s['egr_command'],
                    'egr_actual_pct':s['egr_actual'],'dsg_temp_c':s['dsg_temp'],
                    'awd_request_pct':s['awd_requested'],'awd_feedback_pct':s['awd_actual'],
                    'abs_online':s['abs_online']
                  },
                  'dtc':r['dtc'],'diagnostic_origin':'reguli deterministe, nu AI',
                  'certainty':'Ipoteză; cauza fizică nu este confirmată',
                }
        previous_fr = fr
    return sorted(found.values(),key=lambda e:(e['t_s'],e['type']))


def derive_dtcs(events: list[dict]) -> list[dict]:
    """A virtual ECU sets DTCs for selected observed conditions; illustrative codes."""
    result=[]
    existing=set()
    for event in events:
        code=event.get('dtc')
        if not code or (code,event['module']) in existing: continue
        existing.add((code,event['module']))
        result.append({
          'code':code, 'first_seen_s':round(event['t_s']+1,2),
          'status':'testFailed + confirmed (simulat)', 'module':event['module'],
          'component':event['component'],
          'verification':'Cod exemplificativ, nu citire din Tiguan 2025',
          'note':RULES[event['type']].get('dtc_note','DTC simulat'),
          'service':'UDS 0x19 – model conceptual, nu sesiune OEM reală',
        })
    return result
