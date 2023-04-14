import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

import pandas as pd

df_consumidor = pd.read_csv('consumidor.csv',sep=';',encoding='ISO-8859-1')
df_governo = pd.read_csv('gov.csv',sep=';',encoding='ISO-8859-1')

st.set_page_config(page_title='App AEDA',page_icon="bar_chart:")

st.markdown('# Análise de Medicamentos - Governo e Consumidor')
st.text('RM347299, RM347320, RM346160, RM346267')

st.markdown('## Concatenar a tabela do governo e consumidor')

st.markdown('### Dataframe do governo')
st.dataframe(df_governo.head())

st.markdown('### Dataframe do consumidor')
st.dataframe(df_consumidor.head())

# Renomeando a coluna do dataframe governo para que tenha a mesma nomenclatura do consumidor e concatenando as bases
df_governo.rename({'PRINCÍPIO ATIVO':'SUBSTÂNCIA'},axis=1,inplace=True)
colunas_em_ambos_df = df_governo.columns[df_governo.columns.isin(df_consumidor.columns)]
df_governo.drop(colunas_em_ambos_df, axis=1, inplace=True)
df_conjunto = pd.concat([df_consumidor, df_governo],axis=1)

st.markdown('Fazendo o merge entre elas, temos a seguinte tabela com colunas únicas de cada dataframe:')
st.dataframe(df_conjunto.head())

st.markdown('## Ajustando as variáveis')
st.markdown('### Tarja')
st.dataframe(df_conjunto.TARJA.unique())

st.text('Com a transformação dessa variável, ficamos com os seguintes resultados:')
df_conjunto['TARJA'] = df_conjunto['TARJA'].replace(r'\(\*\*\)', '', regex=True)
df_conjunto['TARJA'] = df_conjunto['TARJA'].replace(r'Tarja Vermelha sob restrição', 'Tarja Vermelha', regex=True)
df_conjunto['TARJA'] = df_conjunto['TARJA'].str.strip()
df_conjunto = df_conjunto[df_conjunto['TARJA'] != '- (*)'].copy()
st.dataframe(df_conjunto.TARJA.unique())

st.markdown('### Tipo de Produto')
st.dataframe(df_conjunto['TIPO DE PRODUTO (STATUS DO PRODUTO)'].unique())
st.text('Com a transformação dessa variável, é possível retirar o "-":')
df_conjunto = df_conjunto[df_conjunto['TIPO DE PRODUTO (STATUS DO PRODUTO)'] != '    -     '].copy()
st.dataframe(df_conjunto['TIPO DE PRODUTO (STATUS DO PRODUTO)'].unique())

st.markdown('## Ajustando as variáveis de preço')
st.text('É possível perceber que todas as variáveis estão apresentadas como "OBJECT"')
st.dataframe(df_conjunto.dtypes.to_frame().T)

def convert(df, column = list): 

    for i in column:
        df[i] = df[i].astype(str)
        df[i] = df[i].str.replace(',', '.')
        df[i] = df[i].astype(np.float32)

    return df.copy()

df_conjunto = convert(df_conjunto, df_conjunto.iloc[:,13:32].columns)
df_conjunto = convert(df_conjunto, df_conjunto.iloc[:,40:50].columns)

st.text('Após o ajuste, é possível perceber que agora as variáveis numéricas estão armazenadas com o tipo correto')
st.dataframe(df_conjunto.dtypes.to_frame().T)


st.markdown('## Removendo Outliers')
st.text("""Ao analisarmos os histogramas das variáveis numéricas,\né possível verificar uma grande distorção devido a outliers""")
df_conjunto.hist(figsize=(30, 30))
st.pyplot(plt.gcf())

st.text('Também é possível perceber isso na tabela abaixo:')
st.dataframe(df_conjunto.describe().T)

q1 = df_conjunto.quantile(0.25)
q3 = df_conjunto.quantile(0.75)
iqr = q3 - q1

# remover as linhas que contêm outliers
df_conjunto_no_outliers = df_conjunto[~((df_conjunto < (q1 - 1.5 * iqr)) | (df_conjunto > (q3 + 1.5 * iqr))).any(axis=1)]

# Ao plotarmos um simples boxplot, podemos verificar a quantidade de outliers nas variáveis numéricas. Iremos removê-las
st.text('Após a remoção dos outliers, podemos ver os gráficos novamente:')

df_conjunto_no_outliers.hist(figsize=(30, 30))
st.pyplot(plt.gcf())

