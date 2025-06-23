import os
import matplotlib.pyplot as plt
from PIL import Image
import re
from pathlib import Path

''' DECLARACIONES '''
base_path = Path("../../TFG")
parameters_path = base_path / "data" / "parameters"
output_path = base_path / "graphics" / "parameters"
output_path.mkdir(parents=True, exist_ok=True)

# Nodos con tratamiento especial
nodos_combinados = {"cliptextencode", "photomakerencode"}

# Funciones auxiliares
def extraer_retrato(nombre_archivo):
    '''
    Extrae el nombre del retrato a partir del nombre de un archivo dado.
    :param nombre_archivo: Nombre del archivo
    :return: string con el nombre del retrato
    '''
    for p in ["obama", "vangogh", "fridakahlo", "jovenperla"]:
        if p in nombre_archivo.lower():
            return p
    return "otro"

def extraer_valor_parametro(nombre_archivo, parametro):
    '''
    Extrae el valor del parámetro de un nombre de archivo. La lógica de extracción varía según el tipo de parámetro.
    :param nombre_archivo: nombre completo del archivo
    :param parametro: nombre del parámetro a extraer
    :return: valor del parametro extraído (string, int, float, etc)
    '''

    # Extraer el nombre base del archivo sin extensión
    nombre = os.path.splitext(os.path.basename(nombre_archivo))[0]

    # Lógica según el tipo de parámetro
    if "aspect_ratio" in parametro.lower():
        match = re.search(r"(\d+)_(\d+)", nombre)
        return f"{match.group(1)}:{match.group(2)}" if match else "invalid"

    if "startat_endat_returnwith" in parametro.lower():
        match = re.search(r"startat_(\d+(?:_\d+)?)_endat_(\d+(?:_\d+)?)_returnwith_([a-zA-Z]+)", nombre)
        if match:
            start = match.group(1).replace("_", ".")
            end = match.group(2).replace("_", ".")
            return f"{start}→{end}\n{match.group(3)}"
        return "invalid"

    if "samplername_scheduler" in parametro.lower():
        match = re.search(r"samplername_([a-zA-Z0-9]+)_scheduler_([a-zA-Z0-9]+)", nombre)
        return f"{match.group(1)}\n{match.group(2)}" if match else "invalid"

    if "startat_endat" in parametro.lower():
        match = re.search(r"startat_(\d+(?:_\d+)?)_endat_(\d+(?:_\d+)?)", nombre)
        if match:
            start = match.group(1).replace("_", ".")
            end = match.group(2).replace("_", ".")
            return f"{start}→{end}"
        return "invalid"

    if "minus_" in nombre:
        nombre = nombre.replace("minus_", "-")

    # Reemplazar guiones bajos por puntos
    nombre = nombre.replace("_", ".")

    # Extraer el último número del nombre del archivo
    match = re.findall(r"-?\d+(?:\.\d+)?", nombre)
    if match:
        valor = match[-1]
        return float(valor) if "." in valor else int(valor)

    # Si no se encuentra un número, intenta extraer el texto después del nombre del parámetro.
    after_param = nombre.split(parametro)[-1].strip("_").lower()
    return after_param if after_param else nombre.split("_")[-1].lower()

def clave_orden(valor):
    '''

    :param valor: valor del parámetro a ordenar.
    :return: tupla empleada como clave para el ordenamiento.
            (0, valor_numérico) para números,
            (1, primer_num_aspect_ratio) para relaciones de aspecto,
            (2, string_valor) para otros strings.
    '''
    if isinstance(valor, (float, int)):
        return (0, float(valor))
    if isinstance(valor, str) and ":" in valor:
        try:
            return (1, int(valor.split(":")[0]))
        except:
            return (1, valor)
    return (2, str(valor))


