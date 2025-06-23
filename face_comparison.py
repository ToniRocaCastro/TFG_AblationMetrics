import argparse
import cv2 as cv
import os
import csv
import re

''' DECLARACIONES'''
def str2bool(v):
    '''
    Devuelve un valor booleano en función del string proporcionado por parámetro.

    :param v: string que se quiere convertir a booleano
    :return: valore booleano del string proporcionado
    '''
    if v.lower() in ['on', 'yes', 'true', 'y', 't']:
        return True
    elif v.lower() in ['off', 'no', 'false', 'n', 'f']:
        return False
    else:
        raise NotImplementedError

# Configurar argumentos
parser = argparse.ArgumentParser()
parser.add_argument('--generated_dir', type=str, help='Carpeta con las imágenes generadas (outputs_refacer)')
parser.add_argument('--real_dir', type=str, help='Carpeta con las imágenes reales (inputs_refacer_real)')
parser.add_argument('--output_csv', type=str, default='results_face_comparison.csv', help='Archivo de salida .csv')
parser.add_argument('--scale', '-sc', type=float, default=0.5, help='Scale factor used to resize input video frames.')
parser.add_argument('--face_detection_model', '-fd', type=str, default='./models/face_detection_yunet_2023mar.onnx', help='Path to the face detection model. Download the model at https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet')
parser.add_argument('--face_recognition_model', '-fr', type=str, default='./models/face_recognition_sface_2021dec.onnx', help='Path to the face recognition model. Download the model at https://github.com/opencv/opencv_zoo/tree/master/models/face_recognition_sface')
parser.add_argument('--score_threshold', type=float, default=0.9, help='Filtering out faces of score < score_threshold.')
parser.add_argument('--nms_threshold', type=float, default=0.3, help='Suppress bounding boxes of iou >= nms_threshold.')
parser.add_argument('--top_k', type=int, default=5000, help='Keep top_k bounding boxes before NMS.')
args = parser.parse_args()

