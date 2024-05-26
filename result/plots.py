import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set font size parameters
plt.rcParams.update({
    'font.size': 20,  # Default text size
    'axes.titlesize': 16,  # Title size
    'axes.labelsize': 20,  # X and Y label size
    'xtick.labelsize': 20,  # X tick label size
    'ytick.labelsize': 20,  # Y tick label size
    'legend.fontsize': 14  # Legend font size
})

# Load JSON data from files
with open('results_6tisch.json') as f:
    data_6tisch = json.load(f)

with open('results_bg_synced.json') as f:
    data_bg_synced = json.load(f)

with open('results_rapdad.json') as f:
    data_rapdad = json.load(f)

with open('results_shmg.json') as f:
    data_shmg = json.load(f)

# Correcting the extraction function to include the 'topo' field
def extract_data_with_topo(data, mode):
    return pd.DataFrame({
        'time_to_desync': [entry.get('time_to_desync', 0) for entry in data],
        'connectivity': [entry.get('connectivity', 0) for entry in data],
        'extra_cost': [entry.get('extra_cost', 0) for entry in data],
        'topo': [entry.get('topo', '') for entry in data],
        'mode': mode
    })

df_6tisch = extract_data_with_topo(data_6tisch, '6tisch')
df_bg_synced = extract_data_with_topo(data_bg_synced, 'bg_synced')
df_rapdad = extract_data_with_topo(data_rapdad, 'rapdad')
df_shmg = extract_data_with_topo(data_shmg, 'shmg')

# Combine all data into a single DataFrame
df = pd.concat([df_6tisch, df_bg_synced, df_rapdad, df_shmg])

# Desired order of topologies
topo_order = ['topology\\topology_10_5.json', 
              'topology\\topology_100_10.json', 
              'topology\\topology_100_50.json', 
              'topology\\topology_100_100.json', 
              'topology\\topology_500_50.json']

# Reorder the grouped DataFrame based on the desired topology order
grouped = df.groupby(['topo', 'mode']).agg(['mean', 'std']).reset_index()
grouped['topo'] = pd.Categorical(grouped['topo'], categories=topo_order, ordered=True)
grouped = grouped.sort_values('topo')

# Rename columns for easier access
grouped.columns = ['topo', 'mode', 'time_to_desync_mean', 'time_to_desync_std', 
                   'connectivity_mean', 'connectivity_std', 
                   'extra_cost_mean', 'extra_cost_std']

# Extract unique topologies and modes for plotting
topologies = grouped['topo'].unique()
modes = grouped['mode'].unique()

# Function to plot and save the figures in PDF format
def plot_with_lines_and_save(data, y_label, title, y_mean_col, y_std_col, filename):
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(topologies))

    for i, mode in enumerate(modes):
        mode_data = data[data['mode'] == mode]
        ax.errorbar(x, mode_data[y_mean_col], yerr=mode_data[y_std_col], fmt='o', capsize=5, label=mode)
        ax.plot(x, mode_data[y_mean_col], label=f"{mode} line")

    ax.set_xticks(x)
    ax.set_xticklabels([t.split('\\')[-1].replace('topology_', '').replace('.json', '') for t in topologies], rotation=0)
    ax.set_xlabel('')
    ax.set_ylabel(y_label)
    # ax.set_title(title)
    ax.legend()
    plt.savefig(f"../../figures/{filename}.png")
    plt.close()

# Plotting and saving each figure as a PDF
plot_with_lines_and_save(grouped, 'Time to Rejoin (s)', 'Time to Desync among Different Topologies', 'time_to_desync_mean', 'time_to_desync_std', 'time_to_desync')
plot_with_lines_and_save(grouped, 'Connectivity', 'Connectivity among Different Topologies', 'connectivity_mean', 'connectivity_std', 'connectivity')
plot_with_lines_and_save(grouped, 'Cost ($)', 'Cost among Different Topologies', 'extra_cost_mean', 'extra_cost_std', 'cost')

# Return the file paths for downloading
file_paths = {
    "time_to_desync":   "../../figures/time_to_desync.pdf",
    "connectivity":     "../../figures/connectivity.pdf",
    "cost":             "../../figures/cost.pdf"
}

file_paths
