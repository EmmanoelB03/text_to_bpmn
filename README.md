[readme_bpmn_generator.md](https://github.com/user-attachments/files/23840005/readme_bpmn_generator.md)
# 🏭 Gerador de BPMN com IA

Transforme descrições em texto para diagramas BPMN 2.0 profissionais usando Google Gemini.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📖 O que é?

Uma aplicação web que converte descrições de processos em diagramas BPMN válidos automaticamente.

**Exemplo:**
```
Você escreve: "Funcionário solicita férias, gestor aprova, RH registra"
   ↓
App gera: Diagrama BPMN completo + arquivo .bpmn
```

## 🚀 Como usar (3 passos)

### 1️⃣ Instalar

```bash
# Clone o projeto
git clone https://github.com/seu-usuario/bpmn-ai-generator.git
cd bpmn-ai-generator

# Crie ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2️⃣ Conseguir API Key (GRÁTIS)

1. Acesse: https://aistudio.google.com/app/apikey
2. Clique em **"Create API Key"**
3. Copie a chave

### 3️⃣ Rodar

```bash
streamlit run app.py
```

Abra o navegador em `http://localhost:8501`, cole sua API Key e pronto! 🎉

## 💡 Exemplo Rápido

**Digite isso:**
```
Processo de compra:
1. Funcionário cria pedido
2. Se valor < R$1000: aprova automático
3. Se valor >= R$1000: gerente aprova
4. Compras executa
5. Finaliza
```

**Resultado:** Diagrama BPMN com decisão, tarefas e eventos!

## 📥 Exportar

- ⬇️ `.bpmn` → Abrir no Camunda Modeler
- ⬇️ `.json` → Estrutura de dados
- ⬇️ `.svg` → Imagem do diagrama

## 🛠️ Tecnologias

- **Streamlit** - Interface web
- **Google Gemini** - IA para geração
- **LangChain** - Framework LLM
- **bpmn-js** - Visualização

## 📦 Estrutura

```
bpmn-ai-generator/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências
└── README.md          # Este arquivo
```

## ❓ Problemas Comuns

**"429 Quota exceeded"**
- Esperou 1 minuto ou troque para `gemini-1.5-flash`

**"API Key inválida"**
- Gere uma nova em https://aistudio.google.com

**Diagrama estranho?**
- Seja mais específico na descrição
- Use: "Se X então Y, senão Z"

## 📝 Licença

MIT - Use livremente!

## 🤝 Contribuir

1. Fork o projeto
2. Crie sua feature (`git checkout -b feature/nova`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova`)
5. Abra um Pull Request

