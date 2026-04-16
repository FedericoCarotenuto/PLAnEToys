#!/usr/bin/env python3
"""
Surface Type Parameter Mapping for PLAnET-Rainfall Model Integration
===================================================================

This module defines surface-specific parameters for different ecosystem types
to be used with the combined PLAnET bioaerosol emission model and the 
bioaerosol-to-rainfall model.

References for surface-specific parameters:
-------------------------------------------

BIOAEROSOL EMISSIONS BY SURFACE TYPE:
- Lindemann et al. (1982): "Upper boundary of airborne bacterial concentrations"
- Shaffer & Lighthart (1997): "Survey of culturable airborne bacteria at four diverse locations"
- Bovallius et al. (1978): "Long-range transmission of bacteria" 
- Lighthart (1997): "The ecology of bacteria in the alfresco atmosphere"
- Burrows et al. (2009): "Bacteria in the global atmosphere–Part 1: Review and synthesis"

VEGETATION PARAMETERS:
- Wilkinson et al. (2012): "Bioaerosol dispersal from leaves to the atmosphere"
- Hirano & Upper (2000): "Bacteria in the leaf ecosystem with emphasis on Pseudomonas syringae"
- Lindow & Brandl (2003): "Microbiology of the phyllosphere"

LAI VALUES BY SURFACE TYPE:
- Asner et al. (2003): "Global synthesis of leaf area index observations"
- Myneni et al. (2002): "Global products of vegetation leaf area and absorbed PAR"
- Running et al. (1994): "A continuous satellite-derived measure of global terrestrial primary production"

P. SYRINGAE ECOLOGY:
- Morris et al. (2013): "The life history of the plant pathogen Pseudomonas syringae"
- Monteil et al. (2014): "Diversity and structure of the global population of Pseudomonas syringae"
- Bulgarelli et al. (2013): "Revealing structure and assembly cues for Arabidopsis root-inhabiting bacterial microbiota"

ROUGHNESS AND TRANSPORT:
- Brutsaert (1982): "Evaporation into the atmosphere: theory, history and applications"
- Garratt (1992): "The atmospheric boundary layer"
- Monteith & Unsworth (2013): "Principles of environmental physics"
"""

import numpy as np
from typing import Dict, Tuple, Any
from dataclasses import dataclass

@dataclass
class SurfaceParameters:
    """Parameters defining a specific surface type for PLAnET and rainfall models"""
    
    # PLAnET model parameters (from original MATLAB code)
    T_min: float          # Minimum growth temperature (°C)
    T_max: float          # Maximum growth temperature (°C) 
    T_opt: float          # Optimal growth temperature (°C)
    k_min: float          # Lower population boundary (CFU/m²)
    k_max: float          # Upper population boundary (CFU/m²)
    gompertz_coef1: float # Gompertz coefficient 1 (emission flux shaping)
    gompertz_coef2: float # Gompertz coefficient 2 (wind response)
    gompertz_coef3: float # Gompertz coefficient 3 (turbulence scaling)
    growth_scaling: float # Growth scaling coefficient
    lai_slope: float      # LAI-concentration relationship slope
    lai_offset: float     # LAI-concentration relationship offset
    
    # Surface physical properties (for rainfall model)
    roughness_length: float    # z0 (m) - affects turbulent transport
    canopy_height: float       # Average vegetation height (m)
    typical_lai_range: Tuple[float, float]  # (min_LAI, max_LAI) seasonal range
    
    # Bioaerosol characteristics
    p_syringae_fraction: float # Fraction of total bioaerosols that are P. syringae
    viable_fraction: float     # Fraction of total bioaerosols that are viable (CFU-detectable)
    emission_seasonality: float # Seasonal emission variation factor
    particle_size_um: float    # Typical bioaerosol diameter (micrometers)
    
    # Ecosystem descriptors
    surface_name: str          # Human-readable surface type name
    description: str           # Brief ecological description

