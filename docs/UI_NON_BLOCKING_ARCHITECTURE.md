# Arquitetura de UI Não-Bloqueante para Upload

## 📋 Contexto

**Problema Original:**
- Upload funcionava perfeitamente no backend
- UI usava `st.rerun()` a cada 1 segundo para atualizar progresso
- Isso bloqueava **toda a aplicação Streamlit**, incluindo outras tabs
- Elemento `st.spinner("Atualizando...")` era criado/destruído causando scroll jumping
- Usuário não podia navegar entre tabs durante processamento

## ✅ Solução Implementada

### 1. **Progress Monitor com Placeholder** (`progress_monitor.py`)

Componente dedicado que:
- ✅ **Não usa `st.rerun()`** para atualizar estado global
- ✅ Usa `st.empty()` placeholder para atualizar apenas um componente
- ✅ Permite navegação livre entre tabs durante processamento
- ✅ Atualiza progresso a cada 3 segundos (vs. 1s anterior)
- ✅ Retorna status final quando job completa

```python
def render_live_progress(job_id: str, placeholder):
    """
    Renderiza progresso em tempo real usando placeholder.
    Não recarrega a página inteira, apenas atualiza o componente.
    """
    processor = AsyncProcessor()
    
    while iteration < max_iterations:
        job = processor.get_job_status(job_id)
        
        # Renderizar progresso no placeholder (sem recarregar página)
        with placeholder.container():
            st.progress(progress)
            st.metric(...)
            # ... atualizar apenas este container
        
        if status != "processing":
            break
        
        time.sleep(3)  # Esperar 3s antes de próximo update
    
    return final_status
```

### 2. **Upload Component Refatorado** (`async_upload.py`)

Mudanças principais:

#### Antes (problemático):
```python
def render_job_progress(job_id: str):
    processor = AsyncProcessor()
    job = processor.get_job_status(job_id)
    
    if status == "processing":
        with st.spinner("Atualizando..."):  # ❌ Cria/destrói elemento
            time.sleep(1)  # ❌ Muito frequente
        st.rerun()  # ❌ Bloqueia TODA a aplicação
```

#### Depois (não-bloqueante):
```python
if "current_job_id" in st.session_state:
    from src.ui.components.progress_monitor import create_progress_monitor
    
    # ✅ Este monitor atualiza automaticamente usando placeholders
    final_status = create_progress_monitor(st.session_state.current_job_id)
    
    # ✅ Mostrar resultados finais
    if final_status and final_status["status"] == "completed":
        _show_job_results(final_status)
```

### 3. **Separação de Responsabilidades**

| Componente | Responsabilidade |
|-----------|-----------------|
| **async_upload.py** | Upload UI, seleção de arquivos, trigger de jobs |
| **progress_monitor.py** | Monitoramento de progresso em tempo real (não-bloqueante) |
| **async_processor.py** | Backend de processamento paralelo (ThreadPoolExecutor) |

## 🎯 Benefícios

### Performance
- ✅ **66% menos reruns**: 3s interval vs. 1s (20x/min vs. 60x/min)
- ✅ **Zero scroll jumping**: sem spinner que cria/destrói elemento
- ✅ **UI responsiva**: outras tabs permanecem funcionais durante upload

### UX
- ✅ **Navegação livre**: usuário pode ir para Reports, Chat, etc. durante upload
- ✅ **Feedback claro**: mensagens informam que interface continua utilizável
- ✅ **Progresso suave**: atualizações a cada 3s sem flickering excessivo

### Arquitetura
- ✅ **Modular**: progress monitor reutilizável
- ✅ **Testável**: componentes separados permitem testes isolados
- ✅ **Escalável**: fácil adicionar novos tipos de monitoramento

## 🔧 Como Funciona

### Fluxo de Execução

```
1. Usuário seleciona arquivos
   └─> render_async_upload_tab()

2. Clica "Processar"
   └─> AsyncProcessor.submit_job(files)
       └─> Retorna job_id
       └─> Salva em session_state.current_job_id

3. Monitor de progresso inicia
   └─> create_progress_monitor(job_id)
       └─> Cria placeholder = st.empty()
       └─> Loop while status == "processing":
           ├─> Atualiza placeholder (SEM st.rerun)
           ├─> time.sleep(3)
           └─> Re-checa status
       └─> Retorna final_status quando completo

4. Resultados exibidos
   └─> _show_job_results(final_status)
       ├─> Tab "Sucessos": lista documentos processados
       └─> Tab "Erros": lista falhas com detalhes
```

### Diferença Chave: Placeholder vs. Rerun

#### Com st.rerun() (ANTIGO - bloqueante):
```python
# PROBLEMA: Recarrega TODA a aplicação
st.progress(0.5)
st.metric("Total", 10)
time.sleep(1)
st.rerun()  # ❌ Bloqueia outras tabs, reinicializa tudo
```

#### Com st.empty() placeholder (NOVO - não-bloqueante):
```python
# SOLUÇÃO: Atualiza apenas o container específico
placeholder = st.empty()

with placeholder.container():
    st.progress(0.5)
    st.metric("Total", 10)

time.sleep(3)

with placeholder.container():  # ✅ Atualiza apenas este bloco
    st.progress(0.75)
    st.metric("Total", 15)
```

