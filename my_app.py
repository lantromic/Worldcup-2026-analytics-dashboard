import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from adjustText import adjust_text

pd.set_option('display.max_columns', None)
sns.set_theme(style="whitegrid", palette="muted")

st.set_page_config(
    page_title="WC 2026",
    layout="wide"  # <--- This expands the main container from edge to edge
)

@st.cache_data
def load_data():
    return pd.read_csv("data/cleaned_players.csv")

data = load_data()

data['goals_per_shot_on_target'] = data['goals_per_shot_on_target'].fillna(0)

data['position'] = data['position'].astype('category')

# 3. Downcast whole-number metrics to int16 (2 bytes instead of 8 bytes)
int16_cols = [
    'age', 'games', 'minutes', 'goals', 'assists', 
    'cards_yellow', 'cards_red', 'shots', 'shots_on_target', 
    'fouls', 'fouled', 'offsides', 'crosses', 'interceptions', 'tackles_won'
]
for col in int16_cols:
    if col in data.columns:
        data[col] = data[col].fillna(0).astype('int16')
# 4. Downcast decimal ratios/rates from float64 to float32 (cut memory in half)
float16_cols = [
    'goals_per_shot', 'goals_per_shot_on_target', 'minutes_per_game',
    'goals_per_90', 'assist_per_90', 'cards_per_fouls_per_90', 'bad_discipline'
]
for col in float16_cols:
    if col in data.columns:
        data[col] = data[col].fillna(0.0).astype('float16')

clubs_available = data['club'].unique().tolist()
teams_available = data['team'].unique().tolist()

# title subheader text write

st.title("World Cup 2026 Player Analysis")

st.sidebar.title("World Cup 2026")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Players", data.shape[0])
with col2:
    st.metric("Goals", int(data['goals'].sum()))
with col3:
    st.metric("Assists", int(data['assists'].sum()))
with col4:
    st.metric("Avg Age", int(data['age'].mean()))
with col5:
    st.metric("Yellow + Red Cards", int(data['cards_yellow'].sum() + data['cards_red'].sum()))

selected_positions = st.sidebar.multiselect(
    "Position", ['GK', 'DF', 'MF', 'FW'], default=['GK', 'DF', 'MF', 'FW']
)



age_min = int(data['age'].min())
age_max = int(data['age'].max())

age_range = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))

min_minutes = st.sidebar.slider("Minimum minutes played", 0, int(data['minutes'].max()), 600)

selected_teams = st.sidebar.multiselect(
    "National team (leave empty = all)", teams_available, default=[]
)

selected_clubs = st.sidebar.multiselect(
    "Club (leave empty = all)", clubs_available, default=[]
)



selected_columns = [
    "player",
    "team",
    "position",
    "age",
    "club",
    "minutes",
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "cards_yellow",
    "cards_red",
    "fouls",
    "fouled",
]

# Filter your DataFrame

data = data[(data['position'].isin(selected_positions)) & ((data['age'] >= age_range[0]) & (data['age'] <= age_range[1])) & (data['minutes'] >= min_minutes)]
data = data[data['team'].isin(selected_teams)] if selected_teams else data
data = data[data['club'].isin(selected_clubs)] if selected_clubs else data

df_subset = data[selected_columns]

selected_tab = st.radio(
    "Navigation", 
    ["Overview", "By Position", "Discipline", "Clubs", "Age Trends", "Top Performers"],
    horizontal=True,
    label_visibility="collapsed"
)

if selected_tab == "Overview":
    st.dataframe(df_subset.sort_values(by='goals', ascending=False), width='stretch', hide_index=True)
elif selected_tab == "By Position":
    st.subheader("Distribution of key stats by position")
    metric_choice = st.selectbox(
        "Metric",
        ["goals", "assists", "tackles_won", "interceptions", "crosses"]
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=data, x="position", y=metric_choice, ax=ax)
    ax.set_title(f"Total {metric_choice} by Position")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    plt.close(fig)

