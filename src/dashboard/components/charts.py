# src/dashboard/components/charts.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl
from datetime import datetime, timedelta

def create_price_chart(df: pl.DataFrame, selected_indicators: list = None) -> go.Figure:
    """
    Crée un graphique de chandelier avec les indicateurs techniques
    
    Args:
        df: DataFrame avec les données
        selected_indicators: Liste des indicateurs à afficher ['sma', 'bb', 'rsi', 'macd']
    """
    selected_indicators = selected_indicators or []
    
    # Création du graphique avec sous-graphiques
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=('Prix BTC/USD', 'Volume')
    )

    # Chandelier japonais
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='BTC/USD'
        ),
        row=1, col=1
    )

    # Moyennes mobiles
    if 'sma' in selected_indicators:
        for period in [20, 50, 200]:
            if f'SMA_{period}' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df[f'SMA_{period}'],
                        name=f'SMA {period}',
                        line=dict(width=1)
                    ),
                    row=1, col=1
                )

    # Bandes de Bollinger
    if 'bb' in selected_indicators:
        if all(col in df.columns for col in ['BB_upper', 'BB_middle', 'BB_lower']):
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['BB_upper'],
                    name='BB Upper',
                    line=dict(color='gray', dash='dash')
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['BB_lower'],
                    name='BB Lower',
                    line=dict(color='gray', dash='dash'),
                    fill='tonexty'
                ),
                row=1, col=1
            )

    # Volume
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume'
        ),
        row=2, col=1
    )

    # Mise en page
    fig.update_layout(
        title='Bitcoin (BTC/USD)',
        yaxis_title='Prix (USD)',
        yaxis2_title='Volume (BTC)',
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return fig

def create_technical_chart(df: pl.DataFrame, selected_indicators: list = None) -> go.Figure:
    """Crée un graphique des indicateurs techniques sélectionnés"""
    selected_indicators = selected_indicators or []
    
    # Ne garder que RSI et MACD
    technical_indicators = [ind for ind in selected_indicators if ind in ['rsi', 'macd']]
    if not technical_indicators:
        # Si aucun indicateur sélectionné, retourner un graphique vide
        fig = go.Figure()
        fig.update_layout(
            title='Sélectionnez des indicateurs techniques (RSI, MACD)',
            height=600
        )
        return fig
    
    # Créer les sous-graphiques
    fig = make_subplots(
        rows=len(technical_indicators),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.5] * len(technical_indicators),
        subplot_titles=[ind.upper() for ind in technical_indicators]
    )

    current_row = 1

    # RSI
    if 'rsi' in technical_indicators and 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['RSI'],
                name='RSI',
                line=dict(color='blue')
            ),
            row=current_row, col=1
        )
        
        # Lignes de survente/surachat
        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="red",
            row=current_row,
            col=1,
            name='Surachat'
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="green",
            row=current_row,
            col=1,
            name='Survente'
        )
        current_row += 1

    # MACD
    if 'macd' in technical_indicators and 'MACD' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['MACD'],
                name='MACD',
                line=dict(color='blue')
            ),
            row=current_row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['MACD_Signal'],
                name='Signal',
                line=dict(color='orange')
            ),
            row=current_row, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['MACD_Histogram'],
                name='Histogram',
                marker=dict(
                    color=['green' if x >= 0 else 'red' for x in df['MACD_Histogram']]
                )
            ),
            row=current_row, col=1
        )

    # Mise en page
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    # Ajuster les marges pour éviter la superposition
    fig.update_layout(margin=dict(t=30, b=50))

    return fig