## 📊 Comparação de Performance

| Métrica | Antes (st.rerun) | Depois (placeholder) | Melhoria |
|---------|------------------|----------------------|----------|
| **Reruns/minuto** | 60 | 0 | 100% |
| **Updates/minuto** | 60 | 20 | 66% menos |
| **Tabs bloqueadas?** | Sim ❌ | Não ✅ | Desbloqueio total |
| **Scroll jumping?** | Sim ❌ | Não ✅ | Eliminado |
| **Interval de update** | 1s | 3s | 3x menos frequente |

## 🚀 Como Testar

### 1. Teste de Upload Normal
```bash
# 1. Iniciar aplicação
streamlit run src/ui/app.py

# 2. Ir para tab "Upload de Documentos"
# 3. Selecionar XML ou ZIP
# 4. Clicar "Processar Documentos"
# 5. Verificar:
#    - Progresso atualiza suavemente (a cada 3s)
#    - Não há scroll jumping
#    - Pode navegar para outras tabs durante processamento
```

### 2. Teste de Navegação Durante Processamento
```bash
# 1. Iniciar upload de arquivo grande (ZIP com muitos XMLs)
# 2. Enquanto processa, clicar em outras tabs:
#    - Chat
#    - Relatórios
#    - Estatísticas
# 3. Verificar que todas funcionam normalmente
# 4. Voltar para tab Upload
# 5. Progresso deve continuar atualizando
```

### 3. Teste de Múltiplos Jobs
```bash
# 1. Iniciar job 1 (upload de ZIP)
# 2. Sem esperar completar, navegar para tab History
# 3. Verificar que job aparece em "Jobs Ativos"
# 4. Voltar para Upload
# 5. Verificar que progresso continua
```

## 🔍 Debugging

### Verificar se Placeholder Está Funcionando

```python
# Adicionar logging em progress_monitor.py
logger.info(f"Updating placeholder - iteration {iteration}, status {status}")
```

### Monitorar Reruns

```python
# Adicionar em async_upload.py (início da função)
logger.info(f"render_async_upload_tab called - rerun count")
```

### Verificar Job Status

```python
# Terminal separado
python -c "
from src.ui.async_processor import AsyncProcessor
p = AsyncProcessor()
jobs = p.get_all_jobs()
for jid, job in jobs.items():
    print(f'{jid}: {job[\"status\"]} - {job[\"processed\"]}/{job[\"total\"]}')
"
```

## 📝 Notas de Implementação

### Por que não usar st.experimental_fragment?

**Resposta:** 
- `st.experimental_fragment` foi introduzido no Streamlit 1.30+
- Requer decorador `@st.experimental_fragment` em funções
- Ainda está em experimental (pode mudar API)
- Nossa solução com `st.empty()` placeholder é:
  - ✅ Estável (API pública desde Streamlit 0.8x)
  - ✅ Simples de entender
  - ✅ Não requer versão específica

### Limitações Conhecidas

1. **Timeout de 3 minutos**: Progress monitor para após 60 iterações × 3s = 180s
   - **Solução**: Aumentar `max_iterations` se necessário
   
2. **Não é real-time streaming**: Updates a cada 3s, não contínuos
   - **Solução**: Para updates mais frequentes, reduzir `time.sleep(3)` para `time.sleep(1)` (trade-off: mais load)

3. **Session state persiste**: Jobs ficam em memória até limpar
   - **Solução**: Botão "Limpar resultados" remove job do session_state

## 🎓 Aprendizados

### O que NÃO fazer em Streamlit

❌ **Usar st.rerun() em loops de atualização**
```python
while processing:
    update_ui()
    st.rerun()  # ❌ Bloqueia tudo
```

❌ **Criar/destruir elementos em loops**
```python
while processing:
    with st.spinner("Atualizando..."):  # ❌ Scroll jumping
        time.sleep(1)
```

### O que FAZER em Streamlit

✅ **Usar placeholders para updates locais**
```python
placeholder = st.empty()
while processing:
    with placeholder.container():
        update_component()  # ✅ Atualiza apenas este bloco
    time.sleep(3)
```

✅ **Processar em background com threads**
```python
executor = ThreadPoolExecutor(max_workers=5)
future = executor.submit(process_files, files)  # ✅ Não bloqueia UI
```

## 🔗 Referências

- [Streamlit st.empty() docs](https://docs.streamlit.io/library/api-reference/layout/st.empty)
- [Streamlit session_state guide](https://docs.streamlit.io/library/api-reference/session-state)
- [ThreadPoolExecutor docs](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)

## ✨ Próximos Passos

- [ ] Implementar WebSocket para updates verdadeiramente real-time (opcional)
- [ ] Adicionar persistência de jobs em SQLite (sobreviver a restarts)
- [ ] Criar dashboard de monitoramento com histórico de jobs
- [ ] Implementar cancelamento de jobs em progresso
- [ ] Adicionar retry automático para falhas temporárias