elif selected_tab == "Discipline":

    st.subheader("Distribution by position(per 90 minutes)")

    fouls_per_90_min_per_position = (data.groupby('position')['fouls'].sum() / data.groupby('position')['minutes'].sum())*90
    fouled_per_90_min_per_position = (data.groupby('position')['fouled'].sum() / data.groupby('position')['minutes'].sum())*90
    yellow_per_90_min = (data.groupby('position')['cards_yellow'].sum() / data.groupby('position')['minutes'].sum())*90
    red_per_90_min = (data.groupby('position')['cards_red'].sum() / data.groupby('position')['minutes'].sum())*90

    col1, col2 = st.columns(2)

    with col1:
        st.text("Fouls committed per 90 minutes by position")
        fig, ax = plt.subplots(figsize=(10, 5))
        fouls_per_90_min_per_position.plot(kind='bar', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close(fig)

        st.text("Yellow cards per 90 minutes by position")
        fig, ax = plt.subplots(figsize=(10, 5))
        yellow_per_90_min.plot(kind='bar', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close(fig)

        

    with col2:
        st.text("Fouls suffered per 90 minutes by position")
        fig, ax = plt.subplots(figsize=(10, 5))
        fouled_per_90_min_per_position.plot(kind='bar', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close(fig)

        st.text("Red cards per 90 minutes by position")
        fig, ax = plt.subplots(figsize=(10, 5))
        red_per_90_min.plot(kind='bar', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Fouls vs Fouled (size = minutes played)")

    fig, ax = plt.subplots(figsize=(10, 5))
    texts=[]
    temp_data = data[((data['fouled']>10) | (data['fouls']>10)) & (data['minutes']>min_minutes)]
    sns.scatterplot(data=temp_data, x='fouls', y='fouled', size='minutes', hue='position', ax=ax)
    for idx, row in temp_data.iterrows():
        texts.append(
        ax.text(row['fouls'], row['fouled'], row['player'], fontsize=12)
        )

    adjust_text(
    texts,
    ax=ax,  # <-- Just add this line to your original code
    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
    expand_text=(1.2, 1.4),                               
    force_text=(0.5, 0.5)                                 
)

    st.pyplot(fig)
    plt.close(fig)

elif selected_tab == "Top Performers":
    st.subheader("Goals vs Shots on Target (size = goals per shot on target)")
    data['goals_per_shot_on_target'] = np.where(
    data['shots_on_target'] > 0, 
    data['goals'] / data['shots_on_target'], 
    0
)

    fig, ax = plt.subplots(figsize=(10, 5))
    texts=[]

    for idx, row in data[data['goals']>3].iterrows():
        texts.append(
            ax.text(row['shots_on_target'], row['goals'], row['player'], fontsize=8)
        )
    sns.scatterplot(data=data, x='shots_on_target', y='goals', size='goals_per_shot_on_target', hue='position', ax=ax)

    adjust_text(
    texts,
    ax=ax,  # <-- Just add this line to your original code
    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
    expand_text=(1.2, 1.4),                               
    force_text=(0.5, 0.5)                                 
)

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Goals vs. assists (per 90 minutes)")
    data['goals_per_90'] = (data['goals'] / data['minutes'])*90
    data['assist_per_90'] = (data['assists'] / data['minutes'])*90

    fig, ax = plt.subplots(figsize=(10, 5))
    texts=[]
    temp_data = data[(data['goals']+data['assists']>3) & (data['minutes']>min_minutes)]
    sns.scatterplot(data=temp_data, x='goals_per_90', y='assist_per_90', size='minutes', hue='position', ax=ax)
    for idx, row in temp_data.iterrows():
        texts.append(
        ax.text(row['goals_per_90'], row['assist_per_90'], row['player'], fontsize=9)
        )

    adjust_text(
    texts,
    ax=ax,  # <-- Just add this line to your original code
    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
    expand_text=(1.2, 1.4),                               
    force_text=(0.5, 0.5)                                 
)
    st.pyplot(fig)
    plt.close(fig)


    st.subheader("Shot accuracy: shots vs. shots on target")
    fig, ax = plt.subplots(figsize=(10, 5))
    texts=[]
    temp_data = data[(data['minutes']>min_minutes)&(data['shots']>10)]
    sns.scatterplot(data=temp_data, x='shots', y='shots_on_target', size='minutes', hue='position', ax=ax)
    for idx, row in temp_data.iterrows():
        texts.append(
        ax.text(row['shots'], row['shots_on_target'], row['player'], fontsize=9)
        )

    adjust_text(
    texts,
    ax=ax,  # <-- Just add this line to your original code
    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
    expand_text=(1.2, 1.4),                               
    force_text=(0.5, 0.5)                                 
)
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Tackles won vs. fouls committed")
    fig, ax = plt.subplots(figsize=(10, 5))
    texts=[]
    temp_data = data[(data['minutes']>min_minutes)&(data['tackles_won']>7)]
    sns.scatterplot(data=temp_data, x='tackles_won', y='fouls', size='minutes', hue='position', ax=ax)
    for idx, row in temp_data.iterrows():
        texts.append(
            ax.text(row['tackles_won'], row['fouls'], row['player'], fontsize=9)
        )
    
    adjust_text(
    texts,
    ax=ax,  # <-- Just add this line to your original code
    arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
    expand_text=(1.2, 1.4),                               
    force_text=(0.5, 0.5)                                 
)
    st.pyplot(fig)
    plt.close(fig)

elif selected_tab == "Clubs":
    fig, ax = plt.subplots(figsize=(10, 5))

    st.subheader("Goals & assists — top clubs by total minutes played")
    st.text("Goals and assists by clubs")

    bar_plot_data_club = data.groupby('club').agg({'goals':'sum', 'assists':'sum', 'minutes':'sum'}).sort_values(by='minutes', ascending=False).head(10)

    plot_data = (
        bar_plot_data_club[['goals', 'assists']]
        .reset_index()
        .melt(
            id_vars='club',
            var_name='metric',
            value_name='value'
        )
    )

    sns.barplot(
        data=plot_data,
        x='club',
        y='value',
        hue='metric'
    )

    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Club')
    plt.ylabel('Total')
    plt.title('Goals and Assists by Club')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Discipline — clubs with the worst average discipline")
    st.text("top 10 clubs with the worst average discipline (yellow + red cards per 90 minutes)")

    data['bad_discipline'] = (data['cards_yellow'] + data['cards_red']*3) / data['minutes'] * 90

    bad_discipline = data.groupby('club').agg({'bad_discipline': 'mean'}).sort_values('bad_discipline', ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=bad_discipline, x=bad_discipline.index, y='bad_discipline', ax=ax)

    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Club')
    plt.ylabel('Average Bad Discipline per 90 Minutes')
    plt.title('Top 10 Clubs by Average Bad Discipline')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

elif selected_tab == "Age Trends":
    st.subheader("Age distribution")
    fig = plt.figure(figsize=(10, 6))
    sns.histplot(data['age'])
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Performance by age")
    fig = plt.figure(figsize=(10, 6))

    col1, col2 = st.columns(2)

    data['age_binned'] = pd.cut(data['age'], bins=[15, 20, 25, 30, 35, 40], labels=['16-20', '21-25', '26-30', '31-35', '36-40'])

    with col1:
        st.text("Goals and assists by age group")
        fig, ax = plt.subplots(figsize=(10, 6))
        data.groupby('age_binned').agg({'goals': 'sum', 'assists': 'sum'}).reset_index().plot(kind='bar', x='age_binned', y=['goals', 'assists'], figsize=(10,6), ax=ax)
        st.pyplot(fig)
        plt.close(fig)

    with col2:
        st.text("Tackles won and interceptions by age group")
        fig, ax = plt.subplots(figsize=(10, 6))
        data.groupby('age_binned').agg({'tackles_won': 'sum', 'interceptions': 'sum'}).reset_index().plot(kind='bar', x='age_binned', y=['tackles_won', 'interceptions'], figsize=(10,6), ax=ax)
        st.pyplot(fig)
        plt.close(fig)

st.subheader("Per-90 rates by age group")
st.text("metrics")
metric_choice = st.selectbox(
        "Metric",
        ["Assist per 90", "Goals per 90", "Tackles won per 90", "Interceptions per 90"]
    )

main_player_data = data[(data['minutes']>min_minutes)]

main_player_data['tackles_won_per_90'] = (main_player_data['tackles_won'] / main_player_data['minutes']) * 90
main_player_data['interceptions_per_90'] = (main_player_data['interceptions'] / main_player_data['minutes']) * 90

_goals_per_90_min = (main_player_data.groupby('age_binned')['goals_per_90'].sum() / main_player_data.groupby('age_binned')['minutes'].sum())*90
_assist_per_90_min = (main_player_data.groupby('age_binned')['assist_per_90'].sum() / main_player_data.groupby('age_binned')['minutes'].sum())*90
_tackles_won_per_90_min = (main_player_data.groupby('age_binned')['tackles_won_per_90'].sum() / main_player_data.groupby('age_binned')['minutes'].sum())*90
_interceptions_per_90_min = (main_player_data.groupby('age_binned')['interceptions_per_90'].sum() / main_player_data.groupby('age_binned')['minutes'].sum())*90 

fig, ax = plt.subplots(figsize=(10, 6))
if metric_choice == "Assist per 90":
    sns.barplot(_assist_per_90_min)
elif metric_choice == "Goals per 90":
    sns.barplot(_goals_per_90_min)
elif metric_choice == "Tackles won per 90":
    sns.barplot(_tackles_won_per_90_min)
elif metric_choice == "Interceptions per 90":
    sns.barplot(_interceptions_per_90_min)
st.pyplot(fig)
plt.close(fig)

