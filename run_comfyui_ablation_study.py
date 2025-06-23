import shutil
from pathlib import Path
from urllib import request
import json
import os
import copy
import time

''' DECLARACIONES'''
# Ruta al workflow por defecto
WORKFLOW_PATH = "user/default/workflows/Refacer_Testing_API.json"

# Carpetas de entrada y salida
INPUT_IMAGES_FOLDER = "inputs_refacer"
OUTPUT_IMAGES_FOLDER = "outputs_refacer"
OUTPUT_DEFAULT_FOLDER = "output"                # Carpeta por defecto donde se almacenan las imágenes
TEMP_WORKFLOW = "user/default/workflows/temp_pipeline.json"   # Pipeline temporal

# Gestión de resultados
MAX_WAIT_TIM_SEC = 300
CHECK_INTERVAL = 5

def safe_value_name(value):
    '''
    Adapta los valores para los nombres de las carpetas.

    :param value: valor a modificar
    :return: string modificado
    '''

    if isinstance(value, float):
        return str(value).replace(".", "_")
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return value.replace(" ", "-").replace(".", "_")
    elif isinstance(value, int):
        return str(value)
    else:
        return str(value)


def get_node_ids_by_class(pipeline, class_type):
    '''
    Devuelve los ids dado el string correspondiente al atributo "class_type" de un nodo.

    :param pipeline: diccionario del pipeline
    :param class_type: string que equivale al nombre del nodo
    :return: ids
    '''
    id = None
    for nids, node in pipeline.items():
        if node["class_type"] == class_type:
            id = nids
            break

    return id


def bypass_nodes(pipeline, target_class, replacement_class, destination_classes):
    '''
    Reemplaza en los nodos destino el id de target_class por el de replacement_class (NO está optimizado para eliminar el nodo silenciado).

    :param pipeline: diccionario del pipeline a modificar
    :param target_class: atributo "class_type" del nodo al cual se le aplica el bypass
    :param replacement_class: atributo "class_type" del nodo que debe sustituir al nodo al que se le aplica el bypass
    :param destination_classes: atributos "class_type" de los nodos destino que deben modificar el id del nodo eliminado
    :param remove: si al hacer bypass se elimina el nodo del flujo o se queda desconectado (con o sin, hay formas más óptimas)
    :return: pipeline modificado
    '''

    # Obtener los ids de los nodos por clase
    target_id = get_node_ids_by_class(pipeline, target_class)
    replacement_id = get_node_ids_by_class(pipeline, replacement_class)
    destination_ids = []
    for nid, node in pipeline.items():
        if node["class_type"] in destination_classes:
            destination_ids.append(nid)

    # Comprobar si se han encontrado los ids
    if not target_id or not replacement_id or not destination_ids:
        raise ValueError(f"No se encontraron los nodos para:{target_class} o {replacement_class} o {destination_classes}")

    print(f" Bypass de {target_class} iniciado: (target {target_id}, replacement {replacement_class}, destinations {destination_classes}")

    # Iterar sobre cada nodo destino para modificar el id antiguo
    for dest_id in destination_ids:
        # Obtener los campos inputs de ese nodo
        inputs = pipeline[dest_id].get("inputs", {})
        # Iterar sobre cada input hasta encontrar el atributo que se pretende modificar
        for input_name, val in inputs.items():
            if isinstance(val, list) and val[0] == target_id:
                new_val = [replacement_id, val[1]] # Ej: ["6", 1] -> ["13", 1]
                pipeline[dest_id]["inputs"][input_name] = new_val

    print(f" Bypass de {target_class} finalizado: (target {target_id}, replacement {replacement_class}, destinations {destination_classes}")
    return pipeline


def clear_prompt_in_node(pipeline, class_type):
    '''
    Reemplaza el atributo text, de los nodos PhotoMakerEncode y ClipTextEncode para emular un bypass.

    :param pipeline: diccionario del pipeline a modificar
    :param class_type: nombre del nodo al que se desea aplicar la modificación
    :return: pipeline modificado
    '''
    # Campo a modificar
    field = "text"

    # Encontrar el nodo
    for node_id, node in pipeline.items():
        if node["class_type"] == class_type and field in node.get("inputs", {}):
            print(f"Limpieza del campo '{field}' en nodo {node_id} ({class_type})")
            node["inputs"][field] = ""

    return pipeline


