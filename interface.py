import streamlit as st
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

st.set_page_config(page_title="Gerador BPMN - JSON to XML", layout="wide")
st.title("🏭 Gerador de BPMN (JSON → XML Strategy)")
st.caption("🎯 Estratégia otimizada: LLM gera JSON estruturado, Python converte para BPMN XML válido")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    modelo = st.selectbox(
        "Modelo:",
        ["deepseek-r1:7b", "llama3.2", "qwen2.5:14b", "mistral:7b"],
        help="DeepSeek R1 recomendado para melhor JSON"
    )
    
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    
    st.divider()
    
    st.header("💡 Vantagens desta Abordagem")
    st.success("""
    ✅ **LLMs são melhores com JSON**
    - Menos erros de sintaxe
    - Validação automática
    - Mais eficiente em tokens
    
    ✅ **Python garante XML válido**
    - Namespaces corretos
    - Estrutura BPMN perfeita
    - Sem erros de formatação
    """)
    
    with st.expander("📦 Instalar modelo"):
        st.code(f"ollama pull {modelo}", language="bash")

# Função para converter JSON para BPMN XML
def json_to_bpmn_xml(data: dict) -> str:
    """Converte estrutura JSON em XML BPMN 2.0 válido"""
    
    # Criar o XML raiz
    root = ET.Element("bpmn:definitions")
    root.set("xmlns:bpmn", "http://www.omg.org/spec/BPMN/20100524/MODEL")
    root.set("xmlns:bpmndi", "http://www.omg.org/spec/BPMN/20100524/DI")
    root.set("xmlns:dc", "http://www.omg.org/spec/DD/20100524/DC")
    root.set("xmlns:di", "http://www.omg.org/spec/DD/20100524/DI")
    root.set("id", "Definitions_1")
    root.set("targetNamespace", "http://bpmn.io/schema/bpmn")
    
    # Criar processo
    process = ET.SubElement(root, "bpmn:process")
    process.set("id", "Process_1")
    process.set("isExecutable", "true")
    
    # Adicionar elementos do processo
    elementos = data.get("elementos", [])
    fluxos = data.get("fluxos", [])
    
    for elem in elementos:
        tipo = elem.get("tipo", "task")
        elem_id = elem.get("id", "Element_1")
        nome = elem.get("nome", "")
        
        if tipo == "startEvent":
            event = ET.SubElement(process, "bpmn:startEvent")
        elif tipo == "endEvent":
            event = ET.SubElement(process, "bpmn:endEvent")
        elif tipo == "task":
            event = ET.SubElement(process, "bpmn:task")
        elif tipo == "userTask":
            event = ET.SubElement(process, "bpmn:userTask")
        elif tipo == "serviceTask":
            event = ET.SubElement(process, "bpmn:serviceTask")
        elif tipo == "exclusiveGateway":
            event = ET.SubElement(process, "bpmn:exclusiveGateway")
        elif tipo == "parallelGateway":
            event = ET.SubElement(process, "bpmn:parallelGateway")
        else:
            event = ET.SubElement(process, "bpmn:task")
        
        event.set("id", elem_id)
        if nome:
            event.set("name", nome)
    
    # Adicionar fluxos
    for i, fluxo in enumerate(fluxos):
        flow = ET.SubElement(process, "bpmn:sequenceFlow")
        flow.set("id", fluxo.get("id", f"Flow_{i+1}"))
        flow.set("sourceRef", fluxo.get("origem"))
        flow.set("targetRef", fluxo.get("destino"))
        if "nome" in fluxo:
            flow.set("name", fluxo["nome"])
    
    # Criar diagrama BPMN
    diagram = ET.SubElement(root, "bpmndi:BPMNDiagram")
    diagram.set("id", "BPMNDiagram_1")
    
    plane = ET.SubElement(diagram, "bpmndi:BPMNPlane")
    plane.set("id", "BPMNPlane_1")
    plane.set("bpmnElement", "Process_1")
    
    # Posicionar elementos visualmente
    x_pos = 100
    y_base = 100
    
    for elem in elementos:
        elem_id = elem.get("id", "Element_1")
        tipo = elem.get("tipo", "task")
        
        shape = ET.SubElement(plane, "bpmndi:BPMNShape")
        shape.set("id", f"Shape_{elem_id}")
        shape.set("bpmnElement", elem_id)
        
        bounds = ET.SubElement(shape, "dc:Bounds")
        
        if tipo in ["startEvent", "endEvent"]:
            bounds.set("x", str(x_pos))
            bounds.set("y", str(y_base))
            bounds.set("width", "36")
            bounds.set("height", "36")
            y_center = y_base + 18
        elif tipo in ["exclusiveGateway", "parallelGateway"]:
            bounds.set("x", str(x_pos))
            bounds.set("y", str(y_base - 10))
            bounds.set("width", "50")
            bounds.set("height", "50")
            y_center = y_base + 15
        else:  # tasks
            bounds.set("x", str(x_pos))
            bounds.set("y", str(y_base - 20))
            bounds.set("width", "100")
            bounds.set("height", "80")
            y_center = y_base + 20
        
        # Guardar posição central para os fluxos
        elem['_x_center'] = x_pos + (36 if tipo in ["startEvent", "endEvent"] else 50)
        elem['_y_center'] = y_center
        
        x_pos += 200
    
    # Criar edges (fluxos visuais)
    for i, fluxo in enumerate(fluxos):
        edge = ET.SubElement(plane, "bpmndi:BPMNEdge")
        edge.set("id", f"Edge_{fluxo.get('id', f'Flow_{i+1}')}")
        edge.set("bpmnElement", fluxo.get("id", f"Flow_{i+1}"))
        
        # Encontrar elementos de origem e destino
        origem_elem = next((e for e in elementos if e.get("id") == fluxo.get("origem")), None)
        destino_elem = next((e for e in elementos if e.get("id") == fluxo.get("destino")), None)
        
        if origem_elem and destino_elem:
            wp1 = ET.SubElement(edge, "di:waypoint")
            wp1.set("x", str(origem_elem.get('_x_center', 100)))
            wp1.set("y", str(origem_elem.get('_y_center', 118)))
            
            wp2 = ET.SubElement(edge, "di:waypoint")
            wp2.set("x", str(destino_elem.get('_x_center', 200)))
            wp2.set("y", str(destino_elem.get('_y_center', 118)))
    
    # Formatar XML com indentação
    xml_string = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remover linhas vazias extras
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    return '\n'.join(lines)

