from pymatgen.ext.matproj import MPRester

API_KEY = "your_key"  #  Materials Project's API Key
mpr = MPRester(API_KEY)

print("[OK] Start downloading!")

# download Al2O3 CIF（Corundum）
al2o3_structure = mpr.get_structure_by_material_id("mp-1143")
al2o3_structure.to(filename="Al2O3_mp-1143.cif")

# download ZnO CIF（Zincite）
zno_structure = mpr.get_structure_by_material_id("mp-2133")
zno_structure.to(filename="ZnO_mp-2133.cif")

print("[OK] CIF saved：Al2O3_mp-1143.cif & ZnO_mp-2133.cif")
