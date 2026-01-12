import cv2  # biblioteca OpenCV
import numpy as np  # numpy para manipulacao de arrays
import json, time   # para salvar os dados de dimensao
import time

start = time.perf_counter()

camera_id = 1  # ID da camera usada
delay = 1  # delay entre frames na captura
window_name = 'OpenCV_QR_Code'  # nome da janela exibida

# nomes dos QR codes que sao esperados serem detectados nos 4 cantos
qr_alvo = {"canto_esquerdo_inf", "canto_esquerdo_sup", "canto_direito_inf", "canto_direito_sup"}
qr_detectados = {}  # espaço para salvar os QR detectados

qcd = cv2.QRCodeDetector()  # inicializa detector de QR
cap = cv2.VideoCapture(camera_id)  # inicia captura da câmera

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # define resolucao largura
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)  # define resolucao altura

imagem_final = None  # variavel pra guardar última imagem capturada

while True:
    ret, frame = cap.read()  # captura frame da câmera
    if not ret:
        print("Erro ao capturar imagem.")  # sai se falhar captura
        break

    imagem_final = frame.copy()  # copia frame para manipular depois

    ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)  # detecta multiplos QR

    if ret_qr:  # se detectou algum QR
        for dado, ponto in zip(decoded_info, points):
            if not dado:  # pula se dado vazio
                continue

            if dado in qr_alvo:  # se QR e um dos alvos
                qr_detectados[dado] = ponto  # salva contorno do QR

            # desenha contorno do QR e texto na imagem ao vivo
            frame = cv2.polylines(frame, [ponto.astype(int)], True, (0, 255, 0), 3)
            centro = tuple(ponto[0].astype(int))
            cv2.putText(frame, dado, centro, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # escreve quantos QR ja foram detectados
    cv2.putText(frame, f"Detectados: {len(qr_detectados)} / 4", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

    cv2.imshow(window_name, frame)  # mostra a imagem ao vivo

    if len(qr_detectados) == 4:  # quando todos 4 detectados sai do loop
        print("Todos os 4 QR codes foram detectados!")
        break

    if cv2.waitKey(delay) & 0xFF == ord('q'):  # espera a tecla 'q' ser pressionada para sair da janela
        break

cap.release()  # libera camera
cv2.destroyAllWindows()  # fecha janelas

# marca os pontos detectados na imagem final
for nome, contorno in qr_detectados.items():
    if "direito" in nome:
        ponto_ref = tuple(contorno[3].astype(int))  # QR direita: pega canto inferior esquerdo
    else:
        ponto_ref = tuple(contorno[2].astype(int))  # QR esquerda: pega canto inferior direito


cv2.imshow("Pontos Finais Detectados", imagem_final)  # mostra imagem com pontos
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite("img/imagem_completa_detectada.png", imagem_final)  # salva imagem marcada

# homografia

# define pontos origem (os 4 cantos) na ordem correta para homografia
pontos_origem = np.array([
    qr_detectados["canto_esquerdo_sup"][3].astype(np.float32),  # canto inferior direito
    qr_detectados["canto_direito_sup"][2].astype(np.float32),   # canto inferior esquerdo
    qr_detectados["canto_direito_inf"][1].astype(np.float32),   # canto inferior esquerdo
    qr_detectados["canto_esquerdo_inf"][0].astype(np.float32)   # canto inferior direito
], dtype=np.float32)

# define tamanho da imagem retificada (cálculo via Pitágoras a partir dos QR codes)
p_sup_esq = qr_detectados["canto_esquerdo_sup"][3].astype(np.float32)
p_sup_dir = qr_detectados["canto_direito_sup"][2].astype(np.float32)
p_inf_esq = qr_detectados["canto_esquerdo_inf"][0].astype(np.float32)
p_inf_dir = qr_detectados["canto_direito_inf"][1].astype(np.float32)

largura_sup = np.linalg.norm(p_sup_dir - p_sup_esq)
largura_inf = np.linalg.norm(p_inf_dir - p_inf_esq)
altura_esq = np.linalg.norm(p_inf_esq - p_sup_esq)
altura_dir = np.linalg.norm(p_inf_dir - p_sup_dir)

largura = int(max(largura_sup, largura_inf))
altura  = int(max(altura_esq, altura_dir))

# pontos destino: retângulo padrão para imagem retificada
pontos_destino = np.array([
    [0, 0],
    [largura - 1, 0],
    [largura - 1, altura - 1],
    [0, altura - 1]
], dtype=np.float32)
print(pontos_origem)

matriz_homografia = cv2.getPerspectiveTransform(pontos_origem, pontos_destino)  # calcula matriz
imagem_retificada = cv2.warpPerspective(imagem_final, matriz_homografia, (largura, altura))  # aplica homografia

end = time.perf_counter()
tempo_total = end - start
print(f"Tempo total do processamento: {tempo_total:.4f} s")

cv2.imshow("Imagem Retificada (Homografia)", imagem_retificada)  # mostra resultado
cv2.imwrite("img/imagem_referencia.png", imagem_retificada)  # salva resultado
cv2.waitKey(0)
cv2.destroyAllWindows()

dados = {
    "largura": int(largura),
    "altura": int(altura),
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "versao": 1
}
with open("dimensoes_placa.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)