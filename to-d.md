1. Report Generator Tool → Gráficos no chat (plotly inline)
2. Archiver Tool → Organização automática de XMLs
3. Progresso Visual → Barra de progresso em batch uploads
4. Classifier Tool: Classificação de centro de custo via LLM - existe classifier.py mas não integrado como LangChain tool
5. Validações API (Implementadas mas não Expostas) - necessario expor ao agente
   ✅ CNPJ via BrasilAPI: existe em external_validators.py mas não exposto como tool ao agente
   ✅ CEP via ViaCEP: idem - validador existe mas agente não pode usar diretamente
   ✅ NCM auto-download: implementado mas agente não pode consultar NCMs diretamente
