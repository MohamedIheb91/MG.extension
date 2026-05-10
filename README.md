# MG Extension

A pyRevit extension for BIM automation, built for architects and structural engineers working with Revit 2025+.

## Tools

### Inserimento Shared Parameters

Loads shared parameters from a `.txt` file and binds them to selected Revit categories through a WPF interface.

![Load Shared Parameters](docs/Load%20Shared%20Parameters.PNG)

**Features:**
- Reads the shared parameter file already loaded in Revit (or browse for a new one)
- Filter categories by type (Model, Annotation, etc.)
- Select individual categories or use All / None
- Choose binding type: Instance or Type
- Set "Varies by Group" and "Group Under" options
- Applies bindings in a single Revit transaction

## Requirements

- Revit 2025+
- pyRevit with CPython engine

## Author

Mohamed Iheb Gherissi
