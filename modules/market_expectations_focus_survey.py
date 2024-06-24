import pandas as pd
import bcb 
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st

def layout_st():
    st.title('Market Expectations')
    st.markdown('---')
    st.subheader('Focus Market Readout - Central Bank of Brazil')
    
    with st.expander('Choose', expanded=True):
        index = st.radio('Select', ['Monthly Market Expectations','Annual Market Expectations','Inflation - Next 12 months'])

    if index == 'Monthly Market Expectations':
            with st.form(key='form_indice'):
                indicator = st.selectbox('Economic Indicator', ['IPCA', 'Câmbio', 'IGP-M'])
                check = st.form_submit_button('Check')
    elif index == 'Annual Market Expectations': 
            with st.form(key='form_indice'):
                indicator = st.selectbox('Economic Indicator', ['IPCA', 'PIB Total', 'Câmbio', 'Selic', 'IGP-M', 'IPCA Administrados', 'Conta corrente', 'Balança comercial', 'Investimento direto no país', 'Dívida líquida do setor público', 'Resultado primário', 'Resultado nominal'])
                check = st.form_submit_button('Check')
    
    elif index == 'Inflation - Next 12 months':
            with st.form(key='form_indice'):
                indicator = st.selectbox('Economic Indicator', ['IPCA', 'IGP-M'])
                check = st.form_submit_button('Check')

    if check:
        if indicator is None:
            indicator = 'IPCA'
        else:
            if index == 'Monthly Market Expectations':
                monthly_market_expectations(indicator)
            elif index == 'Annual Market Expectations':
                annual_market_expectations(indicator)
            elif index == 'Inflation - Next 12 months':
                inflation_expectations(indicator)

@functools.lru_cache()
def dates():
    today = datetime.today()
    one_year_ago = today.replace(year=today.year - 1, month=today.month, day=1)
    start_date = one_year_ago.strftime('%Y-%m-%d')
    current_year = today.year
    reference_date = [str(current_year), str(current_year+1), str(current_year+2), str(current_year+3)]

    months_years = []
    month = today.month
    year = today.year
        
    for _ in range(3):
        months_years.append(f"{month:02d}/{year}")
        month += 1
        if month > 12:
            month = 1
            year += 1
            
    return start_date, reference_date, months_years

def fetch_indicator_expectations(endpoint:str,indicator:str):
    start_date = dates()[0]
    em = bcb.Expectativas()
    ep = em.get_endpoint(endpoint)

    if endpoint == 'ExpectativasMercadoInflacao12Meses':
        indicator_expectations = (ep.query()
        .filter(ep.Indicador == indicator, ep.Suavizada == 'S')
        .filter(ep.Data >= start_date)
        .filter(ep.baseCalculo == 0)
        .select(ep.Data, ep.Mediana)
        .collect())
    
    elif endpoint == 'ExpectativaMercadoMensais':
        indicator_expectations = (ep.query()
                                .filter(ep.Indicador == indicator)
                                .filter(ep.Data >= start_date)
                                .filter(ep.baseCalculo == 0)
                                .select(ep.Data, ep.Mediana, ep.DataReferencia)
                                .collect())
        
    elif endpoint == 'ExpectativasMercadoAnuais':
        indicator_expectations = (ep.query()
                                .filter(ep.Indicador == indicator)
                                .filter(ep.Data >= start_date)
                                .filter(ep.baseCalculo == 0)
                                .select(ep.Data, ep.Mediana, ep.DataReferencia,ep.IndicadorDetalhe)
                                .collect())
    
    return indicator_expectations

def annual_market_expectations(indicator:str):
    reference_date = dates()[1]
    endpoint = 'ExpectativasMercadoAnuais'
    bcb_indicators = {
        'IPCA': 'variação %',
        'PIB Total': r'variação % sobre ano anterior',
        'Câmbio': 'R$/US$',
        'Selic': r'% a.a.',
        'IGP-M': 'variação %',
        'IPCA Administrados': 'variação %',
        'Conta corrente': 'US$ bilhões',
        'Balança comercial': ' (Saldo) US$ bilhões',
        'Investimento direto no país': 'US$ bilhões',
        'Dívida líquida do setor público': '% PIB',
        'Resultado primário': '% PIB',
        'Resultado nominal': '% PIB'
    }

    bcb_expectations = fetch_indicator_expectations(endpoint,indicator)
    bcb_expectations.set_index('Data', inplace=True)

    fig = go.Figure()
    for year in reference_date:
        if indicator != 'Balança comercial':
            df_filter = bcb_expectations['Mediana'].loc[bcb_expectations['DataReferencia'] == year]
            fig.add_trace(go.Scatter(x=df_filter.index, y=df_filter, mode='lines', name=year))
        else:
            df_filter = bcb_expectations['Mediana'].loc[(bcb_expectations['IndicadorDetalhe'] == 'Saldo') & (bcb_expectations['DataReferencia'] == year)]
            fig.add_trace(go.Scatter(x=df_filter.index, y=df_filter, mode='lines', name=year))
    fig.update_layout(xaxis_rangeslider_visible=True,title=f'{indicator} - Market expectations', yaxis_title=bcb_indicators.get(indicator), template='plotly_dark')#,title_x=0.5)
    st.plotly_chart(fig)


def monthly_market_expectations(indicator:str):
    bcb_indicators_monthly = {
        'IPCA': 'variação %',
        'Câmbio': 'R$/US$',
        'IGP-M': 'variação %',
    }
    reference_date_monthly = dates()[2]
    endpoint = 'ExpectativaMercadoMensais'
    
    bcb_expectations = fetch_indicator_expectations(endpoint,indicator)
    bcb_expectations.set_index('Data', inplace=True)

    fig = go.Figure()
    for month in reference_date_monthly:
            df_filter = bcb_expectations['Mediana'].loc[bcb_expectations['DataReferencia'] == month]
            fig.add_trace(go.Scatter(x=df_filter.index, y=df_filter, mode='lines', name=month))
    fig.update_layout(xaxis_rangeslider_visible=True,title=f'{indicator} - Market expectations', yaxis_title=bcb_indicators_monthly.get(indicator), template='plotly_dark',title_x=0.5)
    st.plotly_chart(fig)



def inflation_expectations(indicator:str):
    endpoint = 'ExpectativasMercadoInflacao12Meses'
    bcb_indicators_inflation = {
        'IPCA': 'variação %',
        'IGP-M': 'variação %',
    }

    bcb_expectations = fetch_indicator_expectations('ExpectativasMercadoInflacao12Meses',indicator)
    bcb_expectations.set_index('Data', inplace=True)


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bcb_expectations.index, y=bcb_expectations['Mediana'], mode='lines'))
    fig.update_layout(xaxis_rangeslider_visible=True,title=f'{indicator} - Inflation expectations', yaxis_title=bcb_indicators_inflation.get(indicator), template='plotly_dark',title_x=0.5)
    st.plotly_chart(fig)


def focus_market_expectations():
    layout_st()
 

if __name__ == "__main__":
    focus_market_expectations()