"use client";
import { useState, type FormEvent } from "react";
import { DashboardDialog } from "./dashboard-dialog";
import { validateCameraDraft, validateEnvironmentName, type CameraDraft } from "./dashboard-model";
import type { CameraRecord, EnvironmentRecord, RuleRecord, DataRepository } from "./data-client";

type Access = { repository:DataRepository|null; canEdit:boolean };
export const STORAGE_PENDING = "Conecte o serviço de dados para salvar os cadastros. Os campos preenchidos aqui ainda não serão enviados.";
function AccessNotice({repository,canEdit}:Access){return !repository?<p className="configuration-notice">{STORAGE_PENDING}</p>:!canEdit?<p className="configuration-notice">Salvar exige permissão de administrador confirmada. Aguarde o carregamento ou verifique seu acesso.</p>:null;}

export function CameraForm({initial,environments,onClose,repository,canEdit,onSaved}:{initial?:CameraRecord;environments:EnvironmentRecord[];onClose:()=>void;onSaved:(record:CameraRecord)=>void}&Access){
  const [draft,setDraft]=useState<CameraDraft>(initial?{name:initial.name,environment:initial.environment_id,source:initial.source,address:initial.address}:{name:"",environment:environments[0]?.id??"",source:"webcam",address:"0"});
  const [monitorId,setMonitorId]=useState(initial?.monitor_id??"");
  const [enabled,setEnabled]=useState(initial?.enabled??true);
  const [error,setError]=useState("");const [busy,setBusy]=useState(false);
  const close=()=>{if(!busy)onClose();};
  const change=(key:keyof CameraDraft,value:string)=>{setError("");setDraft(previous=>({...previous,[key]:value}));};
  const save=async(event:FormEvent)=>{
    event.preventDefault();if(busy)return;
    const invalid=validateCameraDraft(draft);if(invalid){setError(invalid);return;}
    if(!repository||!canEdit){setError("Campos válidos. O salvamento precisa de uma conexão e permissão de edição.");return;}
    setBusy(true);setError("");
    try{const record=await repository.saveCamera(draft,monitorId.trim(),enabled,initial);onSaved(record);onClose();}
    catch(reason){setError(reason instanceof Error?reason.message:"Não foi possível salvar.");}finally{setBusy(false);}
  };
  return <DashboardDialog title={initial?"Editar configurações da câmera":"Adicionar câmera"} onClose={close}><AccessNotice repository={repository} canEdit={canEdit}/>
    <form className="management-form" onSubmit={event=>void save(event)} noValidate>
      <fieldset disabled={busy} className="form-fields">
      <label htmlFor="camera-name">Nome da câmera<input id="camera-name" value={draft.name} maxLength={80} onChange={event=>change("name",event.target.value)} required/></label>
      <label htmlFor="camera-environment">Ambiente<select id="camera-environment" value={draft.environment} onChange={event=>change("environment",event.target.value)} required><option value="">Selecione</option>{environments.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {!environments.length&&<p className="field-help">Cadastre um ambiente antes de adicionar a câmera.</p>}
      <label htmlFor="camera-source">Tipo de câmera<select id="camera-source" value={draft.source} onChange={event=>{setDraft(previous=>({...previous,source:event.target.value as CameraDraft["source"],address:event.target.value==="webcam"?"0":""}));setError("");}}><option value="webcam">Webcam deste computador</option><option value="mjpeg">Câmera do celular / MJPEG</option><option value="rtsp">Câmera IP / RTSP</option><option disabled>Gateway ESP32 — integração pendente</option></select></label>
      <label htmlFor="camera-address">{draft.source==="webcam"?"Índice da webcam":"Endereço da câmera, sem credenciais"}<input id="camera-address" value={draft.address} onChange={event=>change("address",event.target.value)} spellCheck={false} autoComplete="off" maxLength={500} placeholder={draft.source==="webcam"?"0":draft.source==="mjpeg"?"http://192.168.1.36:8080/video":"rtsp://192.168.1.10:554/stream"}/></label>
      <label htmlFor="camera-monitor">Identificador no monitor (opcional)<input id="camera-monitor" value={monitorId} onChange={event=>setMonitorId(event.target.value)} maxLength={64} placeholder="Ex.: pc ou phone"/></label>
      <p className="field-help">Use o identificador enviado pelo monitor para associar suas leituras. Deixe vazio para configurar depois.</p>
      <label className="checkbox-field"><input type="checkbox" checked={enabled} onChange={event=>setEnabled(event.target.checked)}/>Habilitada no cadastro</label>
      </fieldset>
      <p className="field-help">Salvar registra a configuração. A conexão do servidor com essa origem é uma etapa separada.</p>
      {error&&<p className="form-feedback" role="alert">{error}</p>}
      <div className="modal-actions"><button className="secondary-button" type="button" disabled={busy} onClick={close}>Cancelar</button><button className="primary-action" type="submit" disabled={busy||!canEdit||!repository}>{busy?"Salvando…":"Salvar câmera"}</button></div>
    </form></DashboardDialog>;
}

export function EnvironmentForm({initial,environments,onClose,onSaved,repository,canEdit}:{initial?:EnvironmentRecord;environments:EnvironmentRecord[];onClose:()=>void;onSaved:(record:EnvironmentRecord)=>void}&Access){
  const [name,setName]=useState(initial?.name??"");const [error,setError]=useState("");const [busy,setBusy]=useState(false);
  const close=()=>{if(!busy)onClose();};
  const save=async(event:FormEvent)=>{
    event.preventDefault();if(busy)return;
    const invalid=validateEnvironmentName(name,environments.filter(item=>item.id!==initial?.id).map(item=>item.name));if(invalid){setError(invalid);return;}
    if(!repository||!canEdit)return;
    setBusy(true);setError("");try{onSaved(await repository.saveEnvironment(name,initial));onClose();}catch(reason){setError(reason instanceof Error?reason.message:"Não foi possível salvar.");}finally{setBusy(false);}
  };
  return <DashboardDialog title={initial?"Editar ambiente":"Novo ambiente"} onClose={close}><AccessNotice repository={repository} canEdit={canEdit}/><form className="management-form" noValidate onSubmit={event=>void save(event)}>
    <label htmlFor="environment-name">Nome do ambiente<input id="environment-name" value={name} maxLength={80} disabled={busy} onChange={event=>{setName(event.target.value);setError("");}} required/></label>
    <p className="field-help">O ambiente pode existir antes de receber suas câmeras.</p>
    {error&&<p className="form-feedback" role="alert">{error}</p>}
    <div className="modal-actions"><button className="secondary-button" type="button" disabled={busy} onClick={close}>Cancelar</button><button className="primary-action" type="submit" disabled={busy||!repository||!canEdit}>{busy?"Salvando…":"Salvar ambiente"}</button></div>
  </form></DashboardDialog>;
}

export function RulesDialog({rules,environments,onClose,onSaved,repository,canEdit}:{rules:RuleRecord[];environments:EnvironmentRecord[];onClose:()=>void;onSaved:(record:RuleRecord)=>void}&Access){
  const [selected,setSelected]=useState("");
  const [busy,setBusy]=useState(false);
  const close=()=>{if(!busy)onClose();};
  return <DashboardDialog title="Regras de alertas" onClose={close}><AccessNotice repository={repository} canEdit={canEdit}/><label className="rule-picker">Regra<select disabled={busy} value={selected} onChange={event=>setSelected(event.target.value)}><option value="">Nova regra</option>{rules.map(rule=><option key={rule.id} value={rule.id}>{rule.name}</option>)}</select></label>
    <RuleEditor key={selected} initial={rules.find(rule=>rule.id===selected)} environments={environments} repository={repository} canEdit={canEdit} onBusy={setBusy} onSaved={record=>{onSaved(record);setSelected(record.id);}}/>
    <div className="modal-actions"><button type="button" disabled={busy} className="secondary-button" onClick={close}>Fechar</button></div>
  </DashboardDialog>;
}
function RuleEditor({initial,environments,repository,canEdit,onSaved,onBusy}:{initial?:RuleRecord;environments:EnvironmentRecord[];onSaved:(record:RuleRecord)=>void;onBusy:(busy:boolean)=>void}&Access){
  const [values,setValues]=useState({name:initial?.name??"",environment_id:initial?.environment_id??environments[0]?.id??"",kind:initial?.kind??"camera_offline",enabled:initial?.enabled??true,start_time:initial?.start_time??"08:00",end_time:initial?.end_time??"18:00",delay_seconds:initial?.delay_seconds??60});
  const [saved,setSaved]=useState<RuleRecord|undefined>(initial);const [busy,setBusy]=useState(false);const [feedback,setFeedback]=useState("");
  const submit=async(event:FormEvent)=>{event.preventDefault();if(busy||!repository||!canEdit)return;setBusy(true);onBusy(true);setFeedback("");try{const result=await repository.saveRule(values,saved);setSaved(result);onSaved(result);setFeedback("Regra salva. Sua aplicação depende do serviço de análise no servidor.");}catch(reason){setFeedback(reason instanceof Error?reason.message:"Não foi possível salvar.");}finally{setBusy(false);onBusy(false);}};
  return <form className="management-form" onSubmit={event=>void submit(event)}><fieldset className="form-fields" disabled={busy}>
    <label>Nome<input required maxLength={80} value={values.name} onChange={event=>setValues({...values,name:event.target.value})}/></label>
    <label>Ambiente<select required value={values.environment_id} onChange={event=>setValues({...values,environment_id:event.target.value})}><option value="">Selecione</option>{environments.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
    <label>Condição<select value={values.kind} onChange={event=>setValues({...values,kind:event.target.value as RuleRecord["kind"]})}><option value="camera_offline">Câmera indisponível</option><option value="occupied_outside_hours">Ocupação fora do horário</option></select></label>
    {values.kind==="occupied_outside_hours"&&<><label>Início do expediente (Brasília)<input type="time" required value={values.start_time} onChange={event=>setValues({...values,start_time:event.target.value})}/></label><label>Fim do expediente (Brasília)<input type="time" required value={values.end_time} onChange={event=>setValues({...values,end_time:event.target.value})}/></label></>}
    <label>Duração mínima (segundos)<input type="number" min={10} max={3600} required value={values.delay_seconds} onChange={event=>setValues({...values,delay_seconds:Number(event.target.value)})}/></label>
    <label className="checkbox-field"><input type="checkbox" checked={values.enabled} onChange={event=>setValues({...values,enabled:event.target.checked})}/>Regra habilitada</label>
  </fieldset>{feedback&&<p role="status" className="form-feedback">{feedback}</p>}<button className="primary-action" type="submit" disabled={busy||!repository||!canEdit}>{busy?"Salvando…":"Salvar regra"}</button></form>;
}
