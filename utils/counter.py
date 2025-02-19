# Declaração de Bibliotecas
import cv2
import numpy as np
from .vehicle import Vehicle
import time
import csv

def preProc (img, ant, maskSize, backgroundSubtractor):
    """
    Parametros da Função
    Img:                  Imagem em escala de cinza
    Ant:                  Frame Anterior
    maskSize:             Tamanho(IMPAR) da mascara para filtro da mediana e rolagem
    backgroundSubtractor: cv2.createBackgroundSubtractorMOG2()
    """
    #Equalização de Histograma
    img = cv2.equalizeHist(img)
    
    # Remoção de Fundo
    img = backgroundSubtractor.apply(img)
    
    # Corte de Tons de Cinza maiores que 127
    # th = (img * (img < 128))/127
    _,th = cv2.threshold(img,45,255,cv2.THRESH_BINARY)
    
    # Remove Ruido aleatorio
    if ant.max() == 999:
        dimX = np.logical_and(np.roll(th,1,axis=1),np.roll(th,2,axis=1),np.roll(th,3,axis=1))
        dimY = np.logical_and(np.roll(th,1,axis=0),np.roll(th,2,axis=0),np.roll(th,3,axis=0))
        img1 = np.logical_and(th, dimX, dimY)
    else:
        ant[:,122] = 1
        o1 = np.logical_or(np.roll(ant,1,axis=1),np.roll(ant,2,axis=1),np.roll(ant,3,axis=1))
        o2 = np.logical_or(np.roll(ant,4,axis=1),np.roll(ant,5,axis=1),np.roll(ant,6,axis=1))
        o3 = np.logical_or(np.roll(ant,7,axis=1),np.roll(ant,8,axis=1),np.roll(ant,9,axis=1))
        img1 = np.logical_and(th, np.logical_or(np.logical_or(o1,o2,o3),np.logical_or(np.roll(ant,1,axis=0),np.roll(ant,2,axis=0),np.roll(ant,3,axis=0))))
    
    # Preenchimento de Falhas
    th = img1
    o1 = np.logical_or(np.roll(th,1,axis=1),np.roll(th,2,axis=1),np.roll(th,3,axis=1))
    o2 = np.logical_or(np.roll(th,4,axis=1),np.roll(th,5,axis=1),np.roll(th,6,axis=1))
    o3 = np.logical_or(np.roll(th,7,axis=1),np.roll(th,8,axis=1),np.roll(th,9,axis=1))
    img = np.logical_and(1 - th, np.logical_or(o1,o2,o3))
    img = np.logical_or(img, img1)    
    img = np.uint8(img*255)    
    
    # Filtro da mediana
    img = cv2.medianBlur(img,maskSize)
    
    # Retorna o Frame
    return np.uint8(img)

