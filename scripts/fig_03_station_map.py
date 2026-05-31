"""Generate Figure 3.1 (Thesis Chapter 3): BMKG station map with admin boundaries.

Indonesia-wide map: admin1 (province) + admin0 (country) + world admin0 (neighbors).
Color-coded stations by region; saved to paper/thesis/figures/.
"""
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ----- Load station coordinates -----
df = pd.read_csv('data/input/stations/idn_cli_weatherstation_location_bmkg.csv',
                 sep=';', encoding='utf-8-sig')
df.columns = [c.strip() for c in df.columns]
print(f'Loaded {len(df)} stations')

# Normalize region names
region_norm = {
    'Sumatra': 'Sumatra',
    'Jawa': 'Java',
    'Java': 'Java',
    'Kalimantan': 'Kalimantan',
    'Sulawesi': 'Sulawesi',
    'Bali Nusa Tenggara': 'Bali-Nusa Tenggara',
    'Bali dan Nusa Tenggara': 'Bali-Nusa Tenggara',
    'Bali-Nusa Tenggara': 'Bali-Nusa Tenggara',
    'Maluku': 'Maluku',
    'Papua': 'Papua',
}
df['region_norm'] = df['region'].str.strip().map(region_norm).fillna(df['region'])

# ----- Load admin boundaries -----
idn_adm0 = gpd.read_file('data/subset/bnd/idn_bnd_adm0.shp')
idn_adm1 = gpd.read_file('data/subset/bnd/idn_bnd_adm1.shp')
wld_adm0 = gpd.read_file('data/subset/bnd/wld_bnd_adm0.shp')
print(f'Loaded admin0 (IDN): {len(idn_adm0)} feature(s)')
print(f'Loaded admin1 (IDN): {len(idn_adm1)} provinces')
print(f'Loaded admin0 (world): {len(wld_adm0)} countries')

# ----- Region color map -----
REGION_COLORS = {
    'Sumatra':           '#1f77b4',
    'Java':              '#d62728',
    'Kalimantan':        '#2ca02c',
    'Sulawesi':          '#9467bd',
    'Bali-Nusa Tenggara':'#ff7f0e',
    'Maluku':            '#17becf',
    'Papua':             '#8c564b',
}

# ----- Figure -----
fig, ax = plt.subplots(figsize=(13, 5.5), constrained_layout=True)

# Indonesia bounding box: 94E-142E, 11.5S-7N
xlim = (94, 142)
ylim = (-11.5, 7.0)

# Layer 1: neighbor countries (faint, deemphasized)
# Clip world to a slightly larger box for visual context
buf = 5
wld_adm0_clip = wld_adm0.clip([xlim[0] - buf, ylim[0] - buf,
                                xlim[1] + buf, ylim[1] + buf])
wld_adm0_clip.plot(ax=ax, facecolor='#e8e8e8', edgecolor='#999999',
                   linewidth=0.4, zorder=1)

# Layer 2: Indonesia provinces (admin1) - light gray lines
idn_adm1.plot(ax=ax, facecolor='#fafaf2', edgecolor='#999999',
              linewidth=0.3, zorder=2)

# Layer 3: Indonesia national boundary (admin0) - dark, prominent
idn_adm0.plot(ax=ax, facecolor='none', edgecolor='#2c2c2c',
              linewidth=0.8, zorder=3)

# Layer 4: stations
for region, color in REGION_COLORS.items():
    sub = df[df['region_norm'] == region]
    if len(sub) > 0:
        ax.scatter(sub['Lon'], sub['Lat'],
                   c=color, s=28, edgecolors='white', linewidths=0.5,
                   label=f'{region} (n={len(sub)})', zorder=4)

# Equator line
ax.axhline(0, color='gray', lw=0.4, ls='--', alpha=0.5, zorder=2.5)
ax.text(141.5, 0.2, 'Equator', fontsize=8, color='gray',
        ha='right', va='bottom', zorder=5)

ax.set_xlim(*xlim)
ax.set_ylim(*ylim)
ax.set_title('BMKG Station Network across Indonesia',
             fontsize=13, fontweight='bold', pad=10)
ax.set_xlabel('Longitude (degrees E)', fontsize=10)
ax.set_ylabel('Latitude (degrees)', fontsize=10)
ax.tick_params(labelsize=9)

ax.legend(loc='lower left', fontsize=8, framealpha=0.95,
          title=f'Total archived: {len(df)} stations  (171 retained, 9 dropped)',
          title_fontsize=8.5,
          ncol=2)

ax.set_aspect('equal', adjustable='box')

# Save
os.makedirs('paper/thesis/figures', exist_ok=True)
out = 'paper/thesis/figures/fig_thesis_03_station_map.png'
plt.savefig(out, dpi=300, bbox_inches='tight')
print(f'Saved: {out}')
