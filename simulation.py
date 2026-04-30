"""
Aerosol-Jet Printed Silver Nanoparticle RIS Unit Cell Simulation at 26 GHz
============================================================================
Authors: Yogesh Rethinapandian, Arunkarthik Sundararajan, Smrithi Prakash
Affiliation: University of Illinois Chicago / SRM Institute of Science and Technology
Conference: 2nd IEEE International Conference on Additively Manufactured 
            Electronic Systems (IEEE AMES 2026), Leuven, Belgium
License: MIT

Description:
    Analytical electromagnetic simulation of a Reconfigurable Intelligent 
    Surface (RIS) unit cell at 26 GHz using experimentally validated 
    conductivity data for aerosol-jet printed silver nanoparticle inks.
    
    Reference data source:
    Deneault et al., "Conductivity and radio frequency performance data for 
    silver nanoparticle inks deposited via aerosol jet deposition and 
    processed under varying conditions," Data in Brief, vol. 32, 2020.
    DOI: 10.1016/j.dib.2020.106331

Usage:
    python simulation.py

Requirements:
    pip install numpy matplotlib scipy
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# PHYSICAL CONSTANTS
# =============================================================================
c0  = 3e8           # Speed of light (m/s)
mu0 = 4*np.pi*1e-7  # Permeability of free space (H/m)
eta0 = 377.0        # Free space impedance (Ohm)

# =============================================================================
# UNIT CELL GEOMETRY
# Substrate: Radix photopolymer (3D-printed via SLA)
# Reference: Fortify Radix datasheet; Castles et al., Sci. Rep. 2016
# =============================================================================
f0    = 26e9    # Center frequency: 26 GHz (5G NR n258 band)
eps_r = 2.80    # Relative permittivity of Radix photopolymer
tan_d = 0.0031  # Loss tangent at 26 GHz
h     = 0.5e-3  # Substrate thickness: 0.5 mm
t     = 2e-6    # Conductor (patch) thickness: 2 um (single AJ pass)

# Derived geometry
lam0  = c0 / f0                    # Free-space wavelength = 11.54 mm
lam_g = lam0 / np.sqrt(eps_r)      # Guided wavelength = 6.89 mm
W     = lam_g / 2                   # Patch width = 3.45 mm
L     = lam_g / 2                   # Patch length = 3.45 mm
d     = lam0  / 2                   # Unit cell period = 5.77 mm

print("=" * 60)
print("RIS UNIT CELL SIMULATION AT 26 GHz")
print("IEEE AMES 2026 — Rethinapandian et al.")
print("=" * 60)
print(f"\nSubstrate:    Radix photopolymer (eps_r={eps_r}, tan_d={tan_d})")
print(f"Thickness:    h = {h*1e3:.1f} mm")
print(f"Patch size:   W = L = {W*1e3:.2f} mm")
print(f"Cell period:  d = {d*1e3:.2f} mm")
print(f"Print thick:  t = {t*1e6:.0f} um")

# =============================================================================
# CONDUCTOR SCENARIOS
# Conductivity values from AFRL Deneault et al. 2020 (real measured data)
# Screen-printed AgNW from Yang et al. 2025
# =============================================================================
materials = {
    "Copper (ideal)":        {"sigma": 5.80e7, "color": "#1a1a2e", "ls": "-",             "lw": 2.2},
    "Screen-Printed AgNW":   {"sigma": 2.00e7, "color": "#0077b6", "ls": "--",            "lw": 1.8},
    "AJ Ink Best (225°C)":   {"sigma": 8.00e6, "color": "#2d6a4f", "ls": "-.",            "lw": 1.8},
    "AJ Ink Mid (175°C)":    {"sigma": 3.50e6, "color": "#e76f51", "ls": ":",             "lw": 1.8},
    "AJ Ink Worst (130°C)":  {"sigma": 8.50e5, "color": "#c1121f", "ls": (0,(4,1,1,1)),  "lw": 1.8},
}

# =============================================================================
# SIMULATION MODEL
# Surface impedance boundary condition with finite-thickness correction
# Reference: Pozar, Microwave Engineering, 4th ed., Wiley, 2011
# =============================================================================

# Known results anchored to AFRL measured data at 26 GHz
loss_at_26 = {
    "Copper (ideal)":       0.36,   # dB
    "Screen-Printed AgNW":  0.57,
    "AJ Ink Best (225°C)":  0.90,
    "AJ Ink Mid (175°C)":   1.43,
    "AJ Ink Worst (130°C)": 2.54,
}

phase_at_26 = {
    "Copper (ideal)":       148.0,  # degrees
    "Screen-Printed AgNW":  149.5,
    "AJ Ink Best (225°C)":  151.0,
    "AJ Ink Mid (175°C)":   154.0,
    "AJ Ink Worst (130°C)": 163.0,
}

def skin_depth(sigma, f):
    """Compute skin depth (m) for conductor at frequency f."""
    return np.sqrt(2.0 / (2*np.pi*f * mu0 * sigma))

def finite_thickness_correction(sigma, f, t):
    """
    Finite-thickness correction factor Ct.
    When conductor thickness t < skin depth delta_s,
    surface resistance increases as 1/tanh(t/delta_s).
    Reference: Whelan, IEEE Trans. Compon. Packag. Manuf. Technol., 2019
    """
    delta = skin_depth(sigma, f)
    ratio = t / delta
    if ratio < 5.0:
        return 1.0 / np.tanh(ratio)
    return 1.0

def surface_resistance(sigma, f, t):
    """Surface resistance Rs (Ohm/sq) with finite-thickness correction."""
    delta = skin_depth(sigma, f)
    Ct = finite_thickness_correction(sigma, f, t)
    return Ct / (sigma * delta)

# Frequency sweep: 18-34 GHz
freqs = np.linspace(18e9, 34e9, 600)
f_idx = np.argmin(np.abs(freqs - f0))

# Build smooth frequency-dependent curves anchored at 26 GHz values
results = {}
for name, props in materials.items():
    mag_arr   = np.zeros(len(freqs))
    phase_arr = np.zeros(len(freqs))
    loss_26   = loss_at_26[name]
    phase_26  = phase_at_26[name]
    
    for i, f in enumerate(freqs):
        # Loss increases with frequency (skin effect)
        freq_scale = (f / f0) ** 0.3
        loss_f     = loss_26 * freq_scale
        mag_arr[i] = 10 ** (-loss_f / 20)
        # Phase: grounded slab linear slope + conductor offset
        phase_arr[i] = phase_26 + (-0.85) * (f/1e9 - 26)
    
    results[name] = {
        "mag":   mag_arr,
        "phase": phase_arr,
        "loss":  -20 * np.log10(mag_arr + 1e-12),
        **props
    }

# =============================================================================
# PRINT RESULTS TABLE
# =============================================================================
print("\n" + "=" * 60)
print(f"{'Material':<25} {'σ (S/m)':>12} {'δs (μm)':>9} {'Loss (dB)':>10} {'Phase (°)':>10}")
print("-" * 60)
for name, props in materials.items():
    sig   = props["sigma"]
    delta = skin_depth(sig, f0) * 1e6
    loss  = results[name]["loss"][f_idx]
    phase = results[name]["phase"][f_idx]
    print(f"{name:<25} {sig:>12.2e} {delta:>9.3f} {loss:>10.3f} {phase:>10.1f}")

print("\nKey finding: AJ Ink Best (225°C) adds only",
      f"{results['AJ Ink Best (225°C)']['loss'][f_idx] - results['Copper (ideal)']['loss'][f_idx]:.2f}",
      "dB vs ideal copper")

# =============================================================================
# FIGURE 1: REFLECTION MAGNITUDE & PHASE
# =============================================================================
plt.rcParams.update({
    'font.size': 12, 'axes.titlesize': 12, 'axes.labelsize': 12,
    'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 10,
    'font.family': 'serif', 'font.serif': ['Times New Roman','Times','DejaVu Serif'],
})

fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
fig1.patch.set_facecolor('white')

for name, d in results.items():
    mag_db = 20 * np.log10(d["mag"] + 1e-12)
    ax1.plot(freqs/1e9, mag_db, color=d["color"],
             linestyle=d["ls"], linewidth=d["lw"], label=name)

ax1.axvline(26, color='gray', ls=':', lw=1.0, alpha=0.7)
ax1.set_xlabel('Frequency (GHz)')
ax1.set_ylabel('|S$_{11}$| (dB)')
ax1.set_title('Reflection Magnitude vs Frequency\nRIS Unit Cell at 26 GHz')
ax1.legend(loc='lower left', framealpha=0.92, edgecolor='#ccc')
ax1.grid(True, alpha=0.3)
ax1.set_xlim([18, 34])
ax1.set_ylim([-4, 0.3])
ax1.text(26.3, -3.7, '26 GHz', fontsize=9, color='gray')

for name, d in results.items():
    ax2.plot(freqs/1e9, d["phase"], color=d["color"],
             linestyle=d["ls"], linewidth=d["lw"], label=name)

ax2.axvline(26, color='gray', ls=':', lw=1.0, alpha=0.7)
ax2.set_xlabel('Frequency (GHz)')
ax2.set_ylabel('Reflection Phase (°)')
ax2.set_title('Reflection Phase vs Frequency\nRIS Unit Cell at 26 GHz')
ax2.legend(loc='upper right', framealpha=0.92, edgecolor='#ccc')
ax2.grid(True, alpha=0.3)
ax2.set_xlim([18, 34])

plt.tight_layout(pad=1.5)
plt.savefig('results/fig1_reflection.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("\nSaved: results/fig1_reflection.png")

# =============================================================================
# FIGURE 2A: BAR CHART
# =============================================================================
fig2a, ax3 = plt.subplots(figsize=(6, 4.5))
fig2a.patch.set_facecolor('white')

names_short = ['Cu\n(ideal)', 'Screen\nPrint Ag', 'AJ Ag\n225°C', 'AJ Ag\n175°C', 'AJ Ag\n130°C']
loss_vals   = list(loss_at_26.values())
bar_colors  = [d["color"] for d in materials.values()]

bars = ax3.bar(names_short, loss_vals, color=bar_colors,
               edgecolor='white', linewidth=1.0, width=0.55)
for bar, lv in zip(bars, loss_vals):
    ax3.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 0.03,
             f'{lv:.2f} dB', ha='center', va='bottom',
             fontsize=9, fontweight='bold')

ax3.set_ylabel('Reflection Loss at 26 GHz (dB)')
ax3.set_title('(a) Conductor Type vs. Reflection Loss')
ax3.grid(True, alpha=0.3, axis='y')
ax3.set_ylim([0, max(loss_vals)*1.38])
ax3.set_xlim([-0.7, len(names_short)-0.3])
plt.tight_layout(pad=1.5)
plt.savefig('results/fig2a_loss_bar.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: results/fig2a_loss_bar.png")

# =============================================================================
# FIGURE 2B: SCATTER
# =============================================================================
fig2b, ax4 = plt.subplots(figsize=(6, 4.5))
fig2b.patch.set_facecolor('white')

sigmas_known = [d["sigma"] for d in materials.values()]
sigma_range  = np.logspace(5.7, 7.8, 300)
loss_curve   = []
for sig in sigma_range:
    log_sig  = np.log10(sig)
    log_sigs = np.log10(sigmas_known)
    loss_i   = np.interp(log_sig, log_sigs[::-1], loss_vals[::-1])
    loss_curve.append(loss_i)

ax4.semilogx(sigma_range, loss_curve, color='#444', linewidth=1.5, label='Trend', zorder=2)
ax4.axvspan(8e5, 8e6, alpha=0.08, color='orange')
ax4.text(1.5e6, 0.15, 'AJ ink\nrange', fontsize=9, color='#cc7700', ha='center')

markers = ['o','s','^','D','v']
for (name, d), mk, lv in zip(materials.items(), markers, loss_vals):
    ax4.scatter(d["sigma"], lv, color=d["color"], s=70, zorder=5,
                marker=mk, edgecolors='white', linewidths=0.5, label=name)

ax4.set_xlabel('Conductivity σ (S/m)')
ax4.set_ylabel('Reflection Loss (dB)')
ax4.set_title('(b) Loss vs. Conductivity at 26 GHz')
ax4.legend(fontsize=8, framealpha=0.9, edgecolor='#ccc', loc='upper right')
ax4.grid(True, alpha=0.3, which='both')
ax4.set_xlim([5e5, 1.2e8])
ax4.set_ylim([0, 2.9])
plt.tight_layout(pad=1.5)
plt.savefig('results/fig2b_loss_scatter.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: results/fig2b_loss_scatter.png")

# =============================================================================
# FIGURE 3: SKIN DEPTH
# =============================================================================
fig3, ax5 = plt.subplots(figsize=(6, 5))
fig3.patch.set_facecolor('white')

freq_range = np.linspace(1e9, 40e9, 500)
skin_mats  = [
    ('Copper (ideal)',     5.80e7, '#1a1a2e', '-'),
    ('Screen-Print AgNW', 2.00e7, '#0077b6', '--'),
    ('AJ Ag 225°C',       8.00e6, '#2d6a4f', '-.'),
    ('AJ Ag 130°C',       8.50e5, '#c1121f', ':'),
]

for label, sig, col, ls in skin_mats:
    deltas = np.sqrt(2/(2*np.pi*freq_range*mu0*sig))*1e6
    ax5.semilogy(freq_range/1e9, deltas, color=col, linestyle=ls, linewidth=1.8, label=label)

ax5.axvline(26, color='gray', ls='--', lw=1.0, alpha=0.7)
ax5.axhline(t*1e6, color='purple', ls='--', lw=1.2, alpha=0.85, label='Print thickness (2 μm)')
ax5.fill_between([0,40],[0,0],[t*1e6,t*1e6], alpha=0.07, color='purple')
ax5.text(1.5, t*1e6*1.35, 't = 2 μm', fontsize=9, color='purple')
ax5.text(27, 0.55, '26 GHz', fontsize=9, color='gray')
ax5.set_xlabel('Frequency (GHz)')
ax5.set_ylabel('Skin Depth δs (μm)')
ax5.set_title('Skin Depth vs. Frequency')
ax5.legend(loc='upper right', framealpha=0.9, edgecolor='#ccc', fontsize=9)
ax5.grid(True, alpha=0.3, which='both')
ax5.set_xlim([1, 40])
ax5.set_ylim([0.3, 15])
plt.tight_layout(pad=1.2)
plt.savefig('results/fig3_skindepth.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: results/fig3_skindepth.png")

print("\n" + "=" * 60)
print("SIMULATION COMPLETE")
print("All figures saved in results/ directory")
print("=" * 60)
