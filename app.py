import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.colors import LinearSegmentedColormap
from pybaseball import statcast_batter

st.set_page_config(page_title="大谷翔平打撃分析",layout="centered")

st.title("大谷翔平 打撃分析")
st.write("MLBデータを用いた打撃ゾーン分析です。")
year=st.selectbox("シーズンを選択",[2026,2025,2024,2023,2022,2021,2020])

# データ取得
@st.cache_data
def load_data(year):
    start = f'{year}-03-01'
    end = f'{year}-11-01'
    df = statcast_batter(start, end, player_id=660271)
    return df

df = load_data(year)

# レギュラーシーズンのみ
#rs = df[df['game_date'] >= '2026-03-26']
rs=df[df['game_type']=="R"]

# 打数の定義
non_ab_events = ['walk', 'hit_by_pitch', 'sac_fly', 'sac_bunt']
at_bats = rs[
    rs['events'].notna() &
    ~rs['events'].isin(non_ab_events)
].dropna(subset=['zone'])

# ヒットの定義
hit_events = ['single', 'double', 'triple', 'home_run']
pitches=len(rs)
pa=len(rs[rs["events"].notna()])
ab=rs[
    rs["events"].notna()&
    ~rs["events"].isin(non_ab_events)
]

h=ab[ab["events"].isin(hit_events)]
single=ab[ab["events"]=="single"]
double =ab[ab["events"]=="double"]
triple=ab[ab["events"]=="triple"]
hr=ab[ab["events"]=="home_run"]
avg=len(h)/len(ab) if len(ab)>0 else 0

so=len(ab[ab["events"]=="strikeout"])
k_pct=so/pa*100 if pa>0 else 0
k_pct = so / pa * 100 if pa > 0 else 0

ev = rs['launch_speed'].mean()
la = rs['launch_angle'].mean()


st.subheader("Summary")

summary = {
    "Pitches": pitches,
    "PA": pa,
    "H": len(h),
    "1B": len(single),
    "2B": len(double),
    "3B": len(triple),
    "HR": len(hr),
    "AVG": f"{avg:.3f}",
    "SO": so,
    "K%": f"{k_pct:.1f}",
    "EV": f"{ev:.1f}",
}

cols = st.columns(len(summary))
for i, (label, value) in enumerate(summary.items()):
    with cols[i]:
        st.markdown(f"**{label}**")
        st.markdown(f"### {value}")

# ゾーンの設定
cmap = LinearSegmentedColormap.from_list('ba', ['#4444aa', '#aa0000'])
sz_top = 0.83
sz_bot = -0.83
x_left = -0.83
x_right = 0.83
zone_width = x_right - x_left
zone_height = sz_top - sz_bot
x_thirds = [x_left, x_left + zone_width/3, x_left + zone_width*2/3, x_right]
z_thirds = [sz_bot, sz_bot + zone_height/3, sz_bot + zone_height*2/3, sz_top]
outer_w = 0.5
outer_h = 0.5
x_mid = (x_left + x_right) / 2
z_mid = (sz_bot + sz_top) / 2

def calc_zone_by_id(zone_ids):
    mask = at_bats['zone'].isin(zone_ids)
    zone_ab = at_bats[mask]
    total = len(zone_ab)
    hits_count = zone_ab['events'].isin(hit_events).sum()
    ba = hits_count / total if total > 0 else 0
    pitch_counts = zone_ab['pitch_type'].value_counts().head(2)
    return ba, total, pitch_counts

def draw_zone(ax, x_min, x_max, z_min, z_max, ba,
              show_pitch=False, pitch_counts=None):
    color = cmap(ba / 0.5) if ba > 0 else '#4444aa'
    rect = patches.Rectangle(
        (x_min, z_min), x_max - x_min, z_max - z_min,
        linewidth=1, edgecolor='white', facecolor=color, alpha=1.0
    )
    ax.add_patch(rect)
    cx = (x_min + x_max) / 2
    cz = (z_min + z_max) / 2
    ax.text(cx, cz + (0.05 if show_pitch else 0),
            f'.{round(ba*1000):03d}',
            ha='center', va='center',
            fontsize=13, fontweight='bold', color='white')
    if show_pitch and pitch_counts is not None and len(pitch_counts) > 0:
        pitch_text = ' '.join([f'{p}:{n}' for p, n in pitch_counts.items()])
        ax.text(cx, cz - 0.07, pitch_text,
                ha='center', va='center', fontsize=7, color='white')

