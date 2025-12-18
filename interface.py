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
        ["gemini-2.5-flash", "gemini-2.5-pro","gemma-3-27b-it"],
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
    """Converte JSON em XML BPMN 2.0 com suporte a Pools e Lanes"""
    
    # Namespaces
    ns = {
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "dc": "http://www.omg.org/spec/DD/20100524/DC",
        "di": "http://www.omg.org/spec/DD/20100524/DI"
    }

    # Criar Root
    root = ET.Element("bpmn:definitions")
    for prefix, uri in ns.items():
        root.set(f"xmlns:{prefix}", uri)
    
    root.set("id", "Definitions_1")
    root.set("targetNamespace", "http://bpmn.io/schema/bpmn")
    
    elementos = data.get("elementos", [])
    fluxos = data.get("fluxos", [])
    
    # 1. Identificar Papéis (Lanes) únicos
    papeis = []
    seen_roles = set()
    
    # Normalizar papéis para evitar duplicatas por case sensitive
    for elem in elementos:
        raw_role = elem.get("papel", "Geral").strip()
        role_key = raw_role.lower()
        elem['_role_normalized'] = role_key  # Guardar para uso posterior
        elem['_role_display'] = raw_role
        
        if role_key not in seen_roles:
            papeis.append(raw_role)
            seen_roles.add(role_key)
    
    # Se não houver papéis, cria um padrão
    if not papeis: 
        papeis = ["Processo Principal"]

    # Mapa de Papel -> Índice (para calcular Y)
    role_map = {p.lower(): i for i, p in enumerate(papeis)}
    
    # 2. Estrutura de Colaboração
    collaboration = ET.SubElement(root, "bpmn:collaboration")
    collaboration.set("id", "Collaboration_1")
    
    participant = ET.SubElement(collaboration, "bpmn:participant")
    participant.set("id", "Participant_1")
    participant.set("name", data.get("processo", "Processo de Negócio"))
    participant.set("processRef", "Process_1")
    
    # 3. Processo e LaneSet
    process = ET.SubElement(root, "bpmn:process")
    process.set("id", "Process_1")
    process.set("isExecutable", "false")
    
    lane_set = ET.SubElement(process, "bpmn:laneSet")
    lane_set.set("id", "LaneSet_1")
    
    lane_ids = {} # Map role -> lane_id
    
    for i, papel in enumerate(papeis):
        lane_id = f"Lane_{i}"
        lane = ET.SubElement(lane_set, "bpmn:lane")
        lane.set("id", lane_id)
        lane.set("name", papel)
        lane_ids[papel.lower()] = lane_id
        
        # Adicionar flowNodeRef para elementos deste papel
        for elem in elementos:
            if elem.get('_role_normalized') == papel.lower():
                ref = ET.SubElement(lane, "bpmn:flowNodeRef")
                ref.text = elem.get("id")
    
    # 4. Criar Elementos no Processo
    node_map = {}
    
    tag_map = {
        "startEvent": "bpmn:startEvent",
        "endEvent": "bpmn:endEvent",
        "task": "bpmn:task",
        "userTask": "bpmn:userTask",
        "serviceTask": "bpmn:serviceTask",
        "exclusiveGateway": "bpmn:exclusiveGateway",
        "parallelGateway": "bpmn:parallelGateway"
    }

    for elem in elementos:
        tipo = elem.get("tipo", "task")
        bpmn_tag = tag_map.get(tipo, "bpmn:task")
        
        node = ET.SubElement(process, bpmn_tag)
        node.set("id", elem.get("id"))
        if elem.get("nome"):
            node.set("name", elem.get("nome"))
            
        node_map[elem.get("id")] = node

    # 5. Criar Fluxos
    for fluxo in fluxos:
        flow = ET.SubElement(process, "bpmn:sequenceFlow")
        flow.set("id", fluxo.get("id"))
        flow.set("sourceRef", fluxo.get("origem"))
        flow.set("targetRef", fluxo.get("destino"))
        
        # Conectar nos nós
        src = node_map.get(fluxo.get("origem"))
        tgt = node_map.get(fluxo.get("destino"))
        if src is not None:
            out_node = ET.SubElement(src, "bpmn:outgoing")
            out_node.text = fluxo.get("id")
        if tgt is not None:
            in_node = ET.SubElement(tgt, "bpmn:incoming")
            in_node.text = fluxo.get("id")

    # === CÁLCULO DE LAYOUT (DI) ===
    
    # Configurações
    LANE_HEIGHT = 200
    LANE_HEADER_WIDTH = 30
    START_X = 150  # Margem esquerda
    ITEM_WIDTH = 100
    ITEM_SPACING = 160
    
    # Construir grafo para definir eixo X (níveis)
    graph_out = {e['id']: [] for e in elementos}
    in_degree = {e['id']: 0 for e in elementos}
    
    for f in fluxos:
        if f['origem'] in graph_out and f['destino'] in in_degree:
            graph_out[f['origem']].append(f['destino'])
            in_degree[f['destino']] += 1
            
    # Níveis (Topological Sort simplificado)
    levels = {}
    queue = [eid for eid, deg in in_degree.items() if deg == 0]
    curr_level = 0
    
    while queue:
        next_queue = []
        for node in queue:
            levels[node] = curr_level
            for neighbor in graph_out[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue
        curr_level += 1
        
    # Calcular coordenadas dos elementos
    max_level = 0
    for elem in elementos:
        eid = elem['id']
        level = levels.get(eid, 0)
        max_level = max(max_level, level)
        
        role_idx = role_map.get(elem['_role_normalized'], 0)
        
        # Dimensões baseadas no tipo
        if "Event" in elem.get("tipo", ""):
            w, h = 36, 36
        elif "Gateway" in elem.get("tipo", ""):
            w, h = 50, 50
        else:
            w, h = 100, 80
            
        # Posição X baseada no nível (sequência)
        x = START_X + (level * ITEM_SPACING)
        
        # Posição Y baseada na Lane (Papel)
        # Centralizar verticalmente na lane
        lane_y_start = role_idx * LANE_HEIGHT
        y = lane_y_start + (LANE_HEIGHT - h) / 2
        
        elem['_x'] = x
        elem['_y'] = y
        elem['_width'] = w
        elem['_height'] = h
        elem['_cx'] = x + w/2
        elem['_cy'] = y + h/2

    # Calcular tamanho total do diagrama
    total_width = START_X + ((max_level + 1) * ITEM_SPACING) + 100
    total_height = len(papeis) * LANE_HEIGHT

    # === GERAR DIAGRAMA (BPMNDI) ===
    diagram = ET.SubElement(root, "bpmndi:BPMNDiagram")
    diagram.set("id", "BPMNDiagram_1")
    plane = ET.SubElement(diagram, "bpmndi:BPMNPlane")
    plane.set("id", "BPMNPlane_1")
    plane.set("bpmnElement", "Collaboration_1")

    # 1. Shapes das Lanes e Participant
    # Participant (Pool inteira)
    shape_pool = ET.SubElement(plane, "bpmndi:BPMNShape")
    shape_pool.set("id", "Participant_1_di")
    shape_pool.set("bpmnElement", "Participant_1")
    shape_pool.set("isHorizontal", "true")
    
    bounds_pool = ET.SubElement(shape_pool, "dc:Bounds")
    bounds_pool.set("x", "50")
    bounds_pool.set("y", "0")
    bounds_pool.set("width", str(int(total_width)))
    bounds_pool.set("height", str(int(total_height)))
    
    # Shapes individuais das Lanes (Opcional em alguns renderizadores, mas bom para compatibilidade)
    for i, papel in enumerate(papeis):
        lid = lane_ids[papel.lower()]
        shape_lane = ET.SubElement(plane, "bpmndi:BPMNShape")
        shape_lane.set("id", f"{lid}_di")
        shape_lane.set("bpmnElement", lid)
        shape_lane.set("isHorizontal", "true")
        
        b_lane = ET.SubElement(shape_lane, "dc:Bounds")
        b_lane.set("x", "80") # 30px offset para o header da pool
        b_lane.set("y", str(i * LANE_HEIGHT))
        b_lane.set("width", str(int(total_width - 30)))
        b_lane.set("height", str(LANE_HEIGHT))

    # 2. Shapes dos Elementos
    for elem in elementos:
        shape = ET.SubElement(plane, "bpmndi:BPMNShape")
        shape.set("id", f"{elem['id']}_di")
        shape.set("bpmnElement", elem['id'])
        
        b = ET.SubElement(shape, "dc:Bounds")
        b.set("x", str(int(elem['_x'])))
        b.set("y", str(int(elem['_y'])))
        b.set("width", str(int(elem['_width'])))
        b.set("height", str(int(elem['_height'])))

    # 3. Edges (Fluxos)
    elem_dict = {e['id']: e for e in elementos}
    
    for fluxo in fluxos:
        edge = ET.SubElement(plane, "bpmndi:BPMNEdge")
        edge.set("id", f"{fluxo['id']}_di")
        edge.set("bpmnElement", fluxo['id'])
        
        origem = elem_dict.get(fluxo['origem'])
        destino = elem_dict.get(fluxo['destino'])
        
        if origem and destino:
            # Lógica simples de waypoint: Centro-Direita -> Centro-Esquerda
            x1 = int(origem['_x'] + origem['_width'])
            y1 = int(origem['_cy'])
            x2 = int(destino['_x'])
            y2 = int(destino['_cy'])
            
            # Ponto 1: Saída
            wp1 = ET.SubElement(edge, "di:waypoint")
            wp1.set("x", str(x1))
            wp1.set("y", str(y1))
            
            # Pontos intermediários para troca de Lane (se necessário)
            # Se a diferença de altura for grande, faz um degrau
            if abs(y1 - y2) > 20:
                mid_x = x1 + (x2 - x1) // 2
                
                wpm1 = ET.SubElement(edge, "di:waypoint")
                wpm1.set("x", str(mid_x))
                wpm1.set("y", str(y1))
                
                wpm2 = ET.SubElement(edge, "di:waypoint")
                wpm2.set("x", str(mid_x))
                wpm2.set("y", str(y2))
            
            # Ponto Final: Entrada
            wp2 = ET.SubElement(edge, "di:waypoint")
            wp2.set("x", str(x2))
            wp2.set("y", str(y2))

    xml_string = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_string)
    return '\n'.join([line for line in dom.toprettyxml(indent="  ").split('\n') if line.strip()])

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

