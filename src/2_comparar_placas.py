import numpy as np
import matplotlib.pyplot as plt
from matplotlib.image import imread
from skimage.color import rgb2ycbcr
from scipy.ndimage import gaussian_filter
import cv2            
import json
import os


ref_fig_name = 'img/imagem_referencia.png'   # imagem de referencia

json_path = 'dimensoes_placa.json'  # arquivo JSON com dimensoes

test_rectified_path = 'img/imagem_teste_retificada.png'  # caminho para salvar a imagem de teste apos homografia

def capturar_e_retificar_imagem_teste(camera_id=1, window_name='OpenCV_QR_Code'):
    """
    Captura uma imagem da placa sob teste, detecta 4 QRs, 
    aplica homografia usando as dimensoes salvas no JSON
    e salva a imagem retificada em test_rectified_path.
    """
    # carrega dimensoes alvo do JSON
    if not os.path.exists(json_path):
        raise FileNotFoundError("Arquivo JSON de dimensoes nao encontrado: {}".format(json_path))
    with open(json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    largura = int(dados.get('largura', 0))
    altura  = int(dados.get('altura', 0))
    if largura <= 0 or altura <= 0:
        raise ValueError("Dimensoes invalidas no JSON (largura/altura).")

    
    cap = cv2.VideoCapture(camera_id)   # inicia camera
    # resolucao da imagem para captura
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

    qcd = cv2.QRCodeDetector()

    qr_alvo = {"canto_esquerdo_inf", "canto_esquerdo_sup",
               "canto_direito_inf", "canto_direito_sup"}
    qr_detectados = {}

    # loop simples ate detectar os 4 QRs ou tecla 'q'
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Falha na captura da camera.")
            break

        # detecta QRs
        ok, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
        if ok and points is not None:
            for dado, ponto in zip(decoded_info, points):
                if not dado:
                    continue
                if dado in qr_alvo:
                    qr_detectados[dado] = ponto  # contorno do QR
                # desenho para visualizacao ao vivo
                frame = cv2.polylines(frame, [ponto.astype(int)], True, (0, 255, 0), 2)
                centro = tuple(ponto[0].astype(int))
                cv2.putText(frame, dado, centro, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        cv2.putText(frame, f"Detectados: {len(qr_detectados)} / 4", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow(window_name, frame)

        if len(qr_detectados) == 4:
            print("4 QRs detectados. Prosseguindo para homografia...")
            imagem_final = frame.copy()
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            imagem_final = frame.copy()
            print("Saindo sem detectar todos QRs.")
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(qr_detectados) < 4:
        raise RuntimeError("Nao foi possivel detectar os 4 QRs para homografia.")

    # seleciona um ponto de referencia de cada QR para formar os 4 cantos
    p_esq_sup = qr_detectados["canto_esquerdo_sup"][3].astype(np.float32)  # canto inf dir do QR sup esq
    p_dir_sup = qr_detectados["canto_direito_sup"][2].astype(np.float32)   # canto inf esq do QR sup dir
    p_dir_inf = qr_detectados["canto_direito_inf"][1].astype(np.float32)   # canto sup esq do QR inf dir
    p_esq_inf = qr_detectados["canto_esquerdo_inf"][0].astype(np.float32)  # canto sup dir do QR inf esq

    pontos_origem = np.array([p_esq_sup, p_dir_sup, p_dir_inf, p_esq_inf], dtype=np.float32)

    # pontos destino com as dimensoes padronizadas lidas do JSON
    pontos_destino = np.array([
        [0, 0],
        [largura - 1, 0],
        [largura - 1, altura - 1],
        [0, altura - 1]
    ], dtype=np.float32)

    # calcula matriz e aplica homografia
    H = cv2.getPerspectiveTransform(pontos_origem, pontos_destino)
    img_retificada = cv2.warpPerspective(imagem_final, H, (largura, altura))

    # salva a imagem retificada para o processamento
    os.makedirs(os.path.dirname(test_rectified_path), exist_ok=True)
    cv2.imwrite(test_rectified_path, img_retificada[:, :, ::-1])  # BGR->RGB

    return test_rectified_path


# Executa captura + homografia antes do processamento
try:
    caminho_teste_retificada = capturar_e_retificar_imagem_teste(camera_id=1)
except Exception as e:
    raise SystemExit("Erro na captura/retificacao da imagem de teste: {}".format(e))


# carrega imagem de referencia
r = imread(ref_fig_name)
ryuv = rgb2ycbcr(r.astype(np.float64))

# carrega imagem de teste (retificada pela etapa acima)
t = imread(caminho_teste_retificada)
tyuv = rgb2ycbcr(t.astype(np.float64))

# Diferenca no canal Cr
prcs = np.absolute(gaussian_filter(ryuv[..., 2] - tyuv[..., 2], sigma=5))

plt.figure()

# Comparacao RGB
plt.subplot(1, 4, 1)
plt.imshow(np.concatenate((r, t), axis=1))
plt.title(f"{ref_fig_name}\n{os.path.basename(caminho_teste_retificada)}")
plt.axis('off')

# Comparacao do canal Cr
plt.subplot(1, 4, 2)
plt.imshow(np.uint8(np.concatenate((ryuv[..., 2], tyuv[..., 2]), axis=1)), cmap='gray')
plt.title("Canais Cr")
plt.axis('off')

# Mapa de diferencas suavizada do canal Cr
plt.subplot(1, 4, 3)
plt.imshow(prcs, cmap='viridis')
plt.title("Diferenca Cr suavizada")
plt.axis('equal')
plt.colorbar()

# Diferenca limiarizada
plt.subplot(1, 4, 4)
plt.imshow(prcs > 4, cmap='gray')
plt.title("Limiar > 4")
plt.axis('equal')

plt.show()