def draw_l_shape(ax, vertices, ba, text_pos):
    codes = ([Path.MOVETO] +
             [Path.LINETO] * (len(vertices) - 2) +
             [Path.CLOSEPOLY])
    path = Path(vertices, codes)
    patch = PathPatch(path, facecolor='#3333aa',
                      edgecolor='white', linewidth=1, alpha=0.5)
    ax.add_patch(patch)
    tx, tz = text_pos
    ax.text(tx, tz, f'.{round(ba*1000):03d}',
            ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')

# グラフ作成
fig, ax = plt.subplots(figsize=(8, 9))

zone_grid = [
    [7, 8, 9],
    [4, 5, 6],
    [1, 2, 3],
]

for row_idx in range(3):
    for col_idx in range(3):
        zone_id = zone_grid[row_idx][col_idx]
        x_min = x_thirds[col_idx]
        x_max = x_thirds[col_idx + 1]
        z_min = z_thirds[row_idx]
        z_max = z_thirds[row_idx + 1]
        ba, total, pitch_counts = calc_zone_by_id([zone_id])
        draw_zone(ax, x_min, x_max, z_min, z_max, ba,
                  show_pitch=True, pitch_counts=pitch_counts)

# 右上L字（zone 11）
ba, _, _ = calc_zone_by_id([11])
draw_l_shape(ax, [
    (x_mid, sz_top),
    (x_mid, sz_top + outer_h),
    (x_right + outer_w, sz_top + outer_h),
    (x_right + outer_w, z_mid),
    (x_right, z_mid),
    (x_right, sz_top),
    (x_mid, sz_top),
], ba, text_pos=(x_right + outer_w/2, (z_mid + sz_top + outer_h)/2))

# 左上L字（zone 12）
ba, _, _ = calc_zone_by_id([12])
draw_l_shape(ax, [
    (x_left - outer_w, z_mid),
    (x_left - outer_w, sz_top + outer_h),
    (x_mid, sz_top + outer_h),
    (x_mid, sz_top),
    (x_left, sz_top),
    (x_left, z_mid),
    (x_left - outer_w, z_mid),
], ba, text_pos=(x_left - outer_w/2, (z_mid + sz_top + outer_h)/2))

# 左下L字（zone 13）
ba, _, _ = calc_zone_by_id([13])
draw_l_shape(ax, [
    (x_left - outer_w, sz_bot - outer_h),
    (x_left - outer_w, z_mid),
    (x_left, z_mid),
    (x_left, sz_bot),
    (x_mid, sz_bot),
    (x_mid, sz_bot - outer_h),
    (x_left - outer_w, sz_bot - outer_h),
], ba, text_pos=(x_left - outer_w/2, (sz_bot - outer_h + z_mid)/2))

# 右下L字（zone 14）
ba, _, _ = calc_zone_by_id([14])
draw_l_shape(ax, [
    (x_mid, sz_bot - outer_h),
    (x_mid, sz_bot),
    (x_right, sz_bot),
    (x_right, z_mid),
    (x_right + outer_w, z_mid),
    (x_right + outer_w, sz_bot - outer_h),
    (x_mid, sz_bot - outer_h),
], ba, text_pos=(x_right + outer_w/2, (sz_bot - outer_h + z_mid)/2))

# 外枠
outer_rect = patches.Rectangle(
    (x_left, sz_bot), zone_width, zone_height,
    linewidth=2, edgecolor='white', facecolor='none'
)
ax.add_patch(outer_rect)

ax.set_xlim(-1.5, 1.5)
ax.set_ylim(sz_bot - 0.8, sz_top + 0.8)
ax.set_title('Shohei Ohtani\nBatting Average by Zone & Pitch Type',
             fontsize=14, fontweight='bold', color='white')
ax.set_facecolor('#1a1a2e')
fig.patch.set_facecolor('#1a1a2e')
ax.axis('off')

# Streamlitで表示
st.pyplot(fig)