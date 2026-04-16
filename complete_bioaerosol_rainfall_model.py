#!/usr/bin/env python3
"""
COMPLETE Bioaerosol-Rainfall Model with Atmospheric Transport
============================================================

This is the final, physically complete model that includes:

1. PLAnET bioaerosol emission model (ground level)
2. Atmospheric transport & vertical mixing (ground → cloud base)
3. Cloud microphysics & ice nucleation (cloud level)
4. Precipitation processes (surface rainfall)

SCIENTIFIC PATHWAY:
Ground Emissions → Vertical Transport → Cloud Base Particles → Precipitation

COMPREHENSIVE PARAMETER CONTROL:
- Population dynamics (k_min, k_max)
- Temperature response (T_min, T_opt, T_max)
- Emission physics (Gompertz coefficients)
- Atmospheric transport (mixing, settling, cloud height)
- Cloud microphysics (CCN, INP, ice enhancement)
- Precipitation efficiency

Version: 1.0 (Complete Physical Model)
Date: April 2026
"""

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import os
import sys
from typing import Dict, Any, Tuple, Optional
from scipy import stats

# Configure matplotlib
try:
    matplotlib.use('widget')
except:
    matplotlib.use('inline')
plt.ioff()

# Import PLAnET
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([current_dir, '.'])

try:
    from planet import PLAnET, ModelParams, ModelConstants, PLAnETResult
    from surface_parameters_fixed import SurfaceTypeLibrary, SurfaceParameters
    print("Successfully imported PLAnET models")
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure planet.py and surface_parameters_fixed.py are available")


class AtmosphericTransportModel:
    """
    Atmospheric transport model for vertical particle mixing
    """
    
    @staticmethod
    def calculate_mixing_scale_height(boundary_layer_height: float, 
                                    atmospheric_stability: str = 'neutral') -> float:
        """
        Calculate effective mixing scale height within the boundary layer
        
        Parameters:
        -----------
        boundary_layer_height : float
            Height of atmospheric boundary layer (m)
        atmospheric_stability : str
            'unstable', 'neutral', or 'stable'
            
        Returns:
        --------
        float
            Effective mixing scale height (m) - always ≤ boundary_layer_height
            
        Physical Basis:
        ---------------
        Atmospheric stability affects what fraction of the boundary layer
        actively participates in vertical mixing, but mixing cannot occur
        above the boundary layer top.
        
        References:
        -----------
        Stull, R.B. (1988): Boundary Layer Meteorology
        Turner, D.B. (1994): Workbook of Atmospheric Dispersion Estimates
        """
        # Fraction of boundary layer that actively mixes
        # Based on mixed layer depth observations (Stull, 1988)
        stability_factors = {
            'unstable':  0.9,    # Deep, well-mixed layer
            'neutral':   0.7,    # Moderate mixing depth  
            'stable':    0.3     # Shallow, surface-based mixing
        }
        
        factor = stability_factors.get(atmospheric_stability, 0.7)
        
        # Effective mixing scale height (always ≤ H_BL)
        mixing_scale_height = boundary_layer_height * factor
        
        return mixing_scale_height
    
    @staticmethod
    def calculate_settling_loss(particle_size_um: float, cloud_height: float,
                              vertical_mixing_velocity: float) -> float:
        """
        Calculate particle loss due to gravitational settling
        
        Parameters:
        -----------
        particle_size_um : float
            Particle diameter (micrometers)
        cloud_height : float
            Height to cloud base (m)
        vertical_mixing_velocity : float
            Characteristic vertical mixing velocity (m/s)
            
        Returns:
        --------
        float
            Fraction of particles lost to settling (0-1)
        """
        # Stokes settling velocity for spherical particles
        particle_density = 1000.0  # kg/m³ (biological particles)
        air_density = 1.225  # kg/m³ at sea level
        air_viscosity = 1.8e-5  # Pa⋅s
        gravity = 9.81  # m/s²
        
        # Convert particle size to meters
        particle_radius = (particle_size_um * 1e-6) / 2.0
        
        # Stokes settling velocity (corrected for buoyancy)
        settling_velocity = (2 * gravity * (particle_density - air_density) * particle_radius**2) / \
                           (9 * air_viscosity)
        
        # Time to reach cloud height via mixing
        # Prevent division by zero for very low wind speeds
        if vertical_mixing_velocity <= 0.0:
            # No vertical mixing → all particles settle out
            return 1.0
        
        mixing_time = cloud_height / vertical_mixing_velocity
        
        # Distance settled during mixing time
        settling_distance = settling_velocity * mixing_time
        
        # Fraction lost to settling
        settling_loss_fraction = min(1.0, settling_distance / cloud_height)
        
        return settling_loss_fraction
    
    @staticmethod
    def calculate_transport_efficiency(ground_particles: np.ndarray,
                                     boundary_layer_height: float,
                                     cloud_base_height: float,
                                     wind_speed: float,
                                     atmospheric_stability: str,
                                     particle_size_um: float,
                                     mixing_efficiency: float) -> np.ndarray:
        """
        Calculate complete atmospheric transport efficiency
        
        This is the key function that determines what fraction of ground-level
        bioaerosol emissions actually reach cloud base where they can influence
        precipitation processes.
        
        Parameters:
        -----------
        ground_particles : np.ndarray
            Ground-level particle concentrations (particles/m²/s)
        boundary_layer_height : float
            Atmospheric boundary layer height (m)
        cloud_base_height : float
            Height to cloud base (m)  
        wind_speed : float
            Surface wind speed (m/s)
        atmospheric_stability : str
            Atmospheric stability class
        particle_size_um : float
            Particle size (micrometers)
        mixing_efficiency : float
            Base mixing efficiency (0-1)
            
        Returns:
        --------
        np.ndarray
            Particles reaching cloud base (particles/m²/s)
        """
        
        # 1. Calculate mixing scale height
        mixing_scale_height = AtmosphericTransportModel.calculate_mixing_scale_height(
            boundary_layer_height, atmospheric_stability
        )
        
        # 2. Vertical mixing efficiency (exponential decay with height)
        height_decay_factor = np.exp(-cloud_base_height / mixing_scale_height)
        
        # 3. Wind-driven vertical mixing velocity
        surface_roughness = 0.1  # m (typical for vegetation)
        
        # Ensure minimum wind speed to prevent division by zero
        safe_wind_speed = max(0.1, wind_speed)  # Minimum 0.1 m/s
        
        friction_velocity = 0.4 * safe_wind_speed / np.log(10.0 / surface_roughness)
        vertical_mixing_velocity = friction_velocity * 0.1  # Typical scaling
        
        # Ensure minimum mixing velocity
        vertical_mixing_velocity = max(0.01, vertical_mixing_velocity)  # Minimum 0.01 m/s
        
        # 4. Particle settling losses
        settling_loss_fraction = AtmosphericTransportModel.calculate_settling_loss(
            particle_size_um, cloud_base_height, vertical_mixing_velocity
        )
        
        # 5. Additional transport processes
        
        # Dry deposition removes particles during transport
        dry_deposition_factor = 0.9  # 90% survive (10% deposit)
        
        # Turbulent diffusion efficiency (depends on atmospheric conditions)
        stability_factors = {'unstable': 1.2, 'neutral': 1.0, 'stable': 0.7}
        diffusion_factor = stability_factors.get(atmospheric_stability, 1.0)
        
        # 6. Combined transport efficiency
        total_efficiency = (mixing_efficiency * 
                           height_decay_factor * 
                           (1.0 - settling_loss_fraction) *
                           dry_deposition_factor * 
                           diffusion_factor)
        
        # Ensure efficiency is between 0 and 1
        total_efficiency = np.clip(total_efficiency, 0.0, 1.0)
        
        # Apply to ground particles
        cloud_base_particles = ground_particles * total_efficiency
        
        return cloud_base_particles, total_efficiency