PROMPT_SYSTEM = """Você é um especialista em BPMN 2.0. Converta a descrição em JSON estruturado com foco em POOLS e LANES.

ESTRUTURA OBRIGATÓRIA:
{
  "processo": "Nome do Processo",
  "elementos": [
    {"id": "StartEvent_1", "tipo": "startEvent", "nome": "Início", "papel": "Cliente"},
    {"id": "Task_1", "tipo": "task", "nome": "Solicitar Pedido", "papel": "Cliente"},
    {"id": "Task_2", "tipo": "userTask", "nome": "Aprovar Pedido", "papel": "Gerente"},
    {"id": "EndEvent_1", "tipo": "endEvent", "nome": "Fim", "papel": "Cliente"}
  ],
  "fluxos": [
    {"id": "Flow_1", "origem": "StartEvent_1", "destino": "Task_1"},
    {"id": "Flow_2", "origem": "Task_1", "destino": "Task_2"}
  ]
}

REGRAS:
1. "papel" é OBRIGATÓRIO (Ex: Cliente, Sistema, Gerente, RH). Agrupe tarefas do mesmo ator.
2. TIPOS PERMITIDOS: startEvent, endEvent, task, userTask, serviceTask, exclusiveGateway, parallelGateway.
3. Se o papel não estiver claro, use "Sistema".
RETORNE APENAS O JSON."""

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