# Prompt otimizado para JSON
TEMPLATE_JSON = """Você é um especialista em modelagem de processos BPMN.

Sua tarefa é analisar a descrição do processo e retornar um JSON estruturado que representa o fluxo BPMN.

ESTRUTURA DO JSON (OBRIGATÓRIA):
{{
  "processo": "Nome do Processo",
  "elementos": [
    {{
      "id": "StartEvent_1",
      "tipo": "startEvent",
      "nome": "Início"
    }},
    {{
      "id": "Task_1",
      "tipo": "task",
      "nome": "Nome da Tarefa"
    }},
    {{
      "id": "EndEvent_1",
      "tipo": "endEvent",
      "nome": "Fim"
    }}
  ],
  "fluxos": [
    {{
      "id": "Flow_1",
      "origem": "StartEvent_1",
      "destino": "Task_1"
    }},
    {{
      "id": "Flow_2",
      "origem": "Task_1",
      "destino": "EndEvent_1"
    }}
  ]
}}

TIPOS DE ELEMENTOS DISPONÍVEIS:
- startEvent: Evento de início (sempre o primeiro)
- endEvent: Evento de fim (sempre o último)
- task: Tarefa genérica
- userTask: Tarefa executada por humano
- serviceTask: Tarefa automatizada/sistema
- exclusiveGateway: Decisão (escolhe um caminho)
- parallelGateway: Execução paralela

REGRAS:
1. Sempre comece com startEvent
2. Sempre termine com endEvent
3. Use IDs sequenciais (Task_1, Task_2, Gateway_1, etc.)
4. Cada fluxo conecta dois elementos (origem → destino)
5. Gateways devem ter múltiplos fluxos de saída
6. Retorne APENAS o JSON, sem explicações

DESCRIÇÃO DO PROCESSO:
{descricao}

Retorne o JSON estruturado:"""

# Inicializar LLM
@st.cache_resource
def get_llm(model, temp):
    return OllamaLLM(model=model, temperature=temp)