st.markdown('## Insight 1 - Analisando a Tarja')

fig,ax = plt.subplots(1,3,figsize=(20,10))

sns.boxplot(data=df_conjunto_no_outliers,x='TARJA',y='PMVG 0%',ax=ax[0])
ax[0].set_title('Valor PMVG 0%')
ax[0].set_ylim(0,400)
ax[0].grid()

sns.boxplot(data=df_conjunto_no_outliers,x='TARJA',y='PF 0%',ax=ax[1])
ax[1].set_title('Valor PF 0%')
ax[1].set_ylim(0,400)
ax[1].grid()

sns.boxplot(data=df_conjunto_no_outliers,x='TARJA',y='PMC 0%',ax=ax[2])
ax[2].set_title('Valor PMC 0%')
ax[2].set_ylim(0,400)
ax[2].grid()

st.pyplot(fig)


st.text('Podemos verificar que os medicamentos de Tarja Vermelha \npossuem a maior variação de preços, com relação ao cliente final,')
st.text('seja ele o governo (PMVG - Preço ao governo), pessoal física \n(PMC - Preço dado pelas farmácias) ou estabelecimento\n(PF - Preço dado pelo laboratório)')

st.text('Na pivot table abaixo, é possível perceber que o governo \nsempre fica com os melhores valores, na tarja vermelha \nesse valor chega a ser ~25% menor do que aquele repassado para pessoa física.')
st.text('Isso se altera quando olhamos para Tarja Preta \nem que o delta desse preço é bem mais baixo')

st.dataframe(pd.pivot_table(data=df_conjunto,index='TARJA',values=['PMVG 0%','PF 0%','PMC 0%'],aggfunc='median'))


st.markdown('## Insight 2 - Tipo de Produto')

st.dataframe(pd.crosstab(df_conjunto_no_outliers['TIPO DE PRODUTO (STATUS DO PRODUTO)'],df_conjunto_no_outliers['TARJA'],normalize='index')*100)
st.text("Quando observamos o tipo de produto, podemos ver que a Tarja Vermelha \né maioria em cada um deles, mas os medicamentos FITOTERÁPICOS se destacam, \nsendo a maior parte medicamentos sem tarja.")
st.text("Além disso, também é possível perceber que os medicamentos biológicos \nsão os mais caros para quaisquer clientes, em específico ao consumidor, \natingindo o dobro de outros tipos de medicamentos")

fig,ax = plt.subplots(1,3,figsize=(20,8))

sns.boxplot(data=df_conjunto_no_outliers,x='TIPO DE PRODUTO (STATUS DO PRODUTO)',y='PMVG 0%',ax=ax[0])
ax[0].set_title('Valor PMVG 0%')
ax[0].set_ylim(0,400)
ax[0].grid()

sns.boxplot(data=df_conjunto_no_outliers,x='TIPO DE PRODUTO (STATUS DO PRODUTO)',y='PF 0%',ax=ax[1])
ax[1].set_title('Valor PF 0%')
ax[1].set_ylim(0,400)
ax[1].grid()

sns.boxplot(data=df_conjunto_no_outliers,x='TIPO DE PRODUTO (STATUS DO PRODUTO)',y='PMC 0%',ax=ax[2])
ax[2].set_title('Valor PMC 0%')
ax[2].set_ylim(0,400)
ax[2].grid()

st.pyplot(fig)

st.markdown('## Insight 3 - Restrição Hospitalar')

st.text('É possível verificar abaixo que a grande maioria dos medicamentos não possui quaisquer restrições hospitalares')
st.dataframe((df_conjunto_no_outliers['RESTRIÇÃO HOSPITALAR'].value_counts(normalize=True)*100).to_frame())

st.text('Quando analisamos o tipo do produto, é possível verificar que os \nmedicamentos específicos são os que mais possuem restrições.')
st.dataframe(pd.crosstab(index=df_conjunto_no_outliers['RESTRIÇÃO HOSPITALAR'],columns=df_conjunto_no_outliers['TIPO DE PRODUTO (STATUS DO PRODUTO)'],normalize='columns')*100)

st.text('Ao olhar para tarja, podemos verificar que a tarja preta e vermelha possuem \npraticamente o mesmo percentual de restrições')
st.dataframe(pd.crosstab(index=df_conjunto_no_outliers['RESTRIÇÃO HOSPITALAR'],columns=df_conjunto_no_outliers['TARJA'],normalize='columns')*100)
