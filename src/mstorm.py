#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import sys
from scipy.signal import argrelextrema

matplotlib.rcParams['axes.linewidth'] = 0.8
matplotlib.ticker.Locator.MAXTICKS = 10000

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')

def load_data(filename):
    data = np.loadtxt(filename)
    year = data[:, 0].astype(int)
    day = data[:, 1].astype(int)
    hour = data[:, 2].astype(int)
    minute = data[:, 3].astype(int)
    sym_h = data[:, 4]
    
    time = []
    for i in range(len(year)):
        dt = datetime(year[i], 1, 1, hour[i], minute[i], 0) + timedelta(days=int(day[i]) - 1)
        time.append(dt)
    
    return np.array(time), sym_h

def find_extrema(sym_h):
    max_ids = argrelextrema(sym_h, np.greater, order=1)[0]
    min_ids = argrelextrema(sym_h, np.less, order=1)[0]
    return max_ids, min_ids

def find_falls(max_ids, min_ids):
    falls = []
    for i in range(len(max_ids) - 1):
        max_idx = max_ids[i]
        rel_min_ids = min_ids[min_ids > max_idx]
        if len(rel_min_ids) > 0:
            min_idx = rel_min_ids[0]
            falls.append([max_idx, min_idx])
    return np.array(falls)

def combine_falls(falls, time, llimit=60):
    if len(falls) == 0:
        return np.array([])
    
    comb_fall = []
    current_fall = falls[0].copy()
    
    for i in range(1, len(falls)):
        time_diff = (time[falls[i][0]] - time[current_fall[1]]).total_seconds() / 60
        if abs(time_diff) <= llimit:
            current_fall[1] = falls[i][1]
        else:
            comb_fall.append(current_fall.copy())
            current_fall = falls[i].copy()
    
    comb_fall.append(current_fall.copy())
    return np.array(comb_fall)

def apply_conditions(comb_fall, time, sym_h):
    first_datetime = []
    first_sym_h = []
    
    for i in range(len(comb_fall)):
        fall_indices = np.arange(int(comb_fall[i, 0]), int(comb_fall[i, 1]) + 1)
        current_fall_datetime = time[fall_indices]
        current_fall_sym_h = sym_h[fall_indices]
        
        min_sym = np.min(current_fall_sym_h)
        min_idx = np.argmin(current_fall_sym_h)
        
        if min_sym > -25:
            continue
        
        if min_idx == 0:
            continue
        
        max_val = np.max(current_fall_sym_h[:min_idx])
        max_idx_candidates = np.where(current_fall_sym_h[:min_idx] == max_val)[0]
        max_idx = max_idx_candidates[-1] if len(max_idx_candidates) > 0 else None
        
        if max_idx is None:
            continue
        
        modified_sym_h = current_fall_sym_h[max_idx:min_idx + 1]
        first_datetime.append(current_fall_datetime[max_idx:min_idx + 1])
        first_sym_h.append(modified_sym_h)
    
    second_datetime = []
    second_sym_h = []
    
    for i in range(len(first_sym_h)):
        current_sym_h = first_sym_h[i]
        current_datetime = first_datetime[i]
        
        max_sym = np.max(current_sym_h)
        min_sym = np.min(current_sym_h)
        max_idx = np.argmax(current_sym_h)
        min_idx = np.argmin(current_sym_h)
        
        time_diff = abs((current_datetime[max_idx] - current_datetime[min_idx]).total_seconds() / 3600)
        
        if time_diff >= 2:
            if min_idx > max_idx:
                second_datetime.append(current_datetime)
                second_sym_h.append(current_sym_h)
    
    third_datetime = []
    third_sym_h = []
    
    for i in range(len(second_sym_h)):
        current_sym_h = second_sym_h[i]
        current_datetime = second_datetime[i]
        
        max_sym = np.max(current_sym_h)
        min_sym = np.min(current_sym_h)
        
        if abs(max_sym - min_sym) >= 50:
            third_datetime.append(current_datetime)
            third_sym_h.append(current_sym_h)
    
    fourth_datetime = []
    fourth_sym_h = []
    
    if len(third_sym_h) == 0:
        return fourth_datetime, fourth_sym_h
    
    for i in range(len(third_sym_h) - 1):
        current_sym_h = third_sym_h[i]
        next_sym_h = third_sym_h[i + 1]
        current_datetime = third_datetime[i]
        next_datetime = third_datetime[i + 1]
        
        min_sym_h = np.min(current_sym_h)
        max_sym_h = np.max(next_sym_h)
        
        min_datetime = current_datetime[np.argmin(current_sym_h)]
        max_datetime = next_datetime[np.argmax(next_sym_h)]
        
        time_diff = (max_datetime - min_datetime).total_seconds() / 3600
        
        if time_diff <= 10:
            missing_mask = (time > min_datetime) & (time < max_datetime)
            missing_sym_h = sym_h[missing_mask]
            missing_datetime = time[missing_mask]
            
            combined_sym_h = np.concatenate([current_sym_h, missing_sym_h, next_sym_h])
            combined_datetime = np.concatenate([current_datetime, missing_datetime, next_datetime])
            
            fourth_sym_h.append(combined_sym_h)
            fourth_datetime.append(combined_datetime)
        else:
            fourth_sym_h.append(current_sym_h)
            fourth_datetime.append(current_datetime)
    
    fourth_sym_h.append(third_sym_h[-1])
    fourth_datetime.append(third_datetime[-1])
    
    return fourth_datetime, fourth_sym_h

