# INSTALLATION GUIDE: Complete Bioaerosol-Rainfall Model
# ========================================================

## SYSTEM REQUIREMENTS

### Minimum System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 2 GB free space
- **Processor**: Intel i5 or equivalent

### Recommended System Requirements
- **Operating System**: Windows 11, macOS 12+, or Linux (Ubuntu 20.04+)
- **Python**: Version 3.9 or 3.10
- **RAM**: 16 GB or more
- **Storage**: 5 GB free space
- **Processor**: Intel i7 or equivalent

---

## PYTHON ENVIRONMENT SETUP

### Option 1: Conda Environment (Recommended)

**1. Install Anaconda or Miniconda**
```bash
# Download and install from: https://www.anaconda.com/download
# Or Miniconda from: https://docs.conda.io/en/latest/miniconda.html
```

**2. Create Environment**
```bash
# Create new environment
conda create -n bioaerosol python=3.9

# Activate environment
conda activate bioaerosol
```

**3. Install Base Packages**
```bash
# Essential packages
conda install numpy pandas matplotlib scipy ipywidgets

# Scientific computing
conda install -c conda-forge ipympl

# Jupyter environment
conda install jupyter jupyterlab
```

**4. Install Additional Dependencies**
```bash
# Additional scientific packages
pip install scikit-learn --break-system-packages
pip install seaborn --break-system-packages

# For enhanced plotting
pip install plotly --break-system-packages
```

### Option 2: Virtual Environment (venv)

**1. Create Virtual Environment**
```bash
# Create environment
python -m venv bioaerosol_env

# Activate environment (Windows)
bioaerosol_env\Scripts\activate

# Activate environment (macOS/Linux)
source bioaerosol_env/bin/activate
```

**2. Upgrade pip**
```bash
python -m pip install --upgrade pip
```

**3. Install Required Packages**
```bash
pip install numpy pandas matplotlib scipy ipywidgets ipympl
pip install jupyter jupyterlab
pip install scikit-learn seaborn plotly
```

### Option 3: System-wide Installation (Not Recommended)

**Only if you cannot use virtual environments:**
```bash
pip install --user numpy pandas matplotlib scipy ipywidgets ipympl
pip install --user jupyter jupyterlab
pip install --user scikit-learn seaborn plotly
```

---

## MODEL FILES INSTALLATION

### Download Model Files

**Required Files:**
1. `complete_bioaerosol_rainfall_model.py` - Main model code
2. `planet.py` - PLAnET model implementation
3. `surface_parameters_fixed.py` - Surface parameter library

### File Organization

**Create Project Directory:**
```bash
# Create main directory
mkdir bioaerosol_model
cd bioaerosol_model

# Create subdirectories
mkdir data
mkdir outputs
mkdir docs
```

**Directory Structure:**
```
bioaerosol_model/
├── complete_bioaerosol_rainfall_model.py
├── planet.py
├── surface_parameters_fixed.py
├── data/
│   └── meteo_2015.csv (your meteorological data)
├── outputs/
│   └── (model results will be saved here)
└── docs/
    ├── TECHNICAL_DOCUMENTATION_COMPLETE.md
    ├── INSTALLATION_GUIDE.md
    └── USER_MANUAL.md
```

### PLAnET Model Dependencies

**If planet.py is not available, create minimal implementation:**

