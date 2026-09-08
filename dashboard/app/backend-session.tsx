"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { backend, type Catalog, type DataRepository } from "./data-client";
import { clearLocalSession, readLocalSession, type AuthUser } from "./auth";

export function useBackendSession() {
  const [ready,setReady]=useState(false);
  const [user,setUser]=useState<AuthUser|null>(null);
  const [repository,setRepository]=useState<DataRepository|null>(null);
  const [catalog,setCatalog]=useState<Catalog|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  const [configured,setConfigured]=useState(false);
  const generation=useRef(0);
  const userId=useRef<string|null>(null);

  const reload = useCallback(async (repo:DataRepository,id:string) => {
    if(userId.current!==id)return;
    const current=++generation.current;
    setLoading(true);setError("");
    try { const result=await repo.catalog(id);if(current===generation.current){setCatalog(result);setUser((previous)=>previous&&({...previous,role:result.role==="admin"?"Administrador":"Visualizador"}));} }
    catch(reason){if(current===generation.current){setCatalog(null);setUser(previous=>previous&&({...previous,role:"Permissões indisponíveis"}));setError(reason instanceof Error?reason.message:"Não foi possível carregar os cadastros.");}}
    finally{if(current===generation.current)setLoading(false);}
  },[]);

  useEffect(()=>{
    let stopped=false;
    const invalidate=()=>{generation.current++;};
    let unsubscribe: (()=>void)|undefined;
    const initial=window.setTimeout(()=>{
      try {
        const connection=backend();
        if(!connection){setUser(readLocalSession());setReady(true);return;}
        setConfigured(true);setRepository(connection.repository);clearLocalSession();
        const {data}=connection.client.auth.onAuthStateChange((_event,session)=>{
          if(stopped)return;
          const id=session?.user.id??null;
          if(id!==userId.current){generation.current++;setCatalog(null);userId.current=id;}
          if(session){
            setUser({id:session.user.id,email:session.user.email??"",name:session.user.email?.split("@")[0]??"Usuário",role:"Carregando permissões"});
            // Do not call other SDK methods while the auth callback holds its lock.
            window.setTimeout(()=>{if(!stopped&&userId.current===id)void reload(connection.repository,session.user.id);},0);
          }else{setUser(null);setCatalog(null);setLoading(false);setError("");}
          setReady(true);
        });
        unsubscribe=()=>data.subscription.unsubscribe();
      } catch(reason){setConfigured(true);setError(reason instanceof Error?reason.message:"Configuração inválida.");setReady(true);}
    },0);
    return ()=>{stopped=true;invalidate();window.clearTimeout(initial);unsubscribe?.();};
  },[reload]);

  const login=async(email:string,password:string)=>{
    const connection=backend();if(!connection)throw new Error("Serviço de acesso não configurado.");
    const {error}=await connection.client.auth.signInWithPassword({email,password});
    if(error)throw new Error("Não foi possível entrar. Confira e-mail, senha e conexão.");
  };
  const logout=async()=>{
    if(configured){const connection=backend();if(connection){const result=await connection.client.auth.signOut({scope:"local"});if(result.error)throw new Error("Não foi possível encerrar a sessão. Tente novamente.");}}
    clearLocalSession();generation.current++;userId.current=null;setUser(null);setCatalog(null);setError("");setLoading(false);
  };
  const refresh=()=>{if(repository&&user?.id)void reload(repository,user.id);};
  useEffect(()=>{
    if(!repository||!user?.id)return;
    const id=user.id;
    const revalidate=()=>{if(document.visibilityState==="visible")void reload(repository,id);};
    const timer=window.setInterval(revalidate,60000);
    window.addEventListener("online",revalidate);document.addEventListener("visibilitychange",revalidate);
    return()=>{window.clearInterval(timer);window.removeEventListener("online",revalidate);document.removeEventListener("visibilitychange",revalidate);};
  },[repository,user?.id,reload]);
  const commitCatalog=(owner:string,update:(previous:Catalog|null)=>Catalog|null)=>{
    if(userId.current!==owner)return;
    // A request started before the mutation must not restore an older snapshot.
    generation.current++;setCatalog(update);setLoading(false);
    if(repository)void reload(repository,owner);
  };
  return {ready,user,repository,catalog,commitCatalog,error,loading,configured,login,logout,refresh,localLogin:setUser};
}