try:
    llm = get_llm(modelo, temperature)
    prompt = PromptTemplate(
        input_variables=["descricao"],
        template=TEMPLATE_JSON
    )
    
    # Parser JSON
    json_parser = JsonOutputParser()
    chain = prompt | llm
    
except Exception as e:
    st.error(f"❌ Erro ao inicializar: {e}")
    st.stop()

# Exemplos
EXEMPLOS = {
    "📝 Selecione...": "",
    "✈️ Aprovação de Férias": """
    Processo de aprovação de férias:
    1. Funcionário solicita férias
    2. Gestor analisa
    3. Se aprovado: RH registra
    4. Se rejeitado: Notifica funcionário
    5. Finaliza
    """,
    "🛒 Compra com Aprovação": """
    Compra de material:
    1. Funcionário solicita
    2. Verifica valor
    3. Se < R$1000: Aprova direto
    4. Se >= R$1000: Diretor aprova
    5. Compras executa
    6. Finaliza
    """,
    "⚡ Tarefas Paralelas": """
    Onboarding:
    1. Inicia processo
    2. Executa em paralelo:
       - Criar email
       - Liberar acessos
       - Preparar equipamento
    3. Agenda reunião
    4. Finaliza
    """
}

# Interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Descrição do Processo")
    
    exemplo = st.selectbox("💡 Exemplos:", list(EXEMPLOS.keys()))
    
    texto = st.text_area(
        "Descreva o processo:",
        value=EXEMPLOS[exemplo],
        height=350,
        placeholder="Descreva passo a passo..."
    )
    
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        btn = st.button("🚀 Gerar BPMN", type="primary", use_container_width=True)
    
    with col_btn2:
        if st.button("🔄", use_container_width=True):
            st.rerun()

with col2:
    st.subheader("📄 Resultado")
    
    if btn and texto:
        
        # ETAPA 1: Gerar JSON
        with st.spinner(f"🤖 {modelo} gerando JSON estruturado..."):
            try:
                resposta = chain.invoke({"descricao": texto})
                
                # Limpar resposta
                json_limpo = resposta.strip()
                
                # Remover markdown
                if "```json" in json_limpo:
                    json_limpo = json_limpo.split("```json")[1].split("```")[0]
                elif "```" in json_limpo:
                    json_limpo = json_limpo.split("```")[1].split("```")[0]
                
                json_limpo = json_limpo.strip()
                
                # Tentar parsear JSON
                try:
                    dados_json = json.loads(json_limpo)
                    st.success("✅ JSON estruturado gerado!")
                    
                    # Mostrar JSON
                    with st.expander("🔍 Ver JSON intermediário", expanded=False):
                        st.json(dados_json)
                    
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON inválido: {e}")
                    st.code(json_limpo, language="json")
                    st.stop()
                
                # ETAPA 2: Converter para XML
                with st.spinner("🔄 Convertendo JSON → XML BPMN..."):
                    try:
                        xml_bpmn = json_to_bpmn_xml(dados_json)
                        
                        st.success("✅ BPMN XML gerado com sucesso!")
                        
                        # Estatísticas
                        num_elementos = len(dados_json.get("elementos", []))
                        num_fluxos = len(dados_json.get("fluxos", []))
                        
                        col_s1, col_s2 = st.columns(2)
                        col_s1.metric("📦 Elementos", num_elementos)
                        col_s2.metric("➡️ Fluxos", num_fluxos)
                        
                        # Exibir XML
                        st.code(xml_bpmn, language="xml", line_numbers=True)
                        
                        # Download
                        st.download_button(
                            "⬇️ Baixar .bpmn",
                            xml_bpmn,
                            f"processo_{modelo.replace(':', '_')}.bpmn",
                            "application/xml",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Erro na conversão XML: {e}")
                        st.info("Verifique a estrutura do JSON gerado")
                
            except Exception as e:
                st.error(f"❌ Erro: {e}")
                st.info("💡 Verifique se o Ollama está rodando: `ollama serve`")
    
    elif btn:
        st.warning("⚠️ Descreva o processo primeiro!")

# Footer
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
col_f1.caption(f"🤖 {modelo}")
col_f2.caption("📊 JSON → XML")
col_f3.caption("🆓 100% Open Source")