class CompleteBioaerosolRainfallModel:
    """
    Complete bioaerosol-rainfall model with atmospheric transport
    """
    
    def __init__(self):
        """Initialize complete model"""
        self.surface_library = SurfaceTypeLibrary()
        self.default_params = ModelParams()
        
        # Complete parameter state - ALL model components
        self.current_state = {
            # PLAnET PARAMETERS
            'k_min': self.default_params.k_min,
            'k_max': self.default_params.k_max,
            'T_min': self.default_params.T_min,
            'T_opt': self.default_params.T_opt,
            'T_max': self.default_params.T_max,
            'slp': self.default_params.slp,
            'slp2': self.default_params.slp2,
            'slp3': self.default_params.slp3,
            'c': self.default_params.c,
            'lai1': self.default_params.lai1,
            'lai2': self.default_params.lai2,
            'lai_scaling': 1.0,
            
            # ATMOSPHERIC TRANSPORT PARAMETERS
            'boundary_layer_height': 1500.0,      # m
            'cloud_base_height': 1500.0,          # m
            'atmospheric_stability': 'neutral',   # unstable/neutral/stable
            'mixing_efficiency': 0.1,             # base mixing efficiency (0-1)
            'particle_size_um': 3.3,              # micrometers
            
            # CLOUD MICROPHYSICS PARAMETERS
            'total_microbe_multiplier': 10.0,     # viable → total scaling
            'psyringae_fraction': 15.0,           # P. syringae percentage
            'ice_enhancement': 5.0,               # ice nucleation efficiency
            'rainfall_efficiency': 1.0,           # precipitation efficiency
            
            # DATA PARAMETERS
            'timesteps': 200
        }
        
        self.last_results = None
        self.csv_data = None
        self.csv_metadata = None
        
        print("COMPLETE Bioaerosol-Rainfall Model initialized!")
        print("Ground Emissions → Atmospheric Transport → Cloud Physics → Precipitation")
        print("Full physical pathway with comprehensive parameter control")
    
    def load_csv_data(self, csv_path: str) -> Tuple[np.ndarray, pd.DatetimeIndex]:
        """Load CSV meteorological data"""
        try:
            df = pd.read_csv(csv_path, header=None)
            print(f"Loading CSV: {csv_path}")
            print(f"   Shape: {df.shape}, Columns: {df.shape[1]} columns (no header)")
            
            if df.shape[1] < 4:
                raise ValueError(f"Need at least 4 columns for PLAnET, got {df.shape[1]}")
            
            data = df.iloc[:, :5].values
            timestamps = pd.date_range('2015-01-01', periods=len(data), freq='30min')
            
            # Column names for metadata (since no header)
            column_names = ['Temperature', 'Pressure', 'u_star', 'LAI', 'Wind_speed'][:df.shape[1]]
            
            self.csv_metadata = {
                'filename': csv_path.split('\\')[-1] if '\\' in csv_path else csv_path.split('/')[-1],
                'n_timesteps': len(data),
                'columns': column_names,
                'temperature_range': (df.iloc[:, 0].min(), df.iloc[:, 0].max()),
                'ustar_range': (df.iloc[:, 2].min(), df.iloc[:, 2].max()),
                'lai_range': (df.iloc[:, 3].min(), df.iloc[:, 3].max()) if df.shape[1] >= 4 else None
            }
            
            print(f"CSV loaded successfully!")
            self.csv_data = data
            return data, timestamps
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None, None
    
    def create_synthetic_data(self, n_timesteps: int) -> Tuple[np.ndarray, pd.DatetimeIndex]:
        """Create synthetic meteorological data"""
        timestamps = pd.date_range('2015-01-01', periods=n_timesteps, freq='30min')
        hours = np.arange(n_timesteps) * 0.5
        day_of_year = timestamps.dayofyear
        
        # Temperature with realistic cycles
        seasonal_temp = 8.0 * np.sin(2 * np.pi * day_of_year / 365.0 - np.pi/2)
        diurnal_temp = 6.0 * np.sin(2 * np.pi * (hours % 24) / 24.0 - np.pi/2)
        temperature = 18.0 + seasonal_temp + diurnal_temp + np.random.normal(0, 2, n_timesteps)
        
        # Wind with atmospheric variability
        wind_speed = 4.0 + np.random.exponential(1.5, n_timesteps)
        wind_speed = np.maximum(0.5, wind_speed)
        ustar = wind_speed * 0.4 / np.log(10.0 / 0.15)
        ustar = np.maximum(0.05, ustar)
        
        # LAI with seasonal vegetation
        seasonal_lai = 2.0 * (0.5 + 0.8 * np.maximum(0, np.sin(2 * np.pi * day_of_year / 365.0 - np.pi/2)))
        lai = np.maximum(0.1, seasonal_lai + np.random.normal(0, 0.1, n_timesteps))
        
        # Atmospheric pressure
        pressure = 101325 + np.random.normal(0, 500, n_timesteps)
        
        meteo_data = np.column_stack([temperature, pressure, ustar, lai, wind_speed])
        return meteo_data, timestamps
    
    def apply_lai_scaling(self, meteo_data: np.ndarray, lai_scaling: float) -> np.ndarray:
        """Apply LAI scaling for vegetation density effects"""
        modified_data = meteo_data.copy()
        modified_data[:, 3] *= lai_scaling
        modified_data[:, 3] = np.maximum(0.1, modified_data[:, 3])
        return modified_data
    
    def create_planet_params(self, state: Dict) -> ModelParams:
        """Create PLAnET parameters from state"""
        return ModelParams(
            k_min=max(1e3, state['k_min']),
            k_max=max(1e4, state['k_max']),
            T_min=state['T_min'],
            T_opt=state['T_opt'], 
            T_max=state['T_max'],
            slp=max(0.1, state['slp']),
            slp2=max(0.1, state['slp2']),
            slp3=max(0.1, state['slp3']),
            c=max(0.001, state['c']),
            lai1=state['lai1'],
            lai2=state['lai2']
        )
    
    def run_complete_model(self, state: Dict, use_csv: bool = False):
        """
        Run complete bioaerosol-rainfall model with atmospheric transport
        
        COMPLETE PHYSICAL PATHWAY:
        1. PLAnET ground emissions
        2. Atmospheric transport (ground → cloud base)  
        3. Cloud microphysics (CCN + INP)
        4. Precipitation processes
        """
        
        # === 1. METEOROLOGICAL DATA ===
        if use_csv and self.csv_data is not None:
            meteo_data = self.csv_data.copy()
            timestamps = pd.date_range('2015-01-01', periods=len(meteo_data), freq='30min')
            print(f"Using CSV data ({len(meteo_data)} timesteps)")
        else:
            meteo_data, timestamps = self.create_synthetic_data(state['timesteps'])
            print(f"Using synthetic data ({len(meteo_data)} timesteps)")
        
        # Apply LAI scaling
        meteo_data = self.apply_lai_scaling(meteo_data, state['lai_scaling'])
        
        # === 2. PLAnET GROUND EMISSIONS ===
        planet_params = self.create_planet_params(state)
        planet_result = PLAnET(data=meteo_data, params=planet_params, ustar_flag=True, depo_flag=True)
        
        # Get viable emissions at ground level
        ground_viable_flux = np.maximum(planet_result.net_flux, 0.0)  # CFU/m²/s
        
        # Convert to total ground particles
        total_multiplier = max(1.0, state['total_microbe_multiplier'])
        ground_total_particles = ground_viable_flux * total_multiplier  # particles/m²/s at ground
        
        print(f"PLAnET Ground Emissions: Mean viable = {np.mean(ground_viable_flux):.2f} CFU/m²/s")
        print(f"Ground Total Particles: Mean = {np.mean(ground_total_particles):.1f} particles/m²/s")
        
        # === 3. ATMOSPHERIC TRANSPORT (GROUND → CLOUD BASE) ===
        
        # Calculate transport efficiency for each timestep
        cloud_base_particles = []
        transport_efficiencies = []
        
        for i in range(len(ground_total_particles)):
            wind_speed = meteo_data[i, 4]  # Wind speed from meteorological data
            
            particles_at_cloud, efficiency = AtmosphericTransportModel.calculate_transport_efficiency(
                ground_particles=ground_total_particles[i],
                boundary_layer_height=state['boundary_layer_height'],
                cloud_base_height=state['cloud_base_height'],
                wind_speed=wind_speed,
                atmospheric_stability=state['atmospheric_stability'],
                particle_size_um=state['particle_size_um'],
                mixing_efficiency=state['mixing_efficiency']
            )
            
            cloud_base_particles.append(particles_at_cloud)
            transport_efficiencies.append(efficiency)
        
        cloud_base_particles = np.array(cloud_base_particles)
        transport_efficiencies = np.array(transport_efficiencies)
        
        print(f"Atmospheric Transport: Mean efficiency = {np.mean(transport_efficiencies):.1%}")
        print(f"Cloud Base Particles: Mean = {np.mean(cloud_base_particles):.1f} particles/m²/s")
        
        # === 4. CLOUD MICROPHYSICS ===
        
        # P. syringae ice nucleating particles at cloud base
        psyringae_fraction = state['psyringae_fraction'] / 100.0
        cloud_psyringae_particles = cloud_base_particles * psyringae_fraction
        
        # Ice nucleation enhancement
        ice_base_enhancement = state['ice_enhancement']
        ice_enhancement = 1.0 + np.log1p(cloud_psyringae_particles / 10.0) * ice_base_enhancement
        
        print(f"Cloud Microphysics: Mean P. syringae = {np.mean(cloud_psyringae_particles):.1f} particles/m²/s")
        print(f"Ice Enhancement: Mean factor = {np.mean(ice_enhancement):.2f}")
        
        # === 5. PRECIPITATION PROCESSES ===
        
        rainfall_efficiency = state['rainfall_efficiency']
        base_conversion = 0.01 * rainfall_efficiency
        
        # Calculate final precipitation
        rainfall_rates = []
        for i, particles in enumerate(cloud_base_particles):
            if particles <= 0:
                rainfall_rates.append(0.0)
            else:
                # Base precipitation from cloud condensation nuclei (warm rain)
                base_rain = base_conversion * np.log1p(particles / 10.0)
                
                # Ice enhancement (cold/mixed-phase rain)
                ice_factor = ice_enhancement[i] if hasattr(ice_enhancement, '__len__') else ice_enhancement
                enhanced_rain = base_rain * ice_factor
                
                # Natural variability
                variability = np.random.lognormal(0, 0.2)
                final_rain = enhanced_rain * variability
                
                rainfall_rates.append(max(0.0, final_rain))
        
        rainfall_rates = np.array(rainfall_rates)
        rain_events = np.sum(rainfall_rates > 0.001)
        
        print(f"Precipitation: Mean rainfall = {np.mean(rainfall_rates):.4f} mm/h")
        print(f"Rain events: {100 * rain_events / len(rainfall_rates):.1f}% of timesteps")
        
        # === 6. COMPILE RESULTS ===
        
        return {
            'meteo_data': meteo_data,
            'timestamps': timestamps,
            'planet_result': planet_result,
            
            # Ground level results
            'ground_viable_flux': ground_viable_flux,
            'ground_total_particles': ground_total_particles,
            
            # Atmospheric transport results  
            'transport_efficiencies': transport_efficiencies,
            'cloud_base_particles': cloud_base_particles,
            
            # Cloud microphysics results
            'cloud_psyringae_particles': cloud_psyringae_particles,
            'ice_enhancement': ice_enhancement,
            
            # Precipitation results
            'rainfall_rates': rainfall_rates,
            'mean_rainfall': np.mean(rainfall_rates),
            'max_rainfall': np.max(rainfall_rates),
            'rain_event_percent': 100 * rain_events / len(rainfall_rates),
            
            'params_used': state.copy(),
            'data_source': 'CSV' if (use_csv and self.csv_data is not None) else 'Synthetic'
        }
    
    def plot_complete_results(self, results: Dict, previous_results: Optional[Dict] = None):
        """Plot complete model results showing all physical processes"""
        
        if previous_results:
            fig, axes = plt.subplots(5, 3, figsize=(20, 20))
            fig.suptitle('COMPLETE BIOAEROSOL-RAINFALL MODEL - Before vs After Comparison', 
                        fontsize=16, fontweight='bold')
        else:
            fig, axes = plt.subplots(5, 3, figsize=(20, 18))
            fig.suptitle('COMPLETE BIOAEROSOL-RAINFALL MODEL - Full Physical Pathway', 
                        fontsize=16, fontweight='bold')
        
        timestamps = results['timestamps']
        hours = np.arange(len(timestamps)) * 0.5
        state = results['params_used']
        meteo_data = results['meteo_data']
        
        # === ROW 1: METEOROLOGICAL FORCING ===
        
        # Plot 1: Temperature forcing with growth limits
        ax1 = axes[0, 0]
        ax1.plot(hours, meteo_data[:, 0], 'red', linewidth=2, label='Temperature')
        ax1.axhline(state['T_min'], color='blue', linestyle='--', alpha=0.7, label=f'T_min: {state["T_min"]:.1f}°C')
        ax1.axhline(state['T_opt'], color='green', linestyle='--', alpha=0.7, label=f'T_opt: {state["T_opt"]:.1f}°C')
        ax1.axhline(state['T_max'], color='orange', linestyle='--', alpha=0.7, label=f'T_max: {state["T_max"]:.1f}°C')
        ax1.set_title('Temperature Forcing & Growth Limits')
        ax1.set_ylabel('Temperature (°C)')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Wind forcing
        ax2 = axes[0, 1]
        ax2.plot(hours, meteo_data[:, 4], 'purple', linewidth=2, label='Wind Speed')
        ax2.set_title('Wind Speed (Transport Driver)')
        ax2.set_ylabel('Wind Speed (m/s)')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: LAI with scaling
        ax3 = axes[0, 2]
        ax3.plot(hours, meteo_data[:, 3], 'darkgreen', linewidth=2, label=f'LAI (scaled {state["lai_scaling"]:.1f}x)')
        ax3.set_title('Leaf Area Index')
        ax3.set_ylabel('LAI')
        ax3.grid(True, alpha=0.3)
        
        # === ROW 2: PLAnET GROUND EMISSIONS ===
        
        # Plot 4: Microbial population
        ax4 = axes[1, 0]
        population = results['planet_result'].population
        ax4.plot(hours, population, 'blue', linewidth=2, label='Population')
        ax4.axhline(state['k_min'], color='red', linestyle='--', alpha=0.7, label=f'k_min: {state["k_min"]:.0e}')
        ax4.axhline(state['k_max'], color='orange', linestyle='--', alpha=0.7, label=f'k_max: {state["k_max"]:.0e}')
        if previous_results:
            ax4.plot(hours, previous_results['planet_result'].population, 'lightblue', alpha=0.7, label='Previous')
        ax4.set_title('Microbial Population Dynamics')
        ax4.set_ylabel('Population (CFU/m²)')
        ax4.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # Plot 5: Ground viable emissions
        ax5 = axes[1, 1]
        ground_viable = results['ground_viable_flux']
        ax5.plot(hours, ground_viable, 'green', linewidth=2, label='Viable Emissions')
        if previous_results:
            ax5.plot(hours, previous_results['ground_viable_flux'], 'lightgreen', alpha=0.7, label='Previous')
        ax5.set_title(f'PLAnET Ground Emissions\n(slp={state["slp"]:.1f})')
        ax5.set_ylabel('Viable Flux (CFU/m²/s)')
        if previous_results:
            ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # Plot 6: Ground total particles  
        ax6 = axes[1, 2]
        ground_total = results['ground_total_particles']
        ax6.plot(hours, ground_viable, 'green', alpha=0.7, label='Viable')
        ax6.plot(hours, ground_total, 'purple', linewidth=2, label=f'Total ({state["total_microbe_multiplier"]:.0f}x)')
        ax6.set_title('Ground Particle Concentrations')
        ax6.set_ylabel('Particles/m²/s at Ground')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        # === ROW 3: ATMOSPHERIC TRANSPORT ===
        
        # Plot 7: Transport efficiency
        ax7 = axes[2, 0]
        transport_eff = results['transport_efficiencies']
        ax7.plot(hours, transport_eff * 100, 'brown', linewidth=2)
        ax7.set_title(f'Atmospheric Transport Efficiency\n(BL={state["boundary_layer_height"]:.0f}m, CB={state["cloud_base_height"]:.0f}m)')
        ax7.set_ylabel('Transport Efficiency (%)')
        ax7.grid(True, alpha=0.3)
        
        # Plot 8: Ground vs cloud particles
        ax8 = axes[2, 1]
        cloud_base = results['cloud_base_particles']
        ax8.plot(hours, ground_total, 'purple', alpha=0.7, label='At Ground')
        ax8.plot(hours, cloud_base, 'orange', linewidth=2, label='At Cloud Base')
        if previous_results:
            ax8.plot(hours, previous_results['cloud_base_particles'], 'wheat', alpha=0.7, label='Previous CB')
        ax8.set_title('Vertical Transport: Ground → Cloud Base')
        ax8.set_ylabel('Particles/m²/s')
        ax8.legend()
        ax8.grid(True, alpha=0.3)
        
        # Plot 9: Atmospheric profile schematic
        ax9 = axes[2, 2]
        heights = [0, state['boundary_layer_height'], state['cloud_base_height'], 4000]
        concentrations = [100, 50, np.mean(transport_eff) * 100, 5]  # Schematic profile
        ax9.plot(concentrations, heights, 'o-', linewidth=3, markersize=8)
        ax9.axhline(state['boundary_layer_height'], color='blue', linestyle='--', alpha=0.7, label='Boundary Layer')
        ax9.axhline(state['cloud_base_height'], color='gray', linestyle='--', alpha=0.7, label='Cloud Base')
        ax9.set_title(f'Atmospheric Profile\n({state["atmospheric_stability"]} stability)')
        ax9.set_xlabel('Relative Concentration')
        ax9.set_ylabel('Height (m)')
        ax9.legend()
        ax9.grid(True, alpha=0.3)
        
        # === ROW 4: CLOUD MICROPHYSICS ===
        
        # Plot 10: P. syringae at cloud base
        ax10 = axes[3, 0]
        cloud_psyr = results['cloud_psyringae_particles']
        ax10.plot(hours, cloud_psyr, 'red', linewidth=2)
        if previous_results:
            ax10.plot(hours, previous_results['cloud_psyringae_particles'], 'lightcoral', alpha=0.7, label='Previous')
        ax10.set_title(f'P. syringae at Cloud Base\n({state["psyringae_fraction"]:.0f}% of particles)')
        ax10.set_ylabel('P. syringae/m²/s')
        if previous_results:
            ax10.legend()
        ax10.grid(True, alpha=0.3)
        
        # Plot 11: Ice enhancement
        ax11 = axes[3, 1]
        ice_enhancement = results['ice_enhancement']
        mean_ice = np.mean(ice_enhancement)
        ax11.plot(hours, ice_enhancement, 'navy', linewidth=2, label=f'Mean: {mean_ice:.2f}x')
        if previous_results:
            prev_ice = previous_results['ice_enhancement']
            ax11.plot(hours, prev_ice, 'lightblue', alpha=0.7, label='Previous')
        ax11.set_title(f'Ice Nucleation Enhancement\n(Factor: {state["ice_enhancement"]:.0f})')
        ax11.set_ylabel('Enhancement Factor')
        ax11.legend()
        ax11.grid(True, alpha=0.3)
        
        # Plot 12: Cloud processes schematic
        ax12 = axes[3, 2]
        # Simple pie chart of processes
        processes = ['Warm Rain\n(All particles)', 'Ice Enhancement\n(P. syringae)']
        sizes = [1, mean_ice - 1] if mean_ice > 1 else [1, 0]
        colors = ['lightblue', 'darkblue']
        ax12.pie(sizes, labels=processes, colors=colors, autopct='%1.1f%%', startangle=90)
        ax12.set_title('Cloud Microphysical Processes')
        
        # === ROW 5: PRECIPITATION ===
        
        # Plot 13: Final rainfall
        ax13 = axes[4, 0]
        rainfall = results['rainfall_rates']
        ax13.plot(hours, rainfall, 'darkblue', linewidth=2, label='Rainfall')
        if previous_results:
            ax13.plot(hours, previous_results['rainfall_rates'], 'lightsteelblue', alpha=0.7, label='Previous')
        ax13.set_title(f'Final Precipitation\n(Efficiency: {state["rainfall_efficiency"]:.0f}x)')
        ax13.set_ylabel('Rainfall Rate (mm/h)')
        ax13.set_xlabel('Time (hours)')
        if previous_results:
            ax13.legend()
        ax13.grid(True, alpha=0.3)
        
        # Plot 14: Process comparison
        ax14 = axes[4, 1]
        mean_ground = np.mean(ground_total)
        mean_cloud = np.mean(cloud_base)
        mean_rain = np.mean(rainfall) * 1000  # Scale for visibility
        
        process_names = ['Ground\nParticles', 'Cloud\nParticles', 'Rainfall\n(×1000)']
        values = [mean_ground, mean_cloud, mean_rain]
        colors = ['purple', 'orange', 'darkblue']
        
        bars = ax14.bar(process_names, values, color=colors, alpha=0.7)
        if previous_results:
            prev_values = [
                np.mean(previous_results['ground_total_particles']),
                np.mean(previous_results['cloud_base_particles']),
                np.mean(previous_results['rainfall_rates']) * 1000
            ]
            ax14.bar(process_names, prev_values, color=colors, alpha=0.3, label='Previous')
        
        ax14.set_title('Process Comparison')
        ax14.set_ylabel('Value')
        if previous_results:
            ax14.legend()
        ax14.grid(True, alpha=0.3)
        
        # Plot 15: Complete pathway summary
        ax15 = axes[4, 2]
        pathway_text = f"""
COMPLETE PHYSICAL PATHWAY

1. PLAnET Ground Emissions
   Mean: {np.mean(ground_viable):.1f} CFU/m²/s

2. Atmospheric Transport  
   Efficiency: {np.mean(transport_eff):.1%}

3. Cloud Base Particles
   Mean: {np.mean(cloud_base):.1f} particles/m²/s

4. Ice Enhancement
   Factor: {mean_ice:.2f}x

5. Final Precipitation
   Mean: {np.mean(rainfall):.3f} mm/h
   Events: {results['rain_event_percent']:.1f}%
        """
        
        ax15.text(0.1, 0.5, pathway_text, transform=ax15.transAxes, fontsize=10,
                 verticalalignment='center', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax15.set_xlim(0, 1)
        ax15.set_ylim(0, 1)
        ax15.axis('off')
        ax15.set_title('Complete Pathway Summary')
        
        plt.tight_layout()
        plt.show()
    
    def create_complete_widget(self, csv_path: Optional[str] = None):
        """Create complete bioaerosol-rainfall widget with atmospheric transport"""
        
        print("Creating COMPLETE Bioaerosol-Rainfall Widget...")
        print("Ground Emissions → Atmospheric Transport → Cloud Physics → Precipitation")
        
        # Load CSV if provided
        if csv_path:
            csv_data, csv_timestamps = self.load_csv_data(csv_path)
            if csv_data is not None:
                print(f"CSV data loaded and ready!")
        
        # === INTERFACE CONTROLS ===
        
        data_source_toggle = widgets.ToggleButtons(
            options=[('Synthetic', 'synthetic'), ('CSV Data', 'csv')] if self.csv_data is not None else [('Synthetic', 'synthetic')],
            value='csv' if self.csv_data is not None else 'synthetic',
            description='Data Source:'
        )
        
        mode_toggle = widgets.ToggleButtons(
            options=[('Real-time', 'realtime'), ('Staging', 'staging')],
            value='staging',
            description='Mode:',
            button_style='info'
        )
        
        # === PLAnET PARAMETER SLIDERS ===
        
        # Population
        k_min_slider = widgets.FloatLogSlider(value=self.current_state['k_min'], min=3, max=6, step=0.1, description='k_min:', readout_format='.0e')
        k_max_slider = widgets.FloatLogSlider(value=self.current_state['k_max'], min=4, max=7, step=0.1, description='k_max:', readout_format='.0e')
        
        # Temperature  
        t_min_slider = widgets.FloatSlider(value=self.current_state['T_min'], min=-10.0, max=25.0, step=0.5, description='T_min (°C):', readout_format='.1f')
        t_opt_slider = widgets.FloatSlider(value=self.current_state['T_opt'], min=5.0, max=40.0, step=0.5, description='T_opt (°C):', readout_format='.1f')
        t_max_slider = widgets.FloatSlider(value=self.current_state['T_max'], min=15.0, max=50.0, step=0.5, description='T_max (°C):', readout_format='.1f')
        
        # Emissions
        slp_slider = widgets.FloatSlider(value=self.current_state['slp'], min=0.1, max=200.0, step=1.0, description='slp:', readout_format='.1f')
        slp2_slider = widgets.FloatSlider(value=self.current_state['slp2'], min=1.0, max=1000.0, step=10.0, description='slp2:', readout_format='.1f')
        slp3_slider = widgets.FloatSlider(value=self.current_state['slp3'], min=1.0, max=100.0, step=1.0, description='slp3:', readout_format='.1f')
        
        # Growth
        c_slider = widgets.FloatSlider(value=self.current_state['c'], min=0.001, max=1.0, step=0.01, description='c:', readout_format='.3f')
        lai_scaling_slider = widgets.FloatSlider(value=self.current_state['lai_scaling'], min=0.1, max=10.0, step=0.1, description='LAI Scaling:', readout_format='.1f')
        
        # === ATMOSPHERIC TRANSPORT SLIDERS ===
        
        bl_height_slider = widgets.FloatSlider(value=self.current_state['boundary_layer_height'], min=200.0, max=4000.0, step=100.0, description='Boundary Layer (m):', readout_format='.0f')
        cloud_height_slider = widgets.FloatSlider(value=self.current_state['cloud_base_height'], min=500.0, max=4000.0, step=100.0, description='Cloud Base (m):', readout_format='.0f')
        
        stability_dropdown = widgets.Dropdown(options=['unstable', 'neutral', 'stable'], value=self.current_state['atmospheric_stability'], description='Stability:')
        mixing_eff_slider = widgets.FloatSlider(value=self.current_state['mixing_efficiency'], min=0.01, max=0.8, step=0.01, description='Mixing Efficiency:', readout_format='.2f')
        particle_size_slider = widgets.FloatSlider(value=self.current_state['particle_size_um'], min=0.5, max=20.0, step=0.5, description='Particle Size (μm):', readout_format='.1f')
        
        # === CLOUD MICROPHYSICS SLIDERS ===
        
        total_mult_slider = widgets.FloatSlider(value=self.current_state['total_microbe_multiplier'], min=1.0, max=1000.0, step=5.0, description='Total Multiplier:', readout_format='.0f')
        psyringae_slider = widgets.FloatSlider(value=self.current_state['psyringae_fraction'], min=0.0, max=50.0, step=1.0, description='P. syringae (%):', readout_format='.0f')
        ice_enh_slider = widgets.FloatSlider(value=self.current_state['ice_enhancement'], min=0.0, max=50.0, step=1.0, description='Ice Enhancement:', readout_format='.0f')
        
        # === PRECIPITATION SLIDERS ===
        
        rain_eff_slider = widgets.FloatSlider(value=self.current_state['rainfall_efficiency'], min=0.0, max=100.0, step=2.0, description='Rain Efficiency:', readout_format='.0f')
        timesteps_slider = widgets.IntSlider(value=self.current_state['timesteps'], min=50, max=400, step=25, description='Timesteps:')
        
        # === CONTROLS ===
        
        apply_button = widgets.Button(description='Apply All Parameters', button_style='success', icon='check')
        compare_button = widgets.Button(description='Compare with Previous', button_style='info', icon='balance-scale')
        reset_button = widgets.Button(description='Reset to Defaults', button_style='warning', icon='refresh')
        
        status_label = widgets.HTML(value="<b>Status:</b> Ready - Adjust parameters and click 'Apply All Parameters'")
        current_params_display = widgets.HTML()
        output = widgets.Output()
        
        # === WIDGET LOGIC ===
        
        def update_mode(*args):
            is_realtime = mode_toggle.value == 'realtime'
            apply_button.layout.display = 'none' if is_realtime else 'block'
            compare_button.layout.display = 'none' if is_realtime else 'block'
            
            if is_realtime:
                status_label.value = "<b>Status:</b> Real-time mode - changes apply immediately"
                for slider in all_sliders:
                    # Only observe if not already observing
                    try:
                        slider.unobserve(run_realtime_update, names='value')
                    except ValueError:
                        pass  # Not observing, that's fine
                    slider.observe(run_realtime_update, names='value')
            else:
                status_label.value = "<b>Status:</b> Staging mode - adjust parameters then click 'Apply All Parameters'"
                for slider in all_sliders:
                    # Only unobserve if currently observing
                    try:
                        slider.unobserve(run_realtime_update, names='value')
                    except ValueError:
                        pass  # Not observing, that's fine
        
        def get_current_slider_state():
            return {
                # PLAnET parameters
                'k_min': k_min_slider.value, 'k_max': k_max_slider.value,
                'T_min': t_min_slider.value, 'T_opt': t_opt_slider.value, 'T_max': t_max_slider.value,
                'slp': slp_slider.value, 'slp2': slp2_slider.value, 'slp3': slp3_slider.value,
                'c': c_slider.value, 'lai_scaling': lai_scaling_slider.value,
                'lai1': self.current_state['lai1'], 'lai2': self.current_state['lai2'],
                
                # Atmospheric transport parameters
                'boundary_layer_height': bl_height_slider.value,
                'cloud_base_height': cloud_height_slider.value,
                'atmospheric_stability': stability_dropdown.value,
                'mixing_efficiency': mixing_eff_slider.value,
                'particle_size_um': particle_size_slider.value,
                
                # Cloud microphysics parameters
                'total_microbe_multiplier': total_mult_slider.value,
                'psyringae_fraction': psyringae_slider.value,
                'ice_enhancement': ice_enh_slider.value,
                'rainfall_efficiency': rain_eff_slider.value,
                
                'timesteps': timesteps_slider.value
            }
        
        def update_params_display():
            state = self.current_state
            current_params_display.value = f"""
            <div style='background-color: #f0f8ff; padding: 10px; margin: 5px; border-left: 4px solid #0066cc;'>
            <b>Applied Parameters (Complete Model):</b><br>
            <strong>PLAnET:</strong> k_max: {state['k_max']:.0e} | T_opt: {state['T_opt']:.1f}°C | slp: {state['slp']:.1f}<br>
            <strong>Transport:</strong> BL: {state['boundary_layer_height']:.0f}m | CB: {state['cloud_base_height']:.0f}m | Mix: {state['mixing_efficiency']:.2f}<br>
            <strong>Cloud:</strong> Mult: {state['total_microbe_multiplier']:.0f}x | P.syr: {state['psyringae_fraction']:.0f}% | Ice: {state['ice_enhancement']:.0f}x
            </div>
            """
        
        def run_realtime_update(*args):
            if mode_toggle.value != 'realtime':
                return
            self.current_state = get_current_slider_state()
            run_model_and_plot(compare=False)
        
        def run_model_and_plot(compare=False):
            with output:
                clear_output(wait=True)
                print("Running COMPLETE bioaerosol-rainfall model...")
                
                try:
                    use_csv_data = (data_source_toggle.value == 'csv') and (self.csv_data is not None)
                    results = self.run_complete_model(self.current_state, use_csv=use_csv_data)
                    
                    previous = self.last_results if compare else None
                    self.plot_complete_results(results, previous)
                    
                    print(f"\nCOMPLETE MODEL RESULTS ({results['data_source']} Data):")
                    print(f"Ground emissions: {np.mean(results['ground_viable_flux']):.2f} CFU/m²/s")
                    print(f"Transport efficiency: {np.mean(results['transport_efficiencies']):.1%}")
                    print(f"Cloud base particles: {np.mean(results['cloud_base_particles']):.1f} particles/m²/s")
                    print(f"Final rainfall: {results['mean_rainfall']:.4f} mm/h")
                    print(f"Rain events: {results['rain_event_percent']:.1f}%")
                    
                    self.last_results = results
                    status_label.value = f"<b>Status:</b> Complete model completed successfully! ({results['data_source']} data)"
                    update_params_display()
                    
                except Exception as e:
                    print(f"ERROR: {e}")
                    import traceback
                    traceback.print_exc()
                    status_label.value = "<b>Status:</b> Error occurred"
        
        def apply_changes(*args):
            self.current_state = get_current_slider_state()
            
            # Validation
            if self.current_state['k_max'] <= self.current_state['k_min']:
                status_label.value = "<b>Status:</b> Error - k_max must be greater than k_min"
                return
            if self.current_state['cloud_base_height'] > self.current_state['boundary_layer_height'] * 3:
                status_label.value = "<b>Status:</b> Warning - Cloud base very high relative to boundary layer"
            
            status_label.value = "<b>Status:</b> Applying complete parameter changes..."
            run_model_and_plot(compare=False)
        
        def compare_with_previous(*args):
            if self.last_results is None:
                status_label.value = "<b>Status:</b> No previous results to compare with"
                return
            
            new_state = get_current_slider_state()
            self.current_state = new_state
            status_label.value = "<b>Status:</b> Comparing with previous results..."
            run_model_and_plot(compare=True)
        
        def reset_parameters(*args):
            defaults = {
                'k_min': self.default_params.k_min, 'k_max': self.default_params.k_max,
                'T_min': self.default_params.T_min, 'T_opt': self.default_params.T_opt, 'T_max': self.default_params.T_max,
                'slp': self.default_params.slp, 'slp2': self.default_params.slp2, 'slp3': self.default_params.slp3,
                'c': self.default_params.c, 'lai_scaling': 1.0,
                'boundary_layer_height': 1500.0, 'cloud_base_height': 1500.0, 'atmospheric_stability': 'neutral',
                'mixing_efficiency': 0.1, 'particle_size_um': 3.3,
                'total_microbe_multiplier': 10.0, 'psyringae_fraction': 15.0, 'ice_enhancement': 5.0,
                'rainfall_efficiency': 1.0, 'timesteps': 200
            }
            
            # Update all sliders
            k_min_slider.value = defaults['k_min']
            k_max_slider.value = defaults['k_max']
            t_min_slider.value = defaults['T_min']
            t_opt_slider.value = defaults['T_opt'] 
            t_max_slider.value = defaults['T_max']
            slp_slider.value = defaults['slp']
            slp2_slider.value = defaults['slp2']
            slp3_slider.value = defaults['slp3']
            c_slider.value = defaults['c']
            lai_scaling_slider.value = defaults['lai_scaling']
            bl_height_slider.value = defaults['boundary_layer_height']
            cloud_height_slider.value = defaults['cloud_base_height']
            stability_dropdown.value = defaults['atmospheric_stability']
            mixing_eff_slider.value = defaults['mixing_efficiency']
            particle_size_slider.value = defaults['particle_size_um']
            total_mult_slider.value = defaults['total_microbe_multiplier']
            psyringae_slider.value = defaults['psyringae_fraction']
            ice_enh_slider.value = defaults['ice_enhancement']
            rain_eff_slider.value = defaults['rainfall_efficiency']
            timesteps_slider.value = defaults['timesteps']
            
            self.current_state = defaults
            status_label.value = "<b>Status:</b> All parameters reset to defaults"
            update_params_display()
        
        # Store all sliders
        all_sliders = [
            k_min_slider, k_max_slider, t_min_slider, t_opt_slider, t_max_slider,
            slp_slider, slp2_slider, slp3_slider, c_slider, lai_scaling_slider,
            bl_height_slider, cloud_height_slider, stability_dropdown, mixing_eff_slider, particle_size_slider,
            total_mult_slider, psyringae_slider, ice_enh_slider, rain_eff_slider, timesteps_slider
        ]
        
        # Connect controls
        mode_toggle.observe(update_mode, names='value')
        apply_button.on_click(apply_changes)
        compare_button.on_click(compare_with_previous)
        reset_button.on_click(reset_parameters)
        
        # === CREATE TABBED INTERFACE ===
        
        planet_population_tab = widgets.VBox([
            widgets.HTML("<h4>Population Parameters</h4>"),
            widgets.HTML("<small><em>k_min and k_max control microbial carrying capacity</em></small>"),
            k_min_slider, k_max_slider
        ])
        
        planet_temperature_tab = widgets.VBox([
            widgets.HTML("<h4>Temperature Parameters</h4>"),
            widgets.HTML("<small><em>Temperature response curve for microbial growth</em></small>"),
            t_min_slider, t_opt_slider, t_max_slider
        ])
        
        planet_emission_tab = widgets.VBox([
            widgets.HTML("<h4>Emission Parameters</h4>"),
            widgets.HTML("<small><em>Gompertz function coefficients for wind-driven emissions</em></small>"),
            slp_slider, slp2_slider, slp3_slider
        ])
        
        planet_growth_tab = widgets.VBox([
            widgets.HTML("<h4>Growth & Vegetation</h4>"),
            widgets.HTML("<small><em>Growth rate and vegetation density scaling</em></small>"),
            c_slider, lai_scaling_slider
        ])
        
        transport_tab = widgets.VBox([
            widgets.HTML("<h4>Atmospheric Transport</h4>"),
            widgets.HTML("<small><em>Vertical transport from ground to cloud base</em></small>"),
            bl_height_slider, cloud_height_slider, stability_dropdown, mixing_eff_slider, particle_size_slider
        ])
        
        cloud_tab = widgets.VBox([
            widgets.HTML("<h4>Cloud Microphysics</h4>"),
            widgets.HTML("<small><em>Cloud condensation nuclei and ice nucleating particles</em></small>"),
            total_mult_slider, psyringae_slider, ice_enh_slider
        ])
        
        precip_tab = widgets.VBox([
            widgets.HTML("<h4>Precipitation</h4>"),
            widgets.HTML("<small><em>Rainfall efficiency and conversion</em></small>"),
            rain_eff_slider
        ])
        
        controls_tab = widgets.VBox([
            widgets.HTML("<h4>Model Controls</h4>"),
            apply_button, compare_button, reset_button
        ])
        
        # Create comprehensive tabs
        param_tabs = widgets.Tab()
        param_tabs.children = [planet_population_tab, planet_temperature_tab, planet_emission_tab, planet_growth_tab, transport_tab, cloud_tab, precip_tab]
        param_tabs.set_title(0, 'Population')
        param_tabs.set_title(1, 'Temperature') 
        param_tabs.set_title(2, 'Emissions')
        param_tabs.set_title(3, 'Growth')
        param_tabs.set_title(4, 'Transport')
        param_tabs.set_title(5, 'Cloud')
        param_tabs.set_title(6, 'Precipitation')
        
        # Complete interface
        interface = widgets.VBox([
            widgets.HTML("<h2>COMPLETE Bioaerosol-Rainfall Model</h2>"),
            widgets.HTML("<p><strong>Ground Emissions → Atmospheric Transport → Cloud Physics → Precipitation</strong></p>"),
            widgets.HTML("<div style='background-color: #e8f4fd; padding: 10px; margin: 5px; border-left: 4px solid #0066cc;'>"
                        "<strong>COMPLETE PHYSICAL PATHWAY:</strong><br>"
                        "1. PLAnET ground emissions (population, temperature, wind)<br>"
                        "2. Atmospheric transport (boundary layer mixing, settling, cloud height)<br>"
                        "3. Cloud microphysics (CCN, INP, ice nucleation)<br>"
                        "4. Precipitation processes (warm rain + ice enhancement)</div>"),
            data_source_toggle,
            mode_toggle,
            status_label,
            current_params_display,
            timesteps_slider,
            widgets.HBox([param_tabs, controls_tab]),
            output
        ])
        
        # Initialize
        update_mode()
        update_params_display()
        
        print("COMPLETE Bioaerosol-Rainfall Widget created!")
        print("Full physical pathway: Ground → Transport → Cloud → Rain")
        print("All model components with comprehensive parameter control")
        
        return interface


if __name__ == "__main__":
    print("COMPLETE BIOAEROSOL-RAINFALL MODEL")
    print("=" * 50)
    print("Ground Emissions → Atmospheric Transport → Cloud Physics → Precipitation")
    print("Comprehensive parameter control over the complete physical pathway")
    print("\nTo use:")
    print("model = CompleteBioaerosolRainfallModel()")
    print("widget = model.create_complete_widget(csv_path='your_file.csv')")
    print("display(widget)")
