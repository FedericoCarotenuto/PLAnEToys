# USER MANUAL: Complete Bioaerosol-Rainfall Model
# ================================================

## TABLE OF CONTENTS

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Parameter Control](#parameter-control)
4. [Data Input](#data-input)
5. [Interpreting Results](#interpreting-results)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Example Workflows](#example-workflows)

---

## GETTING STARTED

### What is this Model?

The Complete Bioaerosol-Rainfall Model simulates how microorganisms emitted from vegetation can enhance precipitation through ice nucleation processes. It follows the complete physical pathway:

**Ground Emissions → Atmospheric Transport → Cloud Physics → Precipitation**

### Before You Start

**Required Files:**
- `complete_bioaerosol_rainfall_model.py`
- `planet.py` (PLAnET model)
- `surface_parameters_fixed.py` (surface parameters)

**Optional:**
- Your meteorological data in CSV format

**Environment:**
- Python 3.8+ with Jupyter Lab/Notebook
- Required packages (see Installation Guide)

### Quick Start

**1. Open Jupyter Lab**
```bash
jupyter lab
```

**2. Create New Notebook**
- File → New → Notebook
- Select Python 3 kernel

**3. Basic Model Setup**
```python
# Import the model
from complete_bioaerosol_rainfall_model import CompleteBioaerosolRainfallModel

# Create model instance
model = CompleteBioaerosolRainfallModel()

# Create widget interface
widget = model.create_complete_widget()

# Display the widget
display(widget)
```

---

## BASIC USAGE

### Starting the Model

**With Synthetic Data:**
```python
from complete_bioaerosol_rainfall_model import CompleteBioaerosolRainfallModel

model = CompleteBioaerosolRainfallModel()
widget = model.create_complete_widget()
display(widget)
```

**With Your CSV Data:**
```python
from complete_bioaerosol_rainfall_model import CompleteBioaerosolRainfallModel

model = CompleteBioaerosolRainfallModel()
widget = model.create_complete_widget(csv_path="path/to/your/data.csv")
display(widget)
```

### Understanding the Interface

**Main Controls:**
- **Data Source Toggle**: Switch between synthetic and CSV data
- **Mode Toggle**: Real-time vs Staging mode
- **Parameter Tabs**: Organized parameter controls
- **Apply/Compare/Reset Buttons**: Model execution controls

**Parameter Tabs:**
1. **Population**: Microbial carrying capacity (k_min, k_max)
2. **Temperature**: Growth temperature limits (T_min, T_opt, T_max)
3. **Emissions**: Wind-driven emission parameters (slp, slp2, slp3)
4. **Growth**: Growth rate and vegetation density
5. **Transport**: Atmospheric transport from ground to cloud
6. **Cloud**: Cloud microphysics and ice nucleation
7. **Precipitation**: Final rainfall efficiency

### Operating Modes

**Real-time Mode:**
- Changes apply immediately
- Good for exploring single parameters
- Can be slow with complex calculations

**Staging Mode (Recommended):**
- Adjust multiple parameters before applying
- Click "Apply All Parameters" to run model
- Better for systematic parameter studies

---

## PARAMETER CONTROL

### 1. Population Parameters

**k_min (Minimum Population):**
- Range: 1×10³ to 1×10⁶ CFU/m²
- Default: 1×10³ CFU/m²
- Effect: Sets baseline microbial population
- Low values → Less emission potential
- High values → Higher baseline emissions

**k_max (Maximum Population):**
- Range: 1×10⁴ to 1×10⁷ CFU/m²
- Default: 1×10⁶ CFU/m²
- Effect: Sets population carrying capacity
- Higher values → More total emission potential
- Must be larger than k_min

**Usage Tips:**
- Start with defaults for typical vegetation
- Increase k_max for dense forests
- Decrease k_max for sparse vegetation

### 2. Temperature Parameters

**T_min (Minimum Growth Temperature):**
- Range: -10°C to 25°C
- Default: 5°C
- Effect: Below this temperature, no growth occurs
- Lower values → Growth at colder temperatures
- Higher values → More temperature-sensitive

**T_opt (Optimal Growth Temperature):**
- Range: 5°C to 40°C
- Default: 21°C
- Effect: Temperature of maximum growth
- Should be between T_min and T_max
- Reflects microbial thermal preferences

**T_max (Maximum Growth Temperature):**
- Range: 15°C to 50°C
- Default: 35°C
- Effect: Above this temperature, growth ceases
- Higher values → Heat-tolerant microbes
- Lower values → Heat-sensitive microbes

**Usage Tips:**
- Narrow range (T_max - T_min small) → Very temperature sensitive
- Wide range → More temperature tolerant
- Adjust T_opt for different microbial communities

### 3. Emission Parameters

**slp (Amplitude Coefficient):**
- Range: 0.1 to 200
- Default: 30.76
- Effect: Controls maximum emission intensity
- Linear scaling of emission magnitude
- Higher values → More emissions at high winds

**slp2 (Rate Coefficient):**
- Range: 1 to 1000
- Default: 103.0
- Effect: Controls wind sensitivity
- Higher values → Less sensitive to wind
- Lower values → More sensitive to wind

**slp3 (Inflection Coefficient):**
- Range: 1 to 100
- Default: 25.0
- Effect: Controls wind threshold for emissions
- Higher values → Lower wind threshold
- Lower values → Higher wind threshold

**Usage Tips:**
- slp controls "how much" emission
- slp2 and slp3 control "when" emission occurs
- Start with defaults and adjust slp first

### 4. Growth Parameters

**c (Growth Rate Coefficient):**
- Range: 0.001 to 1.0
- Default: 0.28
- Effect: Base growth rate scaling
- Higher values → Faster population growth
- Lower values → Slower population response

**LAI Scaling:**
- Range: 0.1 to 10.0
- Default: 1.0
- Effect: Vegetation density modifier
- 2.0 → Twice as dense vegetation
- 0.5 → Half as dense vegetation

**Usage Tips:**
- LAI scaling simulates different forest densities
- Use >1.0 for dense forests, <1.0 for sparse vegetation
- Affects both growth and emission potential

### 5. Atmospheric Transport Parameters

**Boundary Layer Height:**
- Range: 200 to 4000 m
- Default: 1500 m
- Effect: Height of atmospheric mixing layer
- Higher → Better vertical mixing
- Lower → Less mixing, more surface retention

**Cloud Base Height:**
- Range: 500 to 4000 m
- Default: 1500 m
- Effect: Height particles must reach for cloud interaction
- Higher → Harder for particles to reach clouds
- Lower → Easier transport to cloud level

**Atmospheric Stability:**
- Options: Unstable, Neutral, Stable
- Default: Neutral
- Effect: Vertical mixing efficiency
- Unstable → Strong mixing (daytime, convective)
- Stable → Weak mixing (nighttime, inversions)

**Mixing Efficiency:**
- Range: 0.01 to 0.8
- Default: 0.1
- Effect: Base vertical transport efficiency
- Higher → More particles reach clouds
- Lower → More particles settle out

**Particle Size:**
- Range: 0.5 to 20 μm
- Default: 3.3 μm
- Effect: Settling velocity and transport
- Larger → Faster settling, less transport
- Smaller → Slower settling, better transport

**Usage Tips:**
- Transport efficiency typically 1-30%
- Unstable conditions give best transport
- Match cloud height to meteorological conditions

### 6. Cloud Microphysics Parameters

**Total Microbe Multiplier:**
- Range: 1 to 1000
- Default: 10
- Effect: Viable to total particle scaling
- 10 → Atmosphere has 10x more particles than PLAnET measures
- 100 → Atmosphere has 100x more particles
- **CORRECTED LOGIC**: Upward scaling (PLAnET × Multiplier)

**P. syringae Fraction:**
- Range: 0% to 50%
- Default: 15%
- Effect: Percentage of particles that are P. syringae
- Higher → More ice nucleating particles
- Lower → Less ice nucleation potential

**Ice Enhancement Factor:**
- Range: 0 to 50
- Default: 5
- Effect: Ice nucleation efficiency
- Higher → Stronger precipitation enhancement
- 0 → No ice nucleation enhancement

**Usage Tips:**
- Total multiplier has largest effect on results
- P. syringae fraction affects ice nucleation only
- Ice enhancement controls final precipitation boost

### 7. Precipitation Parameters

**Rainfall Efficiency:**
- Range: 0 to 100
- Default: 1
- Effect: Conversion efficiency to precipitation
- Higher → More rainfall per particle
- Lower → Less rainfall per particle

**Usage Tips:**
- Final parameter in the chain
- Scales overall precipitation magnitude
- Combine with other parameters for realistic results

---

## DATA INPUT

### CSV Data Format

**Required Columns (minimum 4):**
1. **Temperature** (°C)
2. **Pressure** (Pa) 
3. **Friction Velocity u*** (m/s)
4. **Leaf Area Index (LAI)** (dimensionless)
5. **Wind Speed** (m/s) - optional, estimated from u* if missing

**Example CSV Format:**
```csv
temperature,pressure,ustar,lai,wind_speed
15.2,101325,0.15,2.1,4.2
16.8,101280,0.18,2.1,4.8
18.1,101245,0.22,2.2,5.1
...
```

### CSV Loading

**Automatic Detection:**
- Model automatically detects CSV structure
- Uses first 5 columns if more are present
- Creates timestamps starting from 2015-01-01
- Assumes 30-minute intervals

**Error Handling:**
- Falls back to synthetic data if CSV loading fails
- Shows error messages for troubleshooting
- Validates minimum column requirements

### Synthetic Data

**When to Use:**
- Testing model functionality
- Exploring parameter effects
- No real meteorological data available
- Educational demonstrations

**Generated Data:**
- Realistic seasonal and diurnal temperature cycles
- Wind speed with atmospheric variability
- LAI with seasonal vegetation patterns
- Atmospheric pressure with random variability

---

## INTERPRETING RESULTS

### Complete Results Dashboard

The model produces a comprehensive 15-panel visualization showing the complete physical pathway:

### Row 1: Meteorological Forcing

**Temperature Forcing:**
- Red line: Temperature time series
- Dashed lines: Growth temperature limits (T_min, T_opt, T_max)
- Shows when conditions favor microbial growth

**Wind Speed:**
- Purple line: Wind speed driving emissions
- Higher winds → More particle emission

**LAI (Leaf Area Index):**
- Green line: Vegetation density (with scaling applied)
- Higher LAI → More surface area for microbes

### Row 2: PLAnET Ground Emissions

**Population Dynamics:**
- Blue line: Microbial population over time
- Dashed lines: Population limits (k_min, k_max)
- Shows population growth and constraints

**Ground Viable Emissions:**
- Green line: PLAnET viable microbe emissions
- Units: CFU/m²/s (Colony Forming Units)
- Wind and population dependent

**Ground Total Particles:**
- Purple line: Total atmospheric particles (viable × multiplier)
- Shows corrected upward scaling

### Row 3: Atmospheric Transport

**Transport Efficiency:**
- Brown line: Percentage of ground particles reaching cloud base
- Typically 1-30% depending on conditions
- Affected by mixing, settling, and atmospheric stability

**Ground vs Cloud Particles:**
- Purple line: Particles at ground level
- Orange line: Particles reaching cloud base
- Shows atmospheric transport losses

**Atmospheric Profile:**
- Schematic showing vertical concentration profile
- Height vs relative particle concentration
- Illustrates mixing and transport processes

### Row 4: Cloud Microphysics

**P. syringae at Cloud Base:**
- Red line: Ice nucleating particles at cloud level
- Subset of total particles that can nucleate ice
- Critical for precipitation enhancement

**Ice Enhancement:**
- Navy line: Ice nucleation enhancement factor
- Typically 1.0 (no enhancement) to 5+ (strong enhancement)
- Depends on P. syringae concentration

**Cloud Processes:**
- Pie chart showing warm vs ice precipitation processes
- Illustrates relative contribution of each process

### Row 5: Final Results

**Final Precipitation:**
- Dark blue line: Final rainfall rates
- Units: mm/h
- Result of complete physical pathway

**Process Comparison:**
- Bar chart comparing ground particles, cloud particles, and rainfall
- Shows relative magnitudes through the pathway

**Complete Pathway Summary:**
- Text summary of key results
- Mean values and event statistics
- Quick assessment of model performance

### Key Metrics to Monitor

**Model Performance Indicators:**

**Ground Emissions:**
- Mean viable emissions: 0.1-100 CFU/m²/s (typical)
- Population range: Should stay within k_min to k_max
- Temperature response: Growth during favorable temperatures

**Atmospheric Transport:**
- Transport efficiency: 1-30% (realistic range)
- Higher efficiency with unstable conditions and lower clouds
- Zero efficiency indicates transport problems

**Cloud Base Particles:**
- Should be 1-30% of ground particles
- Affected by transport efficiency
- Critical for cloud interactions

**Precipitation Enhancement:**
- Ice enhancement: 1.0-10x typical
- Higher with more P. syringae particles
- Final rainfall: 0.001-1 mm/h typical range

**Event Statistics:**
- Rain events: Percentage of timesteps with rain >0.001 mm/h
- Typical: 5-30% depending on conditions
- Higher percentages indicate strong bioaerosol effect

---

## ADVANCED FEATURES

### Parameter Combination Studies

**Using Staging Mode for Systematic Studies:**

1. **Single Parameter Study:**
   - Set all parameters to baseline
   - Vary one parameter across its range
   - Use "Apply" and "Compare" to see effects

2. **Multi-Parameter Study:**
   - Adjust multiple related parameters
   - Example: Increase k_max + slp + LAI scaling together
   - Compare with baseline to see combined effects

3. **Sensitivity Analysis:**
   - Identify high-impact parameters
   - Test extreme values to find thresholds
   - Document parameter interactions

### Before/After Comparisons

**Using Compare Function:**
1. Run model with baseline parameters
2. Adjust parameters for new scenario
3. Click "Compare with Previous"
4. Examine side-by-side plots

**Comparison Features:**
- All plots show current vs previous results
- Easy identification of parameter effects
- Quantitative comparison in results summary

### Real-time Mode Applications

**When to Use Real-time Mode:**
- Quick parameter exploration
- Educational demonstrations
- Interactive presentations
- Single parameter sensitivity tests

**Performance Tips:**
- Reduce timesteps for faster response
- Use synthetic data for speed
- Close other applications for better performance

### CSV Data Analysis

**Working with Real Meteorological Data:**

1. **Data Quality Checks:**
   - Examine CSV metadata display
   - Check temperature and wind ranges
   - Verify LAI patterns match season

2. **Seasonal Analysis:**
   - Use longer time series (months to year)
   - Observe seasonal bioaerosol patterns
   - Link to precipitation seasonal cycles

3. **Event Analysis:**
   - Focus on specific weather events
   - High wind periods for emission events
   - Temperature fluctuations and growth response

### Parameter Optimization

**Finding Optimal Parameters:**

1. **Start with Defaults:**
   - Use PLAnET defaults as baseline
   - Adjust for specific ecosystem type

2. **Systematic Exploration:**
   - Use extreme ranges to find sensitivities
   - Focus on high-impact parameters first
   - Document parameter interactions

3. **Validation Against Observations:**
   - Compare results with known precipitation patterns
   - Adjust for local ecosystem characteristics
   - Use literature values for validation

---

## TROUBLESHOOTING

### Common Issues and Solutions

### Widget Display Problems

**Problem**: Widget not displaying properly
**Solutions:**
```python
# Ensure proper imports
%matplotlib widget
import ipywidgets as widgets

# Clear output and redisplay
from IPython.display import clear_output, display
clear_output()
display(widget)

# Check Jupyter Lab extensions
# In terminal: jupyter labextension list
```

### Model Performance Issues

**Problem**: Model runs slowly or freezes
**Solutions:**
- Reduce timesteps parameter (try 100 instead of 200)
- Use staging mode instead of real-time
- Close other browser tabs and applications
- Restart Python kernel if memory issues

**Problem**: Out of memory errors
**Solutions:**
```python
# Reduce data size
model.current_state['timesteps'] = 48  # 24 hours instead of full dataset

# Use synthetic data instead of CSV
# Select "Synthetic" in data source toggle
```

### Parameter Issues

**Problem**: Unrealistic results
**Common Causes:**
- k_max ≤ k_min (population parameters invalid)
- Temperature parameters in wrong order (T_min ≥ T_opt ≥ T_max)
- Extreme parameter values outside physical range

**Solutions:**
```python
# Reset to defaults
# Click "Reset to Defaults" button

# Check parameter constraints
print("k_min:", model.current_state['k_min'])
print("k_max:", model.current_state['k_max'])
print("Temperature order:", model.current_state['T_min'], 
      model.current_state['T_opt'], model.current_state['T_max'])
```

### CSV Data Issues

**Problem**: CSV file not loading
**Check CSV Format:**
```python
import pandas as pd

# Check your CSV file
df = pd.read_csv('your_file.csv')
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("First few rows:")
print(df.head())

# Minimum requirements
if df.shape[1] < 4:
    print("ERROR: Need at least 4 columns")
    print("Required: Temperature, Pressure, u*, LAI")
```

**Problem**: Strange temperature units
**Solution:**
```python
# Check temperature range
print("Temperature range:", df.iloc[:, 0].min(), "to", df.iloc[:, 0].max())
# Should be roughly -10 to 40 for Celsius
# If 250-320, probably Kelvin → convert to Celsius
```

### Results Interpretation Issues

**Problem**: No precipitation events
**Possible Causes:**
- Transport efficiency too low (all parameters at minimum)
- No viable emissions (population too low, wrong temperatures)
- Ice enhancement disabled (P. syringae fraction = 0)

**Diagnostic Steps:**
1. Check ground emissions are > 0
2. Check transport efficiency > 0
3. Check ice enhancement factor > 1
4. Increase rainfall efficiency parameter

**Problem**: Unrealistically high precipitation
**Possible Causes:**
- Total multiplier too high (>100)
- Ice enhancement too strong (>20)
- Rainfall efficiency too high (>10)

**Solutions:**
- Reduce total multiplier to 10-50 range
- Reduce ice enhancement to 5-15 range
- Keep rainfall efficiency near 1

### Error Messages

**ImportError: Cannot import model**
```python
# Check file location
import os
print("Current directory:", os.getcwd())
print("Files:", os.listdir('.'))

# Check Python path
import sys
print("Python path includes:")
for path in sys.path:
    print("  ", path)
```

**AttributeError in model functions**
```python
# Check model version/integrity
model = CompleteBioaerosolRainfallModel()
print("Model attributes:")
print([attr for attr in dir(model) if not attr.startswith('_')])
```

---

## EXAMPLE WORKFLOWS

### Workflow 1: Basic Model Exploration

**Goal**: Understand how the model works with default parameters

**Steps:**
1. Load model with synthetic data
2. Run with all default parameters
3. Examine complete results dashboard
4. Note key values: transport efficiency, enhancement factors, rainfall

**Expected Results:**
- Transport efficiency: ~10%
- Ice enhancement: ~2-5x
- Rainfall: 0.001-0.01 mm/h typical

### Workflow 2: Temperature Sensitivity Study

**Goal**: Understand how temperature affects bioaerosol emissions

**Steps:**
1. Set baseline parameters (all defaults)
2. Run model and note results
3. Increase T_opt from 21°C to 30°C
4. Compare results using "Compare with Previous"
5. Try T_opt = 15°C and compare again

**Expected Effects:**
- Higher T_opt → Less growth in typical conditions
- Lower T_opt → More growth in cool conditions
- Emission timing shifts with temperature preferences

### Workflow 3: Atmospheric Transport Study

**Goal**: Examine effects of boundary layer and cloud height

**Steps:**
1. Baseline: BL height = 1500m, Cloud height = 1500m
2. Test deep boundary layer: BL = 3000m, Cloud = 1500m
3. Test high clouds: BL = 1500m, Cloud = 3000m
4. Test unstable vs stable atmospheric conditions

**Expected Effects:**
- Deeper BL → Better transport efficiency
- Higher clouds → Lower transport efficiency
- Unstable conditions → Best transport

### Workflow 4: Ice Nucleation Enhancement Study

**Goal**: Quantify precipitation enhancement from P. syringae

**Steps:**
1. Baseline with P. syringae fraction = 15%
2. Test without ice nucleation: P. syringae = 0%
3. Test high ice nucleation: P. syringae = 30%
4. Compare ice enhancement factors and final rainfall

**Expected Effects:**
- No P. syringae → No ice enhancement (factor = 1.0)
- More P. syringae → Higher enhancement factors
- Enhancement depends on total particle concentration

### Workflow 5: Ecosystem Type Comparison

**Goal**: Compare different vegetation types

**Forest Setup:**
- k_max = 5×10⁶ (high microbial capacity)
- LAI scaling = 2.0 (dense vegetation)
- slp = 50 (strong emissions)

**Grassland Setup:**
- k_max = 1×10⁵ (lower capacity) 
- LAI scaling = 0.5 (sparse vegetation)
- slp = 15 (weaker emissions)

**Agricultural Setup:**
- k_max = 3×10⁵ (moderate capacity)
- LAI scaling = 0.8 (managed vegetation)
- slp = 20 (moderate emissions)

**Compare Results:**
- Forest should show highest emissions and rainfall enhancement
- Grassland should show lowest effects
- Agricultural intermediate

### Workflow 6: Real Data Analysis

**Goal**: Analyze your own meteorological data

**Steps:**
1. Prepare CSV with required columns
2. Load model with CSV path
3. Select "CSV Data" as data source
4. Run with default parameters first
5. Adjust parameters for local ecosystem
6. Analyze seasonal patterns in results

**Analysis Points:**
- Seasonal emission patterns
- Temperature dependence in real conditions
- Wind event responses
- LAI seasonal cycle effects

### Workflow 7: Parameter Optimization

**Goal**: Find best parameters for observed conditions

**Method:**
1. Start with literature values for ecosystem type
2. Systematically vary high-impact parameters:
   - Total multiplier (10-100)
   - k_max (10⁵-10⁶)
   - Ice enhancement (1-15)
3. Compare with observed precipitation patterns
4. Document optimal parameter set

**Validation Criteria:**
- Reasonable emission magnitudes
- Realistic transport efficiencies
- Precipitation enhancement within observed ranges
- Seasonal patterns match expectations

---

## BEST PRACTICES

### Model Setup

1. **Always start with defaults** - Provides known baseline
2. **Test with synthetic data first** - Eliminates data issues
3. **Use staging mode for studies** - More systematic than real-time
4. **Document parameter choices** - Record rationale for parameter values

### Parameter Exploration

1. **One parameter at a time** - Understand individual effects first
2. **Use extreme values** - Find parameter sensitivities
3. **Check physical realism** - Ensure results make sense
4. **Compare with literature** - Validate against published studies

### Data Management

1. **Prepare CSV properly** - Check format and units carefully
2. **Keep backup files** - Save working parameter sets
3. **Document results** - Save plots and parameter values
4. **Version control** - Track parameter changes and results

### Interpretation

1. **Focus on relative changes** - Compare scenarios rather than absolute values
2. **Examine complete pathway** - Don't just look at final rainfall
3. **Check intermediate results** - Verify transport and cloud processes
4. **Consider uncertainties** - Model is educational/exploratory tool

---

**This completes the User Manual. For technical details, see TECHNICAL_DOCUMENTATION_COMPLETE.md. For installation help, see INSTALLATION_GUIDE.md.**
