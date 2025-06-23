import os
import matplotlib.pyplot as plt
from PIL import Image

''' DECLARACIONES '''
base_path = "../../TFG"
original_path = os.path.join(base_path, "data", "original")
bypass_base_path = os.path.join(base_path, "data", "bypass")
output_base = os.path.join(base_path, "graphics")
output_path = os.path.join(output_base, "bypass")
os.makedirs(output_path, exist_ok=True)

''' ACCIONES '''
# Cargar imágenes originales
original_images = sorted([
    os.path.join(original_path, f)
    for f in os.listdir(original_path)
    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
])

# Cargar carpetas de bypass
bypass_cases = sorted([
    d for d in os.listdir(bypass_base_path)
    if os.path.isdir(os.path.join(bypass_base_path, d))
])

# Cargar todas las imágenes de cada caso de bypass
bypass_images_dict = {}
for case in bypass_cases:
    folder = os.path.join(bypass_base_path, case)
    imgs = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    bypass_images_dict[case] = imgs

# Crear figura general (todos los bypass juntos)
fig, axes = plt.subplots(
    nrows=len(original_images), ncols=len(bypass_cases) + 1,
    figsize=(3.5 * (len(bypass_cases) + 1), 3.2 * len(original_images)),
    constrained_layout=True
)

column_titles = ["Original"] + [case.replace("_", " ") for case in bypass_cases]
for ax, title in zip(axes[0], column_titles):
    ax.set_title(title, fontsize=15, fontweight='bold', pad=12)

for i, orig_path in enumerate(original_images):
    axes[i, 0].imshow(Image.open(orig_path))
    axes[i, 0].axis("off")
    for j, case in enumerate(bypass_cases):
        if i < len(bypass_images_dict[case]):
            axes[i, j + 1].imshow(Image.open(bypass_images_dict[case][i]))
        axes[i, j + 1].axis("off")

#  Guardar figura general
output_general = os.path.join(output_path, "tabla_bypass_completa.png")
plt.savefig(output_general, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Tabla general guardada en: {output_general}\n")

# Generar una imagen horizontal por cada nodo bypass
for case in bypass_cases:
    fig, axes = plt.subplots(
        nrows=2, ncols=len(original_images),
        figsize=(3.2 * len(original_images), 6),
        constrained_layout=True
    )

    for i, orig_path in enumerate(original_images):
        axes[0, i].imshow(Image.open(orig_path))
        axes[0, i].axis("off")
        axes[1, i].imshow(Image.open(bypass_images_dict[case][i]))
        axes[1, i].axis("off")

    for ax in axes[0]:
        ax.set_title("Original", fontsize=13, fontweight="bold", pad=8)
    for ax in axes[1]:
        ax.set_title(case.replace("_", " "), fontsize=13, fontweight="bold", pad=8)

    filename = f"comparativa_{case}_horizontal.png"
    output_case = os.path.join(output_path, filename)
    plt.savefig(output_case, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Comparativa horizontal individual guardada: {output_case}")
