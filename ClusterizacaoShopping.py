# %%
# 1. Preparando o terreno: importando as ferramentas e ajustando variáveis de ambiente
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Evita alertas chatos de conflito de threads ao usar o KMeans
os.environ["OMP_NUM_THREADS"] = "1"
# %%
# 2. Carregando os dados: deixei o caminho dinâmico para funcionar direto na máquina de quem clonar o repo
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'mall_customers.csv')

# Usando o padrão 'df' para economizar digitação e manter o código mais limpo
df = pd.read_csv(file_path)

# %%
# 3. Dando aquela primeira olhada nos dados para entender o formato e as estatísticas gerais
print('\n--- 5 primeiras linhas ---')
print(df.head())

print('\n--- Dimensões (linhas, colunas) ---')
print(df.shape)

print('\n--- Tipos de dados e memória ---')
df.info()

print('\n--- Estatísticas descritivas ---')
print(df.describe().round(2))

# %%
# 4. Checagem de qualidade: procurando furos nos dados (nulos ou IDs repetidos)
print('\n--- Valores Ausentes ---')
print(df.isnull().sum())

print(f'\nLinhas duplicadas: {df.duplicated().sum()}')
print(f'IDs de clientes repetidos: {df["CustomerID"].duplicated().sum()}')

# %%
# 5. Investigando a distribuição e os outliers usando uma abordagem mais visual (Violino + pontos)
# Isso é bem melhor que o boxplot normal porque mostra onde a massa de dados realmente está concentrada
plt.figure(figsize=(10, 5))
cols_analise = ["Annual Income (k$)", "Spending Score (1-100)"]

sns.violinplot(data=df[cols_analise], inner="quartile", palette="pastel")
sns.stripplot(data=df[cols_analise], color="#404040", alpha=0.5, jitter=True, size=4)

plt.title("Distribuição e Outliers (Violino + Stripplot)", fontweight="bold")
plt.ylabel("Valores")
plt.grid(axis="y", linestyle="--", alpha=0.3)
plt.tight_layout()
plt.show()

# %%
# 6. Outra opção de verificação de outliers, mas agora interativa com o Plotly (gera um HTML)
fig_box = px.box(
    df, y=cols_analise, points="all",
    title="Análise de Outliers Interativa",
    color_discrete_sequence=["#4472C4", "#ED7D31"]
)
fig_box.update_layout(template="plotly_white")
fig_box.write_html("boxplot_interativo.html", include_plotlyjs='cdn')
fig_box.show()

# %%
# 7. Histogramas básicos para ver como a idade, renda e gastos estão espalhados
df[["Age"] + cols_analise].hist(figsize=(10, 8), bins=12, edgecolor="black", color="#5DADE2")
plt.suptitle("Histogramas das Variáveis Numéricas", fontweight="bold")
plt.tight_layout()
plt.show()

# %%
# 8. Olhando a relação direta entre Renda e Gastos. Aqui já dá pra notar uns grupos se formando sozinhos
plt.figure(figsize=(8, 5))
plt.scatter(df["Annual Income (k$)"], df["Spending Score (1-100)"], alpha=0.6, c="#2874A6")
plt.title("Renda Anual vs Pontuação de Gastos", fontweight="bold")
plt.xlabel("Renda Anual (k$)")
plt.ylabel("Pontuação de Gastos")
plt.grid(alpha=0.3)
plt.show()

# %%
# 9. Verificando a matriz de correlação para ver se as variáveis andam juntas (Heatmap)
matriz_corr = df[["Age", "Annual Income (k$)", "Spending Score (1-100)"]].corr()

plt.figure(figsize=(7, 5))
sns.heatmap(matriz_corr, annot=True, cmap="viridis", vmin=-1, vmax=1, fmt=".2f", linewidths=0.5)
plt.title("Matriz de Correlação Linear", fontweight="bold")
plt.tight_layout()
plt.show()

# %%
# 10. Breve análise demográfica: comparando se o gênero influencia muito no gasto e na renda
print('\n--- Distribuição por Gênero ---')
print(df["Gender"].value_counts())

resumo_sexo = df.groupby("Gender")[["Age", "Annual Income (k$)", "Spending Score (1-100)"]].mean()
print('\n--- Médias por Gênero ---')
print(resumo_sexo.round(2))

resumo_sexo["Spending Score (1-100)"].plot(kind="bar", figsize=(6, 4), color=["#A569BD", "#5DADE2"])
plt.title("Média de Gastos por Sexo", fontweight="bold")
plt.xticks(rotation=0)
plt.ylabel("Score Médio")
plt.tight_layout()
plt.show()

# %%
# 11. Preparando e treinando o algoritmo KMeans
features = ['Annual Income (k$)', 'Spending Score (1-100)', 'Age']
X = df[features] # Separando só o que importa pro modelo

# É obrigatório padronizar para o modelo não dar mais peso pra Renda do que pra Idade, por exemplo
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Treinando o modelo com 5 clusters (já que visualmente percebemos 5 grupos antes)
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X_scaled)

# %%
# 12. Avaliando o resultado: tirando a "foto" de quem é quem dentro de cada grupo criado
resumo_clusters = df.groupby("Cluster").agg(
    Qtd=("CustomerID", "count"),
    Idade_Media=("Age", "mean"),
    Renda_Media=("Annual Income (k$)", "mean"),
    Gastos_Medios=("Spending Score (1-100)", "mean")
)
print('\n--- Perfil dos Grupos (Clusters) ---')
print(resumo_clusters.round(1))

# %%
# 13. Plotando o resultado do K-Means em 2D com os centroides no lugar certo (escala original)
centroides = scaler.inverse_transform(kmeans.cluster_centers_)
cores = ["#4472C4", "#ED7D31", "#70AD47", "#A64D79", "#17A398"]

plt.figure(figsize=(10, 6))
for c in range(5):
    dados = df[df["Cluster"] == c]
    plt.scatter(dados["Annual Income (k$)"], dados["Spending Score (1-100)"], 
                color=cores[c], s=60, alpha=0.7, edgecolor="white", label=f"Cluster {c}")

# Marcando o centro de cada grupo com um X grande
plt.scatter(centroides[:, 0], centroides[:, 1], marker="X", s=200, color="black", edgecolor="white", linewidth=1.5, label="Centroides")

plt.title("Segmentação Final (Visão 2D: Renda vs Gastos)", fontweight="bold")
plt.xlabel("Renda Anual (k$)")
plt.ylabel("Pontuação de Gastos")
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# %%
# 14. Gráfico 3D interativo pra visualizar (Idade X Renda X Gasto)
# Ajustando as labels pros clusters ficarem mais bonito na legenda
df['Cluster_Label'] = df['Cluster'].apply(lambda c: f"Cluster {c}")

fig_3d = px.scatter_3d(
    df, x='Age', y='Annual Income (k$)', z='Spending Score (1-100)',
    color='Cluster_Label', opacity=0.7,
    title="Análise 3D Completa dos Perfis com Centroides",
    labels={'Age': 'Idade', 'Annual Income (k$)': 'Renda', 'Spending Score (1-100)': 'Gastos'}
)

# Injetando os centroides originais no gráfico 3D
fig_3d.add_trace(go.Scatter3d(
    x=centroides[:, 2], y=centroides[:, 0], z=centroides[:, 1],
    mode='markers', name='Centroides',
    marker=dict(size=10, symbol='x', color='black', line=dict(color='white', width=2))
))

fig_3d.update_layout(margin=dict(r=0, b=0, l=0, t=40))
fig_3d.write_html("cluster_3d_interativo_final.html", include_plotlyjs='cdn')
fig_3d.show()