def set_multiple_params_by_class(pipeline, class_type, param_value_dict):
    '''
    Modifica uno o varios parámetros del primer nodo encontrado con el class_type especificado.

    :param pipeline: diccionario del pipeline a modificar
    :param class_type: string con el class_type del nodo objetivo
    :param param_value_dict: diccionario con los parámetros a modificar
    :return: pipeline modificado
    '''

    found = False
    # Iterar para buscar el nodo objetivo
    for node_id, node in pipeline.items():
        # Comprobar si es el mismo "class_type"
        if node.get("class_type") == class_type:
            found = True
            # Iterar para cada parámetro a modificar
            for param, value in param_value_dict.items():
                # Asegurarse de que el parámetro está presente
                if param in node.get("inputs", {}):
                    print(f"Modificando nodo {node_id} ({class_type} -> {param} = {value})")
                    node["inputs"][param] = value
                else:
                    print(f"Nodo {node_id} ({class_type} no tiene el parámetro '{param}'")

    if not found:
        print(f"No se encontró ningún nodo con class_type '{class_type}'")

    return pipeline

# Pruebas del estudio de ablación
ABLATION_TESTS = [
    # Ablación estructural (bypass)
    ("bypass", "CLIPTextEncode", lambda p: clear_prompt_in_node(p, "CLIPTextEncode")),
    ("bypass", "PhotoMakerEncode", lambda p: clear_prompt_in_node(p, "PhotoMakerEncode")),
    ("bypass", "AutoCropFaces", lambda p: bypass_nodes(p, target_class="AutoCropFaces", replacement_class="LoadImage", destination_classes=["PhotoMakerEncode", "PreviewImage", "PrepImageForClipVision"])),
    ("bypass", "TGateApply", lambda p: bypass_nodes(p, target_class="TGateApplySimple", replacement_class="LoraLoaderModelOnly", destination_classes=["IPAdapterAdvanced"])),
    ("bypass", "PrepImageForClipVision", lambda p: bypass_nodes(p, target_class="PrepImageForClipVision", replacement_class="AutoCropFaces", destination_classes=["IPAdapterAdvanced"])),
    ("bypass", "LoraLoaderModelOnly", lambda p: bypass_nodes(p, target_class="LoraLoaderModelOnly", replacement_class="CheckpointLoaderSimple", destination_classes=["TGateApplySimple"])),
    ("bypass", "IPAdapterAdvanced", lambda p: bypass_nodes(p, target_class="IPAdapterAdvanced", replacement_class="TGateApplySimple", destination_classes=["KSamplerAdvanced"])),


    # Ablación paramétrica
    # AutoCropFaces - aspect_ratio
    ("parameters", "AutoCropFaces", {"aspect_ratio": "2:3"}),
    ("parameters", "AutoCropFaces", {"aspect_ratio": "3:2"}),
    ("parameters", "AutoCropFaces", {"aspect_ratio": "4:3"}),
    ("parameters", "AutoCropFaces", {"aspect_ratio": "9:16"}),
    ("parameters", "AutoCropFaces", {"aspect_ratio": "16:9"}),

    # AutoCropFaces - scale_factor
    ("parameters", "AutoCropFaces", {"scale_factor": 0.5}),
    ("parameters", "AutoCropFaces", {"scale_factor": 1.0}),
    ("parameters", "AutoCropFaces", {"scale_factor": 1.5}),
    ("parameters", "AutoCropFaces", {"scale_factor": 2.0}),
    ("parameters", "AutoCropFaces", {"scale_factor": 2.5}),
    ("parameters", "AutoCropFaces", {"scale_factor": 3.0}),
    ("parameters", "AutoCropFaces", {"scale_factor": 5.0}),
    ("parameters", "AutoCropFaces", {"scale_factor": 10.0}),

    # AutoCropFaces - shift_factor
    ("parameters", "AutoCropFaces", {"shift_factor": 0.00}),
    ("parameters", "AutoCropFaces", {"shift_factor": 0.25}),
    ("parameters", "AutoCropFaces", {"shift_factor": 0.75}),
    ("parameters", "AutoCropFaces", {"shift_factor": 1.00}),

    # IPAdapterAdvanced - embeds_scaling
    ("parameters", "IPAdapterAdvanced", {"embeds_scaling": "V only"}),
    ("parameters", "IPAdapterAdvanced", {"embeds_scaling": "K+V w/ C penalty"}),
    ("parameters", "IPAdapterAdvanced", {"embeds_scaling": "K+mean(V) w/ C penalty"}),

    # IPAdapterAdvanced - start_at + end_at
    ("parameters", "IPAdapterAdvanced", {"start_at": 0.00, "end_at": 0.10}),
    ("parameters", "IPAdapterAdvanced", {"start_at": 0.00, "end_at": 0.50}),
    ("parameters", "IPAdapterAdvanced", {"start_at": 0.25, "end_at": 0.75}),
    ("parameters", "IPAdapterAdvanced", {"start_at": 0.50, "end_at": 1.00}),

    # IPAdapterAdvanced - weight
    ("parameters", "IPAdapterAdvanced", {"weight": -1.00}),
    ("parameters", "IPAdapterAdvanced", {"weight": -0.50}),
    ("parameters", "IPAdapterAdvanced", {"weight": -0.40}),
    ("parameters", "IPAdapterAdvanced", {"weight": -0.30}),
    ("parameters", "IPAdapterAdvanced", {"weight": -0.20}),
    ("parameters", "IPAdapterAdvanced", {"weight": -0.10}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.10}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.20}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.30}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.40}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.50}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.60}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.70}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.80}),
    ("parameters", "IPAdapterAdvanced", {"weight": 0.90}),
    ("parameters", "IPAdapterAdvanced", {"weight": 1.00}),
    ("parameters", "IPAdapterAdvanced", {"weight": 1.50}),
    ("parameters", "IPAdapterAdvanced", {"weight": 2.00}),
    ("parameters", "IPAdapterAdvanced", {"weight": 2.50}),
    ("parameters", "IPAdapterAdvanced", {"weight": 3.00}),
    ("parameters", "IPAdapterAdvanced", {"weight": 3.50}),
    ("parameters", "IPAdapterAdvanced", {"weight": 4.00}),
    ("parameters", "IPAdapterAdvanced", {"weight": 4.50}),
    ("parameters", "IPAdapterAdvanced", {"weight": 5.00}),

    # SDXL - aspect_ratio
    ("parameters", "SDXLAspectRatioSelector", {"aspect_ratio": "1:1"}),
    ("parameters", "SDXLAspectRatioSelector", {"aspect_ratio": "2:3"}),
    ("parameters", "SDXLAspectRatioSelector", {"aspect_ratio": "3:4"}),
    ("parameters", "SDXLAspectRatioSelector", {"aspect_ratio": "9:16"}),
    ("parameters", "SDXLAspectRatioSelector", {"aspect_ratio": "16:9"}),
    ("parameters", "SDXLAspectRatioSelector", {"aspect_ratio": "21:9"}),

    # TGateApply - start_at
    ("parameters", "TGateApplySimple", {"start_at": 0.05}),
    ("parameters", "TGateApplySimple", {"start_at": 0.10}),
    ("parameters", "TGateApplySimple", {"start_at": 0.25}),
    ("parameters", "TGateApplySimple", {"start_at": 0.33}),
    ("parameters", "TGateApplySimple", {"start_at": 0.50}),
    ("parameters", "TGateApplySimple", {"start_at": 0.66}),
    ("parameters", "TGateApplySimple", {"start_at": 0.75}),
    ("parameters", "TGateApplySimple", {"start_at": 0.90}),
    ("parameters", "TGateApplySimple", {"start_at": 1.00}),

    # KSamplerAdvanced - cfg
    ("parameters", "KSamplerAdvanced", {"cfg": 1}),
    ("parameters", "KSamplerAdvanced", {"cfg": 2}),
    ("parameters", "KSamplerAdvanced", {"cfg": 3}),
    ("parameters", "KSamplerAdvanced", {"cfg": 4}),
    ("parameters", "KSamplerAdvanced", {"cfg": 5}),
    ("parameters", "KSamplerAdvanced", {"cfg": 6}),
    ("parameters", "KSamplerAdvanced", {"cfg": 7}),
    ("parameters", "KSamplerAdvanced", {"cfg": 8}),
    ("parameters", "KSamplerAdvanced", {"cfg": 9}),
    ("parameters", "KSamplerAdvanced", {"cfg": 10}),
    ("parameters", "KSamplerAdvanced", {"cfg": 11}),
    ("parameters", "KSamplerAdvanced", {"cfg": 12}),
    ("parameters", "KSamplerAdvanced", {"cfg": 13}),
    ("parameters", "KSamplerAdvanced", {"cfg": 14}),
    ("parameters", "KSamplerAdvanced", {"cfg": 15}),
    ("parameters", "KSamplerAdvanced", {"cfg": 20}),
    ("parameters", "KSamplerAdvanced", {"cfg": 30}),
    ("parameters", "KSamplerAdvanced", {"cfg": 40}),
    ("parameters", "KSamplerAdvanced", {"cfg": 50}),
    ("parameters", "KSamplerAdvanced", {"cfg": 100}),

    # KSamplerAdvanced - noise_seed
    ("parameters", "KSamplerAdvanced", {"noise_seed": 11}),
    ("parameters", "KSamplerAdvanced", {"noise_seed": 42}),
    ("parameters", "KSamplerAdvanced", {"noise_seed": 1234}),
    ("parameters", "KSamplerAdvanced", {"noise_seed": 9999}),

    # KSamplerAdvanced - steps
    ("parameters", "KSamplerAdvanced", {"steps": 1}),
    ("parameters", "KSamplerAdvanced", {"steps": 2}),
    ("parameters", "KSamplerAdvanced", {"steps": 3}),
    ("parameters", "KSamplerAdvanced", {"steps": 4}),
    ("parameters", "KSamplerAdvanced", {"steps": 5}),
    ("parameters", "KSamplerAdvanced", {"steps": 6}),
    ("parameters", "KSamplerAdvanced", {"steps": 7}),
    ("parameters", "KSamplerAdvanced", {"steps": 8}),
    ("parameters", "KSamplerAdvanced", {"steps": 9}),
    ("parameters", "KSamplerAdvanced", {"steps": 10}),
    ("parameters", "KSamplerAdvanced", {"steps": 11}),
    ("parameters", "KSamplerAdvanced", {"steps": 12}),
    ("parameters", "KSamplerAdvanced", {"steps": 13}),
    ("parameters", "KSamplerAdvanced", {"steps": 14}),
    ("parameters", "KSamplerAdvanced", {"steps": 15}),
    ("parameters", "KSamplerAdvanced", {"steps": 20}),
    ("parameters", "KSamplerAdvanced", {"steps": 30}),
    ("parameters", "KSamplerAdvanced", {"steps": 50}),
    ("parameters", "KSamplerAdvanced", {"steps": 75}),
    ("parameters", "KSamplerAdvanced", {"steps": 100}),

    # LoraLoaderModelOnly - strength_model
    ("parameters", "LoraLoaderModelOnly", {"strength_model": -1.00}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": -0.50}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 0.00}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 0.30}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 0.50}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 0.66}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 1.00}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 1.30}),
    ("parameters", "LoraLoaderModelOnly", {"strength_model": 1.50}),

    # PhotoMakerEncode
    ("parameters", "PhotoMakerEncode", {"text": "A professional HDR photograph of photomaker person in full colour.",}),
    ("parameters", "PhotoMakerEncode", {"text": "cinematic film quality photorealism, clear photo, amazing textures, sharp focus, high-contrast, stunning professionalism,",})
]