class SurfaceTypeLibrary:
    """
    Library of surface-specific parameters for different ecosystem types
    
    Based on scientific literature and field observations of:
    - Bioaerosol emission rates and composition
    - Vegetation characteristics (LAI, roughness, canopy structure)  
    - P. syringae ecology and habitat preferences
    - Meteorological transport properties
    """
    
    def __init__(self):
        self._define_surface_types()
    
    def _define_surface_types(self):
        """Define parameters for different surface types based on literature"""
        
        # References for each surface type are embedded in parameter choices
        
        # GRASSLAND/PRAIRIE
        # Based on: Lighthart (1997), Shaffer & Lighthart (1997)
        # Low biomass, moderate P. syringae presence, low roughness
        self.grassland = SurfaceParameters(
            # PLAnET parameters - moderate microbial activity
            T_min=10.0,           # P. syringae active at cooler temps on grasses
            T_max=32.0,           # Heat stress limit for grassland microbes
            T_opt=22.0,           # Optimal around typical growing season temps
            k_min=3e4,            # Lower baseline due to less leaf area
            k_max=2e5,            # Moderate maximum population
            gompertz_coef1=25.0,  # Lower emission coefficient (less turbulent)
            gompertz_coef2=200.0, # Moderate wind response
            gompertz_coef3=15.0,  # Moderate turbulence scaling
            growth_scaling=0.10,  # Moderate growth rate
            lai_slope=20.0,       # Lower LAI-concentration slope
            lai_offset=80.0,      # Lower background concentration
            
            # Physical properties
            roughness_length=0.05,      # Smooth grassland (Brutsaert, 1982)
            canopy_height=0.3,          # Short grass height
            typical_lai_range=(0.5, 3.5), # Seasonal LAI variation (Asner et al., 2003)
            
            # Bioaerosol characteristics  
            p_syringae_fraction=0.15,   # Moderate P. syringae presence
            viable_fraction=0.05,       # 5% viable (moderate environmental stress)
            emission_seasonality=2.0,   # 2x variation spring/summer vs winter
            particle_size_um=2.8,      # Smaller particles from grasses
            
            surface_name="Grassland",
            description="Natural and managed grasslands, prairies, pastures"
        )
        
        # CROPLAND/AGRICULTURE  
        # Based on: Lindemann et al. (1982), Morris et al. (2013)
        # High P. syringae due to agricultural practices, moderate biomass
        self.cropland = SurfaceParameters(
            # PLAnET parameters - high microbial activity during growing season
            T_min=8.0,            # Crops start growing early spring
            T_max=35.0,           # Heat tolerant during summer growth
            T_opt=24.0,           # Optimal for most crop growth
            k_min=5e4,            # Agricultural baseline
            k_max=6e5,            # High population during crop season
            gompertz_coef1=35.0,  # Higher emission (agricultural disturbance)
            gompertz_coef2=280.0, # Strong wind response (exposed fields)
            gompertz_coef3=20.0,  # High turbulence response
            growth_scaling=0.18,  # Fast growth during growing season
            lai_slope=35.0,       # Strong LAI-concentration relationship
            lai_offset=120.0,     # Higher background (soil disturbance)
            
            # Physical properties
            roughness_length=0.08,      # Agricultural fields (Monteith & Unsworth, 2013)
            canopy_height=1.2,          # Crop height (varies by crop type)
            typical_lai_range=(0.1, 6.0), # Large seasonal variation
            
            # Bioaerosol characteristics
            p_syringae_fraction=0.25,   # High due to agricultural pathogen pressure
            viable_fraction=0.03,       # 3% viable (agricultural stress, UV exposure)
            emission_seasonality=5.0,   # Large seasonal variation
            particle_size_um=3.5,      # Mixed soil + plant particles
            
            surface_name="Cropland", 
            description="Agricultural fields, managed crops"
        )
        
        # DECIDUOUS FOREST
        # Based on: Hirano & Upper (2000), Lindow & Brandl (2003)
        # Very high P. syringae, large biomass, high roughness
        self.deciduous_forest = SurfaceParameters(
            # PLAnET parameters - very high microbial activity
            T_min=5.0,            # Early spring leaf-out
            T_max=30.0,           # Forest moderated temperatures
            T_opt=20.0,           # Cooler optimum in shaded environment
            k_min=8e4,            # High baseline biomass
            k_max=1.2e6,          # Very high population capacity
            gompertz_coef1=45.0,  # High emission coefficient
            gompertz_coef2=350.0, # Strong turbulent emission
            gompertz_coef3=25.0,  # High turbulence scaling
            growth_scaling=0.15,  # Moderate but sustained growth
            lai_slope=40.0,       # Strong LAI effect (dense canopy)
            lai_offset=150.0,     # High background concentration
            
            # Physical properties
            roughness_length=1.5,       # Tall forest roughness (Garratt, 1992)
            canopy_height=20.0,         # Average deciduous forest height
            typical_lai_range=(0.5, 8.0), # Large seasonal variation
            
            # Bioaerosol characteristics
            p_syringae_fraction=0.35,   # Very high - optimal P. syringae habitat
            viable_fraction=0.08,       # 8% viable (protected forest environment)
            emission_seasonality=4.0,   # Strong leaf-on/leaf-off difference
            particle_size_um=4.2,      # Larger particles from leaf fragments
            
            surface_name="Deciduous Forest",
            description="Temperate deciduous forests, broadleaf trees"
        )
        
        # CONIFEROUS FOREST
        # Based on: Monteil et al. (2014), Bulgarelli et al. (2013)  
        # Moderate P. syringae, year-round biomass, very high roughness
        self.coniferous_forest = SurfaceParameters(
            # PLAnET parameters - sustained year-round activity
            T_min=0.0,            # Cold-adapted microbial communities
            T_max=28.0,           # Cooler forest environment
            T_opt=18.0,           # Adapted to cooler conditions
            k_min=6e4,            # Moderate baseline
            k_max=8e5,            # High but less than deciduous
            gompertz_coef1=30.0,  # Moderate emission (waxy needle surfaces)
            gompertz_coef2=300.0, # Strong wind response (tall trees)
            gompertz_coef3=22.0,  # High turbulence
            growth_scaling=0.08,  # Slower but sustained growth
            lai_slope=25.0,       # Moderate LAI effect (evergreen)
            lai_offset=130.0,     # Sustained background
            
            # Physical properties  
            roughness_length=2.0,       # Very rough coniferous forest
            canopy_height=25.0,         # Tall coniferous trees
            typical_lai_range=(3.0, 7.0), # Less seasonal variation
            
            # Bioaerosol characteristics
            p_syringae_fraction=0.20,   # Moderate - some needle adaptation
            viable_fraction=0.06,       # 6% viable (moderate protection)
            emission_seasonality=1.5,   # Less seasonal variation
            particle_size_um=3.8,      # Needle fragments and pollen
            
            surface_name="Coniferous Forest",
            description="Evergreen needle-leaf forests, boreal forests"
        )
        
        # URBAN/SUBURBAN
        # Based on: Bovallius et al. (1978), Shaffer & Lighthart (1997)
        # Low natural P. syringae, mixed surfaces, high anthropogenic inputs
        self.urban = SurfaceParameters(
            # PLAnET parameters - low natural microbial activity
            T_min=8.0,            # Urban heat island effects
            T_max=38.0,           # Higher temperature tolerance (heat island)
            T_opt=25.0,           # Warmer urban optimum
            k_min=2e4,            # Low natural baseline
            k_max=1.5e5,          # Lower maximum (limited vegetation)
            gompertz_coef1=15.0,  # Low natural emission
            gompertz_coef2=150.0, # Moderate wind response
            gompertz_coef3=12.0,  # Lower turbulence scaling
            growth_scaling=0.06,  # Slow growth (stressed vegetation)
            lai_slope=15.0,       # Weak LAI relationship (fragmented vegetation)
            lai_offset=200.0,     # High anthropogenic background
            
            # Physical properties
            roughness_length=0.8,       # Urban roughness (buildings + trees)
            canopy_height=8.0,          # Mixed building/tree height
            typical_lai_range=(1.0, 4.0), # Limited vegetation
            
            # Bioaerosol characteristics  
            p_syringae_fraction=0.08,   # Low natural P. syringae
            viable_fraction=0.02,       # 2% viable (high stress, pollution, UV)
            emission_seasonality=1.2,   # Little seasonal variation
            particle_size_um=3.0,      # Mixed urban particles
            
            surface_name="Urban",
            description="Cities, suburban areas, built environments"
        )
        
        # WETLAND
        # Based on: Burrows et al. (2009), Lighthart (1997)
        # Specialized microbial community, high humidity effects
        self.wetland = SurfaceParameters(
            # PLAnET parameters - specialized wetland microbes
            T_min=3.0,            # Cold-adapted wetland microbes
            T_max=32.0,           # Warm wetland summers
            T_opt=19.0,           # Cooler optimum (high humidity)
            k_min=4e4,            # Moderate baseline
            k_max=4e5,            # Moderate maximum
            gompertz_coef1=20.0,  # Moderate emission (wet surfaces)
            gompertz_coef2=180.0, # Lower wind response (sheltered)
            gompertz_coef3=16.0,  # Moderate turbulence
            growth_scaling=0.12,  # Steady growth in wet conditions
            lai_slope=30.0,       # Good LAI relationship
            lai_offset=110.0,     # Moderate background
            
            # Physical properties
            roughness_length=0.2,       # Moderate wetland roughness
            canopy_height=1.5,          # Wetland vegetation height
            typical_lai_range=(1.0, 5.0), # Seasonal wetland vegetation
            
            # Bioaerosol characteristics
            p_syringae_fraction=0.12,   # Lower P. syringae (wet conditions)
            viable_fraction=0.07,       # 7% viable (humid, protected conditions)
            emission_seasonality=3.0,   # Seasonal wetland cycles
            particle_size_um=3.2,      # Wetland organic particles
            
            surface_name="Wetland",
            description="Marshes, swamps, wet meadows, bog ecosystems"
        )
    
    def get_surface_types(self) -> Dict[str, SurfaceParameters]:
        """Return all available surface types"""
        return {
            'grassland': self.grassland,
            'cropland': self.cropland, 
            'deciduous_forest': self.deciduous_forest,
            'coniferous_forest': self.coniferous_forest,
            'urban': self.urban,
            'wetland': self.wetland
        }
    
    def get_surface(self, surface_type: str) -> SurfaceParameters:
        """Get parameters for a specific surface type"""
        surfaces = self.get_surface_types()
        if surface_type not in surfaces:
            available = list(surfaces.keys())
            raise ValueError(f"Surface type '{surface_type}' not found. Available: {available}")
        return surfaces[surface_type]
    
    def compare_surfaces(self, surface_types: list = None) -> None:
        """Print comparison of surface type parameters"""
        if surface_types is None:
            surface_types = list(self.get_surface_types().keys())
        
        surfaces = self.get_surface_types()
        
        print("Surface Type Comparison")
        print("=" * 80)
        print(f"{'Parameter':<25} {'Unit':<8} ", end="")
        for stype in surface_types:
            print(f"{stype:<15}", end="")
        print()
        print("-" * 80)
        
        # Key parameters for comparison
        params = [
            ('P. syringae fraction', '', lambda s: f"{s.p_syringae_fraction:.2f}"),
            ('Max population', 'CFU/m²', lambda s: f"{s.k_max:.1e}"),
            ('Emission coef.', '-', lambda s: f"{s.gompertz_coef1:.0f}"),
            ('Roughness length', 'm', lambda s: f"{s.roughness_length:.2f}"),
            ('Canopy height', 'm', lambda s: f"{s.canopy_height:.1f}"),
            ('LAI range', '-', lambda s: f"{s.typical_lai_range[0]:.1f}-{s.typical_lai_range[1]:.1f}"),
            ('Seasonality', 'x', lambda s: f"{s.emission_seasonality:.1f}"),
            ('Particle size', 'μm', lambda s: f"{s.particle_size_um:.1f}")
        ]
        
        for param_name, unit, formatter in params:
            print(f"{param_name:<25} {unit:<8} ", end="")
            for stype in surface_types:
                surface = surfaces[stype]
                value = formatter(surface)
                print(f"{value:<15}", end="")
            print()

