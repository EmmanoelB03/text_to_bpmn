import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import streamlit.components.v1 as components
import json
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configuração da Página
st.set_page_config(
    page_title="Gerador BPMN AI",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .exemplo-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .exemplo-card:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header Principal
st.markdown("""
<div class="main-header">
    <h1>🏭 Gerador de BPMN com IA</h1>
    <p style="margin: 0; opacity: 0.9;">Transforme descrições em diagramas BPMN 2.0 profissionais</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("⚙️ Configurações")
    
    with st.expander("🔑 API Key Google AI", expanded=True):
        api_key = st.text_input(
            "Cole sua chave aqui:",
            type="password",
            help="Obtenha grátis em: https://aistudio.google.com/app/apikey"
        )
        
        if api_key:
            st.success("✅ Configurada!")
        else:
            st.info("👆 Configure para começar")
    
    st.divider()
    
    # Modelo
    modelo_selecionado = st.selectbox(
        "🤖 Modelo",
        ["gemini-1.5-flash-exp", "gemini-1.5-flash", "gemini-2.5-pro"],
        help="Flash é mais rápido, Pro é mais preciso"
    )
    
    temperatura = st.slider(
        "🌡️ Criatividade",
        0.0, 1.0, 0.1, 0.1,
        help="0 = preciso, 1 = criativo"
    )
    
    st.divider()
    
    # Opções avançadas
    with st.expander("🎨 Opções de Visualização"):
        mostrar_json = st.checkbox("Exibir JSON intermediário", value=False)
        mostrar_xml = st.checkbox("Exibir código XML", value=False)
    
    st.divider()
    
    # Informações
    st.markdown("### 📊 Sobre")
    st.info("""
    **Stack Técnica:**
    - 🤖 Gemini via LangChain
    - 📊 BPMN 2.0 válido
    - 🎨 bpmn-js viewer
    - ⚡ Geração em ~2s
    
    **Compatível com:**
    - Camunda Modeler
    - Bonita BPM
    - Ferramentas BPMN 2.0
    """)
    
    st.divider()
    
    # Links úteis
    st.markdown("### 🔗 Links Úteis")
    st.markdown("""
    - [Google AI Studio](https://aistudio.google.com/)
    - [Camunda Modeler](https://camunda.com/download/modeler/)
    - [Documentação BPMN](https://www.omg.org/spec/BPMN/)
    """)

# --- FUNÇÕES AUXILIARES ---

def extrair_json(texto: str) -> dict:
    """Extrai JSON de texto com múltiplas estratégias"""
    if not texto:
        raise ValueError("Texto vazio retornado pelo modelo")
    
    texto_limpo = re.sub(r'```json', '', texto, flags=re.IGNORECASE)
    texto_limpo = re.sub(r'```', '', texto_limpo)
    
    inicio = texto_limpo.find('{')
    fim = texto_limpo.rfind('}')
    
    if inicio == -1 or fim == -1:
        raise ValueError("JSON não encontrado na resposta")
    
    json_str = texto_limpo[inicio : fim + 1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        json_str_fixed = re.sub(r',\s*}', '}', json_str)
        json_str_fixed = re.sub(r',\s*]', ']', json_str_fixed)
        return json.loads(json_str_fixed)

def json_to_bpmn_xml(data: dict) -> str:
    """Converte JSON em XML BPMN 2.0"""
    root = ET.Element("bpmn:definitions")
    root.set("xmlns:bpmn", "http://www.omg.org/spec/BPMN/20100524/MODEL")
    root.set("xmlns:bpmndi", "http://www.omg.org/spec/BPMN/20100524/DI")
    root.set("xmlns:dc", "http://www.omg.org/spec/DD/20100524/DC")
    root.set("xmlns:di", "http://www.omg.org/spec/DD/20100524/DI")
    root.set("id", "Definitions_1")
    root.set("targetNamespace", "http://bpmn.io/schema/bpmn")
    
    process = ET.SubElement(root, "bpmn:process")
    process.set("id", "Process_1")
    process.set("isExecutable", "true")
    
    elementos = data.get("elementos", [])
    fluxos = data.get("fluxos", [])
    node_map = {}
    
    for elem in elementos:
        tipo = elem.get("tipo", "task")
        elem_id = elem.get("id", "Element_1")
        nome = elem.get("nome", "")
        
        tag_map = {
            "startEvent": "bpmn:startEvent",
            "endEvent": "bpmn:endEvent",
            "task": "bpmn:task",
            "userTask": "bpmn:userTask",
            "serviceTask": "bpmn:serviceTask",
            "exclusiveGateway": "bpmn:exclusiveGateway",
            "parallelGateway": "bpmn:parallelGateway"
        }
        
        event = ET.SubElement(process, tag_map.get(tipo, "bpmn:task"))
        event.set("id", elem_id)
        if nome:
            event.set("name", nome)
        node_map[elem_id] = event
    
    for i, fluxo in enumerate(fluxos):
        flow = ET.SubElement(process, "bpmn:sequenceFlow")
        flow_id = fluxo.get("id", f"Flow_{i+1}")
        flow.set("id", flow_id)
        flow.set("sourceRef", fluxo.get("origem"))
        flow.set("targetRef", fluxo.get("destino"))
        
        origem = node_map.get(fluxo.get("origem"))
        destino = node_map.get(fluxo.get("destino"))
        if origem is not None:
            outgoing = ET.SubElement(origem, "bpmn:outgoing")
            outgoing.text = flow_id
        if destino is not None:
            incoming = ET.SubElement(destino, "bpmn:incoming")
            incoming.text = flow_id
    
    diagram = ET.SubElement(root, "bpmndi:BPMNDiagram")
    diagram.set("id", "BPMNDiagram_1")
    plane = ET.SubElement(diagram, "bpmndi:BPMNPlane")
    plane.set("id", "BPMNPlane_1")
    plane.set("bpmnElement", "Process_1")
    
    x_pos = 150
    y_base = 150
    
    for elem in elementos:
        elem_id = elem.get("id")
        tipo = elem.get("tipo", "task")
        
        shape = ET.SubElement(plane, "bpmndi:BPMNShape")
        shape.set("id", f"Shape_{elem_id}")
        shape.set("bpmnElement", elem_id)
        
        bounds = ET.SubElement(shape, "dc:Bounds")
        
        if tipo in ["startEvent", "endEvent"]:
            width, height = 36, 36
        elif "Gateway" in tipo:
            width, height = 50, 50
        else:
            width, height = 100, 80
        
        y_pos = y_base - (height / 2)
        bounds.set("x", str(x_pos))
        bounds.set("y", str(y_pos))
        bounds.set("width", str(width))
        bounds.set("height", str(height))
        
        elem['_x_center'] = x_pos + (width / 2)
        elem['_y_center'] = y_base
        x_pos += 200
    
    for i, fluxo in enumerate(fluxos):
        edge = ET.SubElement(plane, "bpmndi:BPMNEdge")
        edge.set("id", f"Edge_{fluxo.get('id', f'Flow_{i+1}')}")
        edge.set("bpmnElement", fluxo.get("id", f"Flow_{i+1}"))
        
        origem = next((e for e in elementos if e.get("id") == fluxo.get("origem")), None)
        destino = next((e for e in elementos if e.get("id") == fluxo.get("destino")), None)
        
        if origem and destino:
            offset_origem = 18 if 'Event' in origem.get('tipo', '') else 50
            offset_destino = 18 if 'Event' in destino.get('tipo', '') else 50
            
            wp1 = ET.SubElement(edge, "di:waypoint")
            wp1.set("x", str(origem['_x_center'] + offset_origem))
            wp1.set("y", str(origem['_y_center']))
            
            wp2 = ET.SubElement(edge, "di:waypoint")
            wp2.set("x", str(destino['_x_center'] - offset_destino))
            wp2.set("y", str(destino['_y_center']))
    
    xml_string = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent="  ")
    return '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

def create_bpmn_viewer(xml_content: str) -> str:
    """Cria visualizador BPMN interativo"""
    xml_escaped = xml_content.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://unpkg.com/bpmn-js@17.11.1/dist/bpmn-viewer.production.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }}
            #canvas {{ width: 100%; height: 650px; background: #fafafa; border-radius: 8px; border: 1px solid #e0e0e0; }}
            .controls {{
                position: absolute;
                top: 15px;
                right: 15px;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                display: flex;
                gap: 8px;
                z-index: 1000;
            }}
            button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            .zoom-display {{
                background: #f8f9fa;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
                color: #333;
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div class="controls">
            <button onclick="zoomIn()">🔍 +</button>
            <button onclick="zoomOut()">🔍 −</button>
            <button onclick="zoomFit()">⚡ Ajustar</button>
            <button onclick="downloadSVG()">📥 SVG</button>
            <div class="zoom-display" id="zoom">100%</div>
        </div>
        <div id="canvas"></div>
        <script>
            const viewer = new BpmnJS({{ container: '#canvas' }});
            
            viewer.importXML(`{xml_escaped}`).then(() => {{
                viewer.get('canvas').zoom('fit-viewport');
                updateZoom();
            }}).catch(err => {{
                console.error('Erro:', err);
                document.getElementById('canvas').innerHTML = 
                    '<div style="padding: 50px; text-align: center; color: #d32f2f;">❌ Erro ao renderizar diagrama</div>';
            }});
            
            function zoomIn() {{
                const canvas = viewer.get('canvas');
                canvas.zoom(canvas.zoom() + 0.1);
                updateZoom();
            }}
            
            function zoomOut() {{
                const canvas = viewer.get('canvas');
                canvas.zoom(canvas.zoom() - 0.1);
                updateZoom();
            }}
            
            function zoomFit() {{
                viewer.get('canvas').zoom('fit-viewport');
                updateZoom();
            }}
            
            function updateZoom() {{
                const zoom = Math.round(viewer.get('canvas').zoom() * 100);
                document.getElementById('zoom').textContent = zoom + '%';
            }}
            
            async function downloadSVG() {{
                try {{
                    const {{ svg }} = await viewer.saveSVG();
                    const blob = new Blob([svg], {{ type: 'image/svg+xml' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'diagrama-bpmn.svg';
                    a.click();
                    URL.revokeObjectURL(url);
                }} catch (err) {{
                    console.error('Erro ao baixar:', err);
                }}
            }}
        </script>
    </body>
    </html>
    """

PROMPT_SYSTEM = """Você é um especialista em BPMN 2.0. Converta a descrição em JSON estruturado.

ESTRUTURA OBRIGATÓRIA:
{
  "processo": "Nome do Processo",
  "elementos": [
    {"id": "StartEvent_1", "tipo": "startEvent", "nome": "Início"},
    {"id": "Task_1", "tipo": "task", "nome": "Descrição da Tarefa"},
    {"id": "EndEvent_1", "tipo": "endEvent", "nome": "Fim"}
  ],
  "fluxos": [
    {"id": "Flow_1", "origem": "StartEvent_1", "destino": "Task_1"},
    {"id": "Flow_2", "origem": "Task_1", "destino": "EndEvent_1"}
  ]
}

TIPOS: startEvent, endEvent, task, userTask, serviceTask, exclusiveGateway, parallelGateway
RETORNE APENAS O JSON, SEM MARKDOWN OU EXPLICAÇÕES."""

def gerar_bpmn(descricao: str, modelo: str, temp: float):
    """Gera BPMN usando Gemini via LangChain"""
    if not api_key:
        raise Exception("Configure a API Key na barra lateral!")
    
    llm = ChatGoogleGenerativeAI(
        model=modelo,
        temperature=temp,
        google_api_key=api_key,
        convert_system_message_to_human=True
    )
    
    messages = [
        SystemMessage(content=PROMPT_SYSTEM),
        HumanMessage(content=f"Descrição: {descricao}")
    ]
    
    response = llm.invoke(messages)
    return extrair_json(response.content)

# --- EXEMPLOS ---
EXEMPLOS = {
    "✈️ Aprovação de Férias": {
        "desc": "Processo simples de aprovação",
        "texto": """Processo de aprovação de férias:
1. Funcionário solicita férias no sistema
2. Gestor direto analisa a solicitação
3. Se aprovado: RH registra no sistema e notifica funcionário
4. Se rejeitado: Sistema notifica funcionário com justificativa
5. Processo finaliza"""
    },
    "🛒 Compra com Aprovação": {
        "desc": "Fluxo com decisão baseada em valor",
        "texto": """Processo de compra de materiais:
1. Funcionário cria requisição no sistema
2. Sistema verifica automaticamente o valor
3. Se valor < R$ 1.000: Aprovação automática
4. Se valor ≥ R$ 1.000: Diretor financeiro precisa aprovar
5. Após aprovação: Setor de compras executa a compra
6. Sistema confirma recebimento e finaliza"""
    },
    "⚡ Onboarding Paralelo": {
        "desc": "Tarefas executadas simultaneamente",
        "texto": """Processo de integração de novo funcionário:
1. RH inicia o processo de onboarding
2. Executar em paralelo:
   - TI cria email corporativo e acessos
   - Administrativo libera sistemas internos
   - Facilities prepara workstation e equipamentos
3. Após conclusão das 3 tarefas: Gestor agenda reunião de boas-vindas
4. Funcionário assina documentos trabalhistas
5. Processo de integração completo"""
    },
    "📞 Suporte Multi-Canal": {
        "desc": "Roteamento por tipo de solicitação",
        "texto": """Fluxo de atendimento ao cliente:
1. Cliente abre ticket de suporte
2. Sistema classifica automaticamente o tipo
3. Decisão por categoria:
   - Técnico → Encaminha para equipe de TI
   - Comercial → Encaminha para equipe de Vendas
   - Financeiro → Encaminha para equipe Financeira
4. Área responsável resolve a solicitação
5. Cliente confirma resolução
6. Sistema fecha o ticket automaticamente"""
    }
}

# --- INTERFACE PRINCIPAL ---

# Seção de Exemplos
st.markdown("### 💡 Exemplos Rápidos")
cols_exemplos = st.columns(4)

for idx, (titulo, dados) in enumerate(EXEMPLOS.items()):
    with cols_exemplos[idx % 4]:
        if st.button(titulo, use_container_width=True, key=f"ex_{idx}"):
            st.session_state['texto_processo'] = dados['texto']
            st.rerun()

st.divider()

# Área de Input
texto_input = st.text_area(
    "📝 Descreva seu processo de negócio:",
    value=st.session_state.get('texto_processo', ''),
    height=200,
    placeholder="Exemplo: O processo inicia quando o cliente faz um pedido. O sistema verifica o estoque. Se houver estoque, prepara o envio. Se não houver, notifica o cliente. O processo termina após a entrega.",
    help="Descreva passo a passo o fluxo do seu processo"
)

# Botões de Ação
col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1])

with col_btn1:
    btn_gerar = st.button("🚀 Gerar Diagrama BPMN", type="primary", use_container_width=True)

with col_btn2:
    if st.button("🔄 Limpar", use_container_width=True):
        st.session_state['texto_processo'] = ''
        st.rerun()

with col_btn3:
    st.button("❓ Ajuda", use_container_width=True)

# Processamento
if btn_gerar and texto_input and api_key:
    
    with st.spinner("🤖 IA trabalhando..."):
        inicio = time.time()
        
        try:
            # Gerar JSON
            json_data = gerar_bpmn(texto_input, modelo_selecionado, temperatura)
            
            # Converter para XML
            xml_data = json_to_bpmn_xml(json_data)
            
            tempo_total = time.time() - inicio
            
            # Métricas
            st.success(f"✅ Diagrama gerado em {tempo_total:.2f} segundos!")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("⏱️ Tempo", f"{tempo_total:.1f}s")
            col_m2.metric("📦 Elementos", len(json_data.get("elementos", [])))
            col_m3.metric("➡️ Fluxos", len(json_data.get("fluxos", [])))
            col_m4.metric("📄 Linhas XML", len(xml_data.split('\n')))
            
            st.divider()
            
            # Visualização
            st.markdown("### 🎨 Diagrama Interativo")
            html_viewer = create_bpmn_viewer(xml_data)
            components.html(html_viewer, height=700, scrolling=False)
            
            # Debug opcional
            if mostrar_json:
                st.divider()
                with st.expander("🔍 JSON Intermediário"):
                    st.json(json_data)
            
            if mostrar_xml:
                st.divider()
                with st.expander("📄 Código XML BPMN 2.0"):
                    st.code(xml_data, language="xml", line_numbers=True)
            
            # Downloads
            st.divider()
            st.markdown("### 📥 Downloads")
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                st.download_button(
                    "⬇️ Baixar .bpmn",
                    xml_data,
                    "processo.bpmn",
                    "application/xml",
                    use_container_width=True
                )
            
            with col_d2:
                st.download_button(
                    "⬇️ Baixar JSON",
                    json.dumps(json_data, indent=2, ensure_ascii=False),
                    "processo.json",
                    "application/json",
                    use_container_width=True
                )
            
            with col_d3:
                st.info(f"🎯 Modelo: {modelo_selecionado}")
            
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")
            with st.expander("🔍 Detalhes do Erro"):
                st.exception(e)

elif btn_gerar and not api_key:
    st.warning("⚠️ Configure sua API Key na barra lateral para continuar!")

elif btn_gerar and not texto_input:
    st.warning("⚠️ Descreva o processo antes de gerar o diagrama!")

# Footer
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
col_f1.caption("⚡ Powered by Google Gemini")
col_f2.caption("📊 BPMN 2.0 Compliant")
col_f3.caption("🎨 Built with Streamlit")