''' ACCIONES '''
if __name__ == '__main__':
    target_size = 512
    failed_dir = "failed_images"
    os.makedirs(failed_dir, exist_ok=True)

    # Inicializar modelos
    detector = cv.FaceDetectorYN.create(
        args.face_detection_model,
        "",
        (target_size, target_size),
        args.score_threshold,
        args.nms_threshold,
        args.top_k
    )
    recognizer = cv.FaceRecognizerSF.create(args.face_recognition_model, "")

    # Pre-cargar las imágenes reales
    real_images = {}
    for real_file in os.listdir(args.real_dir):
        if real_file.endswith(('.webp', '.jpg', '.png', '.jpeg')):
            # Extraer el prefijo del archivo real
            prefix_match = re.match(r"([a-zA-Z_]+)_foto", real_file)
            if prefix_match:
                person_prefix = prefix_match.group(1)
                real_images[person_prefix] = os.path.normpath(os.path.join(args.real_dir, real_file))

    print(f"Cargadas {len(real_images)} imágenes reales.")

    # Crear archivo CSV para almacenar los resultados
    with open(args.output_csv, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(["Type", "Node", "Parameter", "Value", "Person", "Generated_Image_Path", "Real_Image_Path", "Cosine_Similarity", "L2_Distance", "Same_Identity"])

        # Crear archivo CSV para errores en la detección facial
        failed_csv = os.path.join(os.path.dirname(args.output_csv), "failed_images.csv")

        with open(failed_csv, mode='w', newline='') as fail_file:
            fail_writer = csv.writer(fail_file, delimiter=';')
            fail_writer.writerow(["Type", "Node", "Parameter", "Value", "Person", "Image_Path", "Image_Type"])

            # Recorrer las imágenes generadas
            for root, dirs, files in os.walk(args.generated_dir):
                for gen_file in files:
                    if gen_file.endswith(('.webp', '.jpg', '.png', '.jpeg')):
                        # Extraer prefijo para identificar a la persona
                        prefix_match = re.match(r"([a-zA-Z_]+)_retrato", gen_file)
                        if not prefix_match:
                            print(f"[WARN] No se pudo identificar a la persona para {gen_file}")
                            continue

                        person = prefix_match.group(1)

                        # Buscar la imagen real correspondiente
                        real_path = real_images.get(person)
                        if not real_path:
                            print(f"[WARN] No se encontró la imagen real para {person}, path: {real_path}")
                            continue


                        # Extraer estructura del path
                        path_parts = root.split(os.sep)
                        # Identificar si es bypass, normal o parameters
                        if "bypass" in path_parts:
                            prueba_tipo = "bypass"
                            node = path_parts[-1]
                            parameter = "N/A"
                            value = "N/A"
                        elif "parameters" in path_parts:
                            prueba_tipo = "parameters"

                            # Detectar si es un caso compuesto
                            if path_parts[-1].startswith("combination"):
                                # Compuesto
                                node = path_parts[-2]
                                #Extraer los parametros y los valores
                                param_string = path_parts[-1].replace("combination_", "")
                                pairs = param_string.split("__")
                                parameters = []
                                values = []
                                for pair in pairs:
                                    param, val = pair.split("=")
                                    parameters.append(param)
                                    values.append(val)
                                parameter = "|".join(parameters)
                                value = "|".join(values)
                            else:
                                # Simple
                                node = path_parts[-3]
                                parameter = path_parts[-2]
                                value = path_parts[-1]

                        else:
                            # Ignorar otros directorios
                            prueba_tipo = "N/A"
                            node = "N/A"
                            parameter = "N/A"
                            value = "N/A"

                        # Cargar imágenes
                        gen_path = os.path.normpath(os.path.join(root, gen_file))
                        print(f'{gen_path} \n')
                        img1 = cv.imread(real_path)
                        img2 = cv.imread(gen_path)

                        # Validar carga
                        if img1 is None :
                            print(f"[WARN] No se pudo cargar {real_path} \n")
                            continue

                        if img2 is None :
                            print(f"[WARN] No se pudo cargar {gen_path} \n")
                            continue

                        # Escalar imagen
                        img1 = cv.resize(img1, (target_size, target_size))

                        # Configurar tamaño de entrada para el detector
                        detector.setInputSize((img1.shape[1], img1.shape[0]))
                        faces1 = detector.detect(img1)

                        # Validar detección
                        if faces1[1] is None:
                            print(f"[WARN] No se detectó rostro en {real_path}, image_real \n")
                            fail_writer.writerow([prueba_tipo, node, parameter, value, person, real_path, "real"])
                            '''cv.imshow("Imagen Real - Sin Rostro", img1)
                            cv.waitKey(0)
                            cv.destroyAllWindows()'''
                            continue

                        # Escalar imagen
                        img2 = cv.resize(img2, (target_size, target_size))

                        # Configurar tamaño de entrada para el detector
                        detector.setInputSize((img2.shape[1], img2.shape[0]))
                        faces2 = detector.detect(img2)

                        # Validar detección
                        if faces2[1] is None:
                            print(f"[WARN] No se detectó rostro en {gen_path}, image_generated \n")
                            fail_writer.writerow([prueba_tipo, node, parameter, value, person, gen_path, "generated"])
                            '''cv.imshow("Imagen Generada - Sin Rostro", img2)
                            cv.waitKey(0)
                            cv.destroyAllWindows()'''
                            continue

                        # Extraer características faciales
                        face1_align = recognizer.alignCrop(img1, faces1[1][0])
                        face2_align = recognizer.alignCrop(img2, faces2[1][0])
                        face1_feature = recognizer.feature(face1_align)
                        face2_feature = recognizer.feature(face2_align)

                        # Calcular similitudes
                        cosine_score = recognizer.match(face1_feature, face2_feature, cv.FaceRecognizerSF_FR_COSINE)
                        l2_score = recognizer.match(face1_feature, face2_feature, cv.FaceRecognizerSF_FR_NORM_L2)

                        # Decidir si son la misma identidad
                        cosine_similarity_threshold = 0.363
                        l2_similarity_threshold = 1.128
                        same_identity = cosine_score >= cosine_similarity_threshold and l2_score <= l2_similarity_threshold

                        # Escribir resultado en el CSV
                        writer.writerow([prueba_tipo, node, parameter, value, person, gen_path, real_path, round(cosine_score, 4), round(l2_score, 4), same_identity])