''' ACCIONES '''
# Iterar sobre cada directorio
for nodo in sorted(os.listdir(parameters_path)):
    nodo_path = parameters_path / nodo
    # Saltar si no es un directorio
    if not nodo_path.is_dir():
        continue

    # Nodos especiales
    if nodo.lower() in nodos_combinados:
        # Diccionario para almacenar las imágenes por valor de parámetro
        columnas = {}
        # Iterar sobre los subdirectorios dentro del nodo combinado
        for subdir in sorted(os.listdir(nodo_path)):
            sub_path = nodo_path / subdir
            if not sub_path.is_dir():
                continue
            # Buscar imágenes dentro de cada subdirectorio
            for fname in sorted(os.listdir(sub_path)):
                if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    # Extraer el tipo de retrato y almacenar la ruta de la imagen
                    retrato = extraer_retrato(fname)
                    columnas.setdefault(subdir, {})[retrato] = sub_path / fname

        # Ordenar las columnas usando la clave de ordenamiento
        sorted_columnas = sorted(columnas.items(), key=lambda x: clave_orden(x[0]))
        # Obtener todos los nombres de retratos únicos dentro de la imagen
        retratos = sorted({r for col in columnas.values() for r in col})

        # Configurar plot
        fig, axes = plt.subplots(
            nrows=len(retratos), ncols=len(sorted_columnas),
            figsize=(3.2 * len(sorted_columnas), 3.2 * len(retratos)),
            constrained_layout=True
        )

        if len(retratos) == 1:
            axes = [axes]
        if len(sorted_columnas) == 1:
            axes = [[row] for row in axes]

        # Iterar sobre las columnas y filas para colocar cada imagen en su posición
        for col_idx, (valor, retrato_dict) in enumerate(sorted_columnas):
            for row_idx, retrato in enumerate(retratos):
                ax = axes[row_idx][col_idx]
                img_path = retrato_dict.get(retrato)
                if img_path:
                    ax.imshow(Image.open(img_path))
                ax.axis("off")

        # Establecer los títulos de las columnas
        for col_idx, (valor, _) in enumerate(sorted_columnas):
            axes[0][col_idx].set_title(str(valor), fontsize=11, fontweight="bold", pad=10)

        # Guardar la imagen generada
        output_file = output_path / f"{nodo}_completo.png"
        plt.savefig(str(output_file), dpi=300, bbox_inches="tight", facecolor="white")
        plt.close()
        print(f" Tabla combinada para {nodo} guardada: {output_file}")

    else: # Nodos con parámetros individuales
        # Iterar sobre cada subdirectorio
        for parametro in sorted(os.listdir(nodo_path)):
            param_path = nodo_path / parametro
            if not param_path.is_dir():
                continue
            # Diccionario para almacenar las imágenes por valor de parámetro y retrato
            columnas = {}
            # Iterar sobre los archivos de imagen dentro del directorio del parámetro
            for fname in sorted(os.listdir(param_path)):
                if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                    retrato = extraer_retrato(fname)
                    valor = extraer_valor_parametro(fname, parametro)
                    # Almacenar la ruta de la imagen, indexada por el valor del parámetro y el nombre del retrato
                    columnas.setdefault(valor, {})[retrato] = param_path / fname

            # Intentar ordenar las columnas
            try:
                sorted_columnas = sorted(columnas.items(), key=lambda x: clave_orden(x[0]))
            except Exception as e:
                print(f" Error al ordenar columnas en {nodo}/{parametro}: {e}")
                continue

            # Obtener todos los nombres de todos los retratos únicos presentes
            retratos = sorted({r for col in columnas.values() for r in col})

            # Configurar plot
            fig, axes = plt.subplots(
                nrows=len(retratos), ncols=len(sorted_columnas),
                figsize=(3.2 * len(sorted_columnas), 3.2 * len(retratos)),
                constrained_layout=True
            )

            if len(retratos) == 1:
                axes = [axes]
            if len(sorted_columnas) == 1:
                axes = [[row] for row in axes]

            # Iterar sobre las columnas y las filas para colocar cada imagen
            for col_idx, (valor, retrato_dict) in enumerate(sorted_columnas):
                for row_idx, retrato in enumerate(retratos):
                    ax = axes[row_idx][col_idx]
                    img_path = retrato_dict.get(retrato)
                    if img_path:
                        ax.imshow(Image.open(img_path))
                    ax.axis("off")
            # Establecer los títulos de las columnas
            for col_idx, (valor, _) in enumerate(sorted_columnas):
                titulo = f"{valor:.2f}" if isinstance(valor, float) else str(valor)
                axes[0][col_idx].set_title(titulo, fontsize=12, fontweight="bold", pad=10)

            # Guardar la figura
            filename_safe = f"{nodo}_{parametro}".replace(":", "_")
            output_file = output_path / f"{filename_safe}.png"
            plt.savefig(str(output_file), dpi=300, bbox_inches="tight", facecolor="white")
            plt.close()
            print(f" Tabla para {nodo}/{parametro} guardada en: {output_file}")
