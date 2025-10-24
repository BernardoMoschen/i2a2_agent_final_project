# 🚀 Guia Rápido: Deploy no Streamlit Cloud

## TL;DR

**Arquivo principal para apontar no Streamlit Cloud:**

```
src/ui/app.py
```

---

## 📋 Passo a Passo Completo

### 1️⃣ Acesse Streamlit Cloud

🌐 https://share.streamlit.io

### 2️⃣ Clique em "New app"

### 3️⃣ Preencha os campos:

```
┌─────────────────────────────────────────────────┐
│ Repository:  BernardoMoschen/i2a2_agent_final  │
│              _project                           │
├─────────────────────────────────────────────────┤
│ Branch:      main                               │
├─────────────────────────────────────────────────┤
│ Main file:   src/ui/app.py  ⬅️ IMPORTANTE!    │
├─────────────────────────────────────────────────┤
│ App URL:     [seu-nome].streamlit.app          │
└─────────────────────────────────────────────────┘
```

### 4️⃣ (Opcional) Configure Secrets

Click "Advanced settings" → "Secrets":

```toml
# Adicione se quiser uma API key padrão para demo
GEMINI_API_KEY = "sua-chave-aqui"
```

**Nota**: Os usuários ainda podem inserir suas próprias chaves via interface!

### 5️⃣ Click "Deploy!"

⏳ Aguarde ~2-3 minutos para o build e deploy

✅ Seu app estará online em: `https://[seu-nome].streamlit.app`

---

## ⚠️ Avisos Importantes

### 🗄️ Banco de Dados

O SQLite no Streamlit Cloud é **efêmero** (reseta quando o app reinicia/dorme).

**Para produção**, considere:
- PostgreSQL (Supabase, ElephantSQL)
- Cloud storage para arquivos

### 💰 Limites (Free Tier)

- **RAM**: 1 GB
- **Storage**: Temporário
- **Sleep**: Após 7 dias sem uso

### 🔐 Segurança

**✅ NUNCA commite:**
- Chaves de API no código
- Arquivo `.streamlit/secrets.toml`
- Banco de dados com dados reais

**✅ SEMPRE use:**
- Secrets do Streamlit Cloud para chaves sensíveis
- Input do usuário para API keys (como já está implementado!)

---

## 🧪 Testar Localmente Antes

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute o Streamlit
streamlit run src/ui/app.py

# Abra http://localhost:8501
```

Se funcionar localmente, funcionará no cloud! ✅

---

## 📚 Recursos Úteis

- 📖 [Documentação Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud)
- 🔑 [Gerenciar Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- 🐛 [Troubleshooting](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/app-health)

---

## 🎯 Checklist Final

Antes de fazer deploy, verifique:

- [ ] Código está no GitHub (branch `main`)
- [ ] `requirements.txt` está na raiz
- [ ] Testou localmente: `streamlit run src/ui/app.py`
- [ ] Não há secrets hardcoded no código
- [ ] `.gitignore` exclui arquivos sensíveis

---

## 🆘 Problemas Comuns

### ❌ "No module named 'src'"

**Solução**: Certifique-se de usar `src/ui/app.py` (caminho completo)

### ❌ "Requirements installation failed"

**Solução**: Teste localmente:
```bash
pip install -r requirements.txt
```

### ❌ App muito lento

**Solução**: 
- Remova dependências não utilizadas
- Otimize queries ao banco
- Considere upgrade para plano pago

---

## ✨ Pronto!

Seu agente fiscal estará online e acessível para qualquer pessoa! 🎉

**URL de exemplo**: `https://fiscal-agent.streamlit.app`