''' ACCIONES '''
def main():
    # Crear carpeta de salida si no existe
    os.makedirs(OUTPUT_IMAGES_FOLDER, exist_ok=True)

    # Cargar el pipeline base
    f = open(WORKFLOW_PATH, "r")
    base_pipeline = json.load(f)

    # Detectar el nodo LoadImage (Nodo de carga inicial e input del pipeline)
    load_image_node_id = None
    for node_id, node in base_pipeline.items():
        if node["class_type"] == "LoadImage":
            load_image_node_id = node_id
            break   # Finalizar si se ha encontrado

    # Detectar el nodo SaveImage (Nodo de salida, output del pipeline)
    save_image_node_id = None
    for node_id, node in base_pipeline.items():
        if node["class_type"] == "SaveImage":
            save_image_node_id = node_id
            break  # Finalizar si se ha encontrado

    # Comprobar que se ha encontrado el nodo LoadImage
    if load_image_node_id is None:
        raise ValueError("No se encontró el nodo LoadImage")

    # Obtener la lista de imágenes de entrada
    input_images = []
    for img in os.listdir(INPUT_IMAGES_FOLDER):
        if img.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            input_images.append(img)
    expected_count = len(input_images)

    # Iterar sobre todas las pruebas
    for test_type, node_name, data in ABLATION_TESTS:

        # Comprobar el tipo de test
        if test_type == "parameters":
            # Establecer la ruta de la carpeta de salida
            if len(data) == 1:
                key = list(data.keys())[0]
                value = safe_value_name(data[key])

                # Reemplazar ":" solo en los nombres de carpetas
                if key == "aspect_ratio":
                    value = value.replace(":", "x")

                output_folder = Path(OUTPUT_IMAGES_FOLDER) / "parameters" / node_name / key / value
            else:
               parts = [f"{k}={safe_value_name(v)}" for k, v in data.items()]

               # Reemplazar ":" solo en los nombres de carpetas
               parts = [p.replace(":", "x") if "aspect_ratio" in p else p for p in parts]

               test_name = "combination_" + "__".join(parts)
               output_folder = Path(OUTPUT_IMAGES_FOLDER) / "parameters" / node_name / test_name

        elif test_type == "bypass":
            # Establecer la ruta de la carpeta de salida
            output_folder = Path(OUTPUT_IMAGES_FOLDER) / "bypass" / node_name
        else:
            raise ValueError(f"No se encontró el tipo de prueba {test_type}")

        # Crear carpeta de salida
        output_folder.mkdir(parents=True, exist_ok=True)

        # Iterar para todas las imágenes
        for image_name in input_images:

            # Obtener ruta de la imagen y clonar el pipeline
            image_path = os.path.abspath(os.path.join(INPUT_IMAGES_FOLDER, image_name))
            pipeline = copy.deepcopy(base_pipeline)

            # Obtener nombre base (sin extensión)
            base_image_name = Path(image_name).stem

            # Establecer imagen de entrada en LoadImage
            pipeline[load_image_node_id]["inputs"]["image"] = image_path

            # Establecer el prefijo de salida en SaveImage
            pipeline[save_image_node_id]["inputs"]["filename_prefix"] = base_image_name

            # Aplicar modificación
            if test_type == "parameters":
                pipeline = set_multiple_params_by_class(pipeline, node_name, data)
            elif test_type == "bypass":
                pipeline = data(pipeline)
            else:
                raise ValueError(f"Tipo de test no encontrado {test_type}")

            # Enviar el workflow al servidor de ComfyUI
            p = {"prompt": pipeline}
            payload = json.dumps(p).encode('utf-8')
            req = request.Request("http://IP/prompt", data=payload) # Quitado por privacidad
            response = request.urlopen(req)
            print(response.read().decode())

        # Esperar hasta que se generen las imágenes
        start_time = time.time()
        print("Esperando a que se generen todas las imagenes...")

        generated_files = set()
        while True:
            # Buscar nuevos archivos generados
            for f in os.listdir(OUTPUT_DEFAULT_FOLDER):
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    generated_files.add(f)

            if len(generated_files) >= expected_count:
                print("Todas las imágenes generadas, moviendo archivos...")
                break

            elapsed_time = time.time() - start_time
            if elapsed_time > MAX_WAIT_TIM_SEC:
                print("Tiempo máximo de espera alcanzado")
                break

            time.sleep(CHECK_INTERVAL)

        # Iterar sobre las imágenes generadas
        for generated_file in os.listdir(OUTPUT_DEFAULT_FOLDER):
            if not generated_file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue # Ignorar archivos no válidos

            # Obtener ruta de origen y destino
            origin = os.path.join(OUTPUT_DEFAULT_FOLDER, generated_file)
            destination = output_folder / generated_file

            # Mover la imagen
            shutil.move(origin, destination)
            print(f"Imagen movida: {generated_file} -> {destination}")

if __name__ == "__main__":
    main()
    