```python
# Create minimal_planet.py if needed
import numpy as np

class ModelParams:
    def __init__(self):
        self.k_min = 1e3
        self.k_max = 1e6
        self.T_min = 5.0
        self.T_opt = 21.0
        self.T_max = 35.0
        self.slp = 30.76
        self.slp2 = 103.0
        self.slp3 = 25.0
        self.c = 0.28
        self.lai1 = 0.6
        self.lai2 = 0.1

class PLAnETResult:
    def __init__(self, population, growth, net_flux):
        self.population = population
        self.growth = growth
        self.net_flux = net_flux

def PLAnET(data, params, ustar_flag=True, depo_flag=True):
    # Minimal PLAnET implementation
    # Replace with actual PLAnET code if available
    n_timesteps = len(data)
    
    population = np.zeros(n_timesteps)
    growth = np.zeros(n_timesteps)
    net_flux = np.zeros(n_timesteps)
    
    population[0] = params.k_min
    
    for t in range(1, n_timesteps):
        temp = data[t, 0]
        ustar = data[t, 2] if data.shape[1] > 2 else 0.1
        lai = data[t, 3] if data.shape[1] > 3 else 2.0
        
        # Temperature response
        if temp <= params.T_min or temp >= params.T_max:
            temp_factor = 0
        else:
            temp_factor = ((params.T_max - temp)/(params.T_max - params.T_opt)) * \
                         ((temp - params.T_min)/(params.T_opt - params.T_min))**((params.T_opt - params.T_min)/(params.T_max - params.T_opt))
        
        # Growth rate
        lai_factor = params.lai1 * lai + params.lai2
        growth_rate = params.c * temp_factor * lai_factor
        growth[t] = growth_rate
        
        # Population update
        population[t] = population[t-1] * np.exp(growth_rate * 1800)  # 30 min timestep
        population[t] = max(params.k_min, min(population[t], params.k_max))
        
        # Emission calculation
        emission_factor = params.slp * np.exp(-params.slp2 * np.exp(-params.slp3 * ustar))
        net_flux[t] = emission_factor * population[t] / 1800  # Convert to flux
    
    return PLAnETResult(population, growth, net_flux)
```

---

## JUPYTER LAB SETUP

### Configure Jupyter Lab

**1. Install Jupyter Extensions**
```bash
# Install widget extensions
jupyter labextension install @jupyter-widgets/jupyterlab-manager

# Install matplotlib widget
jupyter labextension install jupyter-matplotlib
```

**2. Enable Widget Extensions**
```bash
# Enable widgets
jupyter nbextension enable --py widgetsnbextension --sys-prefix

# For matplotlib
jupyter nbextension enable --py ipympl --sys-prefix
```

**3. Configure Jupyter Settings**

Create `~/.jupyter/jupyter_lab_config.py`:
```python
c.ServerApp.allow_root = False
c.ServerApp.open_browser = True
c.NotebookApp.token = ''
c.NotebookApp.password = ''
```

### Start Jupyter Lab

```bash
# Navigate to project directory
cd bioaerosol_model

# Start Jupyter Lab
jupyter lab

# Or start Jupyter Notebook (alternative)
jupyter notebook
```

---

## TESTING INSTALLATION

### Basic Import Test

Create a test notebook or Python script:

```python
# Test basic imports
try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import ipywidgets as widgets
    from IPython.display import display
    print("✓ Basic packages imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")

# Test model import
try:
    from complete_bioaerosol_rainfall_model import CompleteBioaerosolRainfallModel
    print("✓ Model imported successfully")
except ImportError as e:
    print(f"✗ Model import error: {e}")
    print("Make sure complete_bioaerosol_rainfall_model.py is in the same directory")

# Test widget creation
try:
    model = CompleteBioaerosolRainfallModel()
    print("✓ Model instance created successfully")
except Exception as e:
    print(f"✗ Model creation error: {e}")
```

### Widget Test

```python
# Test widget functionality
try:
    model = CompleteBioaerosolRainfallModel()
    widget = model.create_complete_widget()
    print("✓ Widget created successfully")
    print("Display the widget with: display(widget)")
except Exception as e:
    print(f"✗ Widget creation error: {e}")
```

### Sample Data Test

```python
# Test with synthetic data
try:
    model = CompleteBioaerosolRainfallModel()
    
    # Test synthetic data generation
    meteo_data, timestamps = model.create_synthetic_data(48)  # 24 hours
    print(f"✓ Synthetic data generated: {meteo_data.shape}")
    
    # Test model run
    results = model.run_complete_model(model.current_state, use_csv=False)
    print("✓ Model run completed successfully")
    print(f"Mean rainfall: {results['mean_rainfall']:.6f} mm/h")
    
except Exception as e:
    print(f"✗ Model run error: {e}")
```

---

## TROUBLESHOOTING

### Common Issues and Solutions

**1. Widget Display Issues**

**Problem**: Widgets not displaying in Jupyter Lab
**Solution**:
```bash
# Reinstall widget extensions
jupyter labextension install @jupyter-widgets/jupyterlab-manager --clean
jupyter labextension install jupyter-matplotlib --clean

# Restart Jupyter Lab
```

**2. Matplotlib Backend Issues**

**Problem**: Plots not interactive or not displaying
**Solution**:
```python
# In notebook, use magic commands
%matplotlib widget

# Or set backend explicitly
import matplotlib
matplotlib.use('widget')
```

**3. Memory Issues**

**Problem**: Out of memory errors with large datasets
**Solution**:
- Reduce timesteps parameter
- Use smaller CSV files
- Close unused notebooks
- Restart Python kernel

**4. Import Errors**

**Problem**: Cannot import model modules
**Solution**:
```python
# Add current directory to path
import sys
import os
sys.path.append(os.getcwd())

# Check file locations
import os
print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))
```

**5. CSV Loading Issues**

**Problem**: Cannot load meteorological data
**Solution**:
```python
# Check CSV format
import pandas as pd
df = pd.read_csv('your_file.csv')
print("CSV shape:", df.shape)
print("CSV columns:", df.columns.tolist())
print("First few rows:")
print(df.head())

# Ensure minimum 4 columns: Temperature, Pressure, u*, LAI
```

**6. Performance Issues**

**Problem**: Model runs too slowly
**Solution**:
- Reduce number of timesteps
- Use staging mode instead of real-time
- Close other applications
- Use more powerful hardware

---

## CONDA ENVIRONMENT EXPORT/IMPORT

### Export Environment

**Create environment file for sharing:**
```bash
# Export full environment
conda env export > bioaerosol_environment.yml

# Export minimal requirements
conda list --export > bioaerosol_requirements.txt
```

### Import Environment

**Recreate environment from file:**
```bash
# From full environment file
conda env create -f bioaerosol_environment.yml

# Or create and install from requirements
conda create -n bioaerosol python=3.9
conda activate bioaerosol
conda install --file bioaerosol_requirements.txt
```

---

## UPDATING THE MODEL

### Update Model Code

**To update to a newer version:**
1. Backup current model files
2. Download new model files
3. Replace old files with new versions
4. Test with existing data

**Check for updates:**
```python
# Check model version (if implemented)
from complete_bioaerosol_rainfall_model import CompleteBioaerosolRainfallModel
model = CompleteBioaerosolRainfallModel()
print("Model version information:")
print(model.__doc__)
```

### Update Dependencies

```bash
# Update all packages (conda)
conda update --all

# Update specific packages (pip)
pip install --upgrade numpy pandas matplotlib
```

---

## SUPPORT AND DOCUMENTATION

### Getting Help

**If you encounter issues:**
1. Check this installation guide
2. Review the User Manual
3. Check the Technical Documentation
4. Look at error messages carefully
5. Test with synthetic data first

### Documentation Files

**Make sure you have:**
- `INSTALLATION_GUIDE.md` (this file)
- `USER_MANUAL.md` - How to use the model
- `TECHNICAL_DOCUMENTATION_COMPLETE.md` - All equations and theory

### System Information

**For troubleshooting, gather:**
```python
import sys
import platform
import numpy as np
import pandas as pd
import matplotlib

print("System Information:")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"NumPy version: {np.__version__}")
print(f"Pandas version: {pd.__version__}")
print(f"Matplotlib version: {matplotlib.__version__}")
```

---

**Installation complete! See USER_MANUAL.md for usage instructions.**
