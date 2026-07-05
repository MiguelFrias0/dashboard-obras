Dashboard de Gestão de Projetos


Fala, pessoal. Esse repositório guarda o código-fonte do Painel de Controle de Manutenções e Gestão de Projetos. O objetivo principal desse projeto foi tirar a operação do Excel e construir uma aplicação web robusta, com cara de software profissional, para acompanhar indicadores de orçamentos, produtividade da equipe e distribuição de demandas em campo.

A interface foi inteiramente construída em Python utilizando o Streamlit, com um visual dark focado em Glassmorphism e gráficos dinâmicos.

  Tecnologias Utilizadas
    
    Python 3

    Streamlit: Para a construção de toda a interface web e gerenciamento de estados.

    Plotly: Para a renderização dos gráficos interativos.

    Pandas: Para o tratamento e manipulação dos dados brutos.

    Supabase: Banco de dados em nuvem (PostgreSQL) servindo como nosso backend.

Arquitetura: A Conexão Streamlit + Supabase
Para garantir que a estrutura dos dados fique intacta e o "castelo não caia", a comunicação entre o front-end (Streamlit) e o back-end (Supabase) foi montada focando em segurança e performance.

A lógica de conexão funciona da seguinte forma:

Gestão de Credenciais (Secrets): Não colocamos chaves de API direto no código. Utilizamos o recurso nativo do Streamlit (st.secrets). As credenciais ficam em um arquivo oculto secrets.toml (no ambiente local) ou nas variáveis de ambiente (no deploy). O código puxa a SUPABASE_KEY e a URL de forma segura para instanciar o cliente.

Instância do Cliente (Cache de Recurso):
Para evitar que o Python crie uma nova conexão com o banco de dados toda vez que o usuário interage com a tela, usamos o decorador @st.cache_resource. Isso mantém o túnel com o Supabase aberto de forma global na aplicação.

Consumo de Dados (Cache de Dados):
O dashboard consome a tabela Data_Base_Secundaria. Se o app fizesse um SELECT no banco a cada clique num filtro de data, o sistema ficaria lento e estouraria o limite de requisições. Para resolver isso, a função load_data() está protegida com o decorador @st.cache_data(ttl=600).
Isso significa que o Streamlit puxa os dados do Supabase e guarda na memória por 10 minutos. O usuário pode filtrar, trocar de abas e interagir com os gráficos de forma instantânea, consumindo da memória local. Após 10 minutos, o cache expira e o app busca dados frescos no banco silenciosamente.

Estrutura do Dashboard
O painel é dividido em quatro áreas principais para facilitar a análise:

Visão Geral: KPIs principais (Projetos Recebidos, Despachados, Enviados e Cancelados), taxa de conversão e acompanhamento das metas trimestrais em relação à média histórica.

Análise Individual: Detalhamento do funil de cada orçamentista/analista do time.

Análise do Time: Visão acumulada e comparativa da produtividade de toda a equipe no ano vigente.

Profissionais de Campo: Motor de busca e distribuição visual da alocação de projetos por profissional parceiro e por cliente.

Como rodar o projeto localmente
Se você clonou esse repositório e quer rodar na sua máquina, siga os passos:

Crie um ambiente virtual (venv) e ative.

Instale as dependências executando:
pip install -r requirements.txt

Crie uma pasta chamada .streamlit na raiz do projeto.

Dentro dela, crie um arquivo secrets.toml com as suas credenciais do Supabase no seguinte formato:
SUPABASE_KEY = "sua_chave_aqui"

Inicie a aplicação com o comando:
streamlit run app.py (ou o nome que você deu ao arquivo principal).
