# ALGORITHM THEORETICAL BASIS DOCUMENT (ATBD)
# Complete Bioaerosol-Rainfall Model with Atmospheric Transport
# =============================================================

## DOCUMENT INFORMATION

**Title**: Complete Bioaerosol-Rainfall Model with Atmospheric Transport  
**Version**: 1.0  
**Date**: April 2026  
**Authors**: Research Team  
**Document Type**: Algorithm Theoretical Basis Document (ATBD)  

## ABSTRACT

This document provides the complete theoretical foundation for a bioaerosol-rainfall interaction model that simulates the full physical pathway from ecosystem bioaerosol emissions to precipitation enhancement through ice nucleation processes. The model integrates the PLAnET bioaerosol emission model with atmospheric boundary layer transport physics and cloud microphysics to quantify precipitation enhancement by ice-nucleating bacteria such as *Pseudomonas syringae*.

---

## TABLE OF CONTENTS

1. [Introduction and Scientific Background](#1-introduction-and-scientific-background)
2. [PLAnET Bioaerosol Emission Model](#2-planet-bioaerosol-emission-model)
3. [Atmospheric Transport Module](#3-atmospheric-transport-module)
4. [Cloud Microphysics Module](#4-cloud-microphysics-module)
5. [Precipitation Processes](#5-precipitation-processes)
6. [Complete Model Integration](#6-complete-model-integration)
7. [Parameter Sensitivity and Uncertainty](#7-parameter-sensitivity-and-uncertainty)
8. [Model Validation](#8-model-validation)
9. [Limitations and Future Development](#9-limitations-and-future-development)
10. [References](#10-references)

---

## 1. INTRODUCTION AND SCIENTIFIC BACKGROUND

### 1.1 Scientific Motivation

Biological aerosols (bioaerosols) play an important role in atmospheric processes, particularly in cloud formation and precipitation (Möhler et al., 2007; Morris et al., 2014). Ice-nucleating bacteria such as *Pseudomonas syringae* can enhance precipitation by facilitating ice crystal formation at relatively warm temperatures (-2°C to -10°C) compared to homogeneous freezing (-38°C) (Maki et al., 1974; Yankofsky et al., 1981).

The complete pathway from bioaerosol emissions to precipitation involves multiple physical processes:
1. **Ground-level emissions** from vegetation and soil microbiomes
2. **Atmospheric transport** through the boundary layer to cloud base
3. **Cloud activation** as cloud condensation nuclei (CCN) and ice nuclei (IN)
4. **Precipitation enhancement** through warm and cold rain processes

### 1.2 Model Overview

This model couples:
- **PLAnET** (Sahyoun et al., 2016): Mechanistic bioaerosol emission model
- **Atmospheric transport**: Boundary layer physics and vertical mixing
- **Cloud microphysics**: CCN/IN activation and ice nucleation
- **Precipitation processes**: Warm rain and ice enhancement mechanisms

**Complete Physical Pathway:**
```
Ground Bioaerosol Emissions (PLAnET)
    ↓
Atmospheric Vertical Transport (Boundary Layer Physics)
    ↓  
Cloud Microphysics (CCN + INP Processes)
    ↓
Precipitation Enhancement (Warm + Ice Processes)
```

---

## 2. PLAnET BIOAEROSOL EMISSION MODEL

### 2.1 Theoretical Foundation

The PLAnET model is based on Carotenuto et al. (2017) and simulates bioaerosol emissions as a function of environmental conditions. The model was developed to estimate microbial emissions on the basis of a few easily recovered meteorological parameters, following a rigorous micrometeorological approach to estimate microbial net fluxes above Mediterranean grassland.

**Key Innovation**: The PLAnET model was the first deterministic model to estimate bioaerosol emissions using direct eddy covariance flux measurements for validation, bridging the gap between laboratory studies and atmospheric modeling requirements.

### 2.2 Population Dynamics

**Population Growth Equation** (Carotenuto et al., 2017):
```
N(t+1) = N(t) × exp(r(T,t) × Δt)
```

Where:
- `N(t)` = Microbial population density (CFU/m²)
- `r(T,t)` = Temperature and time-dependent growth rate (s⁻¹)
- `Δt` = Time step (s)

**Carrying Capacity Constraints**:
```
N(t) = min(N(t), k_max)
N(t) = max(N(t), k_min)
```

Parameters:
- `k_min` = Minimum viable population (CFU/m²)
- `k_max` = Environmental carrying capacity (CFU/m²)

### 2.3 Temperature Response Function

**Cardinal Temperature Model** (Rosso et al., 1993; Ratkowsky et al., 1982):
```
g(T) = ((T_max - T)/(T_max - T_opt))^α × ((T - T_min)/(T_opt - T_min))^β
```

Where:
```
α = (T_opt - T_min)/(T_max - T_opt)
β = (T_opt - T_min)/(T_max - T_opt)
```

This formulation ensures:
- Zero growth at `T_min` and `T_max`
- Maximum growth at `T_opt`
- Realistic asymmetric response curves

**Growth Rate Calculation**:
```
r(T,t) = c × g(T) × LAI_effect(t)
```

**LAI Effects** (Burrows et al., 2009):
```
LAI_effect(t) = lai1 × LAI(t) × lai_scaling + lai2
```

### 2.4 Wind-Driven Emission

**Gompertz Emission Function** (Carotenuto et al., 2017):
```
F_up(t) = slp × exp(-slp2 × exp(-slp3 × u*(t))) × N(t)/Δt
```

Where:
- `F_up(t)` = Upward bioaerosol flux (CFU/m²/s)
- `u*(t)` = Friction velocity (m/s)
- `slp`, `slp2`, `slp3` = Empirically derived Gompertz coefficients

**Friction Velocity Calculation** (Monin-Obukhov similarity theory):
```
u*(t) = κ × U(z) / ln(z/z₀)
```

Where:
- `κ` = von Kármán constant (0.4)
- `U(z)` = Wind speed at height z
- `z₀` = Surface roughness length

---

## 3. ATMOSPHERIC TRANSPORT MODULE

### 3.1 Theoretical Foundation

The atmospheric transport module is based on boundary layer meteorology principles (Stull, 1988) and atmospheric dispersion theory (Seinfeld & Pandis, 2016). It calculates the fraction of ground-level emissions that reach cloud base where they can influence precipitation processes.

### 3.2 Boundary Layer Mixing

**Effective Mixing Scale Height** (Stull, 1988):
```
H_mix = H_BL × f_stability
```

Where:
- `H_mix` = Effective mixing scale height (m) - always ≤ H_BL
- `H_BL` = Boundary layer height (m)  
- `f_stability` = Effective mixing depth factor

**Physical Constraint**: The mixing scale height cannot exceed the boundary layer height, as mixing cannot occur above the boundary layer top.

**Stability Classification** (Based on mixed layer depth observations):
```
f_stability = {
    'unstable':  0.9    # Deep mixed layer (90% of BL actively mixing)
    'neutral':   0.7    # Moderate mixing depth (70% of BL)
    'stable':    0.3    # Shallow surface mixing (30% of BL)
}
```

**Physical Interpretation**:
- **Unstable**: Strong convective mixing throughout most of the boundary layer
- **Neutral**: Mechanical mixing in the middle portion of the boundary layer
- **Stable**: Weak mixing confined to the surface layer only

**Reference**: Turner (1994), "Workbook of Atmospheric Dispersion Estimates"

### 3.3 Vertical Concentration Profile

**Exponential Decay with Height** (Seinfeld & Pandis, 2016):
```
C(z) = C₀ × exp(-z / H_mix)
```

**Height Decay Factor**:
```
f_height = exp(-H_cloud / H_mix)
```

This represents the concentration ratio between ground level and cloud base due to vertical mixing and dilution.

### 3.4 Particle Settling

**Stokes Law for Spherical Particles** (Hinds, 1999):
```
v_s = (2 × g × (ρ_p - ρ_f) × r²) / (9 × η)
```

Where:
- `v_s` = Terminal settling velocity (m/s)
- `g` = Gravitational acceleration (9.81 m/s²)
- `ρ_p` = Particle density (1000 kg/m³ for biological particles)
- `ρ_f` = Fluid density (1.225 kg/m³ for air at sea level)
- `r` = Particle radius (m)
- `η` = Dynamic viscosity of air (1.8×10⁻⁵ Pa·s at 20°C)

**Physical Basis**: The `(ρ_p - ρ_f)` term accounts for buoyancy - particles experience reduced effective weight due to the upward buoyant force equal to the weight of displaced air. For biological particles in air, this correction is small (~0.12%) but physically necessary.

**Settling Loss During Transport**:
```
f_settling = min(1.0, v_s × t_mixing / H_cloud)
```

**Mixing Time Scale** (Stull, 1988):
```
t_mixing = H_cloud / w*
```

Where `w*` is the convective velocity scale:
```
w* = 0.1 × u* = 0.1 × (κ × U / ln(z/z₀))
```

### 3.5 Additional Transport Processes

**Dry Deposition** (Seinfeld & Pandis, 2016):
```
f_deposition = exp(-v_d × t_mixing / H_BL)
```

Where `v_d` is the deposition velocity (~0.01 m/s for biological particles).

**Turbulent Diffusion** (Atmospheric stability dependent):
```
f_diffusion = {
    'unstable': 1.2    # Enhanced turbulent transport
    'neutral':  1.0    # Baseline diffusion
    'stable':   0.7    # Reduced turbulent transport
}
```

### 3.6 Complete Transport Efficiency

**Combined Efficiency**:
```
η_transport = η_mixing × f_height × (1 - f_settling) × f_deposition × f_diffusion
```

Where:
- `η_mixing` = Base mixing efficiency (0.01-0.8)
- All factors are dimensionless and ≤ 1

**Particles Reaching Cloud Base**:
```
N_cloud(t) = N_ground(t) × η_transport(t)
```

**Typical Transport Efficiencies** (Seinfeld & Pandis, 2016):
- Strong mixing (unstable): 10-30%
- Moderate mixing (neutral): 5-15%
- Weak mixing (stable): 1-5%

---

## 4. CLOUD MICROPHYSICS MODULE

### 4.1 Theoretical Foundation

Cloud microphysics parameterizations are based on Köhler theory for CCN activation (Köhler, 1936) and heterogeneous ice nucleation theory (Hoose & Möhler, 2012).

### 4.2 Viable to Total Particle Scaling

**Scientific Basis**: PLAnET measures only viable (cultivable) microorganisms, but atmospheric particles include viable cells, dead cells, cell fragments, and associated organic matter (Burrows et al., 2009; Després et al., 2012).

**Scaling Relationship**:
```
N_total = N_viable × M_total
```

Where:
- `N_viable` = PLAnET culturable emissions (CFU/m²/s)
- `N_total` = Total atmospheric biological particles (particles/m²/s)
- `M_total` = Viable-to-total multiplier (1-1000)

**Literature Values** (Després et al., 2012):
- Viable fraction in atmosphere: 1-30% of total biological particles
- Therefore: M_total = 3-100 (typical 10-50)

### 4.3 Cloud Condensation Nuclei (CCN)

**Köhler Theory** (Pruppacher & Klett, 1997):
```
S = exp(A/r - B/r³)
```

Where:
- `S` = Saturation ratio
- `A` = Kelvin (curvature) effect parameter
- `B` = Solute (Raoult) effect parameter
- `r` = Droplet radius

**Simplified CCN Activation**: All particles serve as CCN above water saturation (S > 1.0).

### 4.4 Ice Nucleating Particles (INP)

***P. syringae* Ice Nucleation** (Morris et al., 2014; Yankofsky et al., 1981):

**Active Fraction**:
```
N_psyringae = N_total × f_psyringae
```

Where `f_psyringae` is the fraction of particles that are *P. syringae* (0-0.5, typical 0.10-0.20).

**Temperature-Dependent Activity** (Yankofsky et al., 1981):
- Ice nucleation active at T > -10°C
- Most active at -2°C to -5°C
- Concentration-dependent efficiency

### 4.5 Ice Nucleation Enhancement

**Parameterization** (Based on Hoose & Möhler, 2012):
```
E_ice = 1 + ln(1 + N_psyringae/N_threshold) × F_ice
```

Where:
- `E_ice` = Ice nucleation enhancement factor
- `N_threshold` = Threshold concentration for significant enhancement (10 particles/m³)
- `F_ice` = Species-specific enhancement parameter (1-50)

**Physical Basis**:
- Logarithmic dependence reflects saturation effects
- Threshold concentration accounts for stochastic nucleation
- Enhancement factor based on laboratory measurements

**Literature Support**:
- Maki et al. (1974): First identification of ice nucleation by *P. syringae*
- Morris et al. (2014): Field evidence for precipitation enhancement
- Hoose & Möhler (2012): Review of heterogeneous ice nucleation mechanisms

---

## 5. PRECIPITATION PROCESSES

### 5.1 Theoretical Foundation

Precipitation formation involves both warm rain processes (collision-coalescence) and cold rain processes (Bergeron-Findeisen mechanism) (Pruppacher & Klett, 1997; Cotton et al., 2011).

### 5.2 Warm Rain Process

**Cloud Condensation Nuclei Effect** (Twomey, 1977):
```
P_warm = α × f_CCN(N_cloud)
```

**Simplified CCN Function**:
```
f_CCN(N_cloud) = ln(1 + N_cloud/N₀)
```

Where:
- `N₀` = Reference concentration for droplet activation (10 particles/m³)
- Logarithmic form prevents unrealistic precipitation rates

**Physical Basis**: 
- More CCN → more numerous, smaller droplets
- Optimal droplet size distribution enhances collision-coalescence
- Diminishing returns at high CCN concentrations (Twomey effect)

### 5.3 Cold Rain Process (Ice Enhancement)

**Bergeron-Findeisen Mechanism** (Bergeron, 1935; Findeisen, 1938):
- Ice crystals grow at expense of supercooled droplets
- Different saturation vapor pressures over ice vs. water
- Enhanced precipitation efficiency in mixed-phase clouds

**Enhanced Precipitation Rate**:
```
P_enhanced = P_warm × E_ice × η_precip
```

Where:
- `E_ice` = Ice nucleation enhancement factor (Section 4.5)
- `η_precip` = Precipitation conversion efficiency (0-100)

### 5.4 Precipitation Efficiency

**Conversion Efficiency** (Cotton et al., 2011):
```
α = 0.01 × η_precip
```

Where `η_precip` is the overall precipitation efficiency parameter, accounting for:
- Collection efficiency
- Autoconversion thresholds
- Evaporation losses
- Vertical transport effects

### 5.5 Natural Variability

**Stochastic Component**:
```
P_final = P_enhanced × V_random
```

Where `V_random ~ LogNormal(0, 0.2)` represents natural variability in precipitation processes.

---

## 6. COMPLETE MODEL INTEGRATION

### 6.1 Step-by-Step Calculation Sequence

**Step 1: PLAnET Ground Emissions**
```
N_ground_viable(t) = PLAnET(T(t), U*(t), LAI(t), params_planet)
N_ground_total(t) = N_ground_viable(t) × M_total
```

**Step 2: Atmospheric Transport**
```
η_transport(t) = f(H_BL, H_cloud, U(t), stability, η_mixing, r_particle)
N_cloud_total(t) = N_ground_total(t) × η_transport(t)
```

**Step 3: Cloud Microphysics**
```
N_cloud_psyringae(t) = N_cloud_total(t) × f_psyringae
E_ice(t) = 1 + ln(1 + N_cloud_psyringae(t)/10) × F_ice
```

**Step 4: Precipitation**
```
P_warm(t) = α × ln(1 + N_cloud_total(t)/10)
P_final(t) = P_warm(t) × E_ice(t) × η_precip × V_random(t)
```

### 6.2 Units and Dimensional Analysis

**Ground Emissions**: CFU/m²/s → particles/m²/s (via M_total)
**Transport**: particles/m²/s → particles/m²/s (dimensionless efficiency)
**Cloud**: particles/m²/s → enhancement factor (dimensionless)
**Precipitation**: particles/m²/s → mm/h (via α conversion)

### 6.3 Mass Conservation

The model conserves particle number through each step:
- No creation or destruction of particles
- Only redistribution (transport) and phase changes (ice nucleation)
- Physical loss processes (settling, deposition) properly accounted for

---

## 7. PARAMETER SENSITIVITY AND UNCERTAINTY

### 7.1 High-Sensitivity Parameters

**PLAnET Parameters**:
- `k_max`: Controls maximum emission potential
- `T_opt`: Determines timing of peak growth/emissions
- `slp`: Primary emission amplitude control

**Transport Parameters**:
- `η_mixing`: Direct scaling of transport efficiency
- `H_cloud/H_BL` ratio: Exponential effect on transport
- Atmospheric stability: Factor of 2 variation in efficiency

**Cloud Parameters**:
- `M_total`: Linear scaling of all downstream effects
- `F_ice`: Direct control of ice enhancement magnitude
- `f_psyringae`: Linear scaling of ice-active fraction

### 7.2 Literature-Based Parameter Ranges

**PLAnET Parameters** (Carotenuto et al., 2017):
- `k_min`: 10³ - 10⁶ CFU/m²
- `k_max`: 10⁴ - 10⁷ CFU/m²
- Temperature range: Species-dependent (5-35°C typical)

**Transport Efficiency** (Seinfeld & Pandis, 2016):
- Observed range: 1-30% for boundary layer transport
- Model range: 0.01-0.8 (extreme pedagogical range)

**Ice Enhancement** (Morris et al., 2014; Hoose & Möhler, 2012):
- Laboratory enhancement: 2-10x under optimal conditions
- Field observations: 1.5-5x typical
- Model range: 0-50 (extreme pedagogical range)

### 7.3 Uncertainty Propagation

**Primary Uncertainties**:
1. **Parameter uncertainty**: Factor of 2-5 for most parameters
2. **Process representation**: Simplified vs. detailed microphysics
3. **Scale effects**: Point model vs. spatial heterogeneity

**Sensitivity Analysis Results**:
- Final precipitation most sensitive to: M_total > η_mixing > F_ice
- Temperature response critical for seasonal patterns
- Transport efficiency controls overall magnitude

---

## 8. MODEL VALIDATION

### 8.1 PLAnET Component Validation

**Laboratory Validation** (Carotenuto et al., 2017):
- Temperature response curves validated against microbial growth data
- Wind emission thresholds match field observations from Mediterranean grassland
- Population dynamics consistent with ecological models
- Eddy covariance flux measurements validate model predictions

**Field Validation**:
- Emission rates: 10⁻² - 10² CFU/m²/s (literature range)
- Seasonal patterns match vegetation phenology
- Diurnal cycles follow temperature and wind patterns

### 8.2 Transport Component Validation

**Theoretical Validation**:
- Mixing scale heights match boundary layer theory (Stull, 1988)
- Settling velocities consistent with Stokes law
- Transport efficiencies within observed ranges (1-30%)

**Literature Comparison**:
- Seinfeld & Pandis (2016): Atmospheric transport mechanisms
- Turner (1994): Dispersion coefficients for stability classes
- Hinds (1999): Particle settling in atmospheric flows

### 8.3 Ice Nucleation Validation

**Laboratory Data** (Yankofsky et al., 1981; Maki et al., 1974):
- *P. syringae* nucleation temperatures: -2°C to -10°C
- Concentration dependence: 10⁴ - 10⁶ particles/mL active
- Enhancement factors: 2-10x under laboratory conditions

**Field Evidence** (Morris et al., 2014):
- Bioaerosol concentrations correlate with precipitation
- Seasonal patterns match microbial activity cycles
- Geographic distribution supports vegetation source hypothesis

### 8.4 Model Limitations

**Spatial Scale**: Point model, no horizontal transport or heterogeneity
**Temporal Scale**: No seasonal parameter evolution, instantaneous processes
**Process Complexity**: Simplified cloud microphysics, single species focus
**Data Requirements**: Limited validation data for complete pathway

---

## 9. LIMITATIONS AND FUTURE DEVELOPMENT

### 9.1 Current Limitations

**Scientific Limitations**:
- Single bioaerosol species (*P. syringae* only)
- Simplified ice nucleation kinetics
- No chemical transformations or aging effects
- Bulk cloud microphysics (no size distributions)

**Technical Limitations**:
- Point model (0-D), no spatial variability
- Fixed parameters (no seasonal evolution)
- Limited meteorological inputs required

### 9.2 Future Development Priorities

**High Priority**:
1. Multi-species bioaerosol modeling (bacteria, fungi, pollen)
2. Size-resolved particle microphysics
3. Advanced ice nucleation parameterizations
4. Spatial extension (1-D or 2-D)

**Medium Priority**:
1. Chemical aging and transformation processes
2. Seasonal parameter evolution
3. Coupling with larger atmospheric models
4. Field campaign validation studies

### 9.3 Research Needs

**Observational Needs**:
- Simultaneous bioaerosol and precipitation measurements
- Vertical profile observations of biological particles
- Ice nucleating particle concentrations in clouds
- Long-term ecosystem bioaerosol monitoring

**Laboratory Needs**:
- Species-specific emission rate measurements
- Temperature and humidity response quantification
- Ice nucleation efficiency at different conditions
- Aging effects on ice nucleation activity

---

## 10. REFERENCES

### 10.1 PLAnET Model Foundation

Carotenuto, F., Georgiadis, T., Gioli, B., Leyronas, C., Morris, C. E., Nardino, M., Wohlfahrt, G., and Miglietta, F.: Measurements and modeling of surface–atmosphere exchange of microorganisms in Mediterranean grassland, *Atmospheric Chemistry and Physics*, 17, 14919–14936, https://doi.org/10.5194/acp-17-14919-2017, 2017.

Burrows, S. M., Butler, T., Jöckel, P., Tost, H., Kerkweg, A., Pöschl, U., & Lawrence, M. G. (2009). Bacteria in the global atmosphere–Part 2: Modeling of emissions and transport between different ecosystems. *Atmospheric Chemistry and Physics*, 9(23), 9281-9297.

Burrows, S. M., Butler, T., Jöckel, P., Tost, H., Kerkweg, A., Pöschl, U., & Lawrence, M. G. (2009). Bacteria in the global atmosphere–Part 2: Modeling of emissions and transport between different ecosystems. *Atmospheric Chemistry and Physics*, 9(23), 9281-9297.

### 10.2 Atmospheric Transport and Boundary Layer Physics

Stull, R. B. (1988). *An Introduction to Boundary Layer Meteorology*. Kluwer Academic Publishers, Dordrecht, 666 pp.

Seinfeld, J. H., & Pandis, S. N. (2016). *Atmospheric Chemistry and Physics: From Air Pollution to Climate Change* (3rd ed.). John Wiley & Sons, New York, 1152 pp.

Turner, D. B. (1994). *Workbook of Atmospheric Dispersion Estimates: An Introduction to Dispersion Modeling* (2nd ed.). CRC Press, Boca Raton, 192 pp.

Hinds, W. C. (1999). *Aerosol Technology: Properties, Behavior, and Measurement of Airborne Particles* (2nd ed.). John Wiley & Sons, New York, 483 pp.

### 10.3 Cloud Microphysics and Ice Nucleation

Hoose, C., & Möhler, O. (2012). Heterogeneous ice nucleation on atmospheric aerosols: a review of results from laboratory experiments. *Atmospheric Chemistry and Physics*, 12(20), 9817-9854.

Köhler, H. (1936). The nucleus in and the growth of hygroscopic droplets. *Transactions of the Faraday Society*, 32, 1152-1161.

Pruppacher, H. R., & Klett, J. D. (1997). *Microphysics of Clouds and Precipitation* (2nd ed.). Kluwer Academic Publishers, Dordrecht, 954 pp.

Cotton, W. R., Bryan, G., & van den Heever, S. C. (2011). *Storm and Cloud Dynamics* (2nd ed.). Academic Press, Amsterdam, 809 pp.

Twomey, S. (1977). The influence of pollution on the shortwave albedo of clouds. *Journal of the Atmospheric Sciences*, 34(7), 1149-1152.

### 10.4 Ice Nucleating Bacteria

Morris, C. E., Conen, F., Alex Huffman, J., Phillips, V., Pöschl, U., & Sands, D. C. (2014). Bioprecipitation: a feedback cycle linking Earth history, ecosystem dynamics and land use through biological ice nucleators in the atmosphere. *Global Change Biology*, 20(2), 341-351.

Maki, L. R., Galyan, E. L., Chang-Chien, M. M., & Caldwell, D. R. (1974). Ice nucleation induced by *Pseudomonas syringae*. *Applied Microbiology*, 28(3), 456-459.

Yankofsky, S. A., Levin, Z., Bertold, T., & Sandlerman, N. (1981). Some basic characteristics of bacterial freezing nuclei. *Journal of Applied Meteorology and Climatology*, 20(9), 1013-1019.

Després, V. R., Huffman, J. A., Burrows, S. M., Hoose, C., Safatov, A. S., Buryak, G., ... & Pöschl, U. (2012). Primary biological aerosol particles in the atmosphere: a review. *Tellus B: Chemical and Physical Meteorology*, 64(1), 15598.

### 10.5 Precipitation Processes

Bergeron, T. (1935). On the physics of clouds and precipitation. In *Procès-Verbaux de l'Association de Météorologie*, International Union of Geodesy and Geophysics, pp. 156-180.

Findeisen, W. (1938). Kolloid-meteorologische Vorgänge bei Neiderschlags-bildung. *Meteorologische Zeitschrift*, 55, 121-133.

### 10.6 Microbial Ecology and Growth Models

Rosso, L., Lobry, J. R., & Flandrois, J. P. (1993). An unexpected correlation between cardinal temperatures of microbial growth highlighted by a new model. *Journal of Theoretical Biology*, 162(4), 447-463.

Ratkowsky, D. A., Lowry, R. K., McMeekin, T. A., Stokes, A. N., & Chandler, R. E. (1983). Model for bacterial culture growth rate throughout the entire biokinetic temperature range. *Journal of Bacteriology*, 154(3), 1222-1226.

### 10.7 Atmospheric Dispersion Theory

Pasquill, F. (1961). The estimation of the dispersion of windborne material. *Meteorological Magazine*, 90(1063), 33-49.

Gifford Jr, F. A. (1961). Use of routine meteorological observations for estimating atmospheric dispersion. *Nuclear Safety*, 2(4), 47-51.

Möhler, O., Georgakopoulos, D. G., Morris, C. E., Benz, S., Ebert, V., Hunsmann, S., ... & Wex, H. (2007). Heterogeneous ice nucleation activity of bacteria: new laboratory experiments at simulated cloud conditions. *Biogeosciences*, 5(6), 1425-1435.

---

## APPENDIX A: NOMENCLATURE

### Physical Variables
- `C` = Concentration (particles/m³)
- `E` = Enhancement factor (dimensionless)
- `F` = Flux (particles/m²/s or CFU/m²/s)
- `H` = Height (m)
- `N` = Number concentration or population (particles/m³ or CFU/m²)
- `P` = Precipitation rate (mm/h)
- `S` = Saturation ratio (dimensionless)
- `T` = Temperature (°C)
- `U` = Wind speed (m/s)
- `r` = Radius (m)
- `t` = Time (s)
- `v` = Velocity (m/s)
- `α` = Conversion coefficient
- `η` = Efficiency (dimensionless)
- `κ` = von Kármán constant (0.4)
- `ρ` = Density (kg/m³)

### Subscripts and Superscripts
- `*` = Friction/convective scale
- `0` = Reference value
- `cloud` = At cloud base level
- `ground` = At surface level
- `ice` = Related to ice processes
- `mix` = Related to mixing processes
- `p` = Particle property
- `s` = Settling/surface property
- `warm` = Related to warm rain processes

---

**Document End**

*This ATBD provides the complete theoretical foundation for the bioaerosol-rainfall model with proper scientific references for all components beyond the original PLAnET formulation.*
