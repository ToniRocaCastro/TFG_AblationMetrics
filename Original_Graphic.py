import os
import matplotlib.pyplot as plt
from PIL import Image

''' DECLARACIONES '''
base_path = "../../TFG"
reference_path = os.path.join(base_path, "images")
generated_path = os.path.join(base_path, "data", "original")
output_path = os.path.join(base_path, "graphics/original")
os.makedirs(output_path, exist_ok=True)

''' ACCIONES '''
# Cargar imágenes
reference_images = sorted([
    os.path.join(reference_path, f)
    for f in os.listdir(reference_path)
    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
])

generated_images = sorted([
    os.path.join(generated_path, f)
    for f in os.listdir(generated_path)
    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
])

num_images = min(len(reference_images), len(generated_images))
if num_images == 0:
    raise ValueError("No hay imágenes válidas.")

# Crear figura
fig, axes = plt.subplots(
    nrows=2, ncols=num_images,
    figsize=(3.2 * num_images, 5.5),
    constrained_layout=True
)

# Insertar imágenes
for i in range(num_images):
    axes[0, i].imshow(Image.open(reference_images[i]))
    axes[1, i].imshow(Image.open(generated_images[i]))
    axes[0, i].axis("off")
    axes[1, i].axis("off")

# Añadir etiquetas directamente a los ejes de la primera columna
axes[0, 0].text(
    -0.25, 0.5, "Imagen de referencia",
    fontsize=14, fontweight="bold",
    ha="right", va="center", transform=axes[0, 0].transAxes
)
axes[1, 0].text(
    -0.25, 0.5, "Resultado generado",
    fontsize=14, fontweight="bold",
    ha="right", va="center", transform=axes[1, 0].transAxes
)

# Guardar imagen final sin mostrarla
output_file = os.path.join(output_path, "comparativa_referencia_vs_generada.png")
plt.savefig(output_file, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()  # Cerramos explícitamente la figura

print(f" Imagen final guardada sin mostrar en: {output_file}")
