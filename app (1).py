"""
EquipeApp - Controle simples de demandas
Requisitos:
  pip install streamlit pandas
Execute localmente:
  streamlit run app.py
"""
import sqlite3
from datetime import datetime
import streamlit as st
import pandas as pd

# ---------- Config inicial ----------
DB_NAME = 'equipeapp.sqlite'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descricao TEXT,
                    responsavel TEXT,
                    prioridade TEXT,
                    status TEXT,
                    criado_em TEXT,
                    atualizado_em TEXT)
             """)
    conn.commit()
    conn.close()

# Correção do problema: usar @st.cache_resource em vez de @st.cache_data
# para recursos que não são serializáveis como conexões de banco
@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

init_db()
conn = get_conn()
c = conn.cursor()

# ---------- Funções de DB ----------

def add_task(titulo, desc, resp, prioridade):
    now = datetime.now().isoformat(' ', 'seconds')
    c.execute("INSERT INTO tasks (titulo, descricao, responsavel, prioridade, status, criado_em, atualizado_em) VALUES (?,?,?,?,?,?,?)",
              (titulo, desc, resp, prioridade, 'Novo', now, now))
    conn.commit()

def update_status(task_id, new_status):
    now = datetime.now().isoformat(' ', 'seconds')
    c.execute("UPDATE tasks SET status=?, atualizado_em=? WHERE id=?", (new_status, now, task_id))
    conn.commit()

@st.cache_data(ttl=60)  # Cache por 60 segundos
def load_tasks():
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    return df

# ---------- UI ----------
st.set_page_config(page_title='EquipeApp', layout='wide')
st.title('EquipeApp - Controle de Demandas')

# Sidebar com navegação
menu = st.sidebar.selectbox('Menu', ['Dashboard', 'Nova Solicitação', 'Tarefas', 'Equipe'])

# ---------- Dashboard ----------
if menu == 'Dashboard':
    st.header('Dashboard')

    df = load_tasks()

    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total de Tarefas", len(df))

        with col2:
            novas = len(df[df['status'] == 'Novo'])
            st.metric("Novas", novas)

        with col3:
            andamento = len(df[df['status'] == 'Em Andamento'])
            st.metric("Em Andamento", andamento)

        with col4:
            concluidas = len(df[df['status'] == 'Concluído'])
            st.metric("Concluídas", concluidas)

        # Gráfico de status
        status_count = df['status'].value_counts()
        st.bar_chart(status_count)
    else:
        st.info("Nenhuma tarefa cadastrada ainda!")

# ---------- Nova Solicitação ----------
elif menu == 'Nova Solicitação':
    st.header('Nova Solicitação')

    with st.form('nova_tarefa'):
        titulo = st.text_input('Título', placeholder='Ex: Revisar relatório mensal')
        descricao = st.text_area('Descrição', placeholder='Detalhes da solicitação...')

        col1, col2 = st.columns(2)
        with col1:
            responsavel = st.selectbox('Responsável', 
                                     ['Ana Silva', 'Bruno Santos', 'Carla Oliveira', 'Daniel Costa'])
        with col2:
            prioridade = st.selectbox('Prioridade', ['Alta', 'Média', 'Baixa'])

        submitted = st.form_submit_button('Criar Solicitação', type='primary')

        if submitted:
            if titulo.strip():
                add_task(titulo, descricao, responsavel, prioridade)
                st.success(f'Tarefa "{titulo}" criada com sucesso!')
                st.balloons()
            else:
                st.error('Por favor, preencha o título da tarefa!')

# ---------- Lista de Tarefas ----------
elif menu == 'Tarefas':
    st.header('Lista de Tarefas')

    df = load_tasks()

    if not df.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox('Filtrar por Status', 
                                       ['Todos'] + list(df['status'].unique()))
        with col2:
            resp_filter = st.selectbox('Filtrar por Responsável',
                                     ['Todos'] + list(df['responsavel'].unique()))

        # Aplicar filtros
        filtered_df = df.copy()
        if status_filter != 'Todos':
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        if resp_filter != 'Todos':
            filtered_df = filtered_df[filtered_df['responsavel'] == resp_filter]

        # Mostrar tarefas como cards
        for index, row in filtered_df.iterrows():
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.subheader(f"#{row['id']} - {row['titulo']}")
                    st.write(f"📝 {row['descricao']}")
                    st.write(f"👤 **{row['responsavel']}** | 🎯 **{row['prioridade']}**")
                    st.caption(f"Criado em: {row['criado_em']}")

                with col2:
                    status_color = {'Novo': '🆕', 'Em Andamento': '⏳', 'Concluído': '✅'}
                    st.markdown(f"### {status_color.get(row['status'], '❓')} {row['status']}")

                with col3:
                    new_status = st.selectbox(
                        f'Status #{row["id"]}',
                        ['Novo', 'Em Andamento', 'Concluído'],
                        index=['Novo', 'Em Andamento', 'Concluído'].index(row['status']),
                        key=f"status_{row['id']}"
                    )
                    if new_status != row['status']:
                        update_status(row['id'], new_status)
                        st.rerun()
    else:
        st.info("Nenhuma tarefa encontrada. Que tal criar a primeira?")

# ---------- Equipe ----------
elif menu == 'Equipe':
    st.header('Equipe')

    equipe = [
        {'nome': 'Isabel', 'cargo': 'Analista', 'email': 'isabel.cruz@fgv.br'},
        {'nome': 'Douglas', 'cargo': 'Analista', 'email': 'Douglas@fgv.br'},
        {'nome': 'Guilherme', 'cargo': 'Desenvolvedor', 'email': 'guilherme@fgv.br'},
        {'nome': 'Leandro', 'cargo': 'Coordenador', 'email': 'leandro.vento@fgv.br'}
    ]

    for pessoa in equipe:
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown(f"### 👤 {pessoa['nome']}")
                st.write(f"**{pessoa['cargo']}**")
                st.write(f"📧 {pessoa['email']}")

            with col2:
                # Estatísticas da pessoa
                df = load_tasks()
                if not df.empty:
                    pessoa_tasks = df[df['responsavel'] == pessoa['nome']]
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Total", len(pessoa_tasks))
                    with col_b:
                        andamento = len(pessoa_tasks[pessoa_tasks['status'] == 'Em Andamento'])
                        st.metric("Em Andamento", andamento)
                    with col_c:
                        concluidas = len(pessoa_tasks[pessoa_tasks['status'] == 'Concluído'])
                        st.metric("Concluídas", concluidas)

# Footer
st.markdown("---")
st.markdown("**EquipeApp** - Sistema de Controle de Demandas | Desenvolvido por Bel (Git: BellDataSc) com Streamlit")