def setup_ax_style(ax):
    ax.set_xlabel('UT (Hours)', fontsize=14)
    ax.set_ylabel('SYM/H (nT)', fontsize=14)
    ax.tick_params(axis='both', which='major', labelsize=12, width=1.5, length=6)
    ax.minorticks_on()
    ax.tick_params(axis='both', which='minor', width=1, length=3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.axhline(y=0, color='k', linestyle=':', linewidth=1)

def set_time_axis(ax, t_min, t_max):
    days_diff = (t_max.date() - t_min.date()).days
    if days_diff <= 1:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
    elif days_diff <= 7:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%H'))
    elif days_diff <= 31:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    elif days_diff <= 180:
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif days_diff <= 730:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
    fig = ax.get_figure()
    fig.autofmt_xdate(rotation=45)

def identify_storms(fourth_datetime, fourth_sym_h, time, sym_h):
    storm_table = []
    
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.unicode_minus'] = False
    
    for i in range(len(fourth_sym_h)):
        max_sym = np.max(fourth_sym_h[i])
        min_sym = np.min(fourth_sym_h[i])
        max_idx = np.argmax(fourth_sym_h[i])
        min_idx = np.argmin(fourth_sym_h[i])
        
        time_diff = (fourth_datetime[i][max_idx] - fourth_datetime[i][min_idx]).total_seconds() / 3600
        
        if time_diff == 0:
            continue
        
        if (max_sym - min_sym) / time_diff < -5:
            mpo_datetime = fourth_datetime[i][max_idx]
            min_datetime = fourth_datetime[i][min_idx]
            
            search_end = min_datetime + timedelta(hours=10)
            raw_mask = (time > min_datetime) & (time <= search_end)
            if np.any(raw_mask):
                raw_range = sym_h[raw_mask]
                raw_times = time[raw_mask]
                local_min_idx = np.argmin(raw_range)
                if raw_range[local_min_idx] < min_sym:
                    min_sym = raw_range[local_min_idx]
                    min_datetime = raw_times[local_min_idx]
            
            if fourth_sym_h[i][max_idx] > 0:
                range_indices = np.arange(max_idx, min_idx + 1)
                first_zero_neg = np.where(fourth_sym_h[i][range_indices] <= 0)[0]
                if len(first_zero_neg) > 0:
                    first_zero_neg_idx = first_zero_neg[0] + max_idx
                else:
                    first_zero_neg_idx = max_idx
                
                sum_indices = np.arange(first_zero_neg_idx, min_idx + 1)
                time_diff_1 = (min_datetime - fourth_datetime[i][first_zero_neg_idx]).total_seconds() / 60
                
                adjusted_sym_h = fourth_sym_h[i][max_idx:min_idx + 1] - fourth_sym_h[i][max_idx]
                time_diff_2 = (min_datetime - mpo_datetime).total_seconds() / 60
            else:
                sum_indices = np.arange(max_idx, min_idx + 1)
                time_diff_1 = (min_datetime - mpo_datetime).total_seconds() / 60
                
                adjusted_sym_h = fourth_sym_h[i][max_idx:min_idx + 1]
                time_diff_2 = time_diff_1
            
            sum_sym_h = np.sum(fourth_sym_h[i][sum_indices])
            ips_sym_h = sum_sym_h / time_diff_1 if time_diff_1 > 0 else 0
            
            sum_adjusted_sym_h = np.sum(adjusted_sym_h)
            ips_sym_h_star = sum_adjusted_sym_h / time_diff_2 if time_diff_2 > 0 else 0
            
            if fourth_sym_h[i][max_idx] > 0:
                sym_h_min_star = fourth_sym_h[i][min_idx] - fourth_sym_h[i][max_idx]
            else:
                sym_h_min_star = fourth_sym_h[i][min_idx]
            
            storm_table.append({
                'Fall_Index': i,
                'MPO_Datetime': mpo_datetime,
                'MIN_Datetime': min_datetime,
                'MPO': max_sym,
                'MIN': min_sym,
                'Ips': ips_sym_h,
                'Revised_Min': sym_h_min_star,
                'Revised_Ips': ips_sym_h_star
            })
    
    return storm_table

def plot_single_storm(ax, fall_idx, fourth_datetime, fourth_sym_h, time, sym_h, storm_info):
    mpo_dt = storm_info['MPO_Datetime']
    min_dt = storm_info['MIN_Datetime']
    
    window = timedelta(hours=12)
    t_start = mpo_dt - window
    t_end = min_dt + window
    
    mask = (time >= t_start) & (time <= t_end)
    plot_time = time[mask]
    plot_sym_h = sym_h[mask]
    
    ax.plot(plot_time, plot_sym_h, '-k', linewidth=1.2)
    
    storm_dt = fourth_datetime[fall_idx]
    storm_sh = fourth_sym_h[fall_idx]
    
    if min_dt > storm_dt[-1]:
        ext_mask = (time > storm_dt[-1]) & (time <= min_dt)
        if np.any(ext_mask):
            storm_dt = np.concatenate([storm_dt, time[ext_mask]])
            storm_sh = np.concatenate([storm_sh, sym_h[ext_mask]])
    
    _, unique_indices = np.unique(storm_dt, return_index=True)
    unique_indices = np.sort(unique_indices)
    storm_dt_clean = storm_dt[unique_indices]
    storm_sh_clean = storm_sh[unique_indices]
    
    ax.plot(storm_dt_clean, storm_sh_clean, '-', color='#2196F3', linewidth=1.7)
    
    max_sym = storm_info['MPO']
    min_sym = storm_info['MIN']
    
    ax.fill_between([mdates.date2num(mpo_dt), mdates.date2num(min_dt)], min_sym, max_sym, alpha=0.15, color='#FFC107')
    
    mpo_label = f"{max_sym:.1f} // {mpo_dt.strftime('%H:%M')}"
    min_label = f"{min_sym:.1f} // {min_dt.strftime('%H:%M')}"
    
    ax.annotate(mpo_label, xy=(mpo_dt, max_sym), 
               fontsize=9, fontweight='bold', color='#4CAF50',
               ha='center', va='bottom',
               xytext=(0, 8), textcoords='offset points')
    ax.annotate(min_label, xy=(min_dt, min_sym), 
               fontsize=9, fontweight='bold', color='#F44336',
               ha='center', va='top',
               xytext=(0, -8), textcoords='offset points')
    
    setup_ax_style(ax)
    set_time_axis(ax, t_start, t_end)
    plt.tight_layout()

def plot_all_storms(fourth_datetime, fourth_sym_h, time, sym_h, storm_table):
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(time, sym_h, '-k', linewidth=1.2)
    
    setup_ax_style(ax)
    
    for i in range(len(fourth_sym_h)):
        storm_dt = fourth_datetime[i]
        storm_sh = fourth_sym_h[i]
        
        _, unique_indices = np.unique(storm_dt, return_index=True)
        unique_indices = np.sort(unique_indices)
        storm_dt_clean = storm_dt[unique_indices]
        storm_sh_clean = storm_sh[unique_indices]
        
        ax.plot(storm_dt_clean, storm_sh_clean, '-', color='#2196F3', linewidth=1.7)
        
        max_sym = np.max(fourth_sym_h[i])
        min_sym = np.min(fourth_sym_h[i])
        max_idx = np.argmax(fourth_sym_h[i])
        min_idx = np.argmin(fourth_sym_h[i])
        
        mpo_dt = fourth_datetime[i][max_idx]
        min_dt = fourth_datetime[i][min_idx]
        
        is_storm = any(s['MPO_Datetime'] == mpo_dt and s['MIN_Datetime'] == min_dt for s in storm_table)
        
        if is_storm:
            ax.fill_between([mdates.date2num(mpo_dt), mdates.date2num(min_dt)], min_sym, max_sym, alpha=0.15, color='#FFC107')
            
            mpo_label = f"{max_sym:.1f} // {mpo_dt.strftime('%H:%M')}"
            min_label = f"{min_sym:.1f} // {min_dt.strftime('%H:%M')}"
            
            ax.annotate(mpo_label, xy=(mpo_dt, max_sym), 
                       fontsize=9, fontweight='bold', color='#4CAF50',
                       ha='center', va='bottom',
                       xytext=(0, 8), textcoords='offset points')
            ax.annotate(min_label, xy=(min_dt, min_sym), 
                       fontsize=9, fontweight='bold', color='#F44336',
                       ha='center', va='top',
                       xytext=(0, -8), textcoords='offset points')
    
    set_time_axis(ax, time[0], time[-1])
    plt.tight_layout()
    return fig

def save_results(storm_table, output_dir, plot_all=False, all_fig=None, 
                 fourth_datetime=None, fourth_sym_h=None, time=None, sym_h=None):
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    df = pd.DataFrame(storm_table)
    df['MPO_Datetime'] = df['MPO_Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['MIN_Datetime'] = df['MIN_Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df.to_csv(os.path.join(output_dir, 'stormlist.csv'), index=False)
    print(f"Storm table saved to output/stormlist.csv")
    
    if plot_all and all_fig is not None:
        all_fig.savefig(os.path.join(images_dir, 'allstorms.png'), dpi=150, bbox_inches='tight')
        plt.close(all_fig)
        print(f"All storms plot saved to output/images/allstorms.png")
    
    if not plot_all:
        for storm in storm_table:
            fig, ax = plt.subplots(figsize=(14, 7))
            plot_single_storm(ax, storm['Fall_Index'], fourth_datetime, fourth_sym_h, time, sym_h, storm)
            
            mpo_dt = storm['MPO_Datetime']
            min_dt = storm['MIN_Datetime']
            filename = f"{mpo_dt.strftime('%Y%m%d_%H%M')}-{min_dt.strftime('%Y%m%d_%H%M')}"
            
            fig.savefig(os.path.join(images_dir, f"{filename}.png"), dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Storm plot saved to output/images/{filename}.png")

def main():
    plot_all = False
    llimit = 60
    data_file = None
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--all':
            plot_all = True
            i += 1
        elif args[i] in ('--llimit', '-ll'):
            llimit = int(args[i + 1])
            i += 2
        else:
            data_file = args[i]
            i += 1
    
    if data_file is None:
        data_file = os.path.join(DATA_DIR, 'data.txt')
    
    output_dir = OUTPUT_DIR
    
    print(f"Loading data from {data_file}...")
    time, sym_h = load_data(data_file)
    
    print(f"Data loaded: {len(time)} points from {time[0]} to {time[-1]}")
    
    print("Finding local maxima and minima...")
    max_ids, min_ids = find_extrema(sym_h)
    print(f"Found {len(max_ids)} maxima and {len(min_ids)} minima")
    
    print("Identifying falling regions...")
    falls = find_falls(max_ids, min_ids)
    print(f"Found {len(falls)} falling regions")
    
    print(f"Combining nearby falls (limit={llimit} min)...")
    comb_fall = combine_falls(falls, time, llimit)
    print(f"After combining: {len(comb_fall)} regions")
    
    print("Applying filtering conditions...")
    fourth_datetime, fourth_sym_h = apply_conditions(comb_fall, time, sym_h)
    print(f"After conditions: {len(fourth_sym_h)} candidate regions")
    
    print("Identifying storms...")
    storm_table = identify_storms(fourth_datetime, fourth_sym_h, time, sym_h)
    
    print(f"\nNumber of GeoMagnetic Storms detected: {len(storm_table)}")
    
    if len(storm_table) > 0:
        print("\nStorm Table:")
        df = pd.DataFrame(storm_table)
        print(df.to_string(index=False))
    
    print("\nSaving results...")
    if plot_all:
        all_fig = plot_all_storms(fourth_datetime, fourth_sym_h, time, sym_h, storm_table)
        save_results(storm_table, output_dir, plot_all=True, all_fig=all_fig)
    else:
        save_results(storm_table, output_dir, plot_all=False,
                    fourth_datetime=fourth_datetime, fourth_sym_h=fourth_sym_h, 
                    time=time, sym_h=sym_h)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()
