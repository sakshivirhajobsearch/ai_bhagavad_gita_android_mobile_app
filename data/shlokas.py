# data/shlokas.py
"""
Robust loader for SECTION modules (SECTION_1 .. SECTION_16 and SECTION_13_B).

Problem fixed: Avoids top-level `from data.SECTION_X import ...` imports which raise
`ModuleNotFoundError: No module named 'data'` when the `data` package is not present.

This file dynamically tries multiple import paths for each SECTION module:
 - "SECTION_X" (module in the same directory)
 - "data.SECTION_X" (module inside a `data` package)
 - If import succeeds, it tries to get the expected attribute (e.g. `section_1`).
 - If the expected attribute name isn't found, it searches the module for any
   variable that starts with `section_` and uses that as a fallback.

It also prints a friendly summary and provides minimal runtime checks (safe to run
in environments where some SECTION modules are missing).

If you want stricter behaviour (fail fast when a section is missing), replace the
`warn_only=True` to `False` in the loader call below.
"""

from importlib import import_module
import sys
import types
from typing import Dict, Any, List, Tuple


def try_import_section(module_basename: str, expected_attr: str, warn_only: bool = True) -> Tuple[str, Any]:
    """
    Try to import a module and return the desired attribute value.

    Attempts these module paths, in order:
      1) module_basename (e.g. 'SECTION_1')
      2) 'data.' + module_basename (e.g. 'data.SECTION_1')

    If import succeeds but the expected attribute isn't present, it will try to
    locate any attribute in the module whose name starts with 'section_'.

    Returns (module_path_used, attribute_value) on success, or (None, None) on failure.
    If warn_only is False, raises ModuleNotFoundError or AttributeError on failure.
    """
    tried = []
    candidates = [module_basename, f"data.{module_basename}"]

    for modpath in candidates:
        tried.append(modpath)
        try:
            mod = import_module(modpath)
        except ModuleNotFoundError:
            # continue trying other candidate paths
            continue
        except Exception as e:
            # Other import errors (syntax, etc.) should be raised unless warn_only
            if not warn_only:
                raise
            print(f"⚠️ Warning: import failed for {modpath} — {e}")
            continue

        # If we reach here, module imported successfully
        # Try to get expected attribute
        if hasattr(mod, expected_attr):
            return modpath, getattr(mod, expected_attr)

        # Fallback: look for any attribute starting with 'section_'
        for name in dir(mod):
            if name.startswith('section_'):
                return modpath, getattr(mod, name)

        # No suitable attribute found
        if not warn_only:
            raise AttributeError(f"Module '{modpath}' imported but has no attribute '{expected_attr}' and no 'section_*' fallback.")
        print(f"⚠️ Warning: module '{modpath}' imported but no '{expected_attr}' or 'section_*' found.")
        return modpath, None

    # All candidates failed
    if not warn_only:
        raise ModuleNotFoundError(f"Could not import any of: {tried}")
    print(f"⚠️ Warning: could not import any of: {tried}")
    return None, None


# Mapping of SECTION module basenames to expected attribute names
SECTION_MAP = {
    'SECTION_1': 'section_1',
    'SECTION_2': 'section_2',
    'SECTION_3': 'section_3',
    'SECTION_4': 'section_4',
    'SECTION_5': 'section_5',
    'SECTION_6': 'section_6',
    'SECTION_7': 'section_7',
    'SECTION_8': 'section_8',
    'SECTION_9': 'section_9',
    'SECTION_10': 'section_10',
    'SECTION_11': 'section_11',
    'SECTION_12': 'section_12',
    'SECTION_13': 'section_13',
    'SECTION_13_B': 'section_13_peace',
    'SECTION_15': 'section_15',
    'SECTION_16': 'section_16',
}

LOADED_SECTIONS: Dict[str, Any] = {}
FAILED_SECTIONS: List[str] = []

for mod_basename, attr_name in SECTION_MAP.items():
    modpath, value = try_import_section(mod_basename, attr_name, warn_only=True)
    if modpath is None or value is None:
        FAILED_SECTIONS.append(mod_basename)
    else:
        LOADED_SECTIONS[mod_basename] = value

# Build ALL_SHLOKAS list in the expected order. Keep missing entries out but note them.
ALL_SHLOKAS: List[Any] = []
for mod_basename in SECTION_MAP.keys():
    if mod_basename in LOADED_SECTIONS:
        ALL_SHLOKAS.append(LOADED_SECTIONS[mod_basename])

# Backward compatibility alias
PROBLEM_SECTIONS = ALL_SHLOKAS

if __name__ == '__main__':
    print("🔢 Current Sections Loaded:", len(ALL_SHLOKAS))
    if FAILED_SECTIONS:
        print("⚠️ The following sections could not be loaded:", FAILED_SECTIONS)
        print("Tip: Ensure the SECTION_X modules exist either in the same directory or inside a 'data' package.")
    else:
        print("✅ All sections loaded successfully.")

    # Minimal sanity checks / examples (safe if modules are missing)
    if ALL_SHLOKAS:
        # Show first entry's keys to help debugging
        first = ALL_SHLOKAS[0]
        print("\nFirst loaded section type:", type(first))
        # If it's a dict-like mapping, show its top-level keys
        try:
            if isinstance(first, dict):
                print("Top-level keys in first section:", list(first.keys())[:5])
            elif isinstance(first, list):
                print("First section is a list with length:", len(first))
        except Exception:
            pass
    else:
        print("No sections available to introspect. Create the SECTION_X modules or adjust the loader.")

# Exports for external use
__all__ = ['ALL_SHLOKAS', 'PROBLEM_SECTIONS', 'LOADED_SECTIONS', 'FAILED_SECTIONS']