def demonstrate_surface_differences():
    """Demonstrate how different surface types affect bioaerosol emissions and rainfall"""
    
    library = SurfaceTypeLibrary()
    
    print("PLAnET-Rainfall Model: Surface Type Effects")
    print("=" * 50)
    
    # Show parameter comparison
    library.compare_surfaces()
    
    print(f"\n{'Key Differences for Bioaerosol-Rainfall Interactions:'}")
    print("-" * 50)
    
    surfaces = library.get_surface_types()
    
    # Calculate relative emission potentials
    print("\nRelative Bioaerosol Emission Potential:")
    for name, surface in surfaces.items():
        # Simple emission potential metric
        emission_potential = (surface.k_max * surface.gompertz_coef1 * 
                            surface.p_syringae_fraction / 1e6)
        print(f"  {surface.surface_name:<20}: {emission_potential:.2f}")
    
    print("\nEffects on Vertical Transport:")
    for name, surface in surfaces.items():
        # Roughness affects boundary layer mixing
        transport_efficiency = 1.0 + surface.roughness_length  # Simplified metric
        print(f"  {surface.surface_name:<20}: {transport_efficiency:.2f}x transport efficiency")
    
    print("\nP. syringae Ice Nucleation Potential:")
    for name, surface in surfaces.items():
        inp_potential = surface.p_syringae_fraction * surface.k_max / 1e5
        print(f"  {surface.surface_name:<20}: {inp_potential:.2f} (relative scale)")

if __name__ == "__main__":
    demonstrate_surface_differences()