# Função Principal
def counter(filepath, videoname):
	# Variáveis para armazenar informações do vídeo e da contagem
	info = {}
	counting_info = {"media": [0, 0, 0], "pico": [0, 0, 0]}

	# Variáveis de Contagem
	cnt_min 	 = {"time": "", "total": 0, "pequeno": 0, "medio": 0, "grande": 0}
	cnt_min_rows = []

	cnt_total 	 = {"total": 0, "pequeno": 0, "medio": 0, "grande": 0}

	# Criando o objeto de VideoCapture
	video = cv2.VideoCapture(filepath + videoname)

	# Variáveis de Informação do Vídeo
	img_width = int(video.get(3))
	img_height = int(video.get(4))
	info["3_Resolução"] = "{0} x {1}".format(img_width, img_height)

	fps 		= int(video.get(5))
	duration 	= int(video.get(7) / video.get(5))
	info["5_Taxa de Quadros"] = "{0} FPS".format(fps)
	info["4_Duração"] = "{0}:{1}".format(duration // 60, duration % 60)

	frameArea = img_height*img_width
	areaTH = frameArea / 175

	print("########### VIDEO ###########")
	print("Dimensoes: {0}x{1}".format(img_width, img_height))
	print("Frames p/ Segundo: {0}".format(fps))
	print("Area Total: {0}".format(frameArea))
	print('Area de Threshold: {0}'.format(areaTH))
	print()

	# Linhas de Limite para Contagem
	line_left 		= int(30  * (img_width/100))
	line_right 		= int(95 * (img_width/100))
	line_up			= int(5  * (img_height/100))
	line_down		= int(60  * (img_height/100))

	line_center 	= int(line_left + (50 * ((line_right - line_left)/100)))
	
	print("###### LINHAS DE LIMITE ######")
	print("Região de Interesse (Linha Esquerda): {0}".format(line_left))
	print("Região de Interesse (Linha Cima): {0}".format(line_up))
	print("Região de Interesse (Linha Direita): {0}".format(line_right))
	print("Região de Interesse (Linha Baixo): {0}".format(line_down))
	
	print("Região de Interesse (Linha Central): {0}".format(line_center))
	print()

	# Define o Codec e Objeto de Escrita de Vídeo
	fourcc = cv2.VideoWriter_fourcc(*'VP80')
	out = cv2.VideoWriter(filepath + 'video_counted.webm', fourcc, 30.0, (img_width, img_height), 0)

	# Cria o objeto do extrator de fundo
	rfmg2 = cv2.createBackgroundSubtractorMOG2()

	# Variáveis auxiliares dos processamentos
	font = cv2.FONT_HERSHEY_SIMPLEX
	vehicles = []
	max_p_age = 5000
	pid = 1
	frame_id = 0
	lastTime = -1

	# Seleciona o frame inicial do vídeo
	# 220, 15100, 3800
	video.set(1, 1)

	########################
	## CONTAGEM POR FRAME ##
	########################
	(_, frame) = video.read()
	mask = np.ones(frame.shape[0:2])*999

	while(video.isOpened()):
		# Obtém um frame do arquivo de vídeo
		ret, frame = video.read()
		
		# Calcula a taxa de profundidades de bits, se ela ainda não tiver sido calculada
		if("6_Profundidade de Cores" not in info):
			info["6_Profundidade de Cores"] = "{0} bits/canal".format(int(np.log2(frame.max()+1)))

		# Verifica se o frame em questão é o último do vídeo
		if not ret:
			break;

		# Atualiza contador de frames e o segundo do vídeo
		frame_id += 1	
		frame_time = frame_id // fps

		###################
		## PREPROCESSING ##
		###################
		# Converte a imagem para preto e branco e realiza pré-processamento
		gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		mask = preProc(gray_image, mask, 11, rfmg2)
		
		##################
		## FIND CONTOUR ##
		##################
		# Extrai todos os Contours da imagem
		_, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

		# Para cada contour, iremos buscar um objeto de veículo que mais se assemelha ao contour
		# e verificamos se ele cruzou a linha central.
		for cnt in contours:

			# Calculamos a área do Contour para só considerar contours de tamanho adequado
			area = cv2.contourArea(cnt)
			if area > areaTH and area < 20000:
				################
				#   TRACKING   #
				################
				# Calculamos e exibimos o retângulo de segmentação desse contour
				M = cv2.moments(cnt)
				
				cx = int(M['m10']/M['m00'])
				cy = int(M['m01']/M['m00'])

				x, y, w, h = cv2.boundingRect(cnt)
				
				roi = gray_image[y:y+h, x:x+w]
	
				# Realizamos a busca por algum objeto de Vehicle que possua propriedades (posição e tamanho)
				# semelhante aos do contour que está sendo analisado
				new = True
				for i in vehicles:
					if abs(x - i.x) <= w and abs(y - i.y) <= h:
						new = False

						# Atualizamos as coordenadas do objeto com base nas coordenadas do Contour
						i.updateCoords(cx, cy, w, h)
						
						# Verificamos se o objeto cruzou a linha, e então incluimos na contagem adequada
						if i.crossed_line(line_center, line_down):
							size = i.getSize()
							if(size[0] >= 95 or size[1] >= 70):
								if(size[1] >= 65):
									print("{2} - CARRO GRANDE | MEDIA: {0} | ALTURA: {1} | LARGURA: {3}".format(size[0], h, frame_id, i.w))
									cnt_total["grande"] += 1
									cnt_min["grande"] += 1

								else:
									print("{2} - CARRO MEDIO* | MEDIA: {0} | ALTURA: {1} | LARGURA: {3}".format(size[0]/2, h, frame_id, i.w))
									print("{2} - CARRO MEDIO* | MEDIA: {0} | ALTURA: {1} | LARGURA: {3}".format(size[0]/2, h, frame_id, i.w))
									cnt_total["medio"] += 2
									cnt_total["total"] += 1

									cnt_min["medio"] += 2
									cnt_min["total"] += 1
									
							elif(size[0] >= 55):
								print("{2} - CARRO MEDIO | MEDIA: {0} | ALTURA: {1} | LARGURA: {3}".format(size[0], h, frame_id, i.w))
								cnt_total["medio"] += 1
								cnt_min["medio"] += 1

							elif(size[0] >= 20):
								print("{2} - MOTINHA | MEDIA: {0} | ALTURA: {1} | LARGURA: {3}".format(size[0], h, frame_id, i.w))
								cnt_total["pequeno"] += 1
								cnt_min["pequeno"] += 1

							if(size[0] >= 20):
								cnt_total["total"] += 1
								cnt_min["total"] += 1
						break

					# Caso o veículo possua estado '1' (cruzou a linha de chegada), apagamos esse objeto da lista
					# (Eĺe não poderá ser contado novamente e nem nos interessa).
					if i.state == '1' and i.x > line_center:
						i.setDone()
						index = vehicles.index(i)
						vehicles.pop(index)
						del i

				# Se nenhum objeto de Vehicle foi encontrado no passo anterior, criamos um novo objeto para
				# mantermos esse novo contour em observação.
				if new == True and cx >= line_left and cx <= line_right and cy <= line_down and cy >= line_up:
					p = Vehicle(pid, cx, cy, w, h, max_p_age)
					vehicles.append(p)
					pid += 1

				##################
				##   DRAWING    ##
				##################
				# Desenhamos o bounding-box sobre os contours identiicados
				cv2.circle(gray_image,(cx, cy), 4, (0,0,255), -1)
				cv2.rectangle(gray_image, (x,y), (x+w,y+h), (0,255,0), 2)

		###############
		##   IMAGE   ##
		###############
		# Incluimos algumas linhas de limites para analisar o vídeo
		frame = cv2.line(gray_image, (line_right, 0), (line_right, img_height), (255, 0, 0), 1)
		frame = cv2.line(gray_image, (line_left, 0), (line_left, img_height), (255, 0, 0), 1)
		frame = cv2.line(gray_image, (0, line_up), (img_width, line_up), (255, 0, 0), 1)
		frame = cv2.line(gray_image, (0, line_down), (img_width, line_down), (255, 0, 0), 1)

		frame = cv2.line(gray_image, (line_center, 0), (line_center, img_height), (255, 0, 0), 2)

		# Exibimos o frame atual da contagem na janela
		# cv2.imshow('Frame', cv2.resize(gray_image, (400, 300)))

		# Salva a imagem em um arquivo
		if(frame_time % 30 == 0 and frame_time != lastTime):
			lastTime = frame_time

			actualTime = "{0:02d}:{1:02d}".format(frame_time // 60, frame_time % 60)
			cnt_min_rows.append([actualTime, cnt_min["pequeno"], cnt_min["medio"], cnt_min["grande"]])

			for i, d in enumerate(["pequeno", "medio", "grande"]):
				counting_info["pico"][i] = max(counting_info["pico"][i], cnt_min[d])

			cnt_min = {"total": 0, "pequeno": 0, "medio": 0, "grande": 0}

		out.write(gray_image)

		# Pausa e Verificação da Tecla de Saída (ESC ou Q)
		k = cv2.waitKey(1) & 0xff
		if k == 27:
			break

	# Finalização do Processo de Renderização
	video.release()
	out.release()
	cv2.destroyAllWindows()

	print("########### RESULTADO FINAL ###########")
	print("Total: {0}".format(cnt_total["total"]))
	print("Grandes: {0}".format(cnt_total["grande"]))
	print("Médios: {0}".format(cnt_total["medio"]))
	print("Pequenos: {0}".format(cnt_total["pequeno"]))

	# Salva os dados de contagem 
	with open(filepath + 'counting.csv', 'w', newline='') as fp:
		csv.writer(fp, lineterminator='\n').writerow(["time", "pequeno", "medio", "grande"])
		csv.writer(fp, lineterminator='\n').writerows(cnt_min_rows)

	# Cria o Dicionário com Informações de Contagem
	counting_info["results"] = [cnt_total["pequeno"], cnt_total["medio"], cnt_total["grande"]]
	for i,d in enumerate(["pequeno", "medio", "grande"]):
		counting_info["media"][i] = round(cnt_total[d] / (duration // 60), 2)

	return (info, counting_info)

if __name__ == "__main__":
	counter("../static/data/01/